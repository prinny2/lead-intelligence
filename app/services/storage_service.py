"""
Storage backend — auto-selects based on environment:
  - GOOGLE_CLOUD_PROJECT set → Firestore (persistent, scalable)
  - otherwise → JSONL file (local dev / simple deploys)
"""

import json
import logging
import os
from pathlib import Path

from app.models import StoredLead

logger = logging.getLogger("lead_intelligence")

# ── JSONL backend ─────────────────────────────────────────────────────────────

DEFAULT_LEADS_FILE = Path(__file__).resolve().parent.parent.parent / "leads.jsonl"


def _get_leads_file() -> Path:
    override = os.getenv("LEADS_FILE")
    if override and override.strip():
        return Path(override).expanduser().resolve()
    return DEFAULT_LEADS_FILE


def _save_jsonl(record: StoredLead) -> None:
    path = _get_leads_file()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(record.model_dump_json() + "\n")
        logger.debug("stored name=%s", record.name)
    except Exception as e:
        logger.warning("storage_failed path=%s error=%s", path, str(e))


def _load_jsonl() -> list[StoredLead]:
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
                    leads.append(StoredLead.model_validate(json.loads(line)))
                except Exception as e:
                    logger.debug("skip_invalid_line error=%s", str(e))
        return leads
    except Exception as e:
        logger.warning("load_leads_failed path=%s error=%s", path, str(e))
        return []


def _update_jsonl(lead_id: str, outcome: str, notes: str | None) -> StoredLead | None:
    path = _get_leads_file()
    leads = _load_jsonl()
    updated: StoredLead | None = None
    for i, lead in enumerate(leads):
        if lead.id == lead_id:
            leads[i] = lead.model_copy(update={"outcome": outcome, "outcome_notes": notes})
            updated = leads[i]
            break
    if updated is None:
        return None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            for lead in leads:
                f.write(lead.model_dump_json() + "\n")
    except Exception as e:
        logger.warning("update_lead_failed path=%s error=%s", path, str(e))
    return updated


# ── Firestore backend ──────────────────────────────────────────────────────────

def _firestore_client():
    """Lazy-load Firestore client. Returns None if firebase-admin not installed."""
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore

        if not firebase_admin._apps:
            project_id = os.environ["GOOGLE_CLOUD_PROJECT"]
            cred_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON", "").strip()
            if cred_json:
                # Railway / any PaaS: credentials stored as env var JSON string
                cred_dict = json.loads(cred_json)
                # Fix private key: Railway may store \n as literal \\n
                if "private_key" in cred_dict:
                    cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
                cred = credentials.Certificate(cred_dict)
            else:
                # Cloud Run: Application Default Credentials auto-detected
                cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred, {"projectId": project_id})
        return firestore.client()
    except Exception as e:
        logger.warning("firestore_init_failed error=%s", str(e))
        return None


_COLLECTION = "leads"


def _save_firestore(record: StoredLead) -> None:
    db = _firestore_client()
    if db is None:
        return _save_jsonl(record)
    try:
        db.collection(_COLLECTION).document(record.id).set(record.model_dump())
        logger.debug("firestore stored id=%s", record.id)
    except Exception as e:
        logger.warning("firestore_save_failed error=%s", str(e))
        _save_jsonl(record)  # fallback


def _load_firestore(org_id: str | None = None) -> list[StoredLead]:
    db = _firestore_client()
    if db is None:
        return _load_jsonl()
    try:
        query = db.collection(_COLLECTION)
        if org_id:
            query = query.where("org_id", "==", org_id)
        docs = query.order_by("timestamp", direction="DESCENDING").limit(1000).stream()
        leads = []
        for doc in docs:
            try:
                leads.append(StoredLead.model_validate(doc.to_dict()))
            except Exception:
                pass
        return leads
    except Exception as e:
        logger.warning("firestore_load_failed error=%s", str(e))
        return _load_jsonl()


def _update_firestore(lead_id: str, outcome: str, notes: str | None) -> StoredLead | None:
    db = _firestore_client()
    if db is None:
        return _update_jsonl(lead_id, outcome, notes)
    try:
        ref = db.collection(_COLLECTION).document(lead_id)
        doc = ref.get()
        if not doc.exists:
            return None
        update = {"outcome": outcome}
        if notes is not None:
            update["outcome_notes"] = notes
        ref.update(update)
        updated_doc = ref.get()
        return StoredLead.model_validate(updated_doc.to_dict())
    except Exception as e:
        logger.warning("firestore_update_failed error=%s", str(e))
        return _update_jsonl(lead_id, outcome, notes)


# ── Public API ─────────────────────────────────────────────────────────────────

def _use_firestore() -> bool:
    return bool(os.getenv("GOOGLE_CLOUD_PROJECT", "").strip())


def save_lead(record: StoredLead) -> None:
    if _use_firestore():
        _save_firestore(record)
    else:
        _save_jsonl(record)


def load_leads(org_id: str | None = None) -> list[StoredLead]:
    if _use_firestore():
        return _load_firestore(org_id=org_id)
    leads = _load_jsonl()
    if org_id:
        leads = [l for l in leads if l.org_id == org_id]
    return leads


def update_lead_outcome(lead_id: str, outcome: str, notes: str | None = None) -> StoredLead | None:
    if _use_firestore():
        return _update_firestore(lead_id, outcome, notes)
    return _update_jsonl(lead_id, outcome, notes)
