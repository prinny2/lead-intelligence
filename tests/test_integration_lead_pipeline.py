"""
Teste de integração: fluxo completo do toolkit lead_intelligence (sem API/LLM).
Garante que qualify_lead devolve o contrato esperado ponta a ponta.
"""

from __future__ import annotations

import pytest

from lead_intelligence.qualifier import qualify_lead


def test_integration_qualify_strong_lead_full_shape() -> None:
    lead = {
        "name": "Ana Costa",
        "company": "Indústria Verde Ltda",
        "email": "ana@industriaverde.com.br",
        "phone": "11988776655",
        "title": "Diretora",
        "city": "São Paulo",
        "state": "SP",
        "monthly_bill": 1200,
        "property_type": "comercial",
        "ownership_status": "owned",
        "interest_message": "Preciso de orçamento para sistema solar no telhado.",
    }
    out = qualify_lead(lead)

    assert out["name"] == lead["name"]
    assert "analysis" in out
    assert out["analysis"]["has_valid_contact_channel"] is True
    assert out["analysis"]["critically_incomplete"] is False

    assert "score" in out and isinstance(out["score"], int)
    assert 0 <= out["score"] <= 100

    assert out["decision"] in ("accept", "review", "reject")
    assert isinstance(out["reasons"], list) and len(out["reasons"]) >= 1

    assert "solar" in out and "signals" in out["solar"] and "reasons" in out["solar"]
    assert "interest_signals" in out
    assert out["interest_signals"]["quote_request"] is True


def test_integration_weak_lead_rejected_or_review() -> None:
    out = qualify_lead(
        {
            "name": "Pedro",
            "city": "Belém",
            "monthly_bill": 120,
            "property_type": "apartamento",
            "goal": "Só queria entender como funciona energia solar",
        }
    )
    assert out["decision"] == "reject"
    assert out["score"] <= 25
    assert out["analysis"]["critically_incomplete"] is True


def test_integration_invalid_lead_raises() -> None:
    with pytest.raises(TypeError):
        qualify_lead(None)  # type: ignore[arg-type]
