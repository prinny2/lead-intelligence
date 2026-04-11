"""Webhook endpoint for external lead ingestion (Google Forms, Meta Ads, Zapier, Make)."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, field_validator

from app.models import LeadRequest, LeadResponse, StoredLead
from app.services import hybrid_score, save_lead
from app.services.scoring_service import get_ai_qualification_with_solar
from app.services.audit_service import log_event

logger = logging.getLogger("lead_intelligence")

router = APIRouter()

# --- Flexible form payload ---


class FormPayload(BaseModel):
    """
    Accepts loose field names coming from Google Forms / Zapier / Make.
    Maps common variants to the canonical LeadRequest fields.
    """

    model_config = ConfigDict(str_strip_whitespace=True, extra="allow")

    # Required — accept common aliases
    name: str | None = None
    nome: str | None = None

    city: str | None = None
    cidade: str | None = None

    monthly_bill: float | None = None
    conta_de_luz: str | None = None
    conta: str | None = None
    bill: str | None = None

    property_type: str | None = None
    tipo_imovel: str | None = None
    tipo_de_imovel: str | None = None
    imovel: str | None = None

    goal: str | None = None
    objetivo: str | None = None
    interesse: str | None = None

    # Optional enrichment
    email: str | None = None
    phone: str | None = None
    telefone: str | None = None
    whatsapp: str | None = None
    company: str | None = None
    empresa: str | None = None
    state: str | None = None
    estado: str | None = None
    ownership_status: str | None = None
    titularidade: str | None = None
    interest_message: str | None = None
    mensagem: str | None = None

    @field_validator("monthly_bill", "conta_de_luz", "conta", "bill", mode="before")
    @classmethod
    def coerce_bill_to_float(cls, v: Any) -> Any:
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return float(v)
        s = str(v).strip().replace("R$", "").replace(".", "").replace(",", ".").strip()
        try:
            return float(s)
        except ValueError:
            return None

    def to_lead_request(self) -> LeadRequest:
        """Resolve aliases and build a canonical LeadRequest."""
        name = self.name or self.nome
        city = self.city or self.cidade
        bill = (
            self.monthly_bill
            or self.conta_de_luz
            or self.conta
            or self.bill
            or 0.0
        )
        property_type = (
            self.property_type
            or self.tipo_imovel
            or self.tipo_de_imovel
            or self.imovel
            or "outro"
        )
        goal = self.goal or self.objetivo or self.interesse or "não informado"

        missing = []
        if not name:
            missing.append("name/nome")
        if not city:
            missing.append("city/cidade")
        if missing:
            raise HTTPException(
                status_code=422,
                detail=f"Missing required fields: {', '.join(missing)}",
            )

        return LeadRequest(
            name=name,
            city=city,
            monthly_bill=float(bill),
            property_type=property_type,
            goal=goal,
            email=self.email,
            phone=self.phone or self.telefone or self.whatsapp,
            company=self.company or self.empresa,
            state=self.state or self.estado,
            ownership_status=self.ownership_status or self.titularidade,
            interest_message=self.interest_message or self.mensagem,
        )


# --- Endpoints ---


@router.post("/webhook/form", response_model=LeadResponse)
async def form_webhook(payload: FormPayload, request: Request) -> LeadResponse:
    """
    Receive a lead from Google Forms / Zapier / Make and qualify it.

    Map your form fields to any of the accepted aliases. Required:
      name or nome, city or cidade.
    Optional: monthly_bill/conta_de_luz, property_type/tipo_imovel,
              goal/objetivo, email, phone/telefone/whatsapp, etc.
    """
    lead = payload.to_lead_request()

    # Optional API key via query param — attributes webhook lead to a tenant
    org_id: str | None = None
    api_key_param = request.query_params.get("api_key", "").strip()
    if api_key_param:
        from app.auth import _lookup_api_key_firestore
        client_info = _lookup_api_key_firestore(api_key_param)
        if client_info:
            org_id = client_info.client_id

    logger.info("webhook_form name=%s city=%s org=%s", lead.name, lead.city, org_id or "anon")

    ai_output, solar_context = get_ai_qualification_with_solar(lead)
    result = hybrid_score(lead, ai_output, solar_context)

    logger.info("webhook score=%s urgency=%s", result.response.score, result.response.urgency)

    try:
        stored = StoredLead.from_qualification(
            lead,
            result.response,
            ai_raw_score=result.ai_raw_score,
            rule_delta=result.rule_delta,
            org_id=org_id,
        )
        save_lead(stored)
    except Exception as e:
        logger.warning("webhook_storage_skipped error=%s", str(e))

    log_event(
        "webhook_form_qualified",
        endpoint="/webhook/form",
        method="POST",
        status_code=200,
        score=result.response.score,
        extra={
            "source": "form",
            "org_id": org_id or "anon",
            "decision": result.response.decision,
            "urgency": result.response.urgency,
        },
    )

    try:
        from app.services.notification_service import notify_admin_lead, notify_hot_lead
        notify_admin_lead(
            lead_name=lead.name,
            lead_city=lead.city,
            monthly_bill=lead.monthly_bill,
            score=result.response.score,
            urgency=result.response.urgency,
            decision=result.response.decision,
            whatsapp_message=result.response.whatsapp_message,
            recommendation=result.response.recommendation,
            source="form",
        )
        if org_id:
            notify_hot_lead(
                org_id=org_id,
                lead_name=lead.name,
                lead_city=lead.city,
                monthly_bill=lead.monthly_bill,
                score=result.response.score,
                urgency=result.response.urgency,
                whatsapp_message=result.response.whatsapp_message,
                recommendation=result.response.recommendation,
            )
    except Exception as e:
        logger.debug("notification_skipped error=%s", e)

    return result.response


@router.post("/webhook/form/raw", response_model=LeadResponse)
async def form_webhook_raw(request: Request) -> LeadResponse:
    """
    Fallback: accepts any JSON body, attempts best-effort field extraction.
    Useful for custom form tools that send arbitrary key names.
    """
    try:
        body: dict[str, Any] = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    payload = FormPayload.model_validate(body)
    return await form_webhook(payload, request)


# ── RD Station Webhook ────────────────────────────────────────────────────────

class RDStationPayload(BaseModel):
    """
    RD Station webhook event payload.
    Supports both Marketing (event_type/payload) and CRM (funnel_name/contact) formats.
    Configure in RD Station: Configurações → Integrações → Webhooks
    URL: https://leadsolarintelligence.com.br/webhook/rdstation?api_key=sk-ls-...
    Events: Lead convertido, Lead atualizado
    """
    model_config = ConfigDict(extra="allow")

    # Marketing format
    event_type: str | None = None
    event_family: str | None = None
    payload: dict[str, Any] | None = None

    # CRM format (alternative)
    funnel_name: str | None = None
    contact: dict[str, Any] | None = None


def _parse_rdstation(data: dict[str, Any]) -> dict[str, Any]:
    """Extract lead fields from RD Station payload (Marketing or CRM format)."""
    # Try Marketing format first
    contact = data.get("payload") or data.get("contact") or data

    def _cf(key: str) -> str:
        """Read a custom field value."""
        val = contact.get(key) or contact.get(f"cf_{key}") or ""
        if isinstance(val, list) and val:
            val = val[0]
        return str(val).strip() if val else ""

    name = (contact.get("name") or contact.get("nome") or "").strip()
    email = (contact.get("email") or "").strip()
    phone = (contact.get("mobile_phone") or contact.get("personal_phone")
             or contact.get("phone") or contact.get("telefone") or "").strip()
    city = (_cf("city") or _cf("cidade") or contact.get("city") or "").strip()
    state = (_cf("state") or _cf("estado") or contact.get("state") or "").strip()

    # Custom fields — installers typically set these in RD Station forms
    bill_raw = _cf("conta_de_luz") or _cf("monthly_bill") or _cf("conta") or _cf("bill")
    try:
        bill = float(str(bill_raw).replace("R$", "").replace(".", "").replace(",", ".").strip() or "0")
    except ValueError:
        bill = 0.0

    property_type = (_cf("tipo_imovel") or _cf("property_type") or _cf("imovel") or "outro").strip()
    goal = (_cf("objetivo") or _cf("goal") or _cf("interesse")
            or contact.get("tags", [""])[0] if isinstance(contact.get("tags"), list) else ""
            or "instalar energia solar").strip()

    return {
        "name": name or "Lead RD Station",
        "email": email or None,
        "phone": phone or None,
        "city": city or "Brasil",
        "state": state or None,
        "monthly_bill": bill,
        "property_type": property_type or "outro",
        "goal": goal or "instalar energia solar",
    }


@router.post("/webhook/rdstation")
async def rdstation_webhook(request: Request) -> dict[str, Any]:
    """
    Receive leads from RD Station Marketing or CRM via webhook.

    Setup in RD Station:
      Configurações → Integrações → Webhooks → Novo Webhook
      URL: .../webhook/rdstation?api_key=sk-ls-YOUR_KEY
      Events: Lead convertido

    Optional custom fields to create in RD Station forms:
      conta_de_luz, tipo_imovel, objetivo
    """
    try:
        body: dict[str, Any] = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    # Only process lead creation/update events
    event_type = body.get("event_type", "").lower()
    if event_type and event_type not in (
        "lead.created", "lead.updated", "lead_created", "lead_updated",
        "lead convertido", "lead_convertido", "",
    ):
        return {"received": True, "processed": False, "reason": f"event_type={event_type} ignored"}

    fields = _parse_rdstation(body)
    if not fields.get("name") or fields["name"] == "Lead RD Station" and not fields.get("email"):
        logger.warning("rdstation_missing_name payload_keys=%s", list(body.keys()))

    # Resolve org_id from ?api_key= param
    org_id: str | None = None
    api_key_param = request.query_params.get("api_key", "").strip()
    if api_key_param:
        from app.auth import _lookup_api_key_firestore
        client_info = _lookup_api_key_firestore(api_key_param)
        if client_info:
            org_id = client_info.client_id

    try:
        lead = LeadRequest(**fields)
    except Exception as e:
        logger.warning("rdstation_invalid_lead error=%s fields=%s", e, fields)
        raise HTTPException(status_code=422, detail=f"Campos inválidos: {e}")

    logger.info("rdstation_lead name=%s city=%s org=%s event=%s",
                lead.name, lead.city, org_id or "anon", event_type)

    ai_output, solar_context = get_ai_qualification_with_solar(lead)
    result = hybrid_score(lead, ai_output, solar_context)

    try:
        stored = StoredLead.from_qualification(
            lead, result.response,
            ai_raw_score=result.ai_raw_score,
            rule_delta=result.rule_delta,
            org_id=org_id,
        )
        save_lead(stored)
    except Exception as e:
        logger.warning("rdstation_storage_skipped error=%s", e)

    log_event(
        "webhook_rdstation_qualified",
        endpoint="/webhook/rdstation",
        method="POST",
        status_code=200,
        score=result.response.score,
        extra={
            "source": "rdstation",
            "org_id": org_id or "anon",
            "decision": result.response.decision,
            "event_type": event_type or "unknown",
        },
    )

    try:
        from app.services.notification_service import notify_admin_lead, notify_hot_lead
        notify_admin_lead(
            lead_name=lead.name,
            lead_city=lead.city,
            monthly_bill=lead.monthly_bill,
            score=result.response.score,
            urgency=result.response.urgency,
            decision=result.response.decision,
            whatsapp_message=result.response.whatsapp_message,
            recommendation=result.response.recommendation,
            source="rdstation",
        )
        if org_id:
            notify_hot_lead(
                org_id=org_id,
                lead_name=lead.name,
                lead_city=lead.city,
                monthly_bill=lead.monthly_bill,
                score=result.response.score,
                urgency=result.response.urgency,
                whatsapp_message=result.response.whatsapp_message,
                recommendation=result.response.recommendation,
            )
    except Exception as e:
        logger.debug("rdstation_notification_skipped error=%s", e)

    return {
        "received": True,
        "processed": True,
        "score": result.response.score,
        "urgency": result.response.urgency,
        "decision": result.response.decision,
    }
