"""Tests for app.services.whatsapp_builder — pure Python, no external deps."""

import unittest

from app.models import LeadRequest
from app.services.whatsapp_builder import _first_name, build_whatsapp_message


def _make_lead(**kwargs) -> LeadRequest:
    defaults = {
        "name": "Maria Silva",
        "city": "Fortaleza",
        "monthly_bill": 400.0,
        "property_type": "casa",
        "goal": "reduzir conta",
    }
    defaults.update(kwargs)
    return LeadRequest(**defaults)


class FirstNameTests(unittest.TestCase):
    def test_empty_string_returns_voce(self) -> None:
        self.assertEqual(_first_name(""), "você")

    def test_none_equivalent_returns_voce(self) -> None:
        self.assertEqual(_first_name("   "), "você")

    def test_single_name_is_capitalized(self) -> None:
        self.assertEqual(_first_name("ana"), "Ana")

    def test_multi_word_returns_first_only(self) -> None:
        self.assertEqual(_first_name("João Pedro Silva"), "João")

    def test_already_capitalized_unchanged(self) -> None:
        self.assertEqual(_first_name("Carlos"), "Carlos")


class OpeningLineTests(unittest.TestCase):
    """Opening line varies by urgency / score."""

    def test_urgency_alta_triggers_hoje_mesmo(self) -> None:
        lead = _make_lead()
        msg = build_whatsapp_message(lead, score=5, urgency="alta")
        self.assertIn("hoje mesmo", msg)

    def test_score_8_triggers_hoje_mesmo(self) -> None:
        lead = _make_lead()
        msg = build_whatsapp_message(lead, score=8, urgency="media")
        self.assertIn("hoje mesmo", msg)

    def test_score_5_uses_generic_interest_opening(self) -> None:
        lead = _make_lead()
        msg = build_whatsapp_message(lead, score=5, urgency="media")
        self.assertIn("tem interesse em energia solar", msg)
        self.assertNotIn("hoje mesmo", msg)

    def test_score_below_5_uses_soft_opener(self) -> None:
        lead = _make_lead()
        msg = build_whatsapp_message(lead, score=3, urgency="baixa")
        self.assertIn("Passando para falar", msg)

    def test_lead_name_appears_in_message(self) -> None:
        lead = _make_lead(name="Beatriz")
        msg = build_whatsapp_message(lead, score=5, urgency="media")
        self.assertIn("Beatriz", msg)


class SavingsPercentageTests(unittest.TestCase):
    def test_high_bill_shows_95_percent(self) -> None:
        lead = _make_lead(monthly_bill=600.0)
        msg = build_whatsapp_message(lead, score=5, urgency="media")
        self.assertIn("até 95%", msg)

    def test_low_bill_shows_70_percent(self) -> None:
        lead = _make_lead(monthly_bill=300.0)
        msg = build_whatsapp_message(lead, score=5, urgency="media")
        self.assertIn("até 70%", msg)

    def test_bill_exactly_600_shows_95_percent(self) -> None:
        lead = _make_lead(monthly_bill=600.0)
        msg = build_whatsapp_message(lead, score=5, urgency="media")
        self.assertIn("até 95%", msg)


class ValueLineTests(unittest.TestCase):
    def test_positive_bill_includes_amount(self) -> None:
        lead = _make_lead(monthly_bill=450.0)
        msg = build_whatsapp_message(lead, score=5, urgency="media")
        self.assertIn("R$450/mês", msg)

    def test_zero_bill_uses_generic_savings_line(self) -> None:
        lead = _make_lead(monthly_bill=0.0)
        msg = build_whatsapp_message(lead, score=5, urgency="media")
        # Should not include "R$0/mês" — uses generic line instead
        self.assertNotIn("R$0/mês", msg)
        self.assertIn("dá pra economizar", msg)


class ContextLineTests(unittest.TestCase):
    """Context line varies by property type and ownership."""

    def test_casa_owned_mentions_casa_propria(self) -> None:
        lead = _make_lead(property_type="casa", ownership_status="owned")
        msg = build_whatsapp_message(lead, score=5, urgency="media")
        self.assertIn("casa própria", msg)

    def test_casa_owned_proprio_mentions_casa_propria(self) -> None:
        lead = _make_lead(property_type="casa", ownership_status="próprio")
        msg = build_whatsapp_message(lead, score=5, urgency="media")
        self.assertIn("casa própria", msg)

    def test_casa_without_ownership_uses_generic_casa(self) -> None:
        lead = _make_lead(property_type="casa", ownership_status=None)
        msg = build_whatsapp_message(lead, score=5, urgency="media")
        # Should mention "casa" but not "própria"
        self.assertIn("casa", msg)
        self.assertNotIn("casa própria", msg)

    def test_residencial_owned_mentions_casa_propria(self) -> None:
        lead = _make_lead(property_type="residencial", ownership_status="owned")
        msg = build_whatsapp_message(lead, score=5, urgency="media")
        self.assertIn("casa própria", msg)

    def test_comercial_property_type(self) -> None:
        lead = _make_lead(property_type="comercial")
        msg = build_whatsapp_message(lead, score=5, urgency="media")
        self.assertIn("imóvel comercial", msg)

    def test_empresa_property_type(self) -> None:
        lead = _make_lead(property_type="empresa")
        msg = build_whatsapp_message(lead, score=5, urgency="media")
        self.assertIn("imóvel comercial", msg)

    def test_apartamento_property_type(self) -> None:
        lead = _make_lead(property_type="apartamento")
        msg = build_whatsapp_message(lead, score=5, urgency="media")
        self.assertIn("apartamentos", msg)

    def test_apto_abbreviation(self) -> None:
        lead = _make_lead(property_type="apto")
        msg = build_whatsapp_message(lead, score=5, urgency="media")
        self.assertIn("apartamentos", msg)

    def test_unknown_property_type_falls_back_to_city(self) -> None:
        lead = _make_lead(property_type="galpão", city="Recife")
        msg = build_whatsapp_message(lead, score=5, urgency="media")
        self.assertIn("Recife", msg)

    def test_city_appears_in_context_line(self) -> None:
        lead = _make_lead(city="Salvador", property_type="casa")
        msg = build_whatsapp_message(lead, score=5, urgency="media")
        self.assertIn("Salvador", msg)


class CallToActionTests(unittest.TestCase):
    def test_high_score_cta_mentions_agora(self) -> None:
        lead = _make_lead()
        msg = build_whatsapp_message(lead, score=8, urgency="media")
        self.assertIn("agora", msg)

    def test_medium_score_cta_mentions_rapida(self) -> None:
        lead = _make_lead()
        msg = build_whatsapp_message(lead, score=5, urgency="media")
        self.assertIn("rápida", msg)

    def test_low_score_cta_mentions_material(self) -> None:
        lead = _make_lead()
        msg = build_whatsapp_message(lead, score=3, urgency="baixa")
        self.assertIn("material explicativo", msg)

    def test_all_ctas_include_sem_compromisso_or_leva(self) -> None:
        lead = _make_lead()
        for score, urgency in [(8, "media"), (5, "media"), (3, "baixa")]:
            msg = build_whatsapp_message(lead, score=score, urgency=urgency)
            self.assertTrue(
                "Sem compromisso" in msg or "Leva menos" in msg,
                f"Expected soft close in message for score={score}",
            )


class MessageStructureTests(unittest.TestCase):
    def test_message_is_non_empty_string(self) -> None:
        lead = _make_lead()
        msg = build_whatsapp_message(lead, score=5, urgency="media")
        self.assertIsInstance(msg, str)
        self.assertGreater(len(msg), 50)

    def test_message_parts_are_space_joined(self) -> None:
        """Message should be a single string (no newlines from join)."""
        lead = _make_lead()
        msg = build_whatsapp_message(lead, score=5, urgency="media")
        # Parts are joined with spaces
        self.assertNotIn("\n", msg)


if __name__ == "__main__":
    unittest.main()
