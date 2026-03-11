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

# Prompt: distinguish curiosity vs medium intent vs real purchase intent
SYSTEM_PROMPT = """You are a lead qualifier for a solar energy company. Classify the lead and respond with ONLY a valid JSON object.

Score scale (be strict):
- 0-3: Weak lead. Curiosity only, early research, "só queria entender", "como funciona", low bill (<200), apartment with no clear intent. Use "baixa" urgency and a cautious/educational recommendation.
- 4-6: Medium intent. Some interest, gathering info, or moderate viability. Use "baixa" or "media" and a follow-up recommendation.
- 7-10: Strong lead. Clear purchase intent, high bill (>400), house/commercial, goal to reduce cost or install soon. Use "media" or "alta" and a fast-contact recommendation.

Signals of WEAK intent (score 0-3): low monthly_bill, apartment, goal phrases like "só queria entender", "como funciona", "pesquisando", "talvez", "queria saber", "só cotação", "mais pra frente".
Signals of STRONG intent: high bill, house/commercial, goal to "reduzir conta" or install, urgency in wording.

Output format (exactly these keys):
{"score": <integer 0-10>, "urgency": "baixa"|"media"|"alta", "recommendation": "<short text in Portuguese>"}

Rules: score 0-10 only; urgency exactly one of baixa, media, alta. No markdown."""

USER_PROMPT_TEMPLATE = """Avalie este lead para energia solar:

- Nome: {name}
- Cidade: {city}
- Conta de luz mensal (R$): {monthly_bill}
- Tipo de imóvel: {property_type}
- Objetivo: {goal}

Classifique como lead fraco (0-3), médio (4-6) ou forte (7-10) conforme intenção de compra e viabilidade. Responda apenas com o JSON."""


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
            temperature=0.3,
        )
        content = (response.choices[0].message.content or "").strip()
        logger.debug("ai_raw length=%s", len(content))
    except Exception as e:
        logger.warning("openai_failed error=%s", str(e))
        return None

    parsed = extract_first_json(content)
    if parsed is None:
        logger.warning("ai_invalid_json preview=%s", (content[:100] + "…") if len(content) > 100 else (content or "(empty)"))
        return None

    logger.info("ai score=%s urgency=%s", parsed.get("score"), parsed.get("urgency"))
    return parsed
