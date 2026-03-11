"""Lead qualification and stats endpoints."""

import logging

from fastapi import APIRouter

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
async def analyze_lead(data: LeadRequest) -> LeadResponse:
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


@router.get("/stats", response_model=LeadStats)
async def get_stats() -> LeadStats:
    leads = load_leads()
    if not leads:
        return LeadStats(
            total_leads=0,
            average_score=0.0,
            high_quality_leads=0,
            low_quality_leads=0,
        )
    total = len(leads)
    scores = [l.score for l in leads]
    avg = sum(scores) / total
    high = sum(1 for s in scores if s >= 7)
    low = sum(1 for s in scores if s <= 3)
    return LeadStats(
        total_leads=total,
        average_score=round(avg, 2),
        high_quality_leads=high,
        low_quality_leads=low,
    )
