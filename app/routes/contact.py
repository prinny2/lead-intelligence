"""Contact form endpoint — POST /contact."""

import json
import logging
import os
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger("lead_intelligence")

_DEFAULT_CONTACTS_FILE = Path(__file__).resolve().parent.parent.parent / "contacts.jsonl"


def _contacts_file() -> Path:
    override = os.getenv("CONTACTS_FILE")
    if override and override.strip():
        return Path(override).expanduser().resolve()
    return _DEFAULT_CONTACTS_FILE


class ContactRequest(BaseModel):
    contact: str
    source: str = "landing"


class ContactResponse(BaseModel):
    ok: bool
    message: str


@router.post("/contact", response_model=ContactResponse)
async def save_contact(body: ContactRequest) -> ContactResponse:
    value = body.contact.strip()
    if not value:
        return ContactResponse(ok=False, message="contato vazio")

    record = {
        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "contact": value,
        "source": body.source,
    }

    try:
        path = _contacts_file()
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        logger.info("new_contact source=%s contact=%s", body.source, value[:6] + "***")
    except Exception as e:
        logger.warning("contact_save_failed error=%s", str(e))

    return ContactResponse(ok=True, message="Recebido! Vamos te chamar em breve.")
