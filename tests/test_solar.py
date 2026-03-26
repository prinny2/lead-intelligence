"""Tests for lead_intelligence.solar."""

from lead_intelligence.solar import solar_insights


def test_owned_and_strong_bill():
    out = solar_insights(
        {"ownership_status": "owned", "monthly_bill": 600, "property_type": "casa"},
        min_monthly_bill=250,
    )
    assert out["signals"]["owned_property"] is True
    assert out["signals"]["strong_bill_signal"] is True


def test_rented_apartment_reasons():
    out = solar_insights(
        {"ownership_status": "rented", "property_type": "apartamento", "monthly_bill": 100}
    )
    assert out["signals"].get("rented_property") is True
    assert any("Apartamento" in r for r in out["reasons"])
