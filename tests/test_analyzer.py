"""Tests for the analyzer module."""

from lead_intelligence.analyzer import analyze_lead, _calculate_completeness


class TestAnalyzeLead:
    def test_full_lead(self):
        lead = {"name": "Alice", "email": "alice@example.com", "company": "Acme"}
        result = analyze_lead(lead)
        assert result["analysis"]["has_email"] is True
        assert result["analysis"]["has_company"] is True
        assert result["analysis"]["completeness"] == 1.0

    def test_partial_lead(self):
        lead = {"name": "Bob"}
        result = analyze_lead(lead)
        assert result["analysis"]["has_email"] is False
        assert result["analysis"]["completeness"] == 0.33

    def test_empty_lead(self):
        result = analyze_lead({})
        assert result["analysis"]["completeness"] == 0.0

    def test_invalid_input(self):
        try:
            analyze_lead("not a dict")
            assert False, "Should have raised TypeError"
        except TypeError:
            pass


class TestCalculateCompleteness:
    def test_all_fields(self):
        lead = {"name": "A", "email": "a@b.com", "company": "C"}
        assert _calculate_completeness(lead) == 1.0

    def test_no_fields(self):
        assert _calculate_completeness({}) == 0.0
