"""Hot-lead email notifications via Resend (https://resend.com).

Fires when a qualified lead scores >= HOT_SCORE_THRESHOLD.
Set RESEND_API_KEY in Railway env vars to activate.
Free tier: 100 emails/day — sufficient for early customers.

Falls back silently if the key is missing or the request fails.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger("lead_intelligence.notify")

HOT_SCORE_THRESHOLD = int(os.getenv("HOT_LEAD_SCORE_THRESHOLD", "7"))
FROM_EMAIL = os.getenv("NOTIFY_FROM_EMAIL", "leads@leadsolar.com.br")


def _resend_key() -> str:
    return os.getenv("RESEND_API_KEY", "").strip()


def _get_customer_email(org_id: str) -> str | None:
    """Look up the customer's notification email from Firestore."""
    try:
        import firebase_admin
        from firebase_admin import firestore
        if not firebase_admin._apps:
            return None
        db = firestore.client()
        docs = (
            db.collection("customers")
            .where("email", "==", org_id)
            .where("status", "==", "active")
            .limit(1)
            .get()
        )
        for doc in docs:
            data = doc.to_dict()
            return data.get("notify_email") or data.get("email") or None
    except Exception as e:
        logger.debug("customer_email_lookup_failed org=%s error=%s", org_id, e)
    return None


def _send_email(to: str, subject: str, html: str) -> bool:
    key = _resend_key()
    if not key:
        logger.debug("resend_key_missing — notification skipped")
        return False
    try:
        import httpx
        r = httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"from": FROM_EMAIL, "to": [to], "subject": subject, "html": html},
            timeout=8.0,
        )
        if r.status_code in (200, 201):
            logger.info("notification_sent to=%s subject=%s", to, subject)
            return True
        logger.warning("resend_failed status=%s body=%s", r.status_code, r.text[:200])
    except Exception as e:
        logger.warning("notification_error error=%s", e)
    return False


def _hot_lead_html(
    lead_name: str,
    lead_city: str,
    monthly_bill: float,
    score: int,
    urgency: str,
    whatsapp_message: str | None,
    recommendation: str,
) -> str:
    urgency_label = {"alta": "🔴 Alta", "media": "🟡 Média", "baixa": "⚪ Baixa"}.get(urgency, urgency)
    wa_block = ""
    if whatsapp_message:
        wa_block = f"""
        <div style="background:#0d2218;border:1px solid #16a34a33;border-radius:8px;padding:16px;margin-top:16px">
          <div style="font-size:11px;font-weight:700;color:#22c55e;text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px">📱 MENSAGEM WHATSAPP PRONTA</div>
          <div style="font-size:14px;color:#bbf7d0;line-height:1.6">{whatsapp_message}</div>
        </div>"""
    return f"""<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#060c18;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif">
  <div style="max-width:520px;margin:32px auto;background:#0d1825;border:1px solid #1a2e48;border-radius:16px;overflow:hidden">
    <div style="background:linear-gradient(135deg,#f59e0b,#d97706);padding:20px 24px">
      <div style="font-size:11px;font-weight:700;color:rgba(0,0,0,.6);text-transform:uppercase;letter-spacing:.1em">LeadSolar · Lead Quente</div>
      <div style="font-size:22px;font-weight:900;color:#000;margin-top:4px">Novo lead quente: {lead_name}</div>
    </div>
    <div style="padding:24px">
      <div style="display:flex;gap:12px;margin-bottom:20px;flex-wrap:wrap">
        <div style="background:#132030;border:1px solid #1a2e48;border-radius:8px;padding:12px 16px;flex:1;min-width:120px;text-align:center">
          <div style="font-size:28px;font-weight:900;color:#f59e0b">{score}/10</div>
          <div style="font-size:11px;color:#6b85a0;text-transform:uppercase;letter-spacing:.06em">Pontuação</div>
        </div>
        <div style="background:#132030;border:1px solid #1a2e48;border-radius:8px;padding:12px 16px;flex:1;min-width:120px;text-align:center">
          <div style="font-size:18px;font-weight:700;color:#f1f5f9">{urgency_label}</div>
          <div style="font-size:11px;color:#6b85a0;text-transform:uppercase;letter-spacing:.06em">Urgência</div>
        </div>
        <div style="background:#132030;border:1px solid #1a2e48;border-radius:8px;padding:12px 16px;flex:1;min-width:120px;text-align:center">
          <div style="font-size:18px;font-weight:700;color:#f1f5f9">R${monthly_bill:.0f}</div>
          <div style="font-size:11px;color:#6b85a0;text-transform:uppercase;letter-spacing:.06em">Conta/mês</div>
        </div>
      </div>
      <div style="margin-bottom:8px">
        <span style="font-size:13px;color:#6b85a0">Cidade:</span>
        <span style="font-size:13px;color:#f1f5f9;margin-left:6px;font-weight:600">{lead_city}</span>
      </div>
      <div style="background:#132030;border:1px solid #1a2e48;border-radius:8px;padding:14px;margin-top:12px">
        <div style="font-size:11px;font-weight:700;color:#0ea5e9;text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px">Recomendação para o vendedor</div>
        <div style="font-size:13px;color:#e2e8f0;line-height:1.6">{recommendation}</div>
      </div>
      {wa_block}
      <div style="margin-top:20px;text-align:center">
        <a href="https://lead-intelligence-production.up.railway.app/dashboard"
           style="display:inline-block;background:linear-gradient(135deg,#f59e0b,#d97706);color:#000;font-weight:700;padding:12px 28px;border-radius:8px;text-decoration:none;font-size:14px">
          Ver no Dashboard →
        </a>
      </div>
    </div>
    <div style="padding:16px 24px;border-top:1px solid #1a2e48;text-align:center">
      <div style="font-size:11px;color:#6b85a0">LeadSolar · Qualificação de leads solar</div>
    </div>
  </div>
</body>
</html>"""


def notify_hot_lead(
    *,
    org_id: str,
    lead_name: str,
    lead_city: str,
    monthly_bill: float,
    score: int,
    urgency: str,
    whatsapp_message: str | None,
    recommendation: str,
) -> None:
    """Send hot-lead email if score >= threshold. Never raises — always silent on failure."""
    if score < HOT_SCORE_THRESHOLD:
        return
    if not _resend_key():
        return

    to = _get_customer_email(org_id)
    if not to:
        logger.debug("no_notify_email org=%s", org_id)
        return

    subject = f"🔥 Lead quente: {lead_name} de {lead_city} — nota {score}/10"
    html = _hot_lead_html(lead_name, lead_city, monthly_bill, score, urgency, whatsapp_message, recommendation)
    _send_email(to, subject, html)
