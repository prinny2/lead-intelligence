"""Tests for the scorer module."""

import pytest

from lead_intelligence.scorer import score_lead


class TestScoreLead:
    def test_full_lead(self):
        lead = {
            "name": "Alice",
            "email": "alice@acme.com",
            "company": "Acme",
            "phone": "11987654321",
            "title": "CTO",
        }
        assert score_lead(lead) == 100

    def test_empty_lead(self):
        assert score_lead({}) <= 25
        assert score_lead({}) >= 0

    def test_critically_incomplete_score_never_negative(self):
        assert score_lead({}) >= 0
        assert score_lead({"email": "not-an-email", "name": "X"}) >= 0

    def test_corporate_email_only_insufficient_identity(self):
        # Valid contact but no name/company → critical → capped
        assert score_lead({"email": "solo@acme.com"}) <= 25

    def test_invalid_input(self):
        with pytest.raises(TypeError):
            score_lead("not a dict")

    def test_score_capped_at_100(self):
        lead = {
            "name": "A",
            "email": "a@acme.com",
            "company": "C",
            "phone": "11987654321",
            "title": "T",
        }
        assert score_lead(lead) <= 100

    def test_generic_email_penalty(self):
        base = {
            "name": "A",
            "company": "C",
            "email": "a@gmail.com",
            "phone": "11987654321",
        }
        corporate = {**base, "email": "a@acme.com"}
        assert score_lead(base) < score_lead(corporate)
