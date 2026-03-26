"""Lead persistence — Firestore (primary) with JSONL fallback."""

import json
import logging
import os
from pathlib import Path

from app.models import StoredLead

logger = logging.getLogger("lead_intelligence")

DEFAULT_LEADS_FILE = Path(__file__).resolve().parent.parent.parent / "leads.jsonl"

# ---------------------------------------------------------------------------
# Firestore initialisation (lazy, so import errors never crash the app)
# ---------------------------------------------------------------------------

_db = None


def _get_db():
    """Return a Firestore client, or None if credentials are unavailable."""
    global _db
    if _db is not None:
        return _db

    creds_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    project = os.getenv("GOOGLE_CLOUD_PROJECT", "lead-solar-12345")

    if not creds_json:
        logger.warning("firestore_skip: GOOGLE_APPLICATION_CREDENTIALS_JSON not set")
        return None

    try:
        import firebase_admin
        from firebase_admin import credentials, firestore

        creds_dict = json.loads(creds_json)

        if not firebase_admin._apps:
            cred = credentials.Certificate(creds_dict)
            firebase_admin.initialize_app(cred, {"projectId": project})

        _db = firestore.client()
        logger.info("firestore_connected project=%s", project)
        return _db
    except Exception as e:
        logger.warning("firestore_init_failed error=%s", str(e))
        return None


# ---------------------------------------------------------------------------
# JSONL helpers (fallback)
# ---------------------------------------------------------------------------

def _get_leads_file() -> Path:
    override = os.getenv("LEADS_FILE")
    if override and override.strip():
        return Path(override).expanduser().resolve()
    return DEFAULT_LEADS_FILE


def _save_jsonl(record: StoredLead) -> None:
    path = _get_leads_file()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        line = record.model_dump_json() + "\n"
        with open(path, "a", encoding="utf-8") as f:
            f.write(line)
        logger.debug("jsonl_stored name=%s", record.name)
    except Exception as e:
        logger.warning("jsonl_storage_failed path=%s error=%s", path, str(e))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def save_lead(record: StoredLead) -> None:
    """Save lead to Firestore. Falls back to JSONL on any error."""
    db = _get_db()
    if db is not None:
        try:
            doc_data = json.loads(record.model_dump_json())
            db.collection("leads").document(record.id).set(doc_data)
            logger.info("firestore_saved id=%s name=%s", record.id, record.name)
            return
        except Exception as e:
            logger.warning("firestore_save_failed id=%s error=%s — falling back to JSONL", record.id, str(e))

    _save_jsonl(record)


def load_leads() -> list[StoredLead]:
    """Load all leads. Tries Firestore first, falls back to JSONL."""
    db = _get_db()
    if db is not None:
        try:
            docs = db.collection("leads").order_by(
                "created_at", direction="DESCENDING"
            ).limit(500).stream()
            leads = []
            for doc in docs:
                try:
                    leads.append(StoredLead.model_validate(doc.to_dict()))
                except Exception as e:
                    logger.debug("skip_invalid_doc id=%s error=%s", doc.id, str(e))
            logger.info("firestore_loaded count=%d", len(leads))
            return leads
        except Exception as e:
            logger.warning("firestore_load_failed error=%s — falling back to JSONL", str(e))

    # JSONL fallback
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
                except Exception as e:
                    logger.debug("skip_invalid_line error=%s", str(e))
        return leads
    except Exception as e:
        logger.warning("load_leads_failed path=%s error=%s", path, str(e))
        return []
