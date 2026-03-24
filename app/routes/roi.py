"""ROI calculator for solar energy — POST /roi."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()

# ANEEL average tariffs (R$/kWh) by region — 2024 reference
_REGION_TARIFF: dict[str, float] = {
    "Sul": 0.89,
    "Sudeste": 0.85,
    "Nordeste": 0.82,
    "Centro-Oeste": 0.78,
    "Norte": 0.75,
}

_DEFAULT_TARIFF = 0.83  # national average fallback

_STATE_TO_REGION: dict[str, str] = {
    "RS": "Sul", "SC": "Sul", "PR": "Sul",
    "SP": "Sudeste", "RJ": "Sudeste", "MG": "Sudeste", "ES": "Sudeste",
    "BA": "Nordeste", "SE": "Nordeste", "AL": "Nordeste", "PE": "Nordeste",
    "PB": "Nordeste", "RN": "Nordeste", "CE": "Nordeste", "PI": "Nordeste", "MA": "Nordeste",
    "GO": "Centro-Oeste", "MT": "Centro-Oeste", "MS": "Centro-Oeste", "DF": "Centro-Oeste",
    "PA": "Norte", "AM": "Norte", "RO": "Norte", "AC": "Norte",
    "RR": "Norte", "AP": "Norte", "TO": "Norte",
}

# kWh generated per kWp per month (Brazil average by region)
_REGION_GENERATION: dict[str, float] = {
    "Sul": 110.0,
    "Sudeste": 120.0,
    "Nordeste": 140.0,
    "Centro-Oeste": 130.0,
    "Norte": 125.0,
}
_DEFAULT_GENERATION = 120.0

_COST_PER_KWP = 4_800.0      # R$/kWp installed (market avg 2024)
_GRID_OFFSET = 0.80           # 80% of bill offset by solar (GD rules)
_CO2_FACTOR = 0.075           # kg CO2 per kWh (Brazil grid factor)
_SYSTEM_LIFETIME_YEARS = 25


class ROIRequest(BaseModel):
    monthly_bill: float = Field(..., gt=0, description="Conta de luz mensal em R$")
    state: str | None = Field(default=None, description="UF do imóvel (ex: SP, MG, RS)")


class ROIResponse(BaseModel):
    region: str
    tariff_per_kwh: float
    estimated_system_size_kwp: float
    estimated_system_cost_brl: float
    monthly_savings_brl: float
    annual_savings_brl: float
    estimated_payback_years: float
    estimated_savings_10y_brl: float
    estimated_savings_25y_brl: float
    co2_avoided_kg_per_year: float
    roi_summary: str


@router.post("/roi", response_model=ROIResponse)
def calculate_roi(data: ROIRequest) -> ROIResponse:
    state = (data.state or "").strip().upper()
    region = _STATE_TO_REGION.get(state, "Sudeste")
    tariff = _REGION_TARIFF.get(region, _DEFAULT_TARIFF)
    gen_per_kwp = _REGION_GENERATION.get(region, _DEFAULT_GENERATION)

    monthly_kwh = data.monthly_bill / tariff
    system_kwp = round(monthly_kwh / gen_per_kwp, 2)
    system_cost = round(system_kwp * _COST_PER_KWP, 2)

    monthly_savings = round(data.monthly_bill * _GRID_OFFSET, 2)
    annual_savings = round(monthly_savings * 12, 2)
    payback = round(system_cost / annual_savings, 1) if annual_savings > 0 else 0.0
    savings_10y = round(annual_savings * 10 - system_cost, 2)
    savings_25y = round(annual_savings * _SYSTEM_LIFETIME_YEARS - system_cost, 2)
    co2_per_year = round(monthly_kwh * 12 * _CO2_FACTOR, 1)

    summary = (
        f"Sistema de {system_kwp} kWp custa ~R${system_cost:,.0f} e se paga em {payback} anos. "
        f"Economia em 10 anos: R${savings_10y:,.0f}. "
        f"CO₂ evitado: {co2_per_year} kg/ano."
    )

    return ROIResponse(
        region=region,
        tariff_per_kwh=tariff,
        estimated_system_size_kwp=system_kwp,
        estimated_system_cost_brl=system_cost,
        monthly_savings_brl=monthly_savings,
        annual_savings_brl=annual_savings,
        estimated_payback_years=payback,
        estimated_savings_10y_brl=savings_10y,
        estimated_savings_25y_brl=savings_25y,
        co2_avoided_kg_per_year=co2_per_year,
        roi_summary=summary,
    )
