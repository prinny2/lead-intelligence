"""Tests for lead_intelligence.validator."""

import pytest

from lead_intelligence.validator import (
    has_valid_contact_channel,
    is_critically_incomplete,
    is_generic_email_domain,
    is_valid_email,
    is_valid_phone,
)


class TestIsValidEmail:
    def test_valid(self):
        assert is_valid_email("a@b.co") is True
        assert is_valid_email("  user@example.com  ") is True

    def test_invalid(self):
        assert is_valid_email(None) is False
        assert is_valid_email("") is False
        assert is_valid_email("not-an-email") is False
        assert is_valid_email("@nodomain.com") is False


class TestIsValidPhone:
    def test_valid_br_style(self):
        assert is_valid_phone("(11) 98765-4321") is True
        assert is_valid_phone("+55 11 987654321") is True

    def test_invalid(self):
        assert is_valid_phone(None) is False
        assert is_valid_phone("123") is False


class TestGenericDomain:
    def test_gmail(self):
        assert is_generic_email_domain("x@gmail.com") is True

    def test_corporate(self):
        assert is_generic_email_domain("x@acme.com") is False


class TestContactChannel:
    def test_email_only(self):
        assert has_valid_contact_channel({"email": "a@b.co"}) is True

    def test_phone_only(self):
        assert has_valid_contact_channel({"phone": "11987654321"}) is True

    def test_none(self):
        assert has_valid_contact_channel({}) is False


class TestCriticallyIncomplete:
    def test_no_contact(self):
        assert is_critically_incomplete({"name": "A"}) is True

    def test_junk_email(self):
        assert is_critically_incomplete({"name": "A", "email": "bad"}) is True

    def test_ok_minimal(self):
        assert is_critically_incomplete({"name": "A", "email": "a@corp.com"}) is False
