"""Tests for lead_intelligence.message_analysis."""

from lead_intelligence.message_analysis import analyze_interest_message


def test_curiosity():
    sig = analyze_interest_message("Só queria entender como funciona")
    assert sig["curiosity_only"] is True


def test_quote_request():
    sig = analyze_interest_message("Gostaria de um orçamento para placas")
    assert sig["quote_request"] is True


def test_empty():
    sig = analyze_interest_message("")
    assert not any(sig.values())
