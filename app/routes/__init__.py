"""API route modules."""

from fastapi import APIRouter, Depends

from app.auth import require_api_key
from app.routes import contact, dashboard, demo, landing, leads, payments, roi, webhook

api_router = APIRouter()
# Public pages (no auth)
api_router.include_router(landing.router, tags=["landing"])
api_router.include_router(dashboard.router, tags=["dashboard"])
api_router.include_router(contact.router, tags=["contact"])
api_router.include_router(demo.router, tags=["demo"])
api_router.include_router(payments.router, tags=["payments"])
# All other routes require API key
_secured = APIRouter(dependencies=[Depends(require_api_key)])
_secured.include_router(leads.router, tags=["leads"])
_secured.include_router(webhook.router, tags=["webhook"])
_secured.include_router(roi.router, tags=["roi"])
api_router.include_router(_secured)
