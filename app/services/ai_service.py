"""OpenAI-based lead qualification. Returns raw dict; scoring layer validates and applies rules."""

import logging
import os
from typing import Any

from openai import OpenAI

from app.models import LeadRequest
from app.utils.json_parser import extract_first_json

logger = logging.getLogger("lead_intelligence")
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
OPENAI_TIMEOUT_SECONDS = 20.0

# Spec: recommendation must help the rep act (channel, priority, angle, timeframe) — output still JSON for the API.
SYSTEM_PROMPT = """You qualify leads for a Brazilian residential/commercial solar sales team. Respond with ONLY one valid JSON object (no markdown, no extra text).

JSON keys (exactly):
{"score": <0-10 integer>, "urgency": "baixa"|"media"|"alta", "recommendation": "<string>"}

Scoring (be strict):
- 0-3: weak / exploratory; "baixa" urgency unless data screams otherwise.
- 4-6: medium; "baixa" or "media".
- 7-8: strong opportunity; "media" or "alta".
- 9-10: high conversion; "alta" when justified.

Field "recommendation" rules (Brazilian Portuguese):
- 1 to 3 sentences only. Concise, action-oriented, human and practical — not robotic or academic.
- Help the salesperson decide: next action, channel (prefer WhatsApp for media/alta urgency), priority, commercial angle (economia, viabilidade, proposta).
- Naturally use the lead's city, monthly_bill, property_type, and goal when relevant.
- Suggest what to validate when useful: titular da conta, imóvel próprio, telhado/disponibilidade, se a conta justifica simulação.
- Avoid vague CRM labels alone ("interesse moderado", "lead promissor", "cliente com potencial") unless followed by concrete operational guidance.
- Avoid corporate jargon, buzzwords, empty filler, or aggressive pushy tone.
- Tie timeframe to urgency: alta → same day or within 24h; media → about 2–5 business days; baixa → about 5–10 business days with softer CTA.

Weak signals: low bill, apartment without intent, curiosity phrases. Strong signals: high bill, house/commercial, clear savings/install intent, urgency in goal."""


USER_PROMPT_TEMPLATE = """Gere o JSON para este lead; use cidade, conta, tipo de imóvel e objetivo na recomendação quando fizer sentido.

Nome: {name}
Cidade: {city}
Conta de luz mensal (R$): {monthly_bill}
Tipo de imóvel: {property_type}
Objetivo: {goal}

Responda somente com o objeto JSON."""


def get_ai_qualification(lead: LeadRequest) -> dict[str, Any] | None:
    """
    Call OpenAI and return parsed JSON dict with keys score, urgency, recommendation.
    Returns None if API key missing, request fails, or response is not valid JSON.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or not api_key.strip():
        logger.error("openai_key_missing")
        return None

    model = (os.getenv("OPENAI_MODEL") or DEFAULT_OPENAI_MODEL).strip() or DEFAULT_OPENAI_MODEL
    client = OpenAI(api_key=api_key, timeout=OPENAI_TIMEOUT_SECONDS)
    user_content = USER_PROMPT_TEMPLATE.format(
        name=lead.name,
        city=lead.city,
        monthly_bill=lead.monthly_bill,
        property_type=lead.property_type,
        goal=lead.goal,
    )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.35,
        )
        content = (response.choices[0].message.content or "").strip()
        logger.debug("ai_raw length=%s", len(content))
    except Exception as e:
        logger.warning("openai_failed error=%s", str(e))
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
