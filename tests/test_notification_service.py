"""Tests for app.services.notification_service — verifies email dispatch logic."""

import os
import unittest
from unittest.mock import MagicMock, patch

from app.services.notification_service import (
    HOT_SCORE_THRESHOLD,
    _hot_lead_html,
    _send_email,
    notify_hot_lead,
)


def _notify(**kwargs):
    """Helper to call notify_hot_lead with sensible defaults."""
    defaults = {
        "org_id": "seller@solar.com",
        "lead_name": "João Silva",
        "lead_city": "Fortaleza",
        "monthly_bill": 600.0,
        "score": 9,
        "urgency": "alta",
        "whatsapp_message": "Olá João!",
        "recommendation": "Ligue agora.",
    }
    defaults.update(kwargs)
    return notify_hot_lead(**defaults)


class NotifyScoreGateTests(unittest.TestCase):
    """notify_hot_lead should exit early when score is below threshold."""

    @patch("app.services.notification_service._resend_key", return_value="test-key")
    @patch("app.services.notification_service._get_customer_email", return_value="mgr@solar.com")
    @patch("app.services.notification_service._send_email")
    def test_score_below_threshold_does_not_send(self, mock_send, mock_email, mock_key):
        _notify(score=HOT_SCORE_THRESHOLD - 1)
        mock_send.assert_not_called()

    @patch("app.services.notification_service._resend_key", return_value="test-key")
    @patch("app.services.notification_service._get_customer_email", return_value="mgr@solar.com")
    @patch("app.services.notification_service._send_email")
    def test_score_exactly_at_threshold_sends_email(self, mock_send, mock_email, mock_key):
        _notify(score=HOT_SCORE_THRESHOLD)
        mock_send.assert_called_once()

    @patch("app.services.notification_service._resend_key", return_value="test-key")
    @patch("app.services.notification_service._get_customer_email", return_value="mgr@solar.com")
    @patch("app.services.notification_service._send_email")
    def test_score_above_threshold_sends_email(self, mock_send, mock_email, mock_key):
        _notify(score=10)
        mock_send.assert_called_once()


class NotifyApiKeyGateTests(unittest.TestCase):
    """notify_hot_lead should exit early when RESEND_API_KEY is missing."""

    @patch("app.services.notification_service._get_customer_email", return_value="mgr@solar.com")
    @patch("app.services.notification_service._send_email")
    def test_no_resend_key_does_not_send(self, mock_send, mock_email):
        with patch.dict(os.environ, {}, clear=False):
            # Patch _resend_key to return ""
            with patch("app.services.notification_service._resend_key", return_value=""):
                _notify(score=9)
        mock_send.assert_not_called()


class NotifyCustomerEmailGateTests(unittest.TestCase):
    """notify_hot_lead should exit early when no customer email is found."""

    @patch("app.services.notification_service._resend_key", return_value="test-key")
    @patch("app.services.notification_service._get_customer_email", return_value=None)
    @patch("app.services.notification_service._send_email")
    def test_no_customer_email_does_not_send(self, mock_send, mock_email, mock_key):
        _notify(score=9)
        mock_send.assert_not_called()


class SendEmailTests(unittest.TestCase):
    """Tests for the _send_email helper."""

    def _mock_response(self, status_code: int) -> MagicMock:
        mock_r = MagicMock()
        mock_r.status_code = status_code
        mock_r.text = "ok"
        return mock_r

    def test_success_200_returns_true(self) -> None:
        with patch.dict(os.environ, {"RESEND_API_KEY": "test-key"}):
            with patch("httpx.post", return_value=self._mock_response(200)) as mock_post:
                result = _send_email("to@example.com", "Subject", "<html></html>")
        self.assertTrue(result)

    def test_success_201_returns_true(self) -> None:
        with patch.dict(os.environ, {"RESEND_API_KEY": "test-key"}):
            with patch("httpx.post", return_value=self._mock_response(201)):
                result = _send_email("to@example.com", "Subject", "<html></html>")
        self.assertTrue(result)

    def test_non_2xx_returns_false(self) -> None:
        with patch.dict(os.environ, {"RESEND_API_KEY": "test-key"}):
            with patch("httpx.post", return_value=self._mock_response(500)):
                result = _send_email("to@example.com", "Subject", "<html></html>")
        self.assertFalse(result)

    def test_exception_returns_false(self) -> None:
        with patch.dict(os.environ, {"RESEND_API_KEY": "test-key"}):
            with patch("httpx.post", side_effect=Exception("timeout")):
                result = _send_email("to@example.com", "Subject", "<html></html>")
        self.assertFalse(result)

    def test_missing_key_returns_false(self) -> None:
        env = {k: v for k, v in os.environ.items() if k != "RESEND_API_KEY"}
        with patch.dict(os.environ, env, clear=True):
            with patch("httpx.post") as mock_post:
                result = _send_email("to@example.com", "Subject", "<html></html>")
        self.assertFalse(result)
        mock_post.assert_not_called()


class HotLeadHtmlTests(unittest.TestCase):
    """Tests for the _hot_lead_html template function."""

    def _make_html(self, **kwargs) -> str:
        defaults = {
            "lead_name": "Ana Costa",
            "lead_city": "Recife",
            "monthly_bill": 750.0,
            "score": 9,
            "urgency": "alta",
            "whatsapp_message": "Olá Ana!",
            "recommendation": "Ligar hoje.",
        }
        defaults.update(kwargs)
        return _hot_lead_html(**defaults)

    def test_html_contains_lead_name(self) -> None:
        html = self._make_html()
        self.assertIn("Ana Costa", html)

    def test_html_contains_lead_city(self) -> None:
        html = self._make_html()
        self.assertIn("Recife", html)

    def test_html_contains_score(self) -> None:
        html = self._make_html(score=9)
        self.assertIn("9/10", html)

    def test_html_contains_recommendation(self) -> None:
        html = self._make_html()
        self.assertIn("Ligar hoje.", html)

    def test_html_contains_monthly_bill(self) -> None:
        html = self._make_html(monthly_bill=750.0)
        self.assertIn("750", html)

    def test_urgency_alta_renders_label(self) -> None:
        html = self._make_html(urgency="alta")
        self.assertIn("Alta", html)

    def test_urgency_media_renders_label(self) -> None:
        html = self._make_html(urgency="media")
        self.assertIn("Média", html)

    def test_urgency_baixa_renders_label(self) -> None:
        html = self._make_html(urgency="baixa")
        self.assertIn("Baixa", html)

    def test_unknown_urgency_renders_raw_value(self) -> None:
        html = self._make_html(urgency="unknown_level")
        self.assertIn("unknown_level", html)

    def test_whatsapp_block_present_when_message_provided(self) -> None:
        html = self._make_html(whatsapp_message="Olá João!")
        self.assertIn("MENSAGEM WHATSAPP", html)
        self.assertIn("Olá João!", html)

    def test_whatsapp_block_absent_when_message_is_none(self) -> None:
        html = self._make_html(whatsapp_message=None)
        self.assertNotIn("MENSAGEM WHATSAPP", html)

    def test_html_is_valid_doctype(self) -> None:
        html = self._make_html()
        self.assertTrue(html.strip().startswith("<!DOCTYPE html>"))


if __name__ == "__main__":
    unittest.main()
