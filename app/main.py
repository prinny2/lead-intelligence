"""
Lead Intelligence MVP - FastAPI application.
Solar lead qualification with hybrid AI + rules and local JSONL storage.
"""

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.routes import api_router

# --- Structured logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)

load_dotenv()

app = FastAPI(
    title="Lead Intelligence MVP",
    description="Qualify solar energy leads via AI + rules. POST /lead, GET /stats.",
    version="0.1.0",
)

# CORS para frontends na web (configure CORS_ORIGINS no painel do host)
_cors = os.getenv("CORS_ORIGINS", "").strip()
if _cors:
    _origins = ["*"] if _cors == "*" else [o.strip() for o in _cors.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router)

# --- Static UI for testing ---
_static_dir = Path(__file__).resolve().parent / "static"


@app.get("/ui")
async def ui_redirect() -> RedirectResponse:
    """Redirect /ui to the static test page."""
    return RedirectResponse(url="/static/index.html")


app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")

# Future: mount routers for WhatsApp, webhooks, admin, etc.
# app.include_router(whatsapp_router, prefix="/webhooks", tags=["whatsapp"])
# app.include_router(admin_router, prefix="/admin", tags=["admin"])
