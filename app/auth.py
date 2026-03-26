"""API key authentication with multi-tenant support and tier-based access."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

from fastapi import Header, HTTPException, Request


@dataclass
class ClientInfo:
    client_id: str
    client_name: str
    tier: str  # "free" | "pro" | "enterprise"
    api_key_prefix: str = ""


def _load_clients() -> dict[str, ClientInfo]:
    """
    Build a map of api_key -> ClientInfo from environment variables.

    Supports two formats:
    1. API_KEY=single_key (legacy, treated as pro tier)
    2. API_KEYS=[{"key":"...", "client_id":"...", "client_name":"...", "tier":"pro"}, ...]
    """
    clients: dict[str, ClientInfo] = {}

    # New multi-key format
    raw = os.getenv("API_KEYS", "").strip()
    if raw:
        try:
            entries = json.loads(raw)
            for e in entries:
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

    # Legacy single key fallback
    legacy = os.getenv("API_KEY", "").strip()
    if legacy and legacy not in clients:
        clients[legacy] = ClientInfo(
            client_id="default",
            client_name="Default Client",
            tier="pro",
            api_key_prefix=legacy[:12] + "...",
        )

    return clients


async def require_api_key(
    request: Request,
    x_api_key: str | None = Header(default=None),
) -> ClientInfo:
    """
    FastAPI dependency. Returns ClientInfo for the authenticated client.
    If no keys are configured, returns anonymous ClientInfo (open mode).
    """
    clients = _load_clients()

    # Open mode — no keys configured
    if not clients:
        return ClientInfo(client_id="anonymous", client_name="Anonymous", tier="pro")

    if not x_api_key or x_api_key.strip() not in clients:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

    return clients[x_api_key.strip()]
