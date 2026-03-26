"""Persistent rate limiter — Firestore-backed sliding window, falls back to in-memory."""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from datetime import UTC, datetime, timedelta

logger = logging.getLogger("lead_intelligence.ratelimit")

# In-memory fallback store: key -> list of timestamps
_mem_store: dict[str, list[float]] = defaultdict(list)

TIER_LIMITS: dict[str, int] = {
    "free": 10,
    "pro": 100,
    "enterprise": 1000,
    "demo": 5,  # per IP, for the public demo endpoint
}


def _get_db():
    try:
        import firebase_admin
        from firebase_admin import firestore
        if not firebase_admin._apps:
            return None
        return firestore.client()
    except Exception:
        return None


def _check_memory(key: str, limit: int, window_seconds: int = 60) -> bool:
    """In-memory fallback. Returns True if allowed."""
    now = time.monotonic()
    hits = _mem_store[key]
    _mem_store[key] = [t for t in hits if now - t < window_seconds]
    if len(_mem_store[key]) >= limit:
        return False
    _mem_store[key].append(now)
    return True


def _check_firestore(key: str, limit: int, window_seconds: int = 60) -> bool:
    """Firestore sliding window. Returns True if allowed."""
    db = _get_db()
    if not db:
        return _check_memory(key, limit, window_seconds)

    try:
        now = datetime.now(UTC)
        window_start = now - timedelta(seconds=window_seconds)
        doc_ref = db.collection("rate_limits").document(key)

        # Atomic update using Firestore transaction
        @db.transaction()
        def _update(transaction, doc_ref):
            snapshot = doc_ref.get(transaction=transaction)
            hits: list[str] = snapshot.get("hits") or [] if snapshot.exists else []

            # Filter hits within window
            hits = [h for h in hits if datetime.fromisoformat(h) > window_start]

            if len(hits) >= limit:
                return False

            hits.append(now.isoformat())
            transaction.set(doc_ref, {"hits": hits, "updated_at": now.isoformat()})
            return True

        return _update(doc_ref)
    except Exception as exc:
        logger.debug("rate_limit_firestore_error: %s — falling back to memory", exc)
        return _check_memory(key, limit, window_seconds)


def is_allowed(key: str, tier: str = "free") -> bool:
    """Check if this key is within its rate limit. Returns True if allowed."""
    limit = TIER_LIMITS.get(tier, TIER_LIMITS["free"])
    return _check_firestore(key, limit)
