"""Tests for onboarding BASE_URL resolution — validates that guides and HTML
respect the BASE_URL environment variable instead of hardcoding the production URL."""

import os
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

_PROD_URL = "https://lead-intelligence-production.up.railway.app"
_CUSTOM_URL = "https://my-custom-deploy.example.com"


class OnboardingBaseUrlTests(unittest.TestCase):
    """Test that onboarding endpoints replace hardcoded URLs with BASE_URL."""

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

    def test_onboarding_guide_returns_all_integrations(self) -> None:
        """GET /onboarding/guide returns a list of integration keys."""
        response = self.client.get("/onboarding/guide")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("integrations", data)
        self.assertIn("guides", data)
        self.assertIsInstance(data["integrations"], list)
        self.assertGreater(len(data["integrations"]), 0)

    def test_onboarding_guide_single_integration(self) -> None:
        """GET /onboarding/guide?integration=google_forms returns that guide."""
        response = self.client.get("/onboarding/guide?integration=google_forms")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("label", data)
        self.assertIn("steps", data)

    def test_onboarding_guide_invalid_integration(self) -> None:
        """GET /onboarding/guide?integration=nonexistent returns all guides."""
        response = self.client.get("/onboarding/guide?integration=nonexistent")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("integrations", data)

    @patch("app.routes.onboarding._BASE_URL", _CUSTOM_URL)
    def test_resolve_guides_replaces_prod_url(self) -> None:
        """When BASE_URL differs from production, guide URLs are replaced."""
        from app.routes.onboarding import _resolve_guides

        guides = _resolve_guides()
        raw = str(guides)
        self.assertNotIn(_PROD_URL, raw)
        self.assertIn(_CUSTOM_URL, raw)

    @patch("app.routes.onboarding._BASE_URL", _PROD_URL)
    def test_resolve_guides_no_replace_when_default(self) -> None:
        """When BASE_URL equals production URL, guides are returned as-is."""
        from app.routes.onboarding import _resolve_guides

        guides = _resolve_guides()
        raw = str(guides)
        self.assertIn(_PROD_URL, raw)

    @patch("app.routes.onboarding._BASE_URL", _CUSTOM_URL)
    def test_onboarding_html_replaces_prod_url(self) -> None:
        """GET /onboarding replaces hardcoded production URL in HTML with BASE_URL."""
        response = self.client.get("/onboarding")
        self.assertEqual(response.status_code, 200)
        html = response.text
        self.assertNotIn(_PROD_URL, html)
        self.assertIn(_CUSTOM_URL, html)

    def test_onboarding_html_renders(self) -> None:
        """GET /onboarding returns HTML content."""
        response = self.client.get("/onboarding")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers.get("content-type", ""))


if __name__ == "__main__":
    unittest.main()
