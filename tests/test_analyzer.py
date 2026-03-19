"""Tests for the analyzer module."""

import pytest

from lead_intelligence.analyzer import analyze_lead, _calculate_completeness


class TestAnalyzeLead:
    def test_full_lead(self):
        lead = {"name": "Alice", "email": "alice@example.com", "company": "Acme"}
        result = analyze_lead(lead)
        assert result["analysis"]["has_email"] is True
        assert result["analysis"]["has_company"] is True
        assert result["analysis"]["completeness"] == 1.0
        assert result["analysis"]["valid_email"] is True
        assert result["analysis"]["has_valid_contact_channel"] is True
        assert result["analysis"]["critically_incomplete"] is False

    def test_partial_lead(self):
        lead = {"name": "Bob"}
        result = analyze_lead(lead)
        assert result["analysis"]["has_email"] is False
        assert result["analysis"]["completeness"] == 0.33
        assert result["analysis"]["critically_incomplete"] is True

    def test_empty_lead(self):
        result = analyze_lead({})
        assert result["analysis"]["completeness"] == 0.0
        assert result["analysis"]["critically_incomplete"] is True

    def test_invalid_input(self):
        with pytest.raises(TypeError):
            analyze_lead("not a dict")


class TestCalculateCompleteness:
    def test_all_fields(self):
        lead = {"name": "A", "email": "a@b.com", "company": "C"}
        assert _calculate_completeness(lead) == 1.0

    def test_no_fields(self):
        assert _calculate_completeness({}) == 0.0
