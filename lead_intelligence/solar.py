"""Brazil solar niche heuristics — optional layer for qualifiers (no APIs)."""

from __future__ import annotations

from typing import Any

# Minimum monthly bill (BRL) to consider economically interesting for residential solar
DEFAULT_MIN_MONTHLY_BILL = 250.0


def solar_insights(lead: dict, *, min_monthly_bill: float = DEFAULT_MIN_MONTHLY_BILL) -> dict[str, Any]:
    """Return deterministic signals and human-readable reasons for solar fit.

    Reads optional keys: city, state, monthly_bill, property_type,
    ownership_status, interest_message. Missing keys are ignored.

    Returns:
        dict with keys: ``signals`` (bool flags), ``reasons`` (list of str).
    """
    if not isinstance(lead, dict):
        return {"signals": {}, "reasons": ["Lead inválido (não é dict)."]}

    signals: dict[str, bool] = {}
    reasons: list[str] = []

    ownership = _norm(lead.get("ownership_status"))
    if ownership == "owned":
        signals["owned_property"] = True
        reasons.append("Imóvel próprio — melhor aderência típica para solar.")
    elif ownership == "rented":
        signals["rented_property"] = True
        reasons.append("Imóvel alugado — pode exigir análise de viabilidade/contrato.")

    bill = _to_float(lead.get("monthly_bill"))
    if bill is not None:
        if bill >= min_monthly_bill:
            signals["strong_bill_signal"] = True
            reasons.append(f"Conta de luz relevante (>= R$ {min_monthly_bill:.0f}).")
        else:
            signals["low_bill_signal"] = True
            reasons.append(f"Conta de luz baixa (< R$ {min_monthly_bill:.0f}) — economia pode ser limitada.")

    ptype = _norm(lead.get("property_type"))
    if ptype in {"casa", "house", "residencial"}:
        signals["residential_house"] = True
    elif ptype in {"apartamento", "apto", "ap"}:
        signals["apartment"] = True
        reasons.append("Apartamento — checar área comum / permissão do condomínio.")

    city = _norm(lead.get("city"))
    state = _norm(lead.get("state"))
    if city or state:
        signals["location_present"] = True

    return {"signals": signals, "reasons": reasons}


def _norm(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
