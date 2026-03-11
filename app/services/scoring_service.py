"""Hybrid scoring: AI output + rule-based adjustments. Deterministic and simple."""

import logging
from dataclasses import dataclass
from typing import Any

from app.models import DEFAULT_URGENCY, LeadRequest, LeadResponse, SCORE_MAX, SCORE_MIN, VALID_URGENCIES

logger = logging.getLogger("lead_intelligence")

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
URGENCY_GOAL_WORDS = ("reduzir conta", "urgente", "quero agora", "o mais rápido", "reduzir custo")
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


def _normalize_urgency(raw: str | None) -> str:
    if not raw:
        return DEFAULT_URGENCY
    u = (raw or "").strip().lower()
    return u if u in VALID_URGENCIES else DEFAULT_URGENCY


# Recommendation by score band so output matches strength
RECOMMENDATION_BY_SCORE = {
    "low": "Lead em fase de pesquisa; enviar material educativo e acompanhar depois.",
    "mid": "Interesse moderado; fazer follow-up em 1–2 semanas.",
    "high": "Lead promissor; vale contato comercial rápido.",
}


def _recommendation_for_score(score: int, ai_recommendation: str) -> str:
    """Pick recommendation consistent with final score band (0–3 / 4–6 / 7–10)."""
    if score <= 3:
        return RECOMMENDATION_BY_SCORE["low"]
    if score <= 6:
        return RECOMMENDATION_BY_SCORE["mid"]
    if score >= 7:
        return RECOMMENDATION_BY_SCORE["high"]
    return ai_recommendation or DEFAULT_RECOMMENDATION


@dataclass
class HybridResult:
    response: LeadResponse
    ai_raw_score: int | None
    rule_delta: int


def hybrid_score(lead: LeadRequest, ai_output: dict[str, Any] | None) -> HybridResult:
    """
    Build LeadResponse from AI + rules. Returns result plus ai_raw_score and rule_delta for storage.
    """
    property_normalized = _normalize_property_type(lead.property_type)

    if ai_output is not None:
        try:
            ai_raw = int(ai_output.get("score", DEFAULT_SCORE))
            base = max(SCORE_MIN, min(SCORE_MAX, ai_raw))
        except (TypeError, ValueError):
            base = DEFAULT_SCORE
            ai_raw = None
        recommendation = (ai_output.get("recommendation") or "").strip() or DEFAULT_RECOMMENDATION
        urgency_raw = ai_output.get("urgency")
    else:
        base = DEFAULT_SCORE
        ai_raw = None
        recommendation = DEFAULT_RECOMMENDATION
        urgency_raw = None

    delta = _rule_adjustment(lead, property_normalized)
    score = max(SCORE_MIN, min(SCORE_MAX, base + delta))

    urgency = _normalize_urgency(urgency_raw)
    if score <= 3:
        urgency = "baixa"
    if urgency_raw and urgency_raw.strip().lower() not in VALID_URGENCIES:
        logger.warning("invalid_urgency value=%s fallback=%s", urgency_raw, urgency)

    recommendation = _recommendation_for_score(score, recommendation)

    return HybridResult(
        response=LeadResponse(score=score, urgency=urgency, recommendation=recommendation),
        ai_raw_score=ai_raw,
        rule_delta=delta,
    )
