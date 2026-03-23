"""Optional API key authentication. Set API_KEY env var to enable."""

from __future__ import annotations

import os

from fastapi import Header, HTTPException


async def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """
    FastAPI dependency. Enforces X-API-Key header when API_KEY env var is set.
    If API_KEY is not configured, all requests pass through (open mode).
    """
    expected = os.getenv("API_KEY", "").strip()
    if not expected:
        return  # auth disabled — open mode
    if not x_api_key or x_api_key.strip() != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
