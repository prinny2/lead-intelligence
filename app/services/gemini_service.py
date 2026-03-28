"""Google Gemini lead qualification — drop-in replacement for ai_service (Anthropic).

Priority order in scoring_service: Gemini → Anthropic → rule-only fallback.
Uses the google-generativeai SDK (GEMINI_API_KEY env var).
"""

from __future__ import annotations

import logging
import os
from typing import Any

from app.models import LeadRequest
from app.utils.json_parser import extract_first_json

logger = logging.getLogger("lead_intelligence.gemini")

_SYSTEM_PROMPT = """You qualify leads for a Brazilian residential/commercial solar sales team. Respond with ONLY one valid JSON object (no markdown, no extra text).

JSON keys (exactly):
{"score": <0-10 integer>, "urgency": "baixa"|"media"|"alta", "recommendation": "<string>"}

Scoring (be strict):
- 0-3: weak / exploratory; "baixa" urgency unless data screams otherwise.
- 4-6: medium; "baixa" or "media".
- 7-8: strong opportunity; "media" or "alta".
- 9-10: high conversion; "alta" when justified.

Strong signals: monthly bill >= R$400, house or commercial property, clear savings/install intent, urgency words in goal.
Weak signals: bill < R$200, apartment without ownership, curiosity phrases.

Field "recommendation" rules (Brazilian Portuguese):
- 1 to 3 sentences. Concise, action-oriented, human and practical.
- Help the salesperson: next action, channel (prefer WhatsApp for media/alta), priority, commercial angle.
- Use the lead's city, monthly_bill, property_type, and goal naturally.
- If solar_context is provided, use sunshine hours and payback to strengthen the recommendation.
- Tie timeframe: alta → same day / 24h; media → 2–5 business days; baixa → 5–10 days."""

_USER_TEMPLATE = """Gere o JSON para este lead solar:

Nome: {name}
Cidade: {city}
Conta de luz mensal (R$): {monthly_bill}
Tipo de imóvel: {property_type}
Objetivo: {goal}
{optional}
{solar_block}
Responda somente com o objeto JSON."""


def get_gemini_qualification(
    lead: LeadRequest,
    solar_context: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Call Gemini and return parsed dict with score, urgency, recommendation.

    Returns None if API key missing, request fails, or response is not valid JSON.
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        logger.debug("gemini_key_missing — skipping")
        return None

    try:
        import google.generativeai as genai  # type: ignore
    except ImportError:
        logger.warning("google-generativeai not installed — pip install google-generativeai")
        return None

    genai.configure(api_key=api_key)
    model_id = os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip() or "gemini-2.0-flash"

    optional_lines: list[str] = []
    for label, value in [
        ("Email", lead.email),
        ("Telefone", lead.phone),
        ("Empresa", lead.company),
        ("Estado", lead.state),
        ("Titularidade", lead.ownership_status),
        ("Mensagem", lead.interest_message),
    ]:
        if value:
            optional_lines.append(f"{label}: {value}")

    solar_block = ""
    if solar_context:
        parts: list[str] = []
        if solar_context.get("sunshine_hours"):
            parts.append(f"Horas de sol/ano: {solar_context['sunshine_hours']:.0f}h")
        if solar_context.get("max_panels"):
            parts.append(f"Painéis máximos: {solar_context['max_panels']}")
        if solar_context.get("estimated_payback_years"):
            parts.append(f"Payback estimado: {solar_context['estimated_payback_years']:.1f} anos")
        if solar_context.get("monthly_savings_estimate"):
            parts.append(f"Economia estimada: R${solar_context['monthly_savings_estimate']:.0f}/mês")
        if parts:
            solar_block = "Dados solares da cidade (Google Solar API):\n" + "\n".join(f"- {p}" for p in parts) + "\n"

    prompt = _USER_TEMPLATE.format(
        name=lead.name,
        city=lead.city,
        monthly_bill=lead.monthly_bill,
        property_type=lead.property_type,
        goal=lead.goal,
        optional=("\n".join(optional_lines) + "\n") if optional_lines else "",
        solar_block=solar_block,
    )

    try:
        model = genai.GenerativeModel(
            model_name=model_id,
            system_instruction=_SYSTEM_PROMPT,
        )
        response = model.generate_content(
            prompt,
            generation_config={"max_output_tokens": 512, "temperature": 0.2},
        )
        content = (response.text or "").strip()
        logger.debug("gemini_raw length=%s", len(content))
    except Exception as e:
        logger.warning("gemini_failed error=%s", e)
        return None

    parsed = extract_first_json(content)
    if parsed is None:
        logger.warning("gemini_invalid_json preview=%s", content[:120])
        return None

    logger.info("gemini score=%s urgency=%s", parsed.get("score"), parsed.get("urgency"))
    return parsed
