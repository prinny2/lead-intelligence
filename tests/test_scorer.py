"""Tests for the scorer module."""

import pytest

from lead_intelligence.scorer import score_lead


class TestScoreLead:
    def test_full_lead(self):
        lead = {
            "name": "Alice",
            "email": "alice@example.com",
            "company": "Acme",
            "phone": "555-0100",
            "title": "CTO",
        }
        assert score_lead(lead) == 100

    def test_empty_lead(self):
        assert score_lead({}) == 0

    def test_email_only(self):
        assert score_lead({"email": "a@b.com"}) == 30

    def test_invalid_input(self):
        with pytest.raises(TypeError):
            score_lead("not a dict")

    def test_score_capped_at_100(self):
        lead = {
            "name": "A",
            "email": "a@b.com",
            "company": "C",
            "phone": "123",
            "title": "T",
        }
        assert score_lead(lead) <= 100
