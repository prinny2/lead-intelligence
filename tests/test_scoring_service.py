import unittest

from app.models import LeadRequest
from app.services.scoring_service import hybrid_score


class ScoringServiceTests(unittest.TestCase):
    def test_low_intent_lead_gets_penalized(self) -> None:
        lead = LeadRequest(
            name="Maria",
            city="Fortaleza",
            monthly_bill=150,
            property_type="apartamento",
            goal="so queria entender como funciona",
        )

        result = hybrid_score(
            lead,
            {"score": 8, "urgency": "alta", "recommendation": "ligar agora"},
        )

        self.assertEqual(result.response.score, 0)
        self.assertEqual(result.response.urgency, "baixa")
        self.assertEqual(
            result.response.recommendation,
            "Lead em fase de pesquisa; enviar material educativo e acompanhar depois.",
        )

    def test_invalid_ai_output_falls_back_safely(self) -> None:
        lead = LeadRequest(
            name="Paulo",
            city="Natal",
            monthly_bill=450,
            property_type="casa",
            goal="reduzir conta",
        )

        result = hybrid_score(
            lead,
            {"score": "not-a-number", "urgency": "urgente", "recommendation": ""},
        )

        self.assertEqual(result.ai_raw_score, None)
        self.assertEqual(result.response.score, 6)
        self.assertEqual(result.response.urgency, "baixa")
        self.assertEqual(
            result.response.recommendation,
            "Interesse moderado; fazer follow-up em 1–2 semanas.",
        )


if __name__ == "__main__":
    unittest.main()
