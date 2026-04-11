"""Lead qualification and stats endpoints."""

import csv
import io
import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.auth import ClientInfo, require_auth
from app.models import LeadRequest, LeadResponse, LeadStats, OutcomeUpdate, StoredLead
from app.services import hybrid_score, load_leads, save_lead, update_lead_outcome
from app.services.scoring_service import get_ai_qualification_with_solar
from app.services.audit_service import log_event
from app.services.sheets_service import push_lead_result_to_sheet

logger = logging.getLogger("lead_intelligence")

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.2.0", "stripe": "enabled"}


def _find_duplicate(data: LeadRequest, leads: list[StoredLead]) -> StoredLead | None:
    """Return existing lead if same phone or email seen in last 30 days."""
    if not data.phone and not data.email:
        return None
    cutoff = datetime.now(UTC) - timedelta(days=30)
    for lead in reversed(leads):
        try:
            ts = datetime.fromisoformat(lead.timestamp.replace("Z", "+00:00"))
        except Exception:
            continue
        if ts < cutoff:
            continue
        if data.phone and lead.phone and lead.phone == data.phone:
            return lead
        if data.email and lead.email and lead.email == data.email:
            return lead
    return None


def _score_and_store(data: LeadRequest, org_id: str | None = None) -> LeadResponse:
    ai_output, solar_context = get_ai_qualification_with_solar(data)
    result = hybrid_score(data, ai_output, solar_context)
    try:
        stored = StoredLead.from_qualification(
            data, result.response,
            ai_raw_score=result.ai_raw_score,
            rule_delta=result.rule_delta,
            org_id=org_id,
        )
        save_lead(stored)
    except Exception as e:
        logger.warning("storage_skipped error=%s", str(e))

    # Notify admin of every new lead + notify customer of hot leads (fire-and-forget)
    try:
        from app.services.notification_service import notify_admin_lead, notify_hot_lead
        notify_admin_lead(
            lead_name=data.name,
            lead_city=data.city,
            monthly_bill=data.monthly_bill,
            score=result.response.score,
            urgency=result.response.urgency,
            decision=result.response.decision,
            whatsapp_message=result.response.whatsapp_message,
            recommendation=result.response.recommendation,
            source="api",
        )
        if org_id:
            notify_hot_lead(
                org_id=org_id,
                lead_name=data.name,
                lead_city=data.city,
                monthly_bill=data.monthly_bill,
                score=result.response.score,
                urgency=result.response.urgency,
                whatsapp_message=result.response.whatsapp_message,
                recommendation=result.response.recommendation,
            )
    except Exception as e:
        logger.debug("notification_skipped error=%s", e)

    push_lead_result_to_sheet(
        name=data.name,
        city=data.city,
        state=data.state,
        score=result.response.score,
        decision=result.response.decision,
        urgency=result.response.urgency,
        whatsapp_message=result.response.whatsapp_message,
    )
    return result.response


@router.post("/lead", response_model=LeadResponse)
def analyze_lead(
    data: LeadRequest,
    client: ClientInfo = Depends(require_auth),
) -> LeadResponse:
    org_id = client.client_id
    logger.info("lead name=%s city=%s org=%s", data.name, data.city, org_id)
    existing = _find_duplicate(data, load_leads(org_id=org_id))
    if existing:
        logger.info("duplicate_lead id=%s", existing.id)
        return LeadResponse(
            score=existing.score,
            urgency=existing.urgency,
            recommendation=existing.recommendation,
            whatsapp_message=existing.whatsapp_message,
            decision=existing.decision,
            qualifier_reasons=existing.qualifier_reasons,
        )
    response = _score_and_store(data, org_id=org_id)
    logger.info("lead score=%s urgency=%s", response.score, response.urgency)
    log_event("lead_qualified", endpoint="/lead", method="POST", status_code=200, score=response.score)
    return response


@router.get("/leads", response_model=list[StoredLead])
async def list_leads(
    urgency: str | None = Query(default=None),
    score_min: int | None = Query(default=None, ge=0, le=10),
    score_max: int | None = Query(default=None, ge=0, le=10),
    property_type: str | None = Query(default=None),
    city: str | None = Query(default=None),
    decision: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    client: ClientInfo = Depends(require_auth),
) -> list[StoredLead]:
    leads = load_leads(org_id=client.client_id)
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


@router.get("/leads/export")
async def export_leads_csv(
    client: ClientInfo = Depends(require_auth),
) -> StreamingResponse:
    """Download all leads as CSV."""
    leads = load_leads(org_id=client.client_id)
    fields = [
        "id", "timestamp", "name", "city", "state", "monthly_bill",
        "property_type", "goal", "email", "phone", "company",
        "ownership_status", "score", "urgency", "decision",
        "outcome", "outcome_notes", "ai_raw_score", "rule_delta",
    ]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for lead in leads:
        writer.writerow({f: getattr(lead, f, "") for f in fields})
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads.csv"},
    )


@router.get("/leads/{lead_id}", response_model=StoredLead)
async def get_lead(
    lead_id: str,
    client: ClientInfo = Depends(require_auth),
) -> StoredLead:
    leads = load_leads(org_id=client.client_id)
    for lead in leads:
        if lead.id == lead_id:
            return lead
    raise HTTPException(status_code=404, detail="lead not found")


@router.patch("/leads/{lead_id}/outcome", response_model=StoredLead)
async def update_outcome(
    lead_id: str,
    body: OutcomeUpdate,
    client: ClientInfo = Depends(require_auth),
) -> StoredLead:
    # Verify the lead belongs to this client before updating (multi-tenancy)
    owned = load_leads(org_id=client.client_id)
    if not any(l.id == lead_id for l in owned):
        raise HTTPException(status_code=404, detail="lead not found")
    updated = update_lead_outcome(lead_id, body.outcome, body.notes)
    if updated is None:
        raise HTTPException(status_code=404, detail="lead not found")
    logger.info("outcome_updated lead_id=%s outcome=%s org=%s", lead_id, body.outcome, client.client_id)
    return updated


@router.get("/stats", response_model=LeadStats)
async def get_stats(
    client: ClientInfo = Depends(require_auth),
) -> LeadStats:
    leads = load_leads(org_id=client.client_id)
    if not leads:
        return LeadStats(
            total_leads=0,
            average_score=0.0,
            high_quality_leads=0,
            low_quality_leads=0,
            breakdown_by_urgency={},
            breakdown_by_property_type={},
            breakdown_by_outcome={},
            conversion_rate=0.0,
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

    outcome_breakdown: dict[str, int] = {}
    for lead in leads:
        key = lead.outcome or "sem_retorno"
        outcome_breakdown[key] = outcome_breakdown.get(key, 0) + 1

    closed = sum(1 for lead in leads if lead.outcome == "closed")
    conversion_rate = round(closed / total * 100, 1)

    return LeadStats(
        total_leads=total,
        average_score=round(avg, 2),
        high_quality_leads=high,
        low_quality_leads=low,
        breakdown_by_urgency=urgency_breakdown,
        breakdown_by_property_type=property_breakdown,
        breakdown_by_outcome=outcome_breakdown,
        conversion_rate=conversion_rate,
    )


@router.post("/leads/bulk", response_model=list[LeadResponse])
def bulk_ingest(
    leads_in: list[LeadRequest],
    client: ClientInfo = Depends(require_auth),
) -> list[LeadResponse]:
    """Score up to 50 leads at once. Useful for CSV batch uploads."""
    if len(leads_in) > 50:
        raise HTTPException(status_code=422, detail="max 50 leads per request")
    org_id = client.client_id
    existing = load_leads(org_id=org_id)
    results: list[LeadResponse] = []
    for data in leads_in:
        dup = _find_duplicate(data, existing)
        if dup:
            results.append(LeadResponse(
                score=dup.score, urgency=dup.urgency,
                recommendation=dup.recommendation,
                whatsapp_message=dup.whatsapp_message,
                decision=dup.decision,
                qualifier_reasons=dup.qualifier_reasons,
            ))
        else:
            results.append(_score_and_store(data, org_id=org_id))
    return results
