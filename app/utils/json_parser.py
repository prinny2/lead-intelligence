"""
Safe JSON extraction from LLM output.
Never use eval(). Handles markdown fences and surrounding text.
"""

import logging
import json
import re

logger = logging.getLogger("lead_intelligence")


def _strip_code_fences(text: str) -> str:
    if "```" not in text:
        return text
    return re.sub(r"```(?:json)?\s*", "", text).replace("```", "").strip()


def _candidate_json_objects(text: str):
    depth = 0
    start_index: int | None = None
    in_string = False
    escaped = False

    for index, char in enumerate(text):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
            continue

        if char == "{":
            if depth == 0:
                start_index = index
            depth += 1
            continue

        if char == "}" and depth > 0:
            depth -= 1
            if depth == 0 and start_index is not None:
                yield text[start_index:index + 1]
                start_index = None


def extract_first_json(raw: str) -> dict | None:
    """
    Extract and parse the first JSON object from text.
    Strips markdown code fences and any surrounding text.
    Returns None on empty input or parse failure.
    """
    if not raw or not raw.strip():
        return None
    text = _strip_code_fences(raw.strip())
    for candidate in _candidate_json_objects(text):
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError as e:
            logger.debug("json_parse_failed msg=%s", str(e))
            continue
        if isinstance(parsed, dict):
            return parsed
    return None
