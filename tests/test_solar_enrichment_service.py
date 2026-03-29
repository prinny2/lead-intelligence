"""Tests for app.services.solar_enrichment_service.

Pure-math tests cover _estimate_payback without any mocking.
HTTP tests mock httpx to avoid real network calls.
"""

import unittest
from unittest.mock import MagicMock, patch

from app.services.solar_enrichment_service import (
    _KWH_PER_KWP_YEAR,
    _TARIFF_BRL_PER_KWH,
    _estimate_payback,
    _geocode_city_cached,
    _get_solar_insights_cached,
    enrich_lead_solar,
)


def _clear_caches() -> None:
    _geocode_city_cached.cache_clear()
    _get_solar_insights_cached.cache_clear()


class EstimatePaybackTests(unittest.TestCase):
    """Pure-math tests — no mocking required."""

    def test_returns_all_expected_keys(self) -> None:
        result = _estimate_payback(monthly_bill=500.0, sunshine_hours=1800.0, max_panels=30)
        for key in ("kwp_system", "system_cost_brl", "monthly_savings_estimate", "payback_years"):
            self.assertIn(key, result)

    def test_positive_bill_produces_positive_savings(self) -> None:
        result = _estimate_payback(500.0, 1800.0, 30)
        self.assertGreater(result["monthly_savings_estimate"], 0)

    def test_very_low_bill_floors_kwp_to_1(self) -> None:
        # A tiny monthly bill should still result in at least 1 kWp
        result = _estimate_payback(monthly_bill=1.0, sunshine_hours=1800.0, max_panels=30)
        self.assertGreaterEqual(result["kwp_system"], 1.0)

    def test_very_high_bill_caps_kwp_to_max_panels_factor(self) -> None:
        # With a huge bill and only 5 panels, kwp is capped at max_panels * 0.4 = 2.0
        result = _estimate_payback(monthly_bill=999999.0, sunshine_hours=1800.0, max_panels=5)
        self.assertLessEqual(result["kwp_system"], 5 * 0.4)

    def test_zero_sunshine_falls_back_to_kwh_per_kwp_constant(self) -> None:
        # sunshine_hours=0 should use the _KWH_PER_KWP_YEAR fallback, not divide by zero
        result = _estimate_payback(monthly_bill=500.0, sunshine_hours=0, max_panels=30)
        self.assertGreater(result["kwp_system"], 0)
        self.assertIsFinite(result["payback_years"])

    def test_payback_years_capped_at_30(self) -> None:
        # Degenerate case: nearly zero savings → payback capped to 30y
        result = _estimate_payback(monthly_bill=0.01, sunshine_hours=1800.0, max_panels=1)
        self.assertLessEqual(result["payback_years"], 30.0)

    def test_system_cost_proportional_to_kwp(self) -> None:
        r1 = _estimate_payback(200.0, 1800.0, 30)
        r2 = _estimate_payback(800.0, 1800.0, 30)
        # Larger bill → larger system → higher cost
        self.assertGreater(r2["system_cost_brl"], r1["system_cost_brl"])

    def assertIsFinite(self, value: float, msg: str = "") -> None:
        import math
        self.assertFalse(math.isnan(value), msg or f"Expected finite, got NaN")
        self.assertFalse(math.isinf(value), msg or f"Expected finite, got Inf")


class EnrichLeadSolarTests(unittest.TestCase):
    """Integration tests for enrich_lead_solar — httpx is mocked."""

    def setUp(self) -> None:
        _clear_caches()

    def tearDown(self) -> None:
        _clear_caches()

    def _mock_geocode_response(self, lat: float = -3.7172, lng: float = -38.5437) -> MagicMock:
        mock_r = MagicMock()
        mock_r.json.return_value = {
            "results": [{"geometry": {"location": {"lat": lat, "lng": lng}}}]
        }
        return mock_r

    def _mock_solar_response(
        self,
        sunshine_hours: float = 1800.0,
        max_panels: int = 25,
        max_area: float = 45.0,
        status_code: int = 200,
    ) -> MagicMock:
        mock_r = MagicMock()
        mock_r.status_code = status_code
        mock_r.json.return_value = {
            "solarPotential": {
                "maxSunshineHoursPerYear": sunshine_hours,
                "maxArrayPanelsCount": max_panels,
                "maxArrayAreaMeters2": max_area,
            }
        }
        return mock_r

    # --- No API key ---

    def test_returns_none_when_no_api_key(self) -> None:
        with patch("app.services.solar_enrichment_service._api_key", return_value=""):
            result = enrich_lead_solar("Fortaleza", "CE", 500.0)
        self.assertIsNone(result)

    # --- Geocoding failures ---

    def test_returns_none_when_geocoding_returns_empty_results(self) -> None:
        mock_r = MagicMock()
        mock_r.json.return_value = {"results": []}
        with patch("app.services.solar_enrichment_service._api_key", return_value="key"):
            with patch("httpx.get", return_value=mock_r):
                result = enrich_lead_solar("Nowhere", "XX", 500.0)
        self.assertIsNone(result)

    def test_returns_none_when_geocoding_raises_exception(self) -> None:
        with patch("app.services.solar_enrichment_service._api_key", return_value="key"):
            with patch("httpx.get", side_effect=Exception("network error")):
                result = enrich_lead_solar("Fortaleza", "CE", 500.0)
        self.assertIsNone(result)

    # --- Solar API failures ---

    def test_returns_none_when_solar_api_returns_non_200(self) -> None:
        with patch("app.services.solar_enrichment_service._api_key", return_value="key"):
            with patch("httpx.get", side_effect=[
                self._mock_geocode_response(),         # first call = geocode OK
                self._mock_solar_response(status_code=404),  # second call = solar fails
            ]):
                result = enrich_lead_solar("Fortaleza", "CE", 500.0)
        self.assertIsNone(result)

    def test_returns_none_when_solar_api_raises_exception(self) -> None:
        with patch("app.services.solar_enrichment_service._api_key", return_value="key"):
            with patch("httpx.get", side_effect=[
                self._mock_geocode_response(),
                Exception("solar api timeout"),
            ]):
                result = enrich_lead_solar("Fortaleza", "CE", 500.0)
        self.assertIsNone(result)

    def test_returns_none_when_sunshine_hours_is_zero(self) -> None:
        with patch("app.services.solar_enrichment_service._api_key", return_value="key"):
            with patch("httpx.get", side_effect=[
                self._mock_geocode_response(),
                self._mock_solar_response(sunshine_hours=0),
            ]):
                result = enrich_lead_solar("Fortaleza", "CE", 500.0)
        self.assertIsNone(result)

    # --- Success path ---

    def test_full_success_returns_dict_with_expected_keys(self) -> None:
        with patch("app.services.solar_enrichment_service._api_key", return_value="key"):
            with patch("httpx.get", side_effect=[
                self._mock_geocode_response(lat=-3.7172, lng=-38.5437),
                self._mock_solar_response(sunshine_hours=1800.0, max_panels=25),
            ]):
                result = enrich_lead_solar("Fortaleza", "CE", 500.0)

        self.assertIsNotNone(result)
        for key in ("lat", "lng", "sunshine_hours", "max_panels", "kwp_system",
                    "system_cost_brl", "monthly_savings_estimate", "estimated_payback_years"):
            self.assertIn(key, result)

    def test_full_success_lat_lng_correct(self) -> None:
        with patch("app.services.solar_enrichment_service._api_key", return_value="key"):
            with patch("httpx.get", side_effect=[
                self._mock_geocode_response(lat=-3.7172, lng=-38.5437),
                self._mock_solar_response(),
            ]):
                result = enrich_lead_solar("Fortaleza", "CE", 500.0)

        self.assertAlmostEqual(result["lat"], -3.7172, places=3)
        self.assertAlmostEqual(result["lng"], -38.5437, places=3)

    def test_sunshine_hours_in_result(self) -> None:
        with patch("app.services.solar_enrichment_service._api_key", return_value="key"):
            with patch("httpx.get", side_effect=[
                self._mock_geocode_response(),
                self._mock_solar_response(sunshine_hours=1750.0),
            ]):
                result = enrich_lead_solar("Fortaleza", "CE", 500.0)
        self.assertEqual(result["sunshine_hours"], 1750.0)

    def test_state_none_does_not_crash(self) -> None:
        with patch("app.services.solar_enrichment_service._api_key", return_value="key"):
            with patch("httpx.get", side_effect=[
                self._mock_geocode_response(),
                self._mock_solar_response(),
            ]):
                result = enrich_lead_solar("Fortaleza", None, 500.0)
        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()
