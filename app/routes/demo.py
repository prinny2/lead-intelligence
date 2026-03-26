"""Public demo endpoint — rule-based only, no AI, no auth. Used by landing page live demo."""

import logging
import time
from collections import defaultdict

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.services.scoring_service import hybrid_score
from app.services.whatsapp_builder import build_whatsapp_message

router = APIRouter()
logger = logging.getLogger("lead_intelligence")

# Simple in-memory rate limit: max 5 requests per IP per 60 seconds
_RATE: dict[str, list[float]] = defaultdict(list)
_WINDOW = 60.0
_LIMIT = 5


class DemoRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    city: str = Field(min_length=1, max_length=80)
    monthly_bill: float = Field(ge=50, le=5000)
    property_type: str = Field(min_length=1, max_length=40)
    goal: str = Field(min_length=1, max_length=200)


class DemoResponse(BaseModel):
    score: int
    urgency: str
    decision: str | None
    recommendation: str
    whatsapp_message: str


@router.post("/demo", response_model=DemoResponse)
async def demo_score(body: DemoRequest, request: Request) -> DemoResponse:
    """Score a lead using rule-based logic only. Public, rate-limited to 5 req/min per IP."""
    ip = request.client.host if request.client else "unknown"
    now = time.monotonic()
    hits = _RATE[ip]
    _RATE[ip] = [t for t in hits if now - t < _WINDOW]
    if len(_RATE[ip]) >= _LIMIT:
        raise HTTPException(status_code=429, detail="Limite de demonstrações atingido. Tente em 1 minuto.")
    _RATE[ip].append(now)

    from app.models import LeadRequest
    lead = LeadRequest(
        name=body.name,
        city=body.city,
        monthly_bill=body.monthly_bill,
        property_type=body.property_type,
        goal=body.goal,
    )

    result = hybrid_score(lead, ai_output=None)
    r = result.response
    return DemoResponse(
        score=r.score,
        urgency=r.urgency,
        decision=r.decision,
        recommendation=r.recommendation,
        whatsapp_message=r.whatsapp_message or "",
    )
