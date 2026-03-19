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


def test_urgent_intent_accented_phrase_normalized():
    """User types 'rápido'; haystack is accent-free — must match 'o mais rapido' keyword."""
    sig = analyze_interest_message("Preciso o mais rápido possível")
    assert sig["urgent_intent"] is True


def test_urgent_intent_already_unaccented():
    sig = analyze_interest_message("quero o mais rapido")
    assert sig["urgent_intent"] is True
