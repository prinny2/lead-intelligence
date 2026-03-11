"""
Lead Intelligence MVP - FastAPI application.
Solar lead qualification with hybrid AI + rules and local JSONL storage.
"""

import logging
import sys

from fastapi import FastAPI
from dotenv import load_dotenv

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

app.include_router(api_router)

# Future: mount routers for WhatsApp, webhooks, admin, etc.
# app.include_router(whatsapp_router, prefix="/webhooks", tags=["whatsapp"])
# app.include_router(admin_router, prefix="/admin", tags=["admin"])
