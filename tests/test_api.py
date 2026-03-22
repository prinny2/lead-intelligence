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
        self.env_patcher = patch.dict(
            os.environ, {"LEADS_FILE": self.leads_file}, clear=False)
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
                "recommendation": "Contato imediato.",
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


if __name__ == "__main__":
    unittest.main()
