"""Validation helpers for lead contact data (no external APIs)."""

from __future__ import annotations

import re

# Minimal email pattern: local@domain with a dot in domain
_EMAIL_RE = re.compile(
    r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$",
)

# Digits only for phone length checks (after stripping common separators)
_PHONE_DIGITS_RE = re.compile(r"\d")

# Common consumer / free email providers (lowercase)
_GENERIC_EMAIL_DOMAINS: frozenset[str] = frozenset(
    {
        "gmail.com",
        "googlemail.com",
        "hotmail.com",
        "outlook.com",
        "live.com",
        "msn.com",
        "yahoo.com",
        "yahoo.com.br",
        "ymail.com",
        "icloud.com",
        "me.com",
        "aol.com",
        "protonmail.com",
        "proton.me",
        "uol.com.br",
        "bol.com.br",
        "terra.com.br",
        "ig.com.br",
    }
)


def is_valid_email(email: str | None) -> bool:
    """Return True if *email* looks like a syntactically valid address."""
    if email is None or not isinstance(email, str):
        return False
    candidate = email.strip()
    if not candidate or "@" not in candidate:
        return False
    return bool(_EMAIL_RE.match(candidate))


def is_valid_phone(phone: str | None) -> bool:
    """Return True if *phone* has enough digits to be a plausible contact number.

    Accepts common formatting; requires at least 10 digits (Brazil mobile/landline).
    """
    if phone is None or not isinstance(phone, str):
        return False
    digits = _PHONE_DIGITS_RE.findall(phone)
    if len(digits) < 10:
        return False
    if len(digits) > 15:
        return False
    return True


def is_generic_email_domain(email: str | None) -> bool:
    """Return True if the email domain is a known generic/free provider."""
    if not is_valid_email(email):
        return False
    assert email is not None
    domain = email.strip().split("@", 1)[1].lower()
    return domain in _GENERIC_EMAIL_DOMAINS


def has_valid_contact_channel(lead: dict) -> bool:
    """True if the lead has a valid email or a valid phone."""
    if not isinstance(lead, dict):
        return False
    return is_valid_email(lead.get("email")) or is_valid_phone(lead.get("phone"))


def is_critically_incomplete(lead: dict) -> bool:
    """True when the lead is too thin to treat as actionable.

    Rules (deterministic):
    - No valid contact channel, OR
    - No name and no company (cannot identify who/where), OR
    - Email present but invalid syntax (looks like they tried but data is junk).
    """
    if not isinstance(lead, dict):
        return True

    email_raw = lead.get("email")
    if email_raw is not None and str(email_raw).strip() and not is_valid_email(email_raw):
        return True

    if not has_valid_contact_channel(lead):
        return True

    name_ok = bool(lead.get("name") and str(lead.get("name")).strip())
    company_ok = bool(lead.get("company") and str(lead.get("company")).strip())
    if not name_ok and not company_ok:
        return True

    return False
