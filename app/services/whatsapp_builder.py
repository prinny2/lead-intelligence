"""Generate copy-paste WhatsApp messages for salespeople (PT-BR)."""

from __future__ import annotations

from app.models import LeadRequest


def build_whatsapp_message(lead: LeadRequest, score: int, urgency: str) -> str:
    """Return a short, human WhatsApp opener based on lead data and score."""
    name = _first_name(lead.name)
    bill = int(round(max(lead.monthly_bill, 0)))
    city = lead.city.strip()
    ptype = (lead.property_type or "").strip().lower()
    ownership = (lead.ownership_status or "").strip().lower()

    # Savings hook — headline number
    savings_pct = "até 95%" if bill >= 600 else "até 70%"

    # Opening line varies by urgency / score
    if urgency == "alta" or score >= 8:
        opening = f"Olá, {name}! Vi seu interesse em energia solar e queria falar com você hoje mesmo."
    elif score >= 5:
        opening = f"Olá, {name}! Vi que você tem interesse em energia solar."
    else:
        opening = f"Olá, {name}! Passando para falar sobre energia solar."

    # Core value line using real data
    if bill > 0:
        value_line = (
            f"Com uma conta de cerca de R${bill}/mês, você pode economizar {savings_pct} "
            f"e praticamente zerar esse custo com solar."
        )
    else:
        value_line = f"Com energia solar, dá pra economizar {savings_pct} na conta de luz."

    # Context line (property / ownership)
    context_line = ""
    if ptype in ("casa", "residencial") and ownership in ("owned", "próprio", "proprio"):
        context_line = f"Para uma casa própria em {city}, a instalação costuma ser bem direta."
    elif ptype in ("casa", "residencial"):
        context_line = f"Para uma casa em {city}, posso te mostrar como funciona rapidinho."
    elif ptype in ("comercial", "empresa"):
        context_line = f"Para um imóvel comercial em {city}, o retorno costuma ser ainda mais rápido."
    elif ptype in ("apartamento", "apto", "ap"):
        context_line = f"Em {city}, já temos soluções para apartamentos também."
    else:
        context_line = f"Posso te mostrar uma simulação para {city}."

    # CTA varies by score
    if score >= 8:
        cta = "Posso te mandar uma simulação personalizada agora? Leva menos de 2 minutos."
    elif score >= 5:
        cta = "Quer que eu faça uma simulação rápida pra você? Sem compromisso."
    else:
        cta = "Se quiser, posso te mandar um material explicativo. Sem compromisso nenhum."

    parts = [opening, value_line]
    if context_line:
        parts.append(context_line)
    parts.append(cta)

    return " ".join(parts)


def _first_name(full_name: str) -> str:
    parts = (full_name or "").strip().split()
    return parts[0].capitalize() if parts else "você"
