"""Tests for app.services.gemini_service — mirrors ai_service test structure."""

import os
import sys
import types
import unittest
from unittest.mock import MagicMock, patch

from app.models import LeadRequest


def _make_lead(**kwargs) -> LeadRequest:
    defaults = {
        "name": "Ana",
        "city": "Fortaleza",
        "monthly_bill": 500.0,
        "property_type": "casa",
        "goal": "quero instalar",
    }
    defaults.update(kwargs)
    return LeadRequest(**defaults)


def _make_genai_mock(response_text: str) -> MagicMock:
    """Build a minimal mock of the google.generativeai module."""
    mock_genai = MagicMock()
    mock_response = MagicMock()
    mock_response.text = response_text
    mock_model = MagicMock()
    mock_model.generate_content.return_value = mock_response
    mock_genai.GenerativeModel.return_value = mock_model
    return mock_genai


class GeminiApiKeyTests(unittest.TestCase):
    def test_returns_none_when_api_key_missing(self) -> None:
        env = {k: v for k, v in os.environ.items() if k != "GEMINI_API_KEY"}
        with patch.dict(os.environ, env, clear=True):
            from app.services.gemini_service import get_gemini_qualification
            result = get_gemini_qualification(_make_lead())
        self.assertIsNone(result)

    def test_returns_none_when_api_key_is_empty_string(self) -> None:
        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
            from app.services.gemini_service import get_gemini_qualification
            result = get_gemini_qualification(_make_lead())
        self.assertIsNone(result)

    def test_returns_none_when_api_key_is_whitespace_only(self) -> None:
        with patch.dict(os.environ, {"GEMINI_API_KEY": "   "}):
            from app.services.gemini_service import get_gemini_qualification
            result = get_gemini_qualification(_make_lead())
        self.assertIsNone(result)


class GeminiImportErrorTest(unittest.TestCase):
    def test_returns_none_when_google_generativeai_not_installed(self) -> None:
        """If the google-generativeai package is missing, return None gracefully."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
            # Temporarily hide the module from the import system
            with patch.dict(sys.modules, {"google.generativeai": None}):
                # Re-import to ensure the import path is exercised
                import importlib
                import app.services.gemini_service as gem_mod
                importlib.reload(gem_mod)
                result = gem_mod.get_gemini_qualification(_make_lead())
        self.assertIsNone(result)


class GeminiSuccessTests(unittest.TestCase):
    def _run_with_mock(self, response_text: str, extra_env: dict | None = None):
        env = {"GEMINI_API_KEY": "test-key", **(extra_env or {})}
        mock_genai = _make_genai_mock(response_text)
        with patch.dict(os.environ, env):
            with patch.dict(sys.modules, {"google.generativeai": mock_genai}):
                import importlib
                import app.services.gemini_service as gem_mod
                importlib.reload(gem_mod)
                return gem_mod.get_gemini_qualification(_make_lead())

    def test_successful_plain_json_returns_parsed_dict(self) -> None:
        result = self._run_with_mock(
            '{"score": 8, "urgency": "alta", "recommendation": "Ligar agora."}'
        )
        self.assertIsNotNone(result)
        self.assertEqual(result["score"], 8)
        self.assertEqual(result["urgency"], "alta")
        self.assertEqual(result["recommendation"], "Ligar agora.")

    def test_markdown_fenced_json_is_parsed(self) -> None:
        result = self._run_with_mock(
            '```json\n{"score": 3, "urgency": "baixa", "recommendation": "Educação."}\n```'
        )
        self.assertIsNotNone(result)
        self.assertEqual(result["score"], 3)

    def test_custom_model_from_env_is_used(self) -> None:
        mock_genai = _make_genai_mock(
            '{"score": 5, "urgency": "media", "recommendation": "ok"}'
        )
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key", "GEMINI_MODEL": "gemini-pro"}):
            with patch.dict(sys.modules, {"google.generativeai": mock_genai}):
                import importlib
                import app.services.gemini_service as gem_mod
                importlib.reload(gem_mod)
                gem_mod.get_gemini_qualification(_make_lead())

        called_model = mock_genai.GenerativeModel.call_args.kwargs.get(
            "model_name"
        ) or mock_genai.GenerativeModel.call_args.args[0]
        self.assertEqual(called_model, "gemini-pro")

    def test_whitespace_model_env_falls_back_to_default(self) -> None:
        mock_genai = _make_genai_mock(
            '{"score": 5, "urgency": "media", "recommendation": "ok"}'
        )
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key", "GEMINI_MODEL": "  "}):
            with patch.dict(sys.modules, {"google.generativeai": mock_genai}):
                import importlib
                import app.services.gemini_service as gem_mod
                importlib.reload(gem_mod)
                gem_mod.get_gemini_qualification(_make_lead())

        called_model = mock_genai.GenerativeModel.call_args.kwargs.get(
            "model_name"
        ) or mock_genai.GenerativeModel.call_args.args[0]
        self.assertEqual(called_model, "gemini-2.0-flash")


class GeminiFailureTests(unittest.TestCase):
    def _run_with_exception(self, exc: Exception):
        mock_genai = MagicMock()
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = exc
        mock_genai.GenerativeModel.return_value = mock_model
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
            with patch.dict(sys.modules, {"google.generativeai": mock_genai}):
                import importlib
                import app.services.gemini_service as gem_mod
                importlib.reload(gem_mod)
                return gem_mod.get_gemini_qualification(_make_lead())

    def test_api_exception_returns_none(self) -> None:
        result = self._run_with_exception(Exception("connection timeout"))
        self.assertIsNone(result)

    def test_non_json_response_returns_none(self) -> None:
        mock_genai = _make_genai_mock("Desculpe, não posso ajudar.")
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
            with patch.dict(sys.modules, {"google.generativeai": mock_genai}):
                import importlib
                import app.services.gemini_service as gem_mod
                importlib.reload(gem_mod)
                result = gem_mod.get_gemini_qualification(_make_lead())
        self.assertIsNone(result)

    def test_empty_response_returns_none(self) -> None:
        mock_genai = _make_genai_mock("")
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
            with patch.dict(sys.modules, {"google.generativeai": mock_genai}):
                import importlib
                import app.services.gemini_service as gem_mod
                importlib.reload(gem_mod)
                result = gem_mod.get_gemini_qualification(_make_lead())
        self.assertIsNone(result)


class GeminiPromptBuilderTests(unittest.TestCase):
    """Verify optional fields and solar context appear in the prompt."""

    def _capture_prompt(self, lead: LeadRequest, solar_context=None, extra_env=None):
        mock_genai = _make_genai_mock(
            '{"score": 5, "urgency": "media", "recommendation": "ok"}'
        )
        env = {"GEMINI_API_KEY": "test-key", **(extra_env or {})}
        with patch.dict(os.environ, env):
            with patch.dict(sys.modules, {"google.generativeai": mock_genai}):
                import importlib
                import app.services.gemini_service as gem_mod
                importlib.reload(gem_mod)
                gem_mod.get_gemini_qualification(lead, solar_context=solar_context)
        # Return the prompt string passed to generate_content
        return mock_genai.GenerativeModel.return_value.generate_content.call_args.args[0]

    def test_optional_email_included_when_set(self) -> None:
        lead = _make_lead(email="ana@empresa.com")
        prompt = self._capture_prompt(lead)
        self.assertIn("ana@empresa.com", prompt)

    def test_optional_phone_included_when_set(self) -> None:
        lead = _make_lead(phone="85999999999")
        prompt = self._capture_prompt(lead)
        self.assertIn("85999999999", prompt)

    def test_optional_company_included_when_set(self) -> None:
        lead = _make_lead(company="Empresa Solar")
        prompt = self._capture_prompt(lead)
        self.assertIn("Empresa Solar", prompt)

    def test_solar_context_sunshine_hours_included(self) -> None:
        lead = _make_lead()
        solar = {"sunshine_hours": 1800.0, "max_panels": 20, "estimated_payback_years": 5.5}
        prompt = self._capture_prompt(lead, solar_context=solar)
        self.assertIn("1800", prompt)
        self.assertIn("5.5", prompt)

    def test_no_solar_context_omits_solar_block(self) -> None:
        lead = _make_lead()
        prompt = self._capture_prompt(lead, solar_context=None)
        self.assertNotIn("Horas de sol", prompt)


if __name__ == "__main__":
    unittest.main()
