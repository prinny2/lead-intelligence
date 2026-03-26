"""Tests for lead_intelligence.qualifier."""

import pytest

from lead_intelligence.qualifier import qualify_lead


def test_reject_critically_incomplete():
    out = qualify_lead({"name": "X"})
    assert out["decision"] == "reject"
    assert any("crític" in r.lower() or "critica" in r.lower() for r in out["reasons"])


def test_reject_low_score():
    out = qualify_lead(
        {
            "name": "A",
            "company": "B",
            "email": "bad-email",
            "phone": "123",
        }
    )
    assert out["decision"] == "reject"


def test_accept_strong_lead():
    out = qualify_lead(
        {
            "name": "Maria",
            "company": "Solar SA",
            "email": "maria@solarsa.com.br",
            "phone": "11987654321",
            "title": "Diretora",
            "monthly_bill": 800,
            "ownership_status": "owned",
        }
    )
    assert out["decision"] == "accept"
    assert out["score"] >= 72


def test_review_curiosity_message():
    out = qualify_lead(
        {
            "name": "Pedro",
            "company": "Pedro ME",
            "email": "pedro@empresa.com.br",
            "phone": "21999887766",
            "interest_message": "Só queria entender como funciona energia solar",
        }
    )
    assert out["decision"] in {"review", "accept"}
    assert out["interest_signals"]["curiosity_only"] is True


def test_invalid_lead_type():
    with pytest.raises(TypeError):
        qualify_lead("nope")
