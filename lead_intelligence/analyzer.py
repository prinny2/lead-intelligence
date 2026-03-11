"""Lead analysis module."""


def analyze_lead(lead: dict) -> dict:
    """Analyze a lead and return enriched data.

    Args:
        lead: A dictionary containing lead information.
              Expected keys: 'name', 'email', 'company' (all optional).

    Returns:
        A dictionary with the original lead data plus an 'analysis' section.
    """
    if not isinstance(lead, dict):
        raise TypeError("lead must be a dictionary")

    analysis = {
        "has_email": bool(lead.get("email")),
        "has_company": bool(lead.get("company")),
        "completeness": _calculate_completeness(lead),
    }

    return {**lead, "analysis": analysis}


def _calculate_completeness(lead: dict) -> float:
    """Calculate how complete a lead's information is (0.0 to 1.0)."""
    fields = ["name", "email", "company"]
    filled = sum(1 for f in fields if lead.get(f))
    return round(filled / len(fields), 2)
