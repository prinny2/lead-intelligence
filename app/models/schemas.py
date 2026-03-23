"""Request/response and storage schemas."""

import uuid
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# --- API contract (do not change) ---

UrgencyType = Literal["baixa", "media", "alta"]
DecisionType = Literal["accept", "review", "reject"]

VALID_URGENCIES: frozenset[str] = frozenset({"baixa", "media", "alta"})
DEFAULT_URGENCY: UrgencyType = "baixa"
SCORE_MIN, SCORE_MAX = 0, 10


class LeadRequest(BaseModel):
    """Incoming lead data from POST /lead."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str
    city: str
    monthly_bill: float
    property_type: str
    goal: str
    # Optional enrichment fields
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    state: str | None = None
    ownership_status: str | None = None
    interest_message: str | None = None

    @field_validator("name", "city", "property_type", "goal")
    @classmethod
    def validate_non_empty_text(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("must not be empty")
        return value

    @field_validator("monthly_bill")
    @classmethod
    def validate_monthly_bill(cls, value: float) -> float:
        if value < 0:
            raise ValueError("must be greater than or equal to 0")
        return value

    @field_validator("email", "phone", "company", "state", "ownership_status", "interest_message", mode="before")
    @classmethod
    def coerce_blank_optional_to_none(cls, value: str | None) -> str | None:
        if isinstance(value, str) and not value.strip():
            return None
        return value


class LeadResponse(BaseModel):
    """Qualification result returned by POST /lead."""

    score: int = Field(..., ge=0, le=10)
    urgency: str = Field(..., pattern="^(baixa|media|alta)$")
    recommendation: str
    decision: DecisionType | None = None
    qualifier_reasons: list[str] | None = None


# --- Storage (JSONL records) ---


class StoredLead(BaseModel):
    """Single record written to leads.jsonl. Extra fields for dataset analysis."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str
    name: str
    city: str
    monthly_bill: float
    property_type: str
    goal: str
    # Optional enrichment fields (stored when provided)
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    state: str | None = None
    ownership_status: str | None = None
    interest_message: str | None = None
    score: int = Field(..., ge=0, le=10)
    urgency: str = Field(..., pattern="^(baixa|media|alta)$")
    recommendation: str
    decision: DecisionType | None = None
    qualifier_reasons: list[str] | None = None
    ai_raw_score: int | None = None
    rule_delta: int = 0

    @classmethod
    def from_qualification(
        cls,
        request: LeadRequest,
        response: LeadResponse,
        *,
        ai_raw_score: int | None = None,
        rule_delta: int = 0,
    ) -> "StoredLead":
        return cls(
            timestamp=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            name=request.name,
            city=request.city,
            monthly_bill=request.monthly_bill,
            property_type=request.property_type,
            goal=request.goal,
            email=request.email,
            phone=request.phone,
            company=request.company,
            state=request.state,
            ownership_status=request.ownership_status,
            interest_message=request.interest_message,
            score=response.score,
            urgency=response.urgency,
            recommendation=response.recommendation,
            decision=response.decision,
            qualifier_reasons=response.qualifier_reasons,
            ai_raw_score=ai_raw_score,
            rule_delta=rule_delta,
        )


# --- GET /stats response ---


class LeadStats(BaseModel):
    """Aggregate stats from stored leads."""

    total_leads: int
    average_score: float
    high_quality_leads: int  # score >= 7
    low_quality_leads: int   # score <= 3
    breakdown_by_urgency: dict[str, int]
    breakdown_by_property_type: dict[str, int]
