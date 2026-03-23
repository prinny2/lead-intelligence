"""API route modules."""

from fastapi import APIRouter, Depends

from app.auth import require_api_key
from app.routes import leads, webhook

api_router = APIRouter(dependencies=[Depends(require_api_key)])
api_router.include_router(leads.router, tags=["leads"])
api_router.include_router(webhook.router, tags=["webhook"])
