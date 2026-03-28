"""Persistent rate limiter — Redis → Firestore → in-memory fallback chain.

Priority:
  1. Redis (REDIS_URL set) — fastest, ~1ms per check, survives restarts
  2. Firestore (GOOGLE_CLOUD_PROJECT set) — persistent, ~50ms per check
  3. In-memory — resets on restart, dev/fallback only

Add Redis on Railway: Add-ons → Redis (free tier) → copy REDIS_URL.
"""

from __future__ import annotations

import logging
import os
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


# ── Redis (preferred) ──────────────────────────────────────────────────────────

def _redis_client():
    """Lazy Redis connection. Returns None if REDIS_URL not set or redis not installed."""
    url = os.getenv("REDIS_URL", "").strip()
    if not url:
        return None
    try:
        import redis  # type: ignore
        return redis.from_url(url, socket_connect_timeout=2, socket_timeout=2, decode_responses=True)
    except Exception as e:
        logger.debug("redis_connect_failed error=%s", e)
        return None


def _check_redis(key: str, limit: int, window_seconds: int = 60) -> bool:
    """Redis sorted-set sliding window. Returns True if allowed."""
    r = _redis_client()
    if not r:
        return None  # type: ignore — sentinel: fall through to Firestore

    try:
        now = time.time()
        window_start = now - window_seconds
        pipe = r.pipeline()
        # Remove expired entries, count current, add new hit, set TTL
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, window_seconds + 5)
        results = pipe.execute()
        count_before = results[1]
        if count_before >= limit:
            # Already at limit — undo the zadd we just did
            r.zrem(key, str(now))
            return False
        return True
    except Exception as e:
        logger.debug("redis_ratelimit_error key=%s error=%s", key, e)
        return None  # type: ignore — fall through


# ── Firestore ──────────────────────────────────────────────────────────────────

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

        @db.transaction()
        def _update(transaction, doc_ref):
            snapshot = doc_ref.get(transaction=transaction)
            hits: list[str] = snapshot.get("hits") or [] if snapshot.exists else []
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


# ── Public API ─────────────────────────────────────────────────────────────────

def is_allowed(key: str, tier: str = "free") -> bool:
    """Check rate limit. Redis → Firestore → in-memory fallback chain."""
    limit = TIER_LIMITS.get(tier, TIER_LIMITS["free"])

    result = _check_redis(key, limit)
    if result is not None:
        return result

    return _check_firestore(key, limit)
