"""Google Maps geocoding + Google Solar API enrichment.

Geocodes a city name → lat/lng, then queries the Solar API for building-level
solar potential. Results are cached in memory (cities don't move).

Env vars required:
  GOOGLE_MAPS_API_KEY — key with Maps Geocoding API + Solar API enabled.

Returns None silently when the key is missing or API calls fail — the rest of
the qualification pipeline continues without solar data.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Any

logger = logging.getLogger("lead_intelligence.solar")

_GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
_SOLAR_URL = "https://solar.googleapis.com/v1/buildingInsights:findClosest"

# Average residential tariff in Brazil (R$/kWh) — used for payback estimate
# ANEEL 2024 average: R$0.75/kWh including taxes
_TARIFF_BRL_PER_KWH = float(os.getenv("SOLAR_TARIFF_BRL_KWH", "0.75"))

# Typical residential solar panel output per kWp in Brazil (kWh/year per kWp)
_KWH_PER_KWP_YEAR = 1_350.0

# Average system cost per kWp installed (R$) — 2024 Brazil average
_COST_PER_KWP_BRL = 4_500.0


def _api_key() -> str:
    return os.getenv("GOOGLE_MAPS_API_KEY", "").strip()


@lru_cache(maxsize=256)
def _geocode_city_cached(city: str, state: str) -> tuple[float, float] | None:
    """Returns (lat, lng) or None. Cached per city+state combination."""
    key = _api_key()
    if not key:
        return None

    query = f"{city}, {state}, Brasil" if state else f"{city}, Brasil"
    try:
        import httpx
        r = httpx.get(_GEOCODE_URL, params={"address": query, "key": key}, timeout=5.0)
        data = r.json()
    except Exception as e:
        logger.warning("geocode_failed city=%s error=%s", city, e)
        return None

    results = data.get("results", [])
    if not results:
        logger.debug("geocode_no_results city=%s", city)
        return None

    loc = results[0]["geometry"]["location"]
    lat, lng = float(loc["lat"]), float(loc["lng"])
    logger.debug("geocode_ok city=%s lat=%.4f lng=%.4f", city, lat, lng)
    return lat, lng


@lru_cache(maxsize=256)
def _get_solar_insights_cached(lat: float, lng: float) -> dict[str, Any] | None:
    """Query Google Solar API for building insights. Cached per coordinate pair."""
    key = _api_key()
    if not key:
        return None

    try:
        import httpx
        r = httpx.get(
            _SOLAR_URL,
            params={
                "location.latitude": round(lat, 4),
                "location.longitude": round(lng, 4),
                "requiredQuality": "LOW",
                "key": key,
            },
            timeout=8.0,
        )
        if r.status_code != 200:
            logger.debug("solar_api_status lat=%.4f lng=%.4f status=%s", lat, lng, r.status_code)
            return None
        data = r.json()
    except Exception as e:
        logger.warning("solar_api_failed lat=%.4f lng=%.4f error=%s", lat, lng, e)
        return None

    logger.debug("solar_api_ok lat=%.4f lng=%.4f", lat, lng)
    return data


def _estimate_payback(
    monthly_bill: float,
    sunshine_hours: float,
    max_panels: int,
) -> dict[str, float]:
    """Estimate system size, savings and payback from solar + bill data."""
    # kWh consumed per month
    monthly_kwh = monthly_bill / _TARIFF_BRL_PER_KWH

    # kWp needed to cover 80% of consumption
    kwp_needed = (monthly_kwh * 12 * 0.80) / (sunshine_hours or _KWH_PER_KWP_YEAR)
    kwp_needed = max(1.0, min(kwp_needed, max_panels * 0.4))  # cap to realistic size

    system_cost = kwp_needed * _COST_PER_KWP_BRL
    monthly_generation_kwh = kwp_needed * (sunshine_hours or _KWH_PER_KWP_YEAR) / 12
    monthly_savings = monthly_generation_kwh * _TARIFF_BRL_PER_KWH
    payback_years = system_cost / (monthly_savings * 12) if monthly_savings > 0 else 99.0

    return {
        "kwp_system": round(kwp_needed, 1),
        "system_cost_brl": round(system_cost, 0),
        "monthly_savings_estimate": round(monthly_savings, 0),
        "payback_years": round(min(payback_years, 30.0), 1),
    }


def enrich_lead_solar(
    city: str,
    state: str | None,
    monthly_bill: float,
) -> dict[str, Any] | None:
    """
    Full enrichment pipeline: geocode city → Solar API → payback estimate.
    Returns a dict with solar context, or None if any step fails.

    Keys in returned dict:
      lat, lng, sunshine_hours, max_panels, max_area_m2,
      kwp_system, system_cost_brl, monthly_savings_estimate,
      estimated_payback_years
    """
    key = _api_key()
    if not key:
        return None

    coords = _geocode_city_cached(city or "", state or "")
    if not coords:
        return None

    lat, lng = coords
    insights = _get_solar_insights_cached(round(lat, 4), round(lng, 4))
    if not insights:
        return None

    solar_potential = insights.get("solarPotential", {})
    sunshine_hours = float(solar_potential.get("maxSunshineHoursPerYear", 0) or 0)
    max_panels = int(solar_potential.get("maxArrayPanelsCount", 0) or 0)
    max_area = float(solar_potential.get("maxArrayAreaMeters2", 0) or 0)

    if sunshine_hours <= 0:
        logger.debug("solar_no_sunshine city=%s", city)
        return None

    estimates = _estimate_payback(monthly_bill, sunshine_hours, max_panels)

    result: dict[str, Any] = {
        "lat": lat,
        "lng": lng,
        "sunshine_hours": round(sunshine_hours, 0),
        "max_panels": max_panels,
        "max_area_m2": round(max_area, 1),
        **estimates,
        "estimated_payback_years": estimates["payback_years"],
    }
    logger.info(
        "solar_enriched city=%s sunshine=%.0fh payback=%.1fy savings=R$%.0f/mo",
        city,
        sunshine_hours,
        estimates["payback_years"],
        estimates["monthly_savings_estimate"],
    )
    return result
