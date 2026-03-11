"""Lead scoring module."""


def score_lead(lead: dict) -> int:
    """Score a lead from 0 to 100 based on available data.

    Args:
        lead: A dictionary containing lead information.
              Expected keys: 'name', 'email', 'company', 'phone' (all optional).

    Returns:
        An integer score between 0 and 100.
    """
    if not isinstance(lead, dict):
        raise TypeError("lead must be a dictionary")

    score = 0
    weights = {
        "name": 15,
        "email": 30,
        "company": 25,
        "phone": 20,
        "title": 10,
    }

    for field, weight in weights.items():
        if lead.get(field):
            score += weight

    return min(score, 100)
