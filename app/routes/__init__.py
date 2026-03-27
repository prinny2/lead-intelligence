"""API route modules."""

from fastapi import APIRouter, Depends

from app.auth import require_auth
from app.routes import contact, dashboard, demo, landing, leads, payments, roi, webhook

api_router = APIRouter()

# Public (no auth)
api_router.include_router(landing.router, tags=["landing"])
api_router.include_router(dashboard.router, tags=["dashboard"])
api_router.include_router(contact.router, tags=["contact"])
api_router.include_router(demo.router, tags=["demo"])
api_router.include_router(payments.router, tags=["payments"])

# Auth handled per-endpoint (supports both API key and Firebase token)
api_router.include_router(leads.router, tags=["leads"])

# ROI and webhook: router-level auth guard
_secured = APIRouter(dependencies=[Depends(require_auth)])
_secured.include_router(roi.router, tags=["roi"])
_secured.include_router(webhook.router, tags=["webhook"])
api_router.include_router(_secured)
