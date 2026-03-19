"""Heuristic analysis of free-text interest messages (keywords only, no LLM)."""

from __future__ import annotations

import re
import unicodedata


def analyze_interest_message(text: str | None) -> dict[str, bool]:
    """Extract simple boolean signals from *text* using normalization and keywords.

    Empty or non-string input yields all False.
    """
    if text is None or not isinstance(text, str):
        return {k: False for k in _SIGNAL_KEYS}

    normalized = _normalize_text(text)
    if not normalized:
        return {k: False for k in _SIGNAL_KEYS}

    return {
        "urgent_intent": _any_phrase(normalized, ("urgente", "o mais rápido", "preciso logo", "essa semana")),
        "quote_request": _any_phrase(
            normalized,
            ("orçamento", "orcamento", "cotação", "cotacao", "proposta", "quanto custa", "valor"),
        ),
        "curiosity_only": _any_phrase(
            normalized,
            (
                "como funciona",
                "só queria entender",
                "so queria entender",
                "queria saber",
                "só curiosidade",
                "so curiosidade",
                "apenas pesquisando",
            ),
        ),
        "financing_interest": _any_phrase(
            normalized,
            ("financiamento", "parcelado", "sem entrada", "boleto", "crédito", "credito"),
        ),
        "ownership_signal": _any_phrase(
            normalized,
            ("sou proprietário", "sou proprietario", "casa própria", "casa propria", "imovel proprio", "imóvel próprio"),
        ),
        "rented_signal": _any_phrase(
            normalized,
            ("alugado", "aluguel", "sou inquilino", "condomínio alugado", "condominio alugado"),
        ),
        "commercial_signal": _any_phrase(
            normalized,
            ("comercial", "empresa", "cnpj", "indústria", "industria", "galpão", "galpao", "loja"),
        ),
        "high_bill_signal": _any_phrase(
            normalized,
            ("conta alta", "gasto muito", "acima de 500", "mais de 600", "kwh", "conta veio alta"),
        ),
        "low_bill_signal": _any_phrase(
            normalized,
            ("conta baixa", "pouco consumo", "gasto pouco", "apenas led"),
        ),
        "decision_maker_signal": _any_phrase(
            normalized,
            ("sou o dono", "decido eu", "diretor", "gerente", "sócio", "socio", "responsável pela obra", "responsavel pela obra"),
        ),
    }


_SIGNAL_KEYS = (
    "urgent_intent",
    "quote_request",
    "curiosity_only",
    "financing_interest",
    "ownership_signal",
    "rented_signal",
    "commercial_signal",
    "high_bill_signal",
    "low_bill_signal",
    "decision_maker_signal",
)


def _normalize_text(text: str) -> str:
    """Lowercase, strip accents for robust PT-BR matching."""
    lowered = text.lower().strip()
    normalized = unicodedata.normalize("NFD", lowered)
    without_marks = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    return re.sub(r"\s+", " ", without_marks)


def _any_phrase(haystack: str, phrases: tuple[str, ...]) -> bool:
    return any(p in haystack for p in phrases)
