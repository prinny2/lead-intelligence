"""Webhook endpoint for external lead ingestion (Google Forms, Meta Ads, Zapier, Make)."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, field_validator

from app.models import LeadRequest, LeadResponse, StoredLead
from app.services import hybrid_score, save_lead
from app.services.scoring_service import get_ai_qualification_with_solar

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
async def form_webhook(payload: FormPayload) -> LeadResponse:
    """
    Receive a lead from Google Forms / Zapier / Make and qualify it.

    Map your form fields to any of the accepted aliases. Required:
      name or nome, city or cidade.
    Optional: monthly_bill/conta_de_luz, property_type/tipo_imovel,
              goal/objetivo, email, phone/telefone/whatsapp, etc.
    """
    lead = payload.to_lead_request()
    logger.info("webhook_form name=%s city=%s", lead.name, lead.city)

    ai_output, solar_context = get_ai_qualification_with_solar(lead)
    result = hybrid_score(lead, ai_output, solar_context)

    logger.info("webhook score=%s urgency=%s", result.response.score, result.response.urgency)

    try:
        stored = StoredLead.from_qualification(
            lead,
            result.response,
            ai_raw_score=result.ai_raw_score,
            rule_delta=result.rule_delta,
        )
        save_lead(stored)
    except Exception as e:
        logger.warning("webhook_storage_skipped error=%s", str(e))

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
    return await form_webhook(payload)
