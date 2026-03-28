"""Contact form endpoint — POST /contact."""

import json
import logging
import os
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger("lead_intelligence")

_DEFAULT_CONTACTS_FILE = Path(__file__).resolve().parent.parent.parent / "contacts.jsonl"


def _contacts_file() -> Path:
    override = os.getenv("CONTACTS_FILE")
    if override and override.strip():
        return Path(override).expanduser().resolve()
    return _DEFAULT_CONTACTS_FILE


class ContactRequest(BaseModel):
    contact: str
    source: str = "landing"


class ContactResponse(BaseModel):
    ok: bool
    message: str


@router.post("/contact", response_model=ContactResponse)
async def save_contact(body: ContactRequest) -> ContactResponse:
    value = body.contact.strip()
    if not value:
        return ContactResponse(ok=False, message="contato vazio")

    record = {
        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "contact": value,
        "source": body.source,
    }

    try:
        path = _contacts_file()
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        logger.info("new_contact source=%s contact=%s", body.source, value[:6] + "***")
    except Exception as e:
        logger.warning("contact_save_failed error=%s", str(e))

    # Notify admin — never blocks the response
    try:
        _notify_new_contact(value, body.source)
    except Exception:
        pass

    return ContactResponse(ok=True, message="Recebido! Vamos te chamar em breve.")


def _notify_new_contact(contact: str, source: str) -> None:
    """Send admin email when someone submits the landing contact form. Silent on failure."""
    admin_email = os.getenv("NOTIFY_ADMIN_EMAIL", "").strip()
    resend_key = os.getenv("RESEND_API_KEY", "").strip()
    if not admin_email or not resend_key:
        return

    from_email = os.getenv("NOTIFY_FROM_EMAIL", "leads@leadsolar.com.br")
    ts = datetime.now(UTC).strftime("%d/%m/%Y às %H:%M")

    html = f"""<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#060c18;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif">
  <div style="max-width:460px;margin:32px auto;background:#0d1825;border:1px solid #1a2e48;border-radius:16px;overflow:hidden">
    <div style="background:linear-gradient(135deg,#f59e0b,#d97706);padding:20px 24px">
      <div style="font-size:11px;font-weight:700;color:rgba(0,0,0,.6);text-transform:uppercase;letter-spacing:.1em">LeadSolar · Novo Contato</div>
      <div style="font-size:22px;font-weight:900;color:#000;margin-top:4px">Alguém quer testar grátis 🚀</div>
    </div>
    <div style="padding:24px">
      <div style="background:#132030;border:1px solid #1a2e48;border-radius:10px;padding:16px;margin-bottom:16px">
        <div style="font-size:11px;font-weight:700;color:#6b85a0;text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px">WhatsApp / Contato</div>
        <div style="font-size:22px;font-weight:800;color:#f59e0b">{contact}</div>
      </div>
      <div style="font-size:13px;color:#6b85a0;margin-bottom:4px">Origem: <strong style="color:#e2e8f0">{source}</strong></div>
      <div style="font-size:13px;color:#6b85a0">Recebido em: <strong style="color:#e2e8f0">{ts} UTC</strong></div>
      <div style="margin-top:20px;background:rgba(245,158,11,.08);border:1px solid rgba(245,158,11,.2);border-radius:8px;padding:12px;font-size:12px;color:#f59e0b">
        ⏱ Entre em contato em até 30 minutos para maior taxa de conversão.
      </div>
    </div>
  </div>
</body>
</html>"""

    try:
        import httpx
        httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {resend_key}", "Content-Type": "application/json"},
            json={
                "from": from_email,
                "to": [admin_email],
                "subject": f"🚀 Novo contato LeadSolar: {contact[:30]}",
                "html": html,
            },
            timeout=5.0,
        )
        logger.info("contact_admin_notified admin=%s", admin_email)
    except Exception as e:
        logger.debug("contact_notify_failed error=%s", e)
