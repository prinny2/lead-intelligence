"""Snapshots for deterministic sales recommendations."""

import unittest

from app.models import LeadRequest
from app.services.recommendation_builder import (
    build_sales_recommendation,
    infer_sales_action_plan,
    render_recommendation_from_plan,
)


class RecommendationBuilderTests(unittest.TestCase):
    def test_final_text_does_not_expose_internal_plan_keys(self) -> None:
        lead = LeadRequest(
            name="X",
            city="Curitiba",
            monthly_bill=300,
            property_type="casa",
            goal="orçamento",
        )
        text = build_sales_recommendation(lead, 5, "media", "casa")
        self.assertNotIn("priority_level", text)
        self.assertNotIn("qualification_checks", text)
        self.assertNotIn("SalesActionPlan", text)

    def test_infer_and_render_match_build_sales_recommendation(self) -> None:
        lead = LeadRequest(
            name="Y",
            city="Recife",
            monthly_bill=200,
            property_type="apartamento",
            goal="dúvidas",
        )
        plan = infer_sales_action_plan(lead, 3, "baixa", "apartamento")
        a = render_recommendation_from_plan(plan, lead, "apartamento")
        b = build_sales_recommendation(lead, 3, "baixa", "apartamento")
        self.assertEqual(a, b)

    def test_profile_low_exploratory_apartment(self) -> None:
        lead = LeadRequest(
            name="A",
            city="Fortaleza",
            monthly_bill=150,
            property_type="apartamento",
            goal="só queria entender",
        )
        text = build_sales_recommendation(lead, 2, "baixa", "apartamento")
        self.assertIn("Fortaleza", text)
        self.assertIn("WhatsApp", text)
        self.assertIn("5 a 10 dias úteis", text)
        self.assertIn("pipeline", text.lower())

    def test_profile_mid_house_medium_bill_savings(self) -> None:
        lead = LeadRequest(
            name="B",
            city="Natal",
            monthly_bill=450,
            property_type="casa",
            goal="reduzir a conta",
        )
        text = build_sales_recommendation(lead, 5, "media", "casa")
        self.assertIn("Natal", text)
        self.assertIn("simulação", text.lower())
        self.assertIn("2 a 5 dias úteis", text)
        self.assertIn("WhatsApp", text)

    def test_profile_high_commercial_urgent(self) -> None:
        lead = LeadRequest(
            name="C",
            city="São Paulo",
            monthly_bill=2000,
            property_type="comercial",
            goal="instalar o quanto antes",
        )
        text = build_sales_recommendation(lead, 8, "alta", "comercial")
        self.assertIn("São Paulo", text)
        self.assertIn("instalação", text.lower())
        self.assertIn("24 h", text)
        self.assertIn("simulação", text.lower())

    def test_profile_top_casa_immediate_cta(self) -> None:
        lead = LeadRequest(
            name="D",
            city="Belo Horizonte",
            monthly_bill=900,
            property_type="casa",
            goal="fechar proposta",
        )
        text = build_sales_recommendation(lead, 10, "alta", "casa")
        self.assertIn("Belo Horizonte", text)
        self.assertIn("Prioridade na fila", text)
        self.assertIn("24 h", text)
        self.assertIn("WhatsApp", text)


if __name__ == "__main__":
    unittest.main()
