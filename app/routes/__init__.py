"""API route modules."""

from fastapi import APIRouter

from app.routes import leads

api_router = APIRouter()
api_router.include_router(leads.router, tags=["leads"])
