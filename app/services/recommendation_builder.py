"""
Recomendações comerciais em duas etapas (PT-BR):

1. ``infer_sales_action_plan`` — plano interno estruturado (não exposto na API).
2. ``render_recommendation_from_plan`` — texto curto para o vendedor (1–3 frases).

``build_sales_recommendation`` = inferência + renderização.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.models import LeadRequest

_VALID_URGENCY = frozenset({"baixa", "media", "alta"})

GOAL_URGENCY_MARKERS = (
    "urgente",
    "urgência",
    "urgencia",
    "o mais rápido",
    "o mais rapido",
    "mais rápido",
    "mais rapido",
    "quero agora",
    "imediato",
    "imediata",
    "reduzir conta",
    "reduzir custo",
    "rápido",
    "rapido",
)

HIGH_BILL_THRESHOLD = 400.0

PriorityLevel = Literal["low", "medium", "high", "max"]


@dataclass(frozen=True)
class SalesActionPlan:
    """
    Plano interno de ação (STEP 1). Não deve aparecer literalmente na resposta ao cliente/lead.
    """

    priority_level: PriorityLevel
    response_time: str
    qualification_checks: tuple[str, ...]
    contact_channel: str
    sales_angle: str
    next_action: str


# --- Helpers ---


def _normalize_urgency_key(urgency: str | None) -> str:
    u = (urgency or "baixa").strip().lower()
    return u if u in _VALID_URGENCY else "baixa"


def goal_suggests_urgency(goal: str | None) -> bool:
    g = (goal or "").lower()
    return any(m in g for m in GOAL_URGENCY_MARKERS)


def timeframe_for(urgency: str | None, score: int) -> str:
    sc = max(0, min(10, int(score)))
    u = _normalize_urgency_key(urgency)
    if sc >= 9:
        return "no mesmo dia ou em até 24 h"
    if u == "alta":
        return "no mesmo dia ou em até 24 h"
    if u == "media":
        return "em até 2 a 5 dias úteis"
    return "em até 5 a 10 dias úteis"


def _city_phrase(city: str | None) -> str:
    c = (city or "").strip()
    return f"em {c}" if c else "na região (confirmar cidade no cadastro)"


def _goal_phrase(goal: str | None, *, max_len: int = 88) -> str:
    g = (goal or "").strip()
    if not g:
        return "objetivo a alinhar na primeira conversa"
    if len(g) > max_len:
        cut = g[:max_len].rsplit(" ", 1)[0]
        return cut + "…" if cut else g[:max_len] + "…"
    return g


def _bill_phrase(monthly_bill: float) -> tuple[str, bool]:
    try:
        b = float(monthly_bill)
    except (TypeError, ValueError):
        b = 0.0
    amount = int(round(max(b, 0.0)))
    line = f"Conta de luz em torno de R$ {amount}/mês"
    return line, b >= HIGH_BILL_THRESHOLD


def _property_label(raw: str | None, property_normalized: str) -> str:
    label = (raw or "").strip()
    if label:
        return label
    pn = (property_normalized or "outro").strip().lower()
    if pn == "apartamento":
        return "apartamento"
    if pn == "comercial":
        return "imóvel comercial"
    if pn == "casa":
        return "casa"
    return "imóvel"


def _capitalize_first_only(text: str) -> str:
    """Primeira letra maiúscula sem lowercar o resto (``str.capitalize`` quebra frases com ';')."""
    t = (text or "").strip()
    if not t:
        return t
    return t[0].upper() + t[1:] if len(t) > 1 else t.upper()


def _checks_to_sentence(checks: tuple[str, ...]) -> str:
    if not checks:
        return "os dados mínimos de imóvel e titularidade"
    if len(checks) == 1:
        return checks[0]
    if len(checks) == 2:
        return f"{checks[0]} e {checks[1]}"
    return ", ".join(checks[:-1]) + f" e {checks[-1]}"


# --- STEP 1: infer structured plan ---


def infer_sales_action_plan(
    lead: LeadRequest,
    score: int,
    urgency: str,
    property_normalized: str,
) -> SalesActionPlan:
    """
    Infere um plano de ação comercial a partir de score, urgência e dados do lead.
    """
    sc = max(0, min(10, int(score)))
    u = _normalize_urgency_key(urgency)
    tf = timeframe_for(u, sc)
    pn = (property_normalized or "outro").strip().lower()
    _, bill_high = _bill_phrase(lead.monthly_bill)
    urgent_goal = goal_suggests_urgency(lead.goal)

    if sc <= 3:
        priority: PriorityLevel = "low"
    elif sc <= 6:
        priority = "medium"
    elif sc <= 8:
        priority = "high"
    else:
        priority = "max"

    checks: list[str] = []
    if priority == "low":
        checks.append("se é titular da conta")
        checks.append("tipo de imóvel e se faz sentido continuar o papo")
    else:
        if pn == "apartamento":
            checks.append("telhado próprio ou área comum do condomínio")
        elif pn == "comercial":
            checks.append("consumo e espaço físico para instalação")
        elif pn == "casa":
            checks.append("telhado e incidência para dimensionar o sistema")
        else:
            checks.append("condições do imóvel para instalação")
        checks.append("titularidade da conta")
        checks.append("se o valor da conta justifica abrir simulação")

    if priority == "low":
        channel = "WhatsApp"
    elif priority == "max" or (priority == "high" and u in ("media", "alta")):
        channel = "WhatsApp ou ligação"
    else:
        channel = "WhatsApp"

    if bill_high:
        angle = "puxar pelo que a conta já gasta hoje e traduzir em economia mensal estimada"
    elif priority == "low":
        angle = "explicar payback e rotina sem cobrar decisão na primeira mensagem"
    else:
        angle = "cruzar viabilidade técnica com números reais da fatura"

    if urgent_goal and priority != "low":
        angle = f"{angle}; o que a pessoa escreveu pede resposta rápida"

    if priority == "low":
        next_a = "disparar material curto e só retomar se ela responder"
    elif priority == "medium":
        next_a = "depois de validar, mandar simulação com os dados dela"
    elif priority == "high":
        next_a = "combinar data para visita técnica ou envio de proposta fechada"
    else:
        next_a = "ligar ou escrever hoje, fechar simulação e marcar proposta ou visita em até 24 h"

    return SalesActionPlan(
        priority_level=priority,
        response_time=tf,
        qualification_checks=tuple(checks),
        contact_channel=channel,
        sales_angle=angle,
        next_action=next_a,
    )


# --- STEP 2: natural language for the rep ---


def render_recommendation_from_plan(
    plan: SalesActionPlan,
    lead: LeadRequest,
    property_normalized: str,
) -> str:
    """
    Converte o plano em 1–3 frases para o vendedor. Não expõe nomes de campos internos.
    """
    city = _city_phrase(lead.city)
    bill_line, _ = _bill_phrase(lead.monthly_bill)
    goal = _goal_phrase(lead.goal)
    prop_label = _property_label(lead.property_type, property_normalized)
    checks_w = _checks_to_sentence(plan.qualification_checks)

    if plan.priority_level == "low":
        s1 = (
            f"Lead {city}, {bill_line}; o que veio na mensagem: «{goal}». "
            f"Pelo {plan.contact_channel}, manda um resumo de economia/payback e confirma {checks_w}."
        )
        s2 = (
            f"{_capitalize_first_only(plan.sales_angle)}; {plan.next_action}, {plan.response_time} — "
            f"se não responder, deixa quieto e não gasta pipeline."
        )
        return f"{s1} {s2}".strip()

    if plan.priority_level == "medium":
        s1 = (
            f"Lead {city} ({prop_label}), {bill_line}. Antes de prometer prazo, fecha {checks_w}."
        )
        s2 = (
            f"{_capitalize_first_only(plan.sales_angle)}. Usa {plan.contact_channel} {plan.response_time} "
            f"para {plan.next_action}."
        )
        return f"{s1} {s2}".strip()

    if plan.priority_level == "high":
        s1 = (
            f"Oportunidade firme {city}: {bill_line}, pautado em «{goal}». Valida {checks_w} na primeira troca."
        )
        s2 = (
            f"{_capitalize_first_only(plan.sales_angle)}. Usa {plan.contact_channel} {plan.response_time} "
            f"para {plan.next_action}."
        )
        return f"{s1} {s2}".strip()

    # max
    s1 = (
        f"Prioridade na fila {city}: {bill_line} e recado claro («{goal}»). "
        f"Confere rápido {checks_w}."
    )
    s2 = (
        f"{_capitalize_first_only(plan.sales_angle)}. Use {plan.contact_channel} ainda hoje: {plan.next_action}."
    )
    return f"{s1} {s2}".strip()


def build_sales_recommendation(
    lead: LeadRequest,
    score: int,
    urgency: str,
    property_normalized: str,
) -> str:
    """Orquestra STEP 1 + STEP 2."""
    plan = infer_sales_action_plan(lead, score, urgency, property_normalized)
    return render_recommendation_from_plan(plan, lead, property_normalized)
