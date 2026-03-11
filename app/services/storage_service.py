"""Simple JSONL persistence for leads. Failures do not break the API."""

import json
import logging
import os
from pathlib import Path

from app.models import StoredLead

logger = logging.getLogger("lead_intelligence")

# Store in project root so GET /stats can read without path tricks
DEFAULT_LEADS_FILE = Path(__file__).resolve().parent.parent.parent / "leads.jsonl"


def _get_leads_file() -> Path:
    override = os.getenv("LEADS_FILE")
    if override and override.strip():
        return Path(override).expanduser().resolve()
    return DEFAULT_LEADS_FILE


def save_lead(record: StoredLead) -> None:
    """Append one lead to leads.jsonl. Logs and ignores errors."""
    path = _get_leads_file()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        line = record.model_dump_json() + "\n"
        with open(path, "a", encoding="utf-8") as f:
            f.write(line)
        logger.debug("stored name=%s", record.name)
    except Exception as e:
        logger.warning("storage_failed path=%s error=%s", path, str(e))


def load_leads() -> list[StoredLead]:
    """Read all leads from leads.jsonl. Returns [] if file missing or invalid."""
    path = _get_leads_file()
    if not path.exists():
        return []
    leads: list[StoredLead] = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    leads.append(StoredLead.model_validate(data))
                except (json.JSONDecodeError, Exception) as e:
                    logger.debug("skip_invalid_line error=%s", str(e))
                    continue
        return leads
    except Exception as e:
        logger.warning("load_leads_failed path=%s error=%s", path, str(e))
        return []
