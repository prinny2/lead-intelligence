"""API route modules."""

from fastapi import APIRouter, Depends

from app.auth import require_api_key
from app.routes import dashboard, leads, webhook

api_router = APIRouter()
# Dashboard is public (no auth needed — read-only HTML)
api_router.include_router(dashboard.router, tags=["dashboard"])
# All other routes require API key
_secured = APIRouter(dependencies=[Depends(require_api_key)])
_secured.include_router(leads.router, tags=["leads"])
_secured.include_router(webhook.router, tags=["webhook"])
api_router.include_router(_secured)
