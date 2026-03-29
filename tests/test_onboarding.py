import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


class TestOnboardingEndpoints(unittest.TestCase):
    """Tests for the new Google Login / API key recovery endpoints."""

    def setUp(self) -> None:
        self.client = TestClient(app)

    # ── POST /api/link-google ──────────────────────────────────────────

    @patch("app.auth.link_google_account")
    def test_link_google_success(self, mock_link):
        mock_link.return_value = True
        response = self.client.post(
            "/api/link-google",
            json={"firebase_token": "tok123", "api_key": "ls_key_abc"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"linked": True})
        mock_link.assert_called_once_with("tok123", "ls_key_abc")

    @patch("app.auth.link_google_account")
    def test_link_google_failure_returns_400(self, mock_link):
        mock_link.return_value = False
        response = self.client.post(
            "/api/link-google",
            json={"firebase_token": "tok123", "api_key": "ls_key_abc"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("vincular", response.json()["detail"].lower())

    def test_link_google_missing_fields_returns_422(self):
        response = self.client.post(
            "/api/link-google",
            json={"firebase_token": "tok123"},
        )
        self.assertEqual(response.status_code, 422)

    # ── POST /api/recover-key ──────────────────────────────────────────

    @patch("app.auth.get_api_key_for_firebase_token")
    def test_recover_key_success(self, mock_get):
        mock_get.return_value = "ls_recovered_key_123"
        response = self.client.post(
            "/api/recover-key",
            json={"firebase_token": "tok123"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"api_key": "ls_recovered_key_123"})
        mock_get.assert_called_once_with("tok123")

    @patch("app.auth.get_api_key_for_firebase_token")
    def test_recover_key_not_found_returns_404(self, mock_get):
        mock_get.return_value = None
        response = self.client.post(
            "/api/recover-key",
            json={"firebase_token": "tok123"},
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn("conta", response.json()["detail"].lower())

    def test_recover_key_missing_fields_returns_422(self):
        response = self.client.post(
            "/api/recover-key",
            json={},
        )
        self.assertEqual(response.status_code, 422)

    # ── GET /recover-key ───────────────────────────────────────────────

    def test_recover_key_page_returns_html(self):
        response = self.client.get("/recover-key")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])
        self.assertIn("Recuperar", response.text)
        self.assertIn("recoverWithGoogle", response.text)

    @patch.dict("os.environ", {"FIREBASE_WEB_API_KEY": "AIza-test", "FIREBASE_AUTH_DOMAIN": "proj.firebaseapp.com"})
    def test_recover_key_page_injects_firebase_config(self):
        response = self.client.get("/recover-key")
        self.assertEqual(response.status_code, 200)
        self.assertIn("AIza-test", response.text)
        self.assertIn("proj.firebaseapp.com", response.text)

    # ── GET /onboarding ────────────────────────────────────────────────

    def test_onboarding_page_returns_html(self):
        response = self.client.get("/onboarding")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])

    def test_onboarding_page_has_google_link_button(self):
        response = self.client.get("/onboarding")
        self.assertEqual(response.status_code, 200)
        self.assertIn("googleLinkBtn", response.text)
        self.assertIn("linkGoogleAccount", response.text)

    @patch.dict("os.environ", {"FIREBASE_WEB_API_KEY": "AIza-onb", "FIREBASE_AUTH_DOMAIN": "onb.firebaseapp.com"})
    def test_onboarding_page_injects_firebase_config(self):
        response = self.client.get("/onboarding")
        self.assertEqual(response.status_code, 200)
        self.assertIn("AIza-onb", response.text)
        self.assertIn("onb.firebaseapp.com", response.text)


if __name__ == "__main__":
    unittest.main()
