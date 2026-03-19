"""Lead scoring module (0–100), quality-aware and deterministic."""

from __future__ import annotations

from lead_intelligence.validator import (
    has_valid_contact_channel,
    is_critically_incomplete,
    is_generic_email_domain,
    is_valid_email,
    is_valid_phone,
)


def score_lead(lead: dict) -> int:
    """Score lead quality from 0 to 100.

    Considers presence of fields, valid contact data, generic email penalty,
    completeness of core fields, and critical incompleteness.

    Args:
        lead: Lead mapping (name, email, phone, company, title, ...).

    Returns:
        Integer 0–100.

    Raises:
        TypeError: If *lead* is not a dict.
    """
    if not isinstance(lead, dict):
        raise TypeError("lead must be a dictionary")

    if is_critically_incomplete(lead):
        return min(25, _raw_quality_score(lead))

    raw = _raw_quality_score(lead)
    return max(0, min(100, raw))


def _raw_quality_score(lead: dict) -> int:
    """Uncapped quality sum before critical-incomplete cap."""
    score = 0

    if lead.get("name") and str(lead.get("name")).strip():
        score += 12
    if lead.get("company") and str(lead.get("company")).strip():
        score += 18
    if lead.get("title") and str(lead.get("title")).strip():
        score += 8

    if is_valid_email(lead.get("email")):
        score += 22
    elif lead.get("email"):
        score -= 5

    if is_valid_phone(lead.get("phone")):
        score += 18

    if has_valid_contact_channel(lead):
        score += 10
    else:
        score -= 25

    if is_generic_email_domain(lead.get("email")):
        score -= 8

    fields = ["name", "email", "company"]
    filled = sum(1 for f in fields if lead.get(f))
    completeness = filled / len(fields)
    score += int(round(completeness * 20))

    return score
