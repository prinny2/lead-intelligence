"""Tests for the webhook endpoints — validates the request parameter fix and form processing."""

import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app


class WebhookFormTests(unittest.TestCase):
    """Test /webhook/form endpoint which requires Request for org_id lookup."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.leads_file = os.path.join(self.temp_dir.name, "leads.jsonl")
        self.env_patcher = patch.dict(
            os.environ, {"LEADS_FILE": self.leads_file}, clear=False
        )
        self.env_patcher.start()
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.env_patcher.stop()
        self.temp_dir.cleanup()

    @patch("app.routes.webhook.get_ai_qualification_with_solar")
    def test_form_webhook_basic_lead(self, mock_ai_solar) -> None:
        """POST /webhook/form with basic fields returns a valid qualification."""
        mock_ai_solar.return_value = (
            {"score": 7, "urgency": "média", "recommendation": "Agendar visita."},
            None,
        )
        response = self.client.post(
            "/webhook/form",
            json={"name": "João", "city": "Belém", "monthly_bill": 500},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("score", data)
        self.assertIn("decision", data)

    @patch("app.routes.webhook.get_ai_qualification_with_solar")
    def test_form_webhook_with_api_key_param(self, mock_ai_solar) -> None:
        """POST /webhook/form?api_key=... uses Request to resolve org_id."""
        mock_ai_solar.return_value = (
            {"score": 6, "urgency": "baixa", "recommendation": "Seguir acompanhando."},
            None,
        )
        with patch("app.routes.webhook._lookup_api_key_firestore", create=True):
            response = self.client.post(
                "/webhook/form?api_key=sk-test-123",
                json={"name": "Maria", "city": "Recife", "monthly_bill": 300},
            )
        self.assertEqual(response.status_code, 200)

    @patch("app.routes.webhook.get_ai_qualification_with_solar")
    def test_form_webhook_portuguese_aliases(self, mock_ai_solar) -> None:
        """POST /webhook/form with Portuguese field aliases works."""
        mock_ai_solar.return_value = (
            {"score": 5, "urgency": "baixa", "recommendation": "Nutrir."},
            None,
        )
        response = self.client.post(
            "/webhook/form",
            json={"nome": "Carlos", "cidade": "Manaus", "monthly_bill": 800},
        )
        self.assertEqual(response.status_code, 200)

    def test_form_webhook_missing_required_fields(self) -> None:
        """POST /webhook/form without name/city returns 422."""
        response = self.client.post(
            "/webhook/form",
            json={"email": "test@example.com"},
        )
        self.assertEqual(response.status_code, 422)

    @patch("app.routes.webhook.get_ai_qualification_with_solar")
    def test_form_webhook_raw_delegates_to_form_webhook(self, mock_ai_solar) -> None:
        """POST /webhook/form/raw also works (delegates to form_webhook)."""
        mock_ai_solar.return_value = (
            {"score": 8, "urgency": "alta", "recommendation": "Contato imediato."},
            None,
        )
        response = self.client.post(
            "/webhook/form/raw",
            json={"name": "Ana", "city": "Fortaleza", "monthly_bill": 900},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("score", data)


if __name__ == "__main__":
    unittest.main()
