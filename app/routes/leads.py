"""Lead qualification and stats endpoints."""

import logging

from fastapi import APIRouter, Query

from app.models import LeadRequest, LeadResponse, LeadStats, StoredLead
from app.services import get_ai_qualification, hybrid_score, load_leads, save_lead

logger = logging.getLogger("lead_intelligence")

router = APIRouter()


@router.get("/")
async def root() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/lead", response_model=LeadResponse)
def analyze_lead(data: LeadRequest) -> LeadResponse:
    logger.info("lead name=%s city=%s", data.name, data.city)

    ai_output = get_ai_qualification(data)
    result = hybrid_score(data, ai_output)

    logger.info("lead score=%s urgency=%s", result.response.score, result.response.urgency)

    try:
        stored = StoredLead.from_qualification(
            data,
            result.response,
            ai_raw_score=result.ai_raw_score,
            rule_delta=result.rule_delta,
        )
        save_lead(stored)
    except Exception as e:
        logger.warning("storage_skipped error=%s", str(e))

    return result.response


@router.get("/leads", response_model=list[StoredLead])
async def list_leads(
    urgency: str | None = Query(default=None),
    score_min: int | None = Query(default=None, ge=0, le=10),
    score_max: int | None = Query(default=None, ge=0, le=10),
    property_type: str | None = Query(default=None),
    city: str | None = Query(default=None),
    decision: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
) -> list[StoredLead]:
    leads = load_leads()
    if urgency:
        leads = [l for l in leads if l.urgency == urgency]
    if score_min is not None:
        leads = [l for l in leads if l.score >= score_min]
    if score_max is not None:
        leads = [l for l in leads if l.score <= score_max]
    if property_type:
        pt = property_type.strip().lower()
        leads = [l for l in leads if (l.property_type or "").lower() == pt]
    if city:
        c = city.strip().lower()
        leads = [l for l in leads if (l.city or "").lower() == c]
    if decision:
        leads = [l for l in leads if l.decision == decision]
    return leads[:limit]


@router.get("/stats", response_model=LeadStats)
async def get_stats() -> LeadStats:
    leads = load_leads()
    if not leads:
        return LeadStats(
            total_leads=0,
            average_score=0.0,
            high_quality_leads=0,
            low_quality_leads=0,
            breakdown_by_urgency={},
            breakdown_by_property_type={},
        )
    total = len(leads)
    scores = [lead.score for lead in leads]
    avg = sum(scores) / total
    high = sum(1 for score in scores if score >= 7)
    low = sum(1 for score in scores if score <= 3)

    urgency_breakdown: dict[str, int] = {}
    for lead in leads:
        key = lead.urgency or "desconhecido"
        urgency_breakdown[key] = urgency_breakdown.get(key, 0) + 1

    property_breakdown: dict[str, int] = {}
    for lead in leads:
        key = (lead.property_type or "desconhecido").strip().lower()
        property_breakdown[key] = property_breakdown.get(key, 0) + 1

    return LeadStats(
        total_leads=total,
        average_score=round(avg, 2),
        high_quality_leads=high,
        low_quality_leads=low,
        breakdown_by_urgency=urgency_breakdown,
        breakdown_by_property_type=property_breakdown,
    )
