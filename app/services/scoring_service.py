"""Hybrid scoring: AI output + rule-based adjustments. Deterministic and simple."""

import logging
from dataclasses import dataclass
from typing import Any

from app.models import DEFAULT_URGENCY, LeadRequest, LeadResponse, SCORE_MAX, SCORE_MIN, ScoreFactor, VALID_URGENCIES
from app.services.recommendation_builder import build_sales_recommendation
from app.services.whatsapp_builder import build_whatsapp_message
from lead_intelligence.qualifier import qualify_lead as _qualify_lead

logger = logging.getLogger("lead_intelligence")


def get_ai_qualification_with_solar(lead: LeadRequest) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """
    Run solar enrichment then AI qualification (Gemini → Anthropic fallback).
    Returns (ai_output, solar_context). Either can be None.
    """
    solar_context: dict[str, Any] | None = None
    try:
        from app.services.solar_enrichment_service import enrich_lead_solar
        solar_context = enrich_lead_solar(lead.city, lead.state, lead.monthly_bill)
    except Exception as e:
        logger.debug("solar_enrichment_skipped error=%s", e)

    # Try Gemini first
    ai_output: dict[str, Any] | None = None
    try:
        from app.services.gemini_service import get_gemini_qualification
        ai_output = get_gemini_qualification(lead, solar_context)
    except Exception as e:
        logger.debug("gemini_skipped error=%s", e)

    # Fall back to Anthropic
    if ai_output is None:
        try:
            from app.services.ai_service import get_ai_qualification
            ai_output = get_ai_qualification(lead)
        except Exception as e:
            logger.debug("anthropic_skipped error=%s", e)

    return ai_output, solar_context

DEFAULT_SCORE = 5
DEFAULT_RECOMMENDATION = "Análise indisponível; tente novamente."

# Canonical property types for rules and storage consistency
PROPERTY_TYPE_MAP = {
    "apartamento": "apartamento",
    "apto": "apartamento",
    "ap": "apartamento",
    "casa": "casa",
    "residencial": "casa",
    "comercial": "comercial",
    "empresa": "comercial",
    "industria": "comercial",
}
URGENCY_GOAL_WORDS = (
    "reduzir conta",
    "urgente",
    "quero agora",
    "o mais rápido",
    "o mais rapido",
    "reduzir custo",
)
# Curiosity / early research → negative adjustment so weak leads score 1–3
LOW_INTENT_GOAL_WORDS = (
    "só quero saber", "apenas curiosidade", "talvez", "não sei", "só pesquisando", "só olhando",
    "só queria entender", "queria entender", "como funciona", "pesquisando", "mais pra frente",
    "só cotação", "queria saber", "só tirar dúvida", "apenas informação", "só informar",
)


def _normalize_property_type(raw: str | None) -> str:
    """Map common variants to canonical property_type."""
    if not raw or not raw.strip():
        return "outro"
    key = raw.strip().lower()
    return PROPERTY_TYPE_MAP.get(key, key)


def _rule_adjustment(lead: LeadRequest, property_normalized: str) -> int:
    """Deterministic delta from rules. Stronger penalties for weak solar leads."""
    delta = 0
    if lead.monthly_bill > 700:
        delta += 2
    elif lead.monthly_bill < 200:
        delta -= 3  # stronger penalty for very low bill
    if property_normalized == "apartamento":
        delta -= 2
    goal_lower = (lead.goal or "").lower()
    if any(w in goal_lower for w in URGENCY_GOAL_WORDS):
        delta += 1
    if any(w in goal_lower for w in LOW_INTENT_GOAL_WORDS):
        delta -= 3  # stronger penalty for curiosity wording
    return delta


def _build_breakdown(
    lead: LeadRequest,
    property_normalized: str,
    ai_raw: int | None,
    solar_context: dict[str, Any] | None,
) -> list[ScoreFactor]:
    """Return list of ScoreFactor explaining every point in the final score."""
    factors: list[ScoreFactor] = []

    # 1. AI base
    base = ai_raw if ai_raw is not None else DEFAULT_SCORE
    factors.append(ScoreFactor(
        factor="ai_base",
        label="Análise de contexto",
        impact=0,
        description=f"Pontuação base da IA: {base}/10",
        icon="🤖",
    ))

    # 2. Bill
    bill = lead.monthly_bill
    if bill > 700:
        factors.append(ScoreFactor(factor="bill", label="Conta de luz", impact=2,
            description=f"R${bill:.0f}/mês — muito alto, ótimo retorno solar", icon="⚡"))
    elif bill >= 400:
        factors.append(ScoreFactor(factor="bill", label="Conta de luz", impact=0,
            description=f"R${bill:.0f}/mês — dentro do perfil solar", icon="⚡"))
    elif bill >= 200:
        factors.append(ScoreFactor(factor="bill", label="Conta de luz", impact=0,
            description=f"R${bill:.0f}/mês — razoável, payback mais longo", icon="⚡"))
    else:
        factors.append(ScoreFactor(factor="bill", label="Conta de luz", impact=-3,
            description=f"R${bill:.0f}/mês — baixo, solar pode não se pagar", icon="⚡"))

    # 3. Property
    if property_normalized == "apartamento":
        factors.append(ScoreFactor(factor="property", label="Tipo de imóvel", impact=-2,
            description="Apartamento — instalação limitada ou inviável", icon="🏢"))
    elif property_normalized == "casa":
        factors.append(ScoreFactor(factor="property", label="Tipo de imóvel", impact=0,
            description="Casa — instalação viável no telhado", icon="🏠"))
    elif property_normalized == "comercial":
        factors.append(ScoreFactor(factor="property", label="Tipo de imóvel", impact=0,
            description="Comercial — alto potencial de consumo", icon="🏭"))
    else:
        factors.append(ScoreFactor(factor="property", label="Tipo de imóvel", impact=0,
            description="Tipo não especificado — verificar na abordagem", icon="🏠"))

    # 4. Goal / urgency signal
    goal_lower = (lead.goal or "").lower()
    if any(w in goal_lower for w in URGENCY_GOAL_WORDS):
        factors.append(ScoreFactor(factor="goal", label="Intenção de compra", impact=1,
            description="Objetivo indica urgência: compra próxima", icon="🎯"))
    elif any(w in goal_lower for w in LOW_INTENT_GOAL_WORDS):
        factors.append(ScoreFactor(factor="goal", label="Intenção de compra", impact=-3,
            description="Objetivo indica curiosidade, sem decisão de compra", icon="🎯"))
    else:
        factors.append(ScoreFactor(factor="goal", label="Intenção de compra", impact=0,
            description="Objetivo neutro — confirmar na abordagem", icon="🎯"))

    # 5. Solar potential
    if solar_context:
        payback = solar_context.get("estimated_payback_years", 0)
        savings = solar_context.get("monthly_savings_estimate", 0)
        sunshine = solar_context.get("sunshine_hours", 0)
        if 0 < payback <= 5:
            factors.append(ScoreFactor(factor="solar", label="Potencial solar", impact=1,
                description=f"Payback {payback:.1f} anos em {lead.city} ({sunshine:.0f}h sol/ano) — excelente",
                icon="☀️"))
        elif payback <= 10:
            factors.append(ScoreFactor(factor="solar", label="Potencial solar", impact=0,
                description=f"Payback {payback:.1f} anos — razoável para a região",
                icon="☀️"))
        else:
            factors.append(ScoreFactor(factor="solar", label="Potencial solar", impact=-1,
                description=f"Payback {payback:.1f} anos — longo, abordagem mais cuidadosa",
                icon="☀️"))
        if savings > 0:
            factors[-1].description += f" | Economia est. R${savings:.0f}/mês"

    return factors


def _normalize_urgency(raw: str | None) -> str:
    if not raw:
        return DEFAULT_URGENCY
    u = (raw or "").strip().lower()
    return u if u in VALID_URGENCIES else DEFAULT_URGENCY


def _ai_recommendation_snippet(raw: str, *, max_len: int = 520) -> str | None:
    """Texto da IA utilizável; None se vazio, curto demais ou igual ao fallback de erro."""
    t = (raw or "").strip()
    if not t or t == DEFAULT_RECOMMENDATION:
        return None
    if len(t) < 10:
        return None
    if len(t) > max_len:
        cut = t[:max_len].rsplit(" ", 1)[0]
        t = cut + "…" if cut else t[:max_len] + "…"
    return t


def _recommendation_for_score(
    score: int,
    ai_recommendation: str,
    urgency: str,
    lead: LeadRequest,
    property_normalized: str,
) -> str:
    """
    Faixa baixa: só fallback (a IA pode sugerir ação agressiva incompatível com o score final).
    Faixa média/alta: usa só a recomendação da IA quando houver texto útil; senão fallback comercial.
    """
    if score <= 3:
        return build_sales_recommendation(lead, score, urgency, property_normalized)

    snippet = _ai_recommendation_snippet(ai_recommendation)
    if snippet:
        return snippet

    return build_sales_recommendation(lead, score, urgency, property_normalized)


@dataclass
class HybridResult:
    response: LeadResponse
    ai_raw_score: int | None
    rule_delta: int


def hybrid_score(
    lead: LeadRequest,
    ai_output: dict[str, Any] | None,
    solar_context: dict[str, Any] | None = None,
) -> HybridResult:
    """
    Build LeadResponse from AI + rules + solar data.
    Returns result plus ai_raw_score and rule_delta for storage.
    """
    property_normalized = _normalize_property_type(lead.property_type)

    if ai_output is not None:
        try:
            ai_raw = int(ai_output.get("score", DEFAULT_SCORE))
            base = max(SCORE_MIN, min(SCORE_MAX, ai_raw))
        except (TypeError, ValueError):
            base = DEFAULT_SCORE
            ai_raw = None
        recommendation = (ai_output.get("recommendation")
                          or "").strip() or DEFAULT_RECOMMENDATION
        urgency_raw = ai_output.get("urgency")
    else:
        base = DEFAULT_SCORE
        ai_raw = None
        recommendation = DEFAULT_RECOMMENDATION
        urgency_raw = None

    delta = _rule_adjustment(lead, property_normalized)

    # Solar bonus/penalty: great payback → +1, very poor → -1
    if solar_context:
        payback = solar_context.get("estimated_payback_years", 0)
        if 0 < payback <= 5:
            delta += 1
        elif payback > 15:
            delta -= 1

    score = max(SCORE_MIN, min(SCORE_MAX, base + delta))

    urgency = _normalize_urgency(urgency_raw)
    if score <= 3:
        urgency = "baixa"
    elif score >= 9 and urgency == "baixa":
        # Score forte com urgência inconsistente da IA → pelo menos média
        urgency = "media"
    if urgency_raw and urgency_raw.strip().lower() not in VALID_URGENCIES:
        logger.warning("invalid_urgency value=%s fallback=%s",
                       urgency_raw, urgency)

    recommendation = _recommendation_for_score(
        score,
        recommendation,
        urgency,
        lead,
        property_normalized,
    )

    # Run toolkit qualifier as an additional signal (never breaks the response)
    qualifier_decision = None
    qualifier_reasons = None
    try:
        lead_dict = lead.model_dump(exclude_none=True)
        qual_out = _qualify_lead(lead_dict)
        qualifier_decision = qual_out.get("decision")
        qualifier_reasons = qual_out.get("reasons")
    except Exception as e:
        logger.warning("qualifier_failed error=%s", str(e))

    whatsapp_message = build_whatsapp_message(lead, score, urgency)

    breakdown = _build_breakdown(lead, property_normalized, ai_raw, solar_context)

    return HybridResult(
        response=LeadResponse(
            score=score,
            urgency=urgency,
            recommendation=recommendation,
            whatsapp_message=whatsapp_message,
            decision=qualifier_decision,
            qualifier_reasons=qualifier_reasons,
            score_breakdown=breakdown,
        ),
        ai_raw_score=ai_raw,
        rule_delta=delta,
    )
