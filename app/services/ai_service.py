"""Anthropic Claude-based lead qualification. Returns raw dict; scoring layer validates and applies rules."""

import logging
import os
from typing import Any

import anthropic

from app.models import LeadRequest
from app.utils.json_parser import extract_first_json

logger = logging.getLogger("lead_intelligence")
DEFAULT_MODEL = "claude-haiku-4-5-20251001"
TIMEOUT_SECONDS = 20.0

SYSTEM_PROMPT = """You qualify leads for a Brazilian residential/commercial solar sales team. Respond with ONLY one valid JSON object (no markdown, no extra text).

JSON keys (exactly):
{"score": <0-10 integer>, "urgency": "baixa"|"media"|"alta", "recommendation": "<string>"}

Scoring (be strict):
- 0-3: weak / exploratory; "baixa" urgency unless data screams otherwise.
- 4-6: medium; "baixa" or "media".
- 7-8: strong opportunity; "media" or "alta".
- 9-10: high conversion; "alta" when justified.

Strong signals: monthly bill >= R$400, house or commercial property, clear savings/install intent, urgency words in goal.
Weak signals: bill < R$200, apartment without ownership, curiosity phrases ("só queria entender", "ainda estudando").

Field "recommendation" rules (Brazilian Portuguese):
- 1 to 3 sentences only. Concise, action-oriented, human and practical.
- Help the salesperson decide: next action, channel (prefer WhatsApp for media/alta urgency), priority, commercial angle (economia, viabilidade, proposta).
- Naturally use the lead's city, monthly_bill, property_type, and goal when relevant.
- Suggest what to validate: titular da conta, imóvel próprio, telhado/disponibilidade.
- Tie timeframe to urgency: alta → same day or within 24h; media → about 2–5 business days; baixa → about 5–10 business days with softer CTA.
- Avoid vague labels ("lead promissor") without concrete guidance. No buzzwords."""


USER_PROMPT_TEMPLATE = """Gere o JSON para este lead solar; use cidade, conta, tipo de imóvel e objetivo na recomendação.

Nome: {name}
Cidade: {city}
Conta de luz mensal (R$): {monthly_bill}
Tipo de imóvel: {property_type}
Objetivo: {goal}
{extra}
Responda somente com o objeto JSON."""


def get_ai_qualification(lead: LeadRequest) -> dict[str, Any] | None:
    """
    Call Anthropic Claude and return parsed JSON dict with keys score, urgency, recommendation.
    Returns None if API key missing, request fails, or response is not valid JSON.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or not api_key.strip():
        logger.error("anthropic_key_missing")
        return None

    model = (os.getenv("ANTHROPIC_MODEL") or DEFAULT_MODEL).strip() or DEFAULT_MODEL

    optional_lines = []
    if lead.email:
        optional_lines.append(f"Email: {lead.email}")
    if lead.phone:
        optional_lines.append(f"Telefone: {lead.phone}")
    if lead.company:
        optional_lines.append(f"Empresa: {lead.company}")
    if lead.state:
        optional_lines.append(f"Estado: {lead.state}")
    if lead.ownership_status:
        optional_lines.append(f"Titularidade do imóvel: {lead.ownership_status}")
    if lead.interest_message:
        optional_lines.append(f"Mensagem de interesse: {lead.interest_message}")

    extra = ("\n".join(optional_lines) + "\n") if optional_lines else ""
    user_content = USER_PROMPT_TEMPLATE.format(
        name=lead.name,
        city=lead.city,
        monthly_bill=lead.monthly_bill,
        property_type=lead.property_type,
        goal=lead.goal,
        extra=extra,
    )

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=model,
            max_tokens=512,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_content}],
        )
        content = (message.content[0].text or "").strip()
        logger.debug("ai_raw length=%s", len(content))
    except Exception as e:
        logger.warning("anthropic_failed error=%s", str(e))
        return None

    parsed = extract_first_json(content)
    if parsed is None:
        logger.warning(
            "ai_invalid_json preview=%s",
            (content[:100] + "…") if len(content) > 100 else (content or "(empty)"),
        )
        return None

    logger.info("ai score=%s urgency=%s", parsed.get("score"), parsed.get("urgency"))
    return parsed
