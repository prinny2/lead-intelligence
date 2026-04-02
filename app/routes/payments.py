"""Stripe payment routes — checkout, success page, customer portal, webhook."""

import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel

from app.services.audit_service import log_event
from app.services.stripe_service import (
    PLANS,
    create_checkout_session,
    create_portal_session,
    get_customer_by_email,
    handle_webhook,
    provision_customer,
)

router = APIRouter()
logger = logging.getLogger("lead_intelligence.payments")


# ──────────────────────────────────────────────
# Request models
# ──────────────────────────────────────────────

class CheckoutRequest(BaseModel):
    plan: str
    email: str | None = None
    billing: str = "monthly"  # "monthly" | "annual"


class PortalRequest(BaseModel):
    email: str


# ──────────────────────────────────────────────
# Checkout
# ──────────────────────────────────────────────

@router.post("/checkout/create")
async def create_checkout(body: CheckoutRequest, request: Request):
    if body.plan not in PLANS:
        raise HTTPException(status_code=400, detail="Plano inválido.")
    if body.billing not in ("monthly", "annual"):
        raise HTTPException(status_code=400, detail="Cobrança inválida. Use 'monthly' ou 'annual'.")
    try:
        url = create_checkout_session(body.plan, body.email, body.billing)
        ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (
            request.client.host if request.client else "unknown"
        )
        log_event("checkout_started", ip=ip, endpoint="/checkout/create", method="POST",
                  status_code=200, extra={"plan": body.plan, "billing": body.billing})
        return {"checkout_url": url}
    except Exception as e:
        logger.error("checkout_error: %s", e)
        raise HTTPException(status_code=500, detail="Erro ao criar sessão de pagamento.")


# ──────────────────────────────────────────────
# Success page
# ──────────────────────────────────────────────

@router.get("/checkout/success")
async def checkout_success(session_id: str):
    try:
        customer = provision_customer(session_id)
    except Exception as e:
        logger.error("provision_error: %s", e)
        raise HTTPException(status_code=400, detail="Sessão inválida ou expirada.")

    plan = customer.get("plan", "pro")
    already = customer.get("already_provisioned", False)
    api_key = customer.get("api_key", "")

    log_event("customer_provisioned", endpoint="/checkout/success",
              method="GET", status_code=200, extra={"plan": plan, "already": already})

    # Always redirect to onboarding — api_key is present in both new and already_provisioned cases
    redirect_url = f"/onboarding?api_key={api_key}" if api_key else "/onboarding"
    return RedirectResponse(url=redirect_url, status_code=303)


# ──────────────────────────────────────────────
# Customer portal (manage subscription)
# ──────────────────────────────────────────────

@router.post("/customer/portal")
async def customer_portal(body: PortalRequest):
    """Return a Stripe Customer Portal URL for an existing customer."""
    customer = get_customer_by_email(body.email)
    if not customer:
        raise HTTPException(status_code=404, detail="Email não encontrado. Verifique o email usado no pagamento.")

    stripe_customer_id = customer.get("stripe_customer_id", "")
    if not stripe_customer_id:
        raise HTTPException(status_code=400, detail="Conta sem ID Stripe. Entre em contato com o suporte.")

    try:
        portal_url = create_portal_session(stripe_customer_id)
        return {"portal_url": portal_url}
    except Exception as e:
        logger.error("portal_error: %s", e)
        raise HTTPException(status_code=500, detail="Erro ao abrir portal. Tente novamente.")


# ──────────────────────────────────────────────
# Webhook
# ──────────────────────────────────────────────

@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Stripe webhook — handles subscription lifecycle events."""
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    try:
        event_type = handle_webhook(payload, sig)
        return {"received": True, "event": event_type}
    except Exception as e:
        logger.error("webhook_error: %s", e)
        raise HTTPException(status_code=400, detail=str(e))


# ──────────────────────────────────────────────
# HTML templates
# ──────────────────────────────────────────────

def _plan_label(plan: str) -> str:
    return {"starter": "Starter", "pro": "Pro", "enterprise": "Empresarial"}.get(plan, plan.title())


def _success_html(email: str, plan: str, billing: str, api_key: str, already: bool) -> str:
    label = _plan_label(plan)
    billing_label = "Anual (20% off)" if billing == "annual" else "Mensal"
    key_section = ""
    if api_key and not already:
        key_section = f"""
      <div class="key-card">
        <div class="key-label">🔑 Sua chave de API — guarde agora, não será exibida novamente</div>
        <div class="key-box" id="apikey">{api_key}</div>
        <button class="copy-btn" onclick="copyKey()">Copiar chave</button>
      </div>"""
    elif already:
        key_section = """
      <div class="info-box">
        ✅ Conta já ativa. Sua chave foi enviada quando você assinou.<br>
        <small>Se precisar de suporte, fale no WhatsApp abaixo.</small>
      </div>"""

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Pagamento confirmado — LeadSolar</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#060c18;color:#f1f5f9;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:2rem}}
.card{{background:#0d1825;border:1px solid #1a2e48;border-radius:1.5rem;padding:2.5rem;max-width:560px;width:100%;box-shadow:0 24px 64px rgba(0,0,0,.4)}}
.icon{{font-size:3rem;margin-bottom:1.25rem;text-align:center}}
h1{{font-size:1.6rem;font-weight:900;color:#22c55e;text-align:center;margin-bottom:.4rem;letter-spacing:-.03em}}
.subtitle{{color:#6b85a0;text-align:center;margin-bottom:2rem;font-size:.9rem}}
.plan-badge{{display:inline-flex;align-items:center;gap:.5rem;background:rgba(245,158,11,.1);border:1px solid rgba(245,158,11,.25);color:#f59e0b;font-size:.8rem;font-weight:700;padding:.35rem .9rem;border-radius:999px;margin-bottom:1.5rem}}
.steps{{display:flex;flex-direction:column;gap:.85rem;margin-bottom:2rem}}
.step-item{{display:flex;gap:.85rem;align-items:flex-start;background:#132030;border:1px solid #1a2e48;border-radius:.85rem;padding:1rem}}
.step-num{{width:1.75rem;height:1.75rem;border-radius:50%;background:rgba(245,158,11,.15);border:1.5px solid rgba(245,158,11,.4);color:#f59e0b;font-weight:800;font-size:.8rem;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:.1rem}}
.step-text strong{{display:block;font-size:.88rem;font-weight:700;margin-bottom:.2rem}}
.step-text span{{font-size:.8rem;color:#6b85a0;line-height:1.5}}
.key-card{{background:#0a1f12;border:1px solid rgba(34,197,94,.2);border-radius:1rem;padding:1.25rem;margin-bottom:1.5rem}}
.key-label{{font-size:.72rem;font-weight:700;color:#22c55e;text-transform:uppercase;letter-spacing:.06em;margin-bottom:.75rem}}
.key-box{{font-family:'Courier New',monospace;font-size:.8rem;color:#f59e0b;background:#060c18;border:1px solid #1a2e48;border-radius:.5rem;padding:.85rem 1rem;word-break:break-all;margin-bottom:.75rem}}
.copy-btn{{background:#22c55e;color:#000;font-weight:700;border:none;padding:.55rem 1.25rem;border-radius:.5rem;cursor:pointer;font-size:.82rem;font-family:inherit;transition:background .2s}}
.copy-btn:hover{{background:#16a34a}}
.info-box{{background:#132030;border:1px solid #1a2e48;border-radius:.85rem;padding:1rem;font-size:.85rem;color:#6b85a0;margin-bottom:1.5rem;line-height:1.6}}
.actions{{display:flex;gap:.75rem;flex-wrap:wrap}}
.btn-primary{{flex:1;background:linear-gradient(135deg,#f59e0b,#d97706);color:#000;font-weight:700;padding:.8rem;border-radius:.65rem;text-decoration:none;text-align:center;font-size:.9rem;transition:all .2s}}
.btn-primary:hover{{box-shadow:0 4px 16px rgba(245,158,11,.3)}}
.btn-secondary{{flex:1;background:#25d366;color:#fff;font-weight:700;padding:.8rem;border-radius:.65rem;text-decoration:none;text-align:center;font-size:.9rem;transition:all .2s}}
.btn-secondary:hover{{background:#16a34a}}
.manage-link{{text-align:center;margin-top:1.25rem;font-size:.78rem;color:#6b85a0}}
.manage-link a{{color:#f59e0b;text-decoration:none}}
.manage-link a:hover{{text-decoration:underline}}
</style>
</head>
<body>
<div class="card">
  <div class="icon">🎉</div>
  <h1>Pagamento confirmado!</h1>
  <p class="subtitle">Bem-vindo ao LeadSolar. Sua conta está ativa.</p>
  <div style="text-align:center">
    <span class="plan-badge">✓ Plano {label} · {billing_label} · 30 dias grátis</span>
  </div>

  {key_section}

  <div class="steps">
    <div class="step-item">
      <div class="step-num">1</div>
      <div class="step-text">
        <strong>Conecte seu formulário de leads</strong>
        <span>Leva menos de 20 minutos via Zapier ou Make. Conecte Google Forms, Meta Leads Ads ou qualquer fonte.</span>
      </div>
    </div>
    <div class="step-item">
      <div class="step-num">2</div>
      <div class="step-text">
        <strong>Qualifique seus primeiros leads</strong>
        <span>Use a API com sua chave acima. POST /leads com os dados do lead — score, decisão e WhatsApp prontos em segundos.</span>
      </div>
    </div>
    <div class="step-item">
      <div class="step-num">3</div>
      <div class="step-text">
        <strong>Fale com o time para onboarding</strong>
        <span>Nosso time configura tudo com você em uma chamada de 30 min. É incluso em todos os planos.</span>
      </div>
    </div>
  </div>

  <div class="actions">
    <a href="/onboarding?api_key={api_key}" class="btn-primary" id="onboarding-btn">Configurar sua conta →</a>
    <a href="https://wa.me/5591851566690" class="btn-secondary" target="_blank" rel="noopener">📱 Suporte no WhatsApp</a>
  </div>

  <div class="manage-link">
    Precisa cancelar ou trocar o cartão?
    <a href="/customer/portal-page">Gerenciar assinatura →</a>
  </div>
</div>
<script>
function copyKey() {{
  const txt = document.getElementById('apikey').textContent;
  navigator.clipboard.writeText(txt).then(() => {{
    const btn = document.querySelector('.copy-btn');
    btn.textContent = '✓ Copiado!';
    btn.style.background = '#16a34a';
    setTimeout(() => {{ btn.textContent = 'Copiar chave'; btn.style.background = ''; }}, 2500);
  }});
}}
</script>
</body>
</html>"""


# ──────────────────────────────────────────────
# Customer portal page (HTML form to enter email)
# ──────────────────────────────────────────────

@router.get("/customer/portal-page", response_class=HTMLResponse)
async def portal_page():
    return HTMLResponse(_portal_page_html())


def _portal_page_html() -> str:
    return """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Gerenciar assinatura — LeadSolar</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#060c18;color:#f1f5f9;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:2rem}
.card{background:#0d1825;border:1px solid #1a2e48;border-radius:1.5rem;padding:2.5rem;max-width:440px;width:100%}
h1{font-size:1.4rem;font-weight:900;margin-bottom:.4rem;letter-spacing:-.03em}
p{color:#6b85a0;font-size:.88rem;margin-bottom:2rem;line-height:1.6}
label{display:block;font-size:.75rem;font-weight:700;color:#6b85a0;text-transform:uppercase;letter-spacing:.06em;margin-bottom:.4rem}
input{width:100%;background:#132030;border:1px solid #1a2e48;color:#f1f5f9;padding:.8rem 1rem;border-radius:.6rem;font-size:.9rem;outline:none;font-family:inherit;transition:border-color .2s;margin-bottom:1rem}
input:focus{border-color:#f59e0b}
button{width:100%;background:linear-gradient(135deg,#f59e0b,#d97706);color:#000;font-weight:700;padding:.85rem;border-radius:.65rem;border:none;font-size:.9rem;cursor:pointer;font-family:inherit;transition:all .2s}
button:hover{box-shadow:0 4px 16px rgba(245,158,11,.3)}
button:disabled{opacity:.6;cursor:not-allowed}
.err{color:#ef4444;font-size:.82rem;margin-top:.5rem;display:none}
.back{display:block;text-align:center;margin-top:1.5rem;font-size:.8rem;color:#6b85a0;text-decoration:none}
.back:hover{color:#f59e0b}
</style>
</head>
<body>
<div class="card">
  <h1>Gerenciar assinatura</h1>
  <p>Informe o email que você usou no pagamento. Vamos abrir o portal Stripe para você cancelar, trocar cartão ou mudar de plano.</p>
  <label>Email da conta</label>
  <input type="email" id="email" placeholder="seu@email.com" required/>
  <div class="err" id="err"></div>
  <button id="btn" onclick="openPortal()">Acessar portal →</button>
  <a href="/" class="back">← Voltar para o início</a>
</div>
<script>
async function openPortal() {
  const email = document.getElementById('email').value.trim();
  const btn = document.getElementById('btn');
  const err = document.getElementById('err');
  if (!email) return;
  btn.disabled = true;
  btn.textContent = 'Abrindo...';
  err.style.display = 'none';
  try {
    const r = await fetch('/customer/portal', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({email})
    });
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail || 'Erro desconhecido');
    window.location.href = data.portal_url;
  } catch(e) {
    err.textContent = e.message;
    err.style.display = 'block';
    btn.disabled = false;
    btn.textContent = 'Acessar portal →';
  }
}
document.getElementById('email').addEventListener('keydown', e => { if (e.key === 'Enter') openPortal(); });
</script>
</body>
</html>"""
