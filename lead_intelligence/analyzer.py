"""Lead analysis module."""

from __future__ import annotations

from lead_intelligence.validator import (
    has_valid_contact_channel,
    is_critically_incomplete,
    is_generic_email_domain,
    is_valid_email,
    is_valid_phone,
)


def analyze_lead(lead: dict) -> dict:
    """Analyze a lead and return enriched data.

    Args:
        lead: A dictionary containing lead information.
              Common keys: name, email, phone, company, title (all optional).

    Returns:
        The original lead mapping plus an ``analysis`` section.

    Raises:
        TypeError: If *lead* is not a dict.
    """
    if not isinstance(lead, dict):
        raise TypeError("lead must be a dictionary")

    analysis = {
        "has_email": bool(lead.get("email")),
        "has_company": bool(lead.get("company")),
        "completeness": _calculate_completeness(lead),
        "valid_email": is_valid_email(lead.get("email")),
        "valid_phone": is_valid_phone(lead.get("phone")),
        "generic_email_domain": is_generic_email_domain(lead.get("email")),
        "has_valid_contact_channel": has_valid_contact_channel(lead),
        "critically_incomplete": is_critically_incomplete(lead),
    }

    return {**lead, "analysis": analysis}


def _calculate_completeness(lead: dict) -> float:
    """Calculate how complete core identity fields are (0.0 to 1.0)."""
    fields = ["name", "email", "company"]
    filled = sum(1 for f in fields if lead.get(f))
    return round(filled / len(fields), 2)
