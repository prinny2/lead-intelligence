"""API route modules."""

from fastapi import APIRouter, Depends

from app.auth import require_auth
from app.routes import contact, dashboard, demo, landing, leads, onboarding, payments, roi, webhook

api_router = APIRouter()

# Public (no auth)
api_router.include_router(landing.router, tags=["landing"])
api_router.include_router(dashboard.router, tags=["dashboard"])
api_router.include_router(contact.router, tags=["contact"])
api_router.include_router(demo.router, tags=["demo"])
api_router.include_router(payments.router, tags=["payments"])
api_router.include_router(onboarding.router, tags=["onboarding"])
# ROI: public — pure math, called from landing page without credentials
api_router.include_router(roi.router, tags=["roi"])

# Auth handled per-endpoint (supports both API key and Firebase token)
api_router.include_router(leads.router, tags=["leads"])

# Webhook: public — Stripe and external forms cannot send API keys
api_router.include_router(webhook.router, tags=["webhook"])
