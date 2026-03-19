import os
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.leads_file = os.path.join(self.temp_dir.name, "leads.jsonl")
        self.env_patcher = patch.dict(os.environ, {"LEADS_FILE": self.leads_file}, clear=False)
        self.env_patcher.start()
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.env_patcher.stop()
        self.temp_dir.cleanup()

    @patch("app.routes.leads.get_ai_qualification")
    def test_post_lead_returns_hybrid_score(self, mock_ai) -> None:
        mock_ai.return_value = {
            "score": 8,
            "urgency": "alta",
            "recommendation": "Contato imediato.",
        }

        response = self.client.post(
            "/lead",
            json={
                "name": "Ana",
                "city": "Fortaleza",
                "monthly_bill": 850,
                "property_type": "casa",
                "goal": "quero reduzir conta o mais rapido possivel",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "score": 10,
                "urgency": "alta",
                "recommendation": "Lead promissor; vale contato comercial rápido.",
            },
        )

    def test_post_lead_rejects_blank_fields(self) -> None:
        response = self.client.post(
            "/lead",
            json={
                "name": "   ",
                "city": "Fortaleza",
                "monthly_bill": 200,
                "property_type": "casa",
                "goal": "reduzir conta",
            },
        )

        self.assertEqual(response.status_code, 422)

    def test_stats_uses_configured_storage_file(self) -> None:
        self.client.post(
            "/lead",
            json={
                "name": "Leo",
                "city": "Recife",
                "monthly_bill": 500,
                "property_type": "casa",
                "goal": "reduzir conta",
            },
        )

        response = self.client.get("/stats")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total_leads"], 1)

    def test_root_returns_ok(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_health_returns_ok(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_stats_returns_zeros_when_no_leads(self) -> None:
        response = self.client.get("/stats")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["total_leads"], 0)
        self.assertEqual(body["average_score"], 0.0)
        self.assertEqual(body["high_quality_leads"], 0)
        self.assertEqual(body["low_quality_leads"], 0)

    @patch("app.routes.leads.get_ai_qualification")
    def test_stats_calculates_high_and_low_quality_counts(self, mock_ai) -> None:
        lead_base = {
            "city": "Salvador",
            "monthly_bill": 500,
            "property_type": "casa",
            "goal": "quero instalar",
        }
        # High-quality lead: ai score 8 → delta 0 → final 8
        mock_ai.return_value = {"score": 8, "urgency": "alta", "recommendation": "ok"}
        self.client.post("/lead", json={"name": "High", **lead_base})
        # Low-quality lead: ai score 2 → delta 0 → final 2
        mock_ai.return_value = {"score": 2, "urgency": "baixa", "recommendation": "ok"}
        self.client.post("/lead", json={"name": "Low", **lead_base})
        # Medium lead: ai score 5 → delta 0 → final 5
        mock_ai.return_value = {"score": 5, "urgency": "media", "recommendation": "ok"}
        self.client.post("/lead", json={"name": "Mid", **lead_base})

        response = self.client.get("/stats")
        body = response.json()
        self.assertEqual(body["total_leads"], 3)
        self.assertEqual(body["high_quality_leads"], 1)
        self.assertEqual(body["low_quality_leads"], 1)
        self.assertAlmostEqual(body["average_score"], round((8 + 2 + 5) / 3, 2))

    @patch("app.routes.leads.get_ai_qualification")
    def test_post_lead_when_ai_returns_none_falls_back_to_rules(self, mock_ai) -> None:
        mock_ai.return_value = None

        response = self.client.post(
            "/lead",
            json={
                "name": "Carlos",
                "city": "Manaus",
                "monthly_bill": 450,
                "property_type": "casa",
                "goal": "quero instalar",
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        # No AI output → base=5, delta=0 (no urgency word, no low-intent word, bill not >700/<200)
        self.assertEqual(body["score"], 5)
        self.assertIn(body["urgency"], ("baixa", "media", "alta"))
        self.assertIsInstance(body["recommendation"], str)

    @patch("app.routes.leads.get_ai_qualification")
    @patch("app.routes.leads.save_lead")
    def test_post_lead_returns_response_even_when_storage_fails(
        self, mock_save, mock_ai
    ) -> None:
        mock_ai.return_value = {"score": 7, "urgency": "alta", "recommendation": "ok"}
        mock_save.side_effect = Exception("disk full")

        response = self.client.post(
            "/lead",
            json={
                "name": "Beatriz",
                "city": "Curitiba",
                "monthly_bill": 750,
                "property_type": "casa",
                "goal": "reduzir conta",
            },
        )

        self.assertEqual(response.status_code, 200)

    def test_post_lead_rejects_negative_monthly_bill(self) -> None:
        response = self.client.post(
            "/lead",
            json={
                "name": "Pedro",
                "city": "Campinas",
                "monthly_bill": -50,
                "property_type": "casa",
                "goal": "reduzir conta",
            },
        )
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
