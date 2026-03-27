"""Authentication — API key (env vars + Firestore) and Firebase ID token."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field

from fastapi import Header, HTTPException, Request

logger = logging.getLogger("lead_intelligence.auth")


@dataclass
class ClientInfo:
    client_id: str          # email (stable org_id) or env-var client_id
    client_name: str
    tier: str               # "starter" | "pro" | "enterprise" | "free"
    api_key_prefix: str = ""
    email: str = ""


# ──────────────────────────────────────────────
# Env-var API keys (legacy / dev)
# ──────────────────────────────────────────────

def _load_env_clients() -> dict[str, ClientInfo]:
    clients: dict[str, ClientInfo] = {}
    raw = os.getenv("API_KEYS", "").strip()
    if raw:
        try:
            for e in json.loads(raw):
                k = e.get("key", "").strip()
                if k:
                    clients[k] = ClientInfo(
                        client_id=e.get("client_id", "unknown"),
                        client_name=e.get("client_name", "Unknown"),
                        tier=e.get("tier", "free"),
                        api_key_prefix=k[:12] + "...",
                    )
        except Exception:
            pass
    legacy = os.getenv("API_KEY", "").strip()
    if legacy and legacy not in clients:
        clients[legacy] = ClientInfo(
            client_id="default",
            client_name="Default Client",
            tier="pro",
            api_key_prefix=legacy[:12] + "...",
        )
    return clients


# ──────────────────────────────────────────────
# Firestore helpers
# ──────────────────────────────────────────────

def _get_firestore():
    try:
        import firebase_admin
        from firebase_admin import firestore
        if not firebase_admin._apps:
            return None
        return firestore.client()
    except Exception:
        return None


def _lookup_api_key_firestore(api_key: str) -> ClientInfo | None:
    """Look up an API key in the Firestore customers collection."""
    db = _get_firestore()
    if not db:
        return None
    try:
        docs = (
            db.collection("customers")
            .where("api_key", "==", api_key)
            .where("status", "==", "active")
            .limit(1)
            .get()
        )
        for doc in docs:
            data = doc.to_dict()
            email = data.get("email", "")
            tier = data.get("tier", "starter")
            return ClientInfo(
                client_id=email or api_key,
                client_name=email or "Customer",
                tier=tier,
                api_key_prefix=api_key[:12] + "...",
                email=email,
            )
    except Exception as e:
        logger.warning("firestore_api_key_lookup_failed error=%s", e)
    return None


def _verify_firebase_token(token: str) -> ClientInfo | None:
    """Verify a Firebase ID token and look up the customer by email."""
    try:
        import firebase_admin
        from firebase_admin import auth as fb_auth

        if not firebase_admin._apps:
            return None

        decoded = fb_auth.verify_id_token(token)
        uid = decoded["uid"]
        email = decoded.get("email", "")
        name = decoded.get("name", email)

        db = _get_firestore()
        tier = "free"
        if db and email:
            try:
                docs = (
                    db.collection("customers")
                    .where("email", "==", email)
                    .limit(1)
                    .get()
                )
                for doc in docs:
                    data = doc.to_dict()
                    if data.get("status") == "active":
                        tier = data.get("tier", "starter")
                        break
            except Exception:
                pass

        return ClientInfo(
            client_id=email or uid,
            client_name=name,
            tier=tier,
            api_key_prefix="firebase",
            email=email,
        )
    except Exception as e:
        logger.debug("firebase_token_invalid error=%s", e)
        return None


# ──────────────────────────────────────────────
# FastAPI dependencies
# ──────────────────────────────────────────────

async def require_api_key(
    request: Request,
    x_api_key: str | None = Header(default=None),
) -> ClientInfo:
    """Accept API key from env vars or Firestore customers collection."""
    env_clients = _load_env_clients()

    # Open mode — no keys configured anywhere
    if not env_clients and not os.getenv("GOOGLE_CLOUD_PROJECT"):
        return ClientInfo(client_id="anonymous", client_name="Anonymous", tier="pro")

    if x_api_key:
        key = x_api_key.strip()
        if key in env_clients:
            return env_clients[key]
        # Try Firestore
        client = _lookup_api_key_firestore(key)
        if client:
            return client

    raise HTTPException(status_code=401, detail="Invalid or missing API key")


async def require_auth(
    request: Request,
    x_api_key: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
) -> ClientInfo:
    """Accept Firebase Bearer token OR API key. Firebase token takes priority."""
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()
        client = _verify_firebase_token(token)
        if client:
            return client

    return await require_api_key(request, x_api_key)
