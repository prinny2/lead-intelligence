"""Stripe payment routes — checkout, success page, webhook."""

import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel

from app.services.audit_service import log_event
from app.services.stripe_service import (
    create_checkout_session,
    handle_webhook,
    provision_customer,
)

router = APIRouter()
logger = logging.getLogger("lead_intelligence.payments")


class CheckoutRequest(BaseModel):
    plan: str
    email: str | None = None
    billing: str = "monthly"  # "monthly" | "annual"


@router.post("/checkout/create")
async def create_checkout(body: CheckoutRequest, request: Request):
    """Create a Stripe Checkout session and redirect."""
    if body.plan not in ("starter", "pro", "enterprise"):
        raise HTTPException(status_code=400, detail="Plano inválido.")
    if body.billing not in ("monthly", "annual"):
        raise HTTPException(status_code=400, detail="Billing inválido. Use 'monthly' ou 'annual'.")
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


@router.get("/checkout/success", response_class=HTMLResponse)
async def checkout_success(session_id: str):
    """Success page shown after payment. Provisions API key."""
    try:
        customer = provision_customer(session_id)
    except Exception as e:
        logger.error("provision_error: %s", e)
        raise HTTPException(status_code=400, detail="Sessão inválida ou expirada.")

    if customer.get("already_provisioned"):
        return HTMLResponse(_already_provisioned_html(customer["email"], customer["plan"]))

    api_key = customer["api_key"]
    email = customer["email"]
    plan = customer["plan"]
    log_event("customer_provisioned", endpoint="/checkout/success",
              method="GET", status_code=200, extra={"plan": plan})
    return HTMLResponse(_success_html(email, plan, api_key))


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Stripe webhook endpoint — handles subscription lifecycle events."""
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    try:
        event_type = handle_webhook(payload, sig)
        return {"received": True, "event": event_type}
    except Exception as e:
        logger.error("webhook_error: %s", e)
        raise HTTPException(status_code=400, detail=str(e))


def _success_html(email: str, plan: str, api_key: str) -> str:
    plan_label = "Pro" if plan == "pro" else "Enterprise"
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Pagamento confirmado — LeadSolar</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#080e1a;color:#f1f5f9;display:flex;align-items:center;justify-content:center;min-height:100vh;padding:2rem}}
.card{{background:#0f1929;border:1px solid #1a3050;border-radius:1rem;padding:2.5rem;max-width:540px;width:100%;text-align:center}}
.icon{{font-size:3rem;margin-bottom:1rem}}
h1{{font-size:1.75rem;font-weight:800;color:#22c55e;margin-bottom:.5rem}}
p{{color:#7c94b0;margin-bottom:1.5rem}}
.key-box{{background:#162338;border:1px solid #1a3050;border-radius:.5rem;padding:1rem;font-family:monospace;font-size:.85rem;color:#f59e0b;word-break:break-all;margin-bottom:1rem;text-align:left}}
.warn{{font-size:.8rem;color:#ef4444;margin-bottom:1.5rem}}
.btn{{display:inline-block;background:#f59e0b;color:#000;font-weight:700;padding:.75rem 2rem;border-radius:.5rem;text-decoration:none;font-size:1rem}}
.btn:hover{{background:#d97706}}
</style>
</head>
<body>
<div class="card">
  <div class="icon">🎉</div>
  <h1>Pagamento confirmado!</h1>
  <p>Plano <strong>{plan_label}</strong> ativado para <strong>{email}</strong></p>
  <p style="color:#f1f5f9;font-weight:600;margin-bottom:.5rem">Sua chave de API:</p>
  <div class="key-box">{api_key}</div>
  <p class="warn">⚠️ Guarde essa chave agora — ela não será exibida novamente.</p>
  <p style="color:#7c94b0;font-size:.85rem;margin-bottom:1.5rem">
    Use no header: <code style="color:#f59e0b">X-API-Key: {api_key[:20]}...</code>
  </p>
  <a href="/" class="btn">Ir para o dashboard →</a>
</div>
</body>
</html>"""


def _already_provisioned_html(email: str, plan: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"/><title>LeadSolar</title>
<style>body{{font-family:sans-serif;background:#080e1a;color:#f1f5f9;display:flex;align-items:center;justify-content:center;min-height:100vh}}.card{{background:#0f1929;border:1px solid #1a3050;border-radius:1rem;padding:2.5rem;max-width:480px;text-align:center}}</style>
</head>
<body><div class="card">
<p style="font-size:2rem">✅</p>
<h2 style="color:#22c55e;margin:.5rem 0">Conta já ativada</h2>
<p style="color:#7c94b0">A conta <strong>{email}</strong> já foi provisionada.<br>Verifique seu email ou entre em contato com o suporte.</p>
<a href="/" style="display:inline-block;margin-top:1.5rem;color:#f59e0b">← Voltar</a>
</div></body></html>"""
