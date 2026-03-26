"""Audit log service — records every API action to Firestore (falls back to structured log)."""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("lead_intelligence.audit")


def _get_db():
    """Return Firestore client or None."""
    try:
        import firebase_admin
        from firebase_admin import firestore
        if not firebase_admin._apps:
            return None
        return firestore.client()
    except Exception:
        return None


def log_event(
    event_type: str,
    *,
    client_id: str = "anonymous",
    api_key_prefix: str = "",
    ip: str = "",
    endpoint: str = "",
    method: str = "",
    status_code: int = 0,
    lead_id: str = "",
    score: int | None = None,
    error: str = "",
    extra: dict[str, Any] | None = None,
) -> None:
    """Write an audit event. Non-blocking — errors are swallowed."""
    payload: dict[str, Any] = {
        "timestamp": datetime.now(UTC).isoformat(),
        "event_type": event_type,
        "client_id": client_id,
        "api_key_prefix": api_key_prefix,
        "ip": ip,
        "endpoint": endpoint,
        "method": method,
        "status_code": status_code,
    }
    if lead_id:
        payload["lead_id"] = lead_id
    if score is not None:
        payload["score"] = score
    if error:
        payload["error"] = error
    if extra:
        payload.update(extra)

    # Always log to stdout (visible in Railway / Cloud Run logs)
    logger.info(
        "audit event=%s client=%s ip=%s endpoint=%s status=%s",
        event_type, client_id, ip, endpoint, status_code,
    )

    # Try to persist to Firestore
    try:
        db = _get_db()
        if db:
            db.collection("audit_logs").add(payload)
    except Exception as exc:
        logger.debug("audit_firestore_skip: %s", exc)
