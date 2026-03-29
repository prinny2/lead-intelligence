"""Tests for app.services.ai_service – covers Anthropic integration paths."""

import os
import unittest
from unittest.mock import MagicMock, patch

from app.models import LeadRequest
from app.services.ai_service import DEFAULT_MODEL, get_ai_qualification


def _make_lead(**kwargs):
    defaults = {
        "name": "Ana",
        "city": "Fortaleza",
        "monthly_bill": 500.0,
        "property_type": "casa",
        "goal": "quero instalar",
    }
    defaults.update(kwargs)
    return LeadRequest(**defaults)


def _make_message(text: str) -> MagicMock:
    """Build a minimal mock that mimics an Anthropic message response."""
    content_block = MagicMock()
    content_block.text = text
    msg = MagicMock()
    msg.content = [content_block]
    return msg


class AiServiceApiKeyTests(unittest.TestCase):
    # --- API-key validation ---

    def test_returns_none_when_api_key_missing(self) -> None:
        env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
        with patch.dict(os.environ, env, clear=True):
            result = get_ai_qualification(_make_lead())
        self.assertIsNone(result)

    def test_returns_none_when_api_key_is_empty_string(self) -> None:
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""}):
            result = get_ai_qualification(_make_lead())
        self.assertIsNone(result)

    def test_returns_none_when_api_key_is_whitespace_only(self) -> None:
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "   "}):
            result = get_ai_qualification(_make_lead())
        self.assertIsNone(result)


class AiServiceSuccessTests(unittest.TestCase):
    # --- Successful call ---

    @patch("app.services.ai_service.anthropic.Anthropic")
    def test_successful_call_returns_parsed_dict(self, mock_anthropic_cls) -> None:
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.return_value = _make_message(
            '{"score": 8, "urgency": "alta", "recommendation": "Ligar agora."}'
        )

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            result = get_ai_qualification(_make_lead())

        self.assertIsNotNone(result)
        self.assertEqual(result["score"], 8)
        self.assertEqual(result["urgency"], "alta")
        self.assertEqual(result["recommendation"], "Ligar agora.")

    @patch("app.services.ai_service.anthropic.Anthropic")
    def test_markdown_wrapped_json_is_parsed(self, mock_anthropic_cls) -> None:
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.return_value = _make_message(
            '```json\n{"score": 3, "urgency": "baixa", "recommendation": "Educação."}\n```'
        )

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            result = get_ai_qualification(_make_lead())

        self.assertIsNotNone(result)
        self.assertEqual(result["score"], 3)

    @patch("app.services.ai_service.anthropic.Anthropic")
    def test_optional_fields_included_in_prompt(self, mock_anthropic_cls) -> None:
        """Email, phone, company, state, ownership_status, interest_message appear in prompt."""
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.return_value = _make_message(
            '{"score": 7, "urgency": "media", "recommendation": "ok"}'
        )

        lead = _make_lead(
            email="ana@empresa.com",
            phone="85999999999",
            company="Empresa Solar",
            state="CE",
            ownership_status="owned",
            interest_message="quero instalar logo",
        )
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            get_ai_qualification(lead)

        call_kwargs = mock_client.messages.create.call_args.kwargs
        messages_content = call_kwargs["messages"][0]["content"]
        self.assertIn("ana@empresa.com", messages_content)
        self.assertIn("85999999999", messages_content)
        self.assertIn("Empresa Solar", messages_content)
        self.assertIn("CE", messages_content)
        self.assertIn("owned", messages_content)
        self.assertIn("quero instalar logo", messages_content)


class AiServiceFailureTests(unittest.TestCase):
    # --- Failure / error paths ---

    @patch("app.services.ai_service.anthropic.Anthropic")
    def test_api_exception_returns_none(self, mock_anthropic_cls) -> None:
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.side_effect = Exception("connection timeout")

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            result = get_ai_qualification(_make_lead())

        self.assertIsNone(result)

    @patch("app.services.ai_service.anthropic.Anthropic")
    def test_non_json_response_returns_none(self, mock_anthropic_cls) -> None:
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.return_value = _make_message(
            "Desculpe, não posso ajudar com isso."
        )

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            result = get_ai_qualification(_make_lead())

        self.assertIsNone(result)

    @patch("app.services.ai_service.anthropic.Anthropic")
    def test_empty_response_content_returns_none(self, mock_anthropic_cls) -> None:
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.return_value = _make_message("")

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            result = get_ai_qualification(_make_lead())

        self.assertIsNone(result)


class AiServiceModelSelectionTests(unittest.TestCase):
    # --- Model selection ---

    @patch("app.services.ai_service.anthropic.Anthropic")
    def test_uses_custom_model_from_env(self, mock_anthropic_cls) -> None:
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.return_value = _make_message(
            '{"score": 5, "urgency": "media", "recommendation": "ok"}'
        )

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key", "ANTHROPIC_MODEL": "claude-opus-4-6"}):
            get_ai_qualification(_make_lead())

        called_model = mock_client.messages.create.call_args.kwargs["model"]
        self.assertEqual(called_model, "claude-opus-4-6")

    @patch("app.services.ai_service.anthropic.Anthropic")
    def test_whitespace_model_env_falls_back_to_default(self, mock_anthropic_cls) -> None:
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.return_value = _make_message(
            '{"score": 5, "urgency": "media", "recommendation": "ok"}'
        )

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key", "ANTHROPIC_MODEL": "   "}):
            get_ai_qualification(_make_lead())

        called_model = mock_client.messages.create.call_args.kwargs["model"]
        self.assertEqual(called_model, DEFAULT_MODEL)

    @patch("app.services.ai_service.anthropic.Anthropic")
    def test_missing_model_env_falls_back_to_default(self, mock_anthropic_cls) -> None:
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.return_value = _make_message(
            '{"score": 5, "urgency": "media", "recommendation": "ok"}'
        )

        env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_MODEL"}
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key", **env}, clear=True):
            get_ai_qualification(_make_lead())

        called_model = mock_client.messages.create.call_args.kwargs["model"]
        self.assertEqual(called_model, DEFAULT_MODEL)


if __name__ == "__main__":
    unittest.main()
