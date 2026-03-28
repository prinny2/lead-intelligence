"""Public demo endpoint — rule-based only, no AI, no auth. Used by landing page live demo."""

import logging

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.services.audit_service import log_event
from app.services.rate_limit_service import is_allowed
from app.services.scoring_service import hybrid_score
from app.services.whatsapp_builder import build_whatsapp_message

router = APIRouter()
logger = logging.getLogger("lead_intelligence")


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
    ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (
        request.client.host if request.client else "unknown"
    )

    if not is_allowed(f"demo:{ip}", tier="demo"):
        log_event("rate_limited", ip=ip, endpoint="/demo", method="POST", status_code=429)
        raise HTTPException(
            status_code=429,
            detail="Limite de demonstrações atingido. Tente em 1 minuto.",
        )

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

    log_event(
        "demo_used",
        ip=ip,
        endpoint="/demo",
        method="POST",
        status_code=200,
        score=r.score,
        extra={"city": body.city, "monthly_bill": body.monthly_bill},
    )

    # Derive decision from score for demo (qualifier needs contact info not available here)
    if r.score >= 7:
        decision = "accept"
    elif r.score >= 4:
        decision = "review"
    else:
        decision = "reject"

    return DemoResponse(
        score=r.score,
        urgency=r.urgency,
        decision=decision,
        recommendation=r.recommendation,
        whatsapp_message=r.whatsapp_message or "",
    )
