"""Commercial qualification: accept / review / reject with explainable reasons."""

from __future__ import annotations

from typing import Any, Literal

from lead_intelligence.analyzer import analyze_lead
from lead_intelligence.message_analysis import analyze_interest_message
from lead_intelligence.scorer import score_lead
from lead_intelligence.solar import solar_insights

Decision = Literal["accept", "review", "reject"]


def qualify_lead(lead: dict) -> dict[str, Any]:
    """Run analysis, scoring, niche heuristics, and return a decision.

    Output keys:
        - Spread of original lead fields (shallow copy semantics via analyze_lead)
        - ``analysis``, ``score``, ``decision``, ``reasons``
        - ``solar``: output of :func:`solar_insights`
        - ``interest_signals``: output of :func:`analyze_interest_message`
    """
    if not isinstance(lead, dict):
        raise TypeError("lead must be a dictionary")

    enriched = analyze_lead(lead)
    analysis = enriched["analysis"]
    score = score_lead(lead)

    solar = solar_insights(lead)
    interest_text = lead.get("interest_message")
    interest_signals = analyze_interest_message(interest_text if isinstance(interest_text, str) else None)

    decision, reasons = _decide(analysis, score, solar, interest_signals)

    # Build response: original keys + analysis block + meta
    out = {**enriched, "score": score, "decision": decision, "reasons": reasons}
    out["solar"] = solar
    out["interest_signals"] = interest_signals
    return out


def _decide(
    analysis: dict[str, Any],
    score: int,
    solar: dict[str, Any],
    interest_signals: dict[str, bool],
) -> tuple[Decision, list[str]]:
    reasons: list[str] = []

    if analysis["critically_incomplete"]:
        reasons.append("Lead criticamente incompleto (contato inválido ou identificação insuficiente).")
        return "reject", reasons

    if not analysis["has_valid_contact_channel"]:
        reasons.append("Sem canal de contato válido (e-mail ou telefone).")
        return "reject", reasons

    if score <= 32:
        reasons.append(f"Score muito baixo ({score}/100).")
        return "reject", reasons

    # Solar / message nudges
    for r in solar.get("reasons", []):
        if "alugado" in r.lower() or "Apartamento" in r:
            reasons.append(r)

    if interest_signals.get("curiosity_only"):
        reasons.append("Mensagem sugere apenas curiosidade — priorizar educação, não fechamento.")

    if interest_signals.get("urgent_intent") or interest_signals.get("quote_request"):
        reasons.append("Mensagem indica urgência ou pedido de orçamento.")

    completeness = float(analysis.get("completeness", 0.0))

    strong_fit = (
        score >= 72
        and completeness >= 0.67
        and not analysis["generic_email_domain"]
    )
    weak_fit = score < 55 or completeness < 0.34 or analysis["generic_email_domain"]

    if strong_fit and not interest_signals.get("curiosity_only"):
        reasons.append("Contato válido, dados sólidos e score alto — priorizar contato comercial.")
        return "accept", reasons

    if strong_fit and interest_signals.get("curiosity_only"):
        reasons.append("Dados bons, mas intenção ainda exploratória — tratar como oportunidade com nutrição.")
        return "review", reasons

    if weak_fit:
        reasons.append("Dados ou score intermediários — validar fit e coletar campos faltantes.")
        return "review", reasons

    reasons.append("Perfil razoável — revisar mensagem e dados antes de priorizar fila comercial.")
    return "review", reasons
