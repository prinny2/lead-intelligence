"""Onboarding wizard — served at /onboarding after Stripe checkout."""

import os

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

_BASE_URL = os.getenv("BASE_URL", "https://lead-intelligence-production.up.railway.app")

# ---------------------------------------------------------------------------
# Helper data: per-integration setup guide (also exposed as JSON endpoint)
# ---------------------------------------------------------------------------

_GUIDES: dict[str, dict] = {
    "google_forms": {
        "label": "Google Forms",
        "icon": "📋",
        "steps": [
            "Abra seu formulário no Google Forms.",
            "No Zapier, crie um novo Zap e escolha Google Forms como trigger.",
            "Conecte ao LeadSolar via webhook: Action → Webhook by Zapier → POST → https://lead-intelligence-production.up.railway.app/webhook/form",
            "Mapeie os campos: Nome → name, Cidade → city, Conta de luz → monthly_bill, Tipo de imóvel → property_type.",
            "Ative o Zap e envie uma resposta de teste para confirmar.",
        ],
        "code": 'POST https://lead-intelligence-production.up.railway.app/webhook/form\nContent-Type: application/json\n\n{\n  "name": "{{Nome}}",\n  "city": "{{Cidade}}",\n  "monthly_bill": {{Conta de Luz}},\n  "property_type": "{{Tipo de Imóvel}}"\n}',
    },
    "meta_ads": {
        "label": "Meta Leads Ads",
        "icon": "📣",
        "steps": [
            "Acesse o Meta Business Suite → Leads Center.",
            "Clique em \"Integrações\" → \"CRM\" e escolha Zapier.",
            "No Zapier, conecte o trigger do Meta Lead Ads à sua conta.",
            "Adicione uma Action: Webhook by Zapier → POST → https://lead-intelligence-production.up.railway.app/webhook/form",
            "Mapeie os campos do formulário do anúncio para name, city, monthly_bill e property_type. Ative o Zap.",
        ],
        "code": 'POST https://lead-intelligence-production.up.railway.app/webhook/form\nContent-Type: application/json\n\n{\n  "name": "{{full_name}}",\n  "city": "{{city}}",\n  "monthly_bill": {{conta_de_luz}},\n  "property_type": "{{tipo_de_imovel}}"\n}',
    },
    "rdstation": {
        "label": "RD Station",
        "icon": "📊",
        "steps": [
            "No RD Station, vá em Configurações → Integrações → Webhooks.",
            "Clique em \"Novo Webhook\" e insira a URL: https://lead-intelligence-production.up.railway.app/webhook/rdstation",
            "Selecione o evento: \"Lead convertido\".",
            "Configure os campos personalizados do formulário: cf_conta_de_luz, cf_tipo_imovel.",
            "Salve e teste enviando um lead de conversão.",
        ],
        "code": '# URL do Webhook RD Station\nhttps://lead-intelligence-production.up.railway.app/webhook/rdstation\n\n# Campos personalizados esperados\ncf_conta_de_luz   → monthly_bill\ncf_tipo_imovel    → property_type\nnome              → name\ncidade            → city',
    },
    "zapier_make": {
        "label": "Zapier / Make",
        "icon": "⚡",
        "steps": [
            "Crie um novo Zap ou Cenário no Zapier/Make.",
            "Defina o trigger: seu formulário, CRM ou qualquer fonte de lead.",
            "Adicione uma Action: HTTP Request (Make) ou Webhook by Zapier.",
            "Configure: método POST, URL https://lead-intelligence-production.up.railway.app/webhook/form, Content-Type: application/json.",
            "Mapeie os campos e ative o Zap/Cenário.",
        ],
        "code": 'POST https://lead-intelligence-production.up.railway.app/webhook/form\nContent-Type: application/json\nX-API-Key: SUA_CHAVE_AQUI\n\n{\n  "name": "string",\n  "city": "string",\n  "monthly_bill": 350,\n  "property_type": "casa_propria | apartamento | comercial",\n  "goal": "economia | independencia | revenda"\n}',
    },
    "manual": {
        "label": "Inserção Manual",
        "icon": "✏️",
        "steps": [
            "Copie sua chave de API exibida na etapa anterior.",
            "Faça um POST para https://lead-intelligence-production.up.railway.app/lead com o header X-API-Key.",
            "Inclua no body JSON os campos obrigatórios: name, city, monthly_bill, property_type.",
            "A resposta retornará score (0-10), decision, urgency e whatsapp_message prontos.",
            "Use o dashboard em /dashboard para ver todos os seus leads qualificados.",
        ],
        "code": 'curl -X POST https://lead-intelligence-production.up.railway.app/lead \\\n  -H "Content-Type: application/json" \\\n  -H "X-API-Key: SUA_CHAVE_AQUI" \\\n  -d \'{\n    "name": "João Silva",\n    "city": "Fortaleza",\n    "monthly_bill": 480,\n    "property_type": "casa_propria",\n    "goal": "economia"\n  }\'',
    },
}


# ---------------------------------------------------------------------------
# JSON guide endpoint (for future dashboard use)
# ---------------------------------------------------------------------------

def _resolve_guides() -> dict[str, dict]:
    """Return guides with BASE_URL substituted for the hardcoded production URL."""
    import json
    _PROD_URL = "https://lead-intelligence-production.up.railway.app"
    if _BASE_URL == _PROD_URL:
        return _GUIDES
    raw = json.dumps(_GUIDES).replace(_PROD_URL, _BASE_URL)
    return json.loads(raw)


@router.get("/onboarding/guide")
async def onboarding_guide(integration: Optional[str] = Query(default=None)):
    """Return setup steps JSON for a given integration key."""
    guides = _resolve_guides()
    if integration and integration in guides:
        return JSONResponse(content=guides[integration])
    return JSONResponse(content={"integrations": list(guides.keys()), "guides": guides})


# ---------------------------------------------------------------------------
# Google account linking endpoints
# ---------------------------------------------------------------------------

class LinkGoogleRequest(BaseModel):
    firebase_token: str
    api_key: str


@router.post("/api/link-google")
async def link_google(body: LinkGoogleRequest):
    """Link a Google account (Firebase UID) to an API key for future recovery."""
    from app.auth import link_google_account
    ok = link_google_account(body.firebase_token, body.api_key)
    if not ok:
        raise HTTPException(status_code=400, detail="Não foi possível vincular. Verifique a chave e tente novamente.")
    return {"linked": True}


class OnboardingLinkRequest(BaseModel):
    uid: str
    api_key: str


@router.post("/onboarding/link")
async def onboarding_link(body: OnboardingLinkRequest):
    """
    Save google_uid to the customer document identified by api_key.
    Called after Firebase signInWithPopup on the onboarding page.
    Receives the Firebase UID directly (not a token) since the client already
    has it from the Auth result.
    """
    from app.auth import _get_firestore
    import logging as _logging
    _log = _logging.getLogger("lead_intelligence.onboarding")
    db = _get_firestore()
    if not db:
        raise HTTPException(status_code=503, detail="Serviço temporariamente indisponível.")
    try:
        docs = (
            db.collection("customers")
            .where("api_key", "==", body.api_key)
            .limit(1)
            .get()
        )
        for doc in docs:
            doc.reference.update({"google_uid": body.uid})
            return {"linked": True}
        raise HTTPException(status_code=404, detail="Chave não encontrada. Verifique e tente novamente.")
    except HTTPException:
        raise
    except Exception as e:
        _log.warning("onboarding_link_failed error=%s", e)
        raise HTTPException(status_code=500, detail="Erro ao salvar vínculo. Tente novamente.")


class RecoverKeyRequest(BaseModel):
    firebase_token: str


@router.post("/api/recover-key")
async def recover_key(body: RecoverKeyRequest):
    """Return the API key for a verified Firebase token."""
    from app.auth import get_api_key_for_firebase_token
    key = get_api_key_for_firebase_token(body.firebase_token)
    if not key:
        raise HTTPException(status_code=404, detail="Nenhuma conta encontrada para este login Google.")
    return {"api_key": key}


# ---------------------------------------------------------------------------
# Main onboarding page
# ---------------------------------------------------------------------------

_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Configuração — LeadSolar</title>
<link rel="icon" type="image/png" href="/static/favicon.png"/>
<style>
:root{
  --bg:#060c18;--surface:#0d1825;--surface2:#132030;--border:#1a2e48;
  --sun:#f59e0b;--sun-dark:#d97706;--sun-light:#fbbf24;
  --text:#f1f5f9;--muted:#6b85a0;--green:#22c55e;--red:#ef4444;--sky:#0ea5e9;
  --glow:rgba(245,158,11,.18);
}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{
  font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
  background:var(--bg);color:var(--text);min-height:100vh;
  background-image:radial-gradient(ellipse 80% 50% at 50% -10%,rgba(245,158,11,.07),transparent);
}

/* ── NAV ── */
nav{
  position:fixed;top:0;left:0;right:0;z-index:100;
  background:rgba(6,12,24,.92);backdrop-filter:blur(16px);
  border-bottom:1px solid var(--border);
  padding:.85rem 2rem;display:flex;justify-content:space-between;align-items:center;
}
.logo{font-size:1.15rem;font-weight:900;color:var(--sun);letter-spacing:-.02em;text-decoration:none}
.logo span{color:var(--text);font-weight:400}

/* ── LAYOUT ── */
.page{max-width:720px;margin:0 auto;padding:7rem 1.5rem 4rem}

/* ── STEP INDICATOR ── */
.steps-bar{display:flex;align-items:center;justify-content:center;gap:.5rem;margin-bottom:3rem}
.step-dot{
  width:10px;height:10px;border-radius:50%;
  background:var(--border);border:2px solid var(--border);
  transition:all .3s ease;cursor:default;
}
.step-dot.active{background:var(--sun);border-color:var(--sun);box-shadow:0 0 10px rgba(245,158,11,.5)}
.step-dot.done{background:var(--green);border-color:var(--green)}
.step-line{width:48px;height:2px;background:var(--border);transition:background .3s}
.step-line.done{background:var(--green)}

/* ── STEP PANELS ── */
.step{display:none;animation:fadeIn .35s ease}
.step.active{display:block}
@keyframes fadeIn{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}

/* ── COMMON CARD ── */
.card{
  background:var(--surface);border:1px solid var(--border);
  border-radius:1rem;padding:2.5rem 2rem;
}
.card-title{font-size:1.6rem;font-weight:800;letter-spacing:-.025em;margin-bottom:.5rem}
.card-sub{color:var(--muted);font-size:.95rem;line-height:1.6;margin-bottom:2rem}

/* ── STEP 1: CHAVE PRONTA ── */
.success-icon{
  width:80px;height:80px;border-radius:50%;
  background:linear-gradient(135deg,rgba(34,197,94,.2),rgba(34,197,94,.05));
  border:2px solid rgba(34,197,94,.4);
  display:flex;align-items:center;justify-content:center;
  font-size:2.5rem;margin:0 auto 1.75rem;
  box-shadow:0 0 30px rgba(34,197,94,.15);
}
.api-key-box{
  background:var(--surface2);border:1px solid var(--border);
  border-radius:.65rem;padding:1rem 1.25rem;
  display:flex;align-items:center;gap:.75rem;
  margin-bottom:1rem;
}
.api-key-box code{
  flex:1;font-family:'Courier New',monospace;font-size:.88rem;
  color:var(--sun-light);word-break:break-all;letter-spacing:.03em;
}
.btn-copy{
  background:transparent;border:1px solid var(--border);color:var(--muted);
  padding:.4rem .85rem;border-radius:.4rem;cursor:pointer;
  font-size:.8rem;white-space:nowrap;transition:all .2s;
}
.btn-copy:hover{border-color:var(--sun);color:var(--sun)}
.btn-copy.copied{border-color:var(--green);color:var(--green)}
.warn-box{
  background:rgba(245,158,11,.07);border:1px solid rgba(245,158,11,.25);
  border-radius:.5rem;padding:.75rem 1rem;
  font-size:.82rem;color:var(--sun-light);
  display:flex;align-items:center;gap:.6rem;margin-bottom:2rem;
}

/* ── STEP 2: INTEGRATION CARDS ── */
.integration-grid{
  display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));
  gap:.75rem;margin-bottom:2rem;
}
.int-card{
  background:var(--surface2);border:2px solid var(--border);
  border-radius:.75rem;padding:1.25rem 1rem;
  cursor:pointer;text-align:center;transition:all .2s;
  user-select:none;
}
.int-card:hover{border-color:rgba(245,158,11,.4);transform:translateY(-2px)}
.int-card.selected{
  border-color:var(--sun);background:rgba(245,158,11,.07);
  box-shadow:0 0 18px rgba(245,158,11,.12);
}
.int-icon{font-size:2rem;margin-bottom:.6rem}
.int-label{font-size:.82rem;font-weight:600;color:var(--muted);line-height:1.3}
.int-card.selected .int-label{color:var(--sun)}

/* ── STEP 3: GUIDE ── */
.guide-header{
  display:flex;align-items:center;gap:.75rem;
  margin-bottom:1.5rem;
}
.guide-icon{font-size:2rem}
.guide-title{font-size:1.1rem;font-weight:700}
.guide-sub{font-size:.82rem;color:var(--muted)}
.steps-list{list-style:none;display:flex;flex-direction:column;gap:.9rem;margin-bottom:1.75rem}
.steps-list li{
  display:flex;gap:1rem;align-items:flex-start;
  font-size:.9rem;line-height:1.6;color:var(--text);
}
.step-num{
  width:26px;height:26px;min-width:26px;border-radius:50%;
  background:linear-gradient(135deg,var(--sun),var(--sun-dark));
  color:#000;font-weight:800;font-size:.75rem;
  display:flex;align-items:center;justify-content:center;
  margin-top:.1rem;
}
.code-block{
  background:#050b14;border:1px solid var(--border);
  border-radius:.6rem;padding:1.1rem 1.25rem;
  font-family:'Courier New',monospace;font-size:.78rem;
  color:#7dd3fc;line-height:1.7;overflow-x:auto;
  margin-bottom:1.75rem;white-space:pre;
}

/* ── STEP 4: TEST FORM ── */
.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-bottom:1.5rem}
@media(max-width:500px){.form-grid{grid-template-columns:1fr}}
.field{display:flex;flex-direction:column;gap:.4rem}
.field label{font-size:.8rem;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.05em}
.field input,.field select{
  background:var(--surface2);border:1px solid var(--border);
  color:var(--text);padding:.7rem .9rem;border-radius:.5rem;
  font-size:.9rem;transition:border-color .2s;outline:none;
  font-family:inherit;
}
.field input:focus,.field select:focus{border-color:var(--sun)}
.field input::placeholder{color:var(--muted)}
.field select option{background:var(--surface2);color:var(--text)}
.field-full{grid-column:1/-1}

/* ── RESULT CARD ── */
.result-card{
  background:var(--surface2);border:1px solid var(--border);
  border-radius:.75rem;padding:1.75rem;margin-top:1.5rem;
  display:none;animation:fadeIn .35s ease;
}
.result-card.visible{display:block}
.result-row{display:flex;align-items:flex-start;gap:1.5rem;flex-wrap:wrap}
.score-circle{
  width:80px;height:80px;border-radius:50%;
  border:3px solid var(--green);background:rgba(34,197,94,.08);
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  flex-shrink:0;
}
.score-num{font-size:1.6rem;font-weight:900;line-height:1}
.score-lbl{font-size:.6rem;color:var(--muted);font-weight:600;text-transform:uppercase;letter-spacing:.05em}
.result-info{flex:1;min-width:180px}
.decision-badge{
  display:inline-flex;align-items:center;gap:.4rem;
  padding:.3rem .8rem;border-radius:999px;
  font-size:.78rem;font-weight:700;margin-bottom:.75rem;
}
.badge-hot{background:rgba(239,68,68,.15);color:#f87171;border:1px solid rgba(239,68,68,.3)}
.badge-warm{background:rgba(245,158,11,.12);color:var(--sun);border:1px solid rgba(245,158,11,.3)}
.badge-cold{background:rgba(107,133,160,.1);color:var(--muted);border:1px solid rgba(107,133,160,.2)}
.wa-block{margin-top:.75rem}
.wa-label{font-size:.75rem;color:var(--muted);font-weight:600;text-transform:uppercase;letter-spacing:.05em;margin-bottom:.35rem}
.wa-msg{
  background:#050b14;border:1px solid var(--border);border-radius:.5rem;
  padding:.85rem;font-size:.82rem;color:#a3e635;line-height:1.65;
  position:relative;white-space:pre-wrap;
}
.btn-copy-wa{
  position:absolute;top:.5rem;right:.5rem;
  background:transparent;border:1px solid var(--border);color:var(--muted);
  padding:.25rem .6rem;border-radius:.35rem;cursor:pointer;font-size:.72rem;
  transition:all .2s;
}
.btn-copy-wa:hover{border-color:var(--green);color:var(--green)}
.result-footer{
  margin-top:1.5rem;padding-top:1.25rem;border-top:1px solid var(--border);
  text-align:center;
}

/* ── BUTTONS ── */
.btn-row{display:flex;gap:.75rem;align-items:center;flex-wrap:wrap}
.btn-primary{
  background:linear-gradient(135deg,var(--sun),var(--sun-dark));
  color:#000;font-weight:800;padding:.8rem 1.75rem;border-radius:.6rem;
  border:none;cursor:pointer;font-size:.9rem;transition:all .2s;
  white-space:nowrap;font-family:inherit;
  box-shadow:0 4px 18px rgba(245,158,11,.28);
}
.btn-primary:hover{transform:translateY(-1px);box-shadow:0 6px 24px rgba(245,158,11,.4)}
.btn-primary:disabled{opacity:.5;cursor:not-allowed;transform:none}
.btn-secondary{
  background:transparent;border:1px solid var(--border);color:var(--muted);
  padding:.8rem 1.5rem;border-radius:.6rem;cursor:pointer;
  font-size:.9rem;transition:all .2s;font-family:inherit;white-space:nowrap;
}
.btn-secondary:hover{border-color:var(--muted);color:var(--text)}
.btn-link{
  background:var(--surface);border:1px solid var(--border);color:var(--text);
  padding:.85rem 2rem;border-radius:.65rem;text-decoration:none;
  font-size:.9rem;font-weight:600;transition:all .2s;display:inline-block;
}
.btn-link:hover{border-color:var(--sun);color:var(--sun)}
.btn-dash{
  background:linear-gradient(135deg,var(--sun),var(--sun-dark));
  color:#000;font-weight:800;padding:.85rem 2rem;border-radius:.65rem;
  text-decoration:none;font-size:.9rem;display:inline-block;
  box-shadow:0 4px 18px rgba(245,158,11,.3);transition:all .2s;
}
.btn-dash:hover{transform:translateY(-1px);box-shadow:0 6px 24px rgba(245,158,11,.4)}

/* ── GOOGLE LOGIN ── */
.google-btn{
  display:flex;align-items:center;justify-content:center;gap:.7rem;
  background:#fff;color:#1a1a1a;font-weight:600;padding:.75rem 1.5rem;
  border-radius:.6rem;border:none;cursor:pointer;font-size:.9rem;
  width:100%;font-family:inherit;transition:all .2s;
  box-shadow:0 2px 8px rgba(0,0,0,.18);
}
.google-btn:hover{box-shadow:0 4px 16px rgba(0,0,0,.25);transform:translateY(-1px)}
.google-btn:disabled{opacity:.5;cursor:not-allowed;transform:none}
.google-btn img{width:20px;height:20px}
.link-success{
  background:rgba(34,197,94,.1);border:1px solid rgba(34,197,94,.3);
  border-radius:.5rem;padding:.75rem 1rem;font-size:.85rem;color:#22c55e;
  text-align:center;display:none;margin-top:.75rem;
}
.skip-link{
  display:block;text-align:center;margin-top:.6rem;
  font-size:.78rem;color:var(--muted);cursor:pointer;text-decoration:underline;
}
.skip-link:hover{color:var(--text)}

/* ── SPINNER ── */
.spinner{
  width:18px;height:18px;border:2px solid rgba(0,0,0,.2);
  border-top-color:#000;border-radius:50%;
  animation:spin .7s linear infinite;display:inline-block;vertical-align:middle;
}
@keyframes spin{to{transform:rotate(360deg)}}

/* ── TOAST ── */
.toast{
  position:fixed;bottom:1.5rem;left:50%;transform:translateX(-50%) translateY(20px);
  background:#1a2e48;border:1px solid var(--border);border-radius:.5rem;
  padding:.6rem 1.25rem;font-size:.85rem;color:var(--text);
  opacity:0;transition:all .3s;pointer-events:none;z-index:200;white-space:nowrap;
}
.toast.show{opacity:1;transform:translateX(-50%) translateY(0)}

@media(max-width:600px){
  .card{padding:1.75rem 1.25rem}
  .card-title{font-size:1.35rem}
  .integration-grid{grid-template-columns:repeat(2,1fr)}
  .btn-row{flex-direction:column;align-items:stretch}
  .btn-row .btn-primary,.btn-row .btn-secondary{text-align:center}
}
</style>
</head>
<body>

<nav>
  <a class="logo" href="/">Lead<span>Solar</span></a>
</nav>

<div class="page">

  <!-- Step indicator -->
  <div class="steps-bar" id="stepsBar">
    <div class="step-dot active" id="dot-1"></div>
    <div class="step-line" id="line-1"></div>
    <div class="step-dot" id="dot-2"></div>
    <div class="step-line" id="line-2"></div>
    <div class="step-dot" id="dot-3"></div>
    <div class="step-line" id="line-3"></div>
    <div class="step-dot" id="dot-4"></div>
  </div>

  <!-- ────────────────────────────────────────────── -->
  <!-- STEP 1: Chave Pronta                          -->
  <!-- ────────────────────────────────────────────── -->
  <div class="step active" id="step-1">
    <div class="card" style="text-align:center">
      <div class="success-icon">✅</div>
      <div class="card-title">Sua conta está ativa! 🎉</div>
      <p class="card-sub">Sua chave de API foi gerada. Guarde-a agora — ela não será exibida novamente após você sair desta página.</p>

      <div class="api-key-box">
        <code id="apiKeyDisplay">—</code>
        <button class="btn-copy" id="copyKeyBtn" onclick="copyApiKey()">Copiar</button>
      </div>

      <div class="warn-box">
        <span>⚠️</span>
        <span><strong>Guarde agora</strong> — não será exibida novamente. Salve em um gerenciador de senhas ou documento seguro.</span>
      </div>

      <!-- Google account linking -->
      <div style="border:1px solid var(--border);border-radius:.75rem;padding:1.25rem;margin-bottom:1.5rem;background:var(--surface2)">
        <div style="font-size:.85rem;font-weight:700;margin-bottom:.35rem">🔐 Entrar no Dashboard</div>
        <div style="font-size:.8rem;color:var(--muted);margin-bottom:.85rem;line-height:1.5">Vincule seu Google para acessar o dashboard agora e recuperar a chave no futuro sem precisar guardá-la.</div>
        <button class="google-btn" id="googleLinkBtn" onclick="linkGoogleAccount()">
          <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" alt="Google"/>
          Entrar no Dashboard com Google
        </button>
        <div class="link-success" id="linkSuccess">✓ Conta Google vinculada! Redirecionando para o dashboard…</div>
        <span class="skip-link" onclick="goToStep(2)">Pular por agora →</span>
      </div>

      <div class="btn-row" style="justify-content:center">
        <button class="btn-primary" id="btnNext1" onclick="goToStep(2)">Escolher integração →</button>
      </div>
    </div>
  </div>

  <!-- ────────────────────────────────────────────── -->
  <!-- STEP 2: Escolha sua integração               -->
  <!-- ────────────────────────────────────────────── -->
  <div class="step" id="step-2">
    <div class="card">
      <div class="card-title">Como chegam seus leads hoje?</div>
      <p class="card-sub">Escolha a fonte principal de leads e veja o guia de configuração personalizado para você.</p>

      <div class="integration-grid">
        <div class="int-card" data-int="google_forms" onclick="selectIntegration(this)">
          <div class="int-icon">📋</div>
          <div class="int-label">Google Forms</div>
        </div>
        <div class="int-card" data-int="meta_ads" onclick="selectIntegration(this)">
          <div class="int-icon">📣</div>
          <div class="int-label">Meta Leads Ads<br><span style="font-weight:400;font-size:.75rem;color:var(--muted)">(Facebook/Instagram)</span></div>
        </div>
        <div class="int-card" data-int="rdstation" onclick="selectIntegration(this)">
          <div class="int-icon">📊</div>
          <div class="int-label">RD Station</div>
        </div>
        <div class="int-card" data-int="zapier_make" onclick="selectIntegration(this)">
          <div class="int-icon">⚡</div>
          <div class="int-label">Zapier / Make</div>
        </div>
        <div class="int-card" data-int="manual" onclick="selectIntegration(this)">
          <div class="int-icon">✏️</div>
          <div class="int-label">Vou inserir manualmente</div>
        </div>
      </div>

      <div class="btn-row">
        <button class="btn-secondary" onclick="goToStep(1)">← Voltar</button>
        <button class="btn-primary" id="btnSeeGuide" onclick="goToStep(3)" disabled>Ver como configurar →</button>
      </div>
    </div>
  </div>

  <!-- ────────────────────────────────────────────── -->
  <!-- STEP 3: Guia de configuração                 -->
  <!-- ────────────────────────────────────────────── -->
  <div class="step" id="step-3">
    <div class="card">
      <div class="guide-header">
        <div class="guide-icon" id="guideIcon"></div>
        <div>
          <div class="guide-title" id="guideTitle"></div>
          <div class="guide-sub">Siga os passos abaixo para conectar em minutos</div>
        </div>
      </div>

      <ol class="steps-list" id="guideStepsList"></ol>

      <div class="code-block" id="guideCode"></div>

      <p style="font-size:.8rem;color:var(--muted);margin-bottom:1.75rem">
        Base URL: <code style="color:var(--sky);font-size:.8rem">https://lead-intelligence-production.up.railway.app</code>
      </p>

      <div class="btn-row">
        <button class="btn-secondary" onclick="goToStep(2)">← Voltar</button>
        <button class="btn-primary" onclick="goToStep(4)">Testar agora →</button>
      </div>
    </div>
  </div>

  <!-- ────────────────────────────────────────────── -->
  <!-- STEP 4: Teste                                -->
  <!-- ────────────────────────────────────────────── -->
  <div class="step" id="step-4">
    <div class="card">
      <div class="card-title">Tudo pronto! Envie seu primeiro lead</div>
      <p class="card-sub">Teste a qualificação ao vivo. Veja o score, decisão e mensagem de WhatsApp gerados automaticamente.</p>

      <form id="testForm" onsubmit="submitTestLead(event)">
        <div class="form-grid">
          <div class="field">
            <label>Nome</label>
            <input type="text" id="leadName" placeholder="Ex: João Silva" required/>
          </div>
          <div class="field">
            <label>Cidade</label>
            <input type="text" id="leadCity" placeholder="Ex: Fortaleza" required/>
          </div>
          <div class="field">
            <label>Conta de luz (R$)</label>
            <input type="number" id="leadBill" placeholder="350" min="0" step="10" required/>
          </div>
          <div class="field">
            <label>Tipo de imóvel</label>
            <select id="leadProperty" required>
              <option value="" disabled selected>Selecione…</option>
              <option value="casa_propria">Casa própria</option>
              <option value="apartamento">Apartamento</option>
              <option value="comercial">Imóvel comercial</option>
              <option value="rural">Propriedade rural</option>
            </select>
          </div>
          <div class="field field-full">
            <label>Objetivo</label>
            <select id="leadGoal" required>
              <option value="" disabled selected>Selecione…</option>
              <option value="economia">Reduzir conta de luz</option>
              <option value="independencia">Independência energética</option>
              <option value="revenda">Revender energia</option>
              <option value="sustentabilidade">Sustentabilidade</option>
            </select>
          </div>
        </div>

        <div class="btn-row">
          <button class="btn-secondary" type="button" onclick="goToStep(3)">← Voltar</button>
          <button class="btn-primary" type="submit" id="btnQualify">
            <span id="qualifyLabel">Qualificar agora →</span>
          </button>
        </div>
      </form>

      <!-- Result area -->
      <div class="result-card" id="resultCard">
        <div class="result-row">
          <div class="score-circle" id="scoreCircle">
            <span class="score-num" id="scoreNum">—</span>
            <span class="score-lbl">score</span>
          </div>
          <div class="result-info">
            <div class="decision-badge" id="decisionBadge">—</div>
            <div style="font-size:.88rem;color:var(--muted)" id="urgencyText"></div>
          </div>
        </div>
        <div class="wa-block" style="margin-top:1.25rem">
          <div class="wa-label">Mensagem WhatsApp gerada</div>
          <div class="wa-msg" id="waMsg" style="position:relative">
            <span id="waMsgText"></span>
            <button class="btn-copy-wa" onclick="copyWaMsg()">Copiar</button>
          </div>
        </div>
        <div class="result-footer">
          <p style="color:var(--muted);font-size:.88rem;margin-bottom:1rem">
            Seu time já pode usar o LeadSolar. Acesse o dashboard para ver todos os leads.
          </p>
          <a href="/dashboard" class="btn-dash">Acessar o dashboard →</a>
        </div>
      </div>
    </div>
  </div>

</div><!-- /page -->

<div class="toast" id="toast"></div>

<script>
// ── State ──────────────────────────────────────────────────────────────────
let currentStep = 1;
let selectedIntegration = null;

const GUIDES = {
  google_forms: {
    label: 'Google Forms', icon: '📋',
    steps: [
      'Abra seu formulário no Google Forms.',
      'No Zapier, crie um novo Zap e escolha Google Forms como trigger.',
      'Conecte ao LeadSolar via webhook: Action → Webhook by Zapier → POST → https://lead-intelligence-production.up.railway.app/webhook/form',
      'Mapeie os campos: Nome → name, Cidade → city, Conta de luz → monthly_bill, Tipo de imóvel → property_type.',
      'Ative o Zap e envie uma resposta de teste para confirmar.'
    ],
    code: 'POST https://lead-intelligence-production.up.railway.app/webhook/form\nContent-Type: application/json\n\n{\n  "name": "{{Nome}}",\n  "city": "{{Cidade}}",\n  "monthly_bill": {{Conta de Luz}},\n  "property_type": "{{Tipo de Im\\u00f3vel}}"\n}'
  },
  meta_ads: {
    label: 'Meta Leads Ads', icon: '📣',
    steps: [
      'Acesse o Meta Business Suite → Leads Center.',
      'Clique em "Integrações" → "CRM" e escolha Zapier.',
      'No Zapier, conecte o trigger do Meta Lead Ads à sua conta.',
      'Adicione uma Action: Webhook by Zapier → POST → https://lead-intelligence-production.up.railway.app/webhook/form',
      'Mapeie os campos do formulário do anúncio para name, city, monthly_bill e property_type. Ative o Zap.'
    ],
    code: 'POST https://lead-intelligence-production.up.railway.app/webhook/form\nContent-Type: application/json\n\n{\n  "name": "{{full_name}}",\n  "city": "{{city}}",\n  "monthly_bill": {{conta_de_luz}},\n  "property_type": "{{tipo_de_imovel}}"\n}'
  },
  rdstation: {
    label: 'RD Station', icon: '📊',
    steps: [
      'No RD Station, vá em Configurações → Integrações → Webhooks.',
      'Clique em "Novo Webhook" e insira a URL: https://lead-intelligence-production.up.railway.app/webhook/rdstation',
      'Selecione o evento: "Lead convertido".',
      'Configure os campos personalizados do formulário: cf_conta_de_luz, cf_tipo_imovel.',
      'Salve e teste enviando um lead de conversão.'
    ],
    code: '# URL do Webhook RD Station\nhttps://lead-intelligence-production.up.railway.app/webhook/rdstation\n\n# Campos personalizados esperados\ncf_conta_de_luz   → monthly_bill\ncf_tipo_imovel    → property_type\nnome              → name\ncidade            → city'
  },
  zapier_make: {
    label: 'Zapier / Make', icon: '⚡',
    steps: [
      'Crie um novo Zap ou Cenário no Zapier/Make.',
      'Defina o trigger: seu formulário, CRM ou qualquer fonte de lead.',
      'Adicione uma Action: HTTP Request (Make) ou Webhook by Zapier.',
      'Configure: método POST, URL https://lead-intelligence-production.up.railway.app/webhook/form, Content-Type: application/json.',
      'Mapeie os campos e ative o Zap/Cenário.'
    ],
    code: 'POST https://lead-intelligence-production.up.railway.app/webhook/form\nContent-Type: application/json\nX-API-Key: SUA_CHAVE_AQUI\n\n{\n  "name": "string",\n  "city": "string",\n  "monthly_bill": 350,\n  "property_type": "casa_propria | apartamento | comercial",\n  "goal": "economia | independencia | revenda"\n}'
  },
  manual: {
    label: 'Inserção Manual', icon: '✏️',
    steps: [
      'Copie sua chave de API exibida na etapa 1.',
      'Faça um POST para https://lead-intelligence-production.up.railway.app/lead com o header X-API-Key.',
      'Inclua no body JSON os campos obrigatórios: name, city, monthly_bill, property_type.',
      'A resposta retornará score (0-10), decision, urgency e whatsapp_message prontos.',
      'Use o dashboard em /dashboard para ver todos os seus leads qualificados.'
    ],
    code: "curl -X POST https://lead-intelligence-production.up.railway.app/lead \\\\\n  -H \"Content-Type: application/json\" \\\\\n  -H \"X-API-Key: SUA_CHAVE_AQUI\" \\\\\n  -d '{\n    \"name\": \"Jo\\u00e3o Silva\",\n    \"city\": \"Fortaleza\",\n    \"monthly_bill\": 480,\n    \"property_type\": \"casa_propria\",\n    \"goal\": \"economia\"\n  }'"
  }
};

// ── Init: read URL params ─────────────────────────────────────────────────
(function init() {
  const params = new URLSearchParams(window.location.search);
  const apiKey = params.get('api_key') || '';
  const el = document.getElementById('apiKeyDisplay');
  if (apiKey) {
    el.textContent = apiKey;
    el.title = apiKey;
  } else {
    el.textContent = 'ls_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx';
    el.style.color = 'var(--muted)';
    el.title = 'Sua chave aparecerá aqui após a confirmação do pagamento';
  }
})();

// ── Step navigation ────────────────────────────────────────────────────────
function goToStep(n) {
  // hide current
  document.getElementById('step-' + currentStep).classList.remove('active');
  // show new
  document.getElementById('step-' + n).classList.add('active');

  // update dots & lines
  for (let i = 1; i <= 4; i++) {
    const dot = document.getElementById('dot-' + i);
    dot.classList.remove('active', 'done');
    if (i < n) dot.classList.add('done');
    else if (i === n) dot.classList.add('active');
  }
  for (let i = 1; i <= 3; i++) {
    const line = document.getElementById('line-' + i);
    line.classList.toggle('done', i < n);
  }

  currentStep = n;
  window.scrollTo({ top: 0, behavior: 'smooth' });

  if (n === 3) renderGuide();
}

// ── Integration selection ──────────────────────────────────────────────────
function selectIntegration(el) {
  document.querySelectorAll('.int-card').forEach(c => c.classList.remove('selected'));
  el.classList.add('selected');
  selectedIntegration = el.dataset.int;
  document.getElementById('btnSeeGuide').disabled = false;
}

// ── Render guide for selected integration ─────────────────────────────────
function renderGuide() {
  if (!selectedIntegration || !GUIDES[selectedIntegration]) return;
  const g = GUIDES[selectedIntegration];

  document.getElementById('guideIcon').textContent = g.icon;
  document.getElementById('guideTitle').textContent = g.label;

  const list = document.getElementById('guideStepsList');
  list.innerHTML = '';
  g.steps.forEach((s, i) => {
    const li = document.createElement('li');
    li.innerHTML = '<div class="step-num">' + (i + 1) + '</div><span>' + escHtml(s) + '</span>';
    list.appendChild(li);
  });

  document.getElementById('guideCode').textContent = g.code;
}

function escHtml(str) {
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// ── Copy API key ───────────────────────────────────────────────────────────
function copyApiKey() {
  const key = document.getElementById('apiKeyDisplay').textContent.trim();
  navigator.clipboard.writeText(key).then(() => {
    const btn = document.getElementById('copyKeyBtn');
    btn.textContent = 'Copiado!';
    btn.classList.add('copied');
    showToast('Chave copiada para a área de transferência');
    setTimeout(() => {
      btn.textContent = 'Copiar';
      btn.classList.remove('copied');
    }, 2500);
  }).catch(() => showToast('Erro ao copiar — selecione e copie manualmente'));
}

// ── Copy WA message ────────────────────────────────────────────────────────
function copyWaMsg() {
  const msg = document.getElementById('waMsgText').textContent.trim();
  navigator.clipboard.writeText(msg).then(() => {
    showToast('Mensagem WhatsApp copiada!');
  });
}

// ── Toast ──────────────────────────────────────────────────────────────────
function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2800);
}

// ── Test lead submission ──────────────────────────────────────────────────
async function submitTestLead(e) {
  e.preventDefault();
  const btn = document.getElementById('btnQualify');
  const label = document.getElementById('qualifyLabel');

  btn.disabled = true;
  label.innerHTML = '<span class="spinner"></span> Qualificando…';

  const payload = {
    name: document.getElementById('leadName').value.trim(),
    city: document.getElementById('leadCity').value.trim(),
    monthly_bill: parseFloat(document.getElementById('leadBill').value) || 0,
    property_type: document.getElementById('leadProperty').value,
    goal: document.getElementById('leadGoal').value,
  };

  try {
    const res = await fetch('/demo', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Erro ' + res.status);
    }

    const data = await res.json();
    renderResult(data);
  } catch (err) {
    showToast('Erro: ' + err.message);
  } finally {
    btn.disabled = false;
    label.textContent = 'Qualificar agora →';
  }
}

function renderResult(data) {
  const card = document.getElementById('resultCard');
  card.classList.add('visible');

  // Score
  const score = typeof data.score === 'number' ? data.score : parseFloat(data.score) || 0;
  document.getElementById('scoreNum').textContent = score.toFixed(1);

  const circle = document.getElementById('scoreCircle');
  circle.style.borderColor = scoreColor(score);
  circle.style.background = scoreColor(score, true);

  // Decision badge
  const badge = document.getElementById('decisionBadge');
  const decision = (data.decision || '').toLowerCase();
  badge.textContent = data.decision || '—';
  badge.className = 'decision-badge';
  if (decision.includes('quente') || decision.includes('hot') || decision === 'venda imediata') {
    badge.classList.add('badge-hot');
  } else if (decision.includes('morno') || decision.includes('warm') || decision === 'nutrir') {
    badge.classList.add('badge-warm');
  } else {
    badge.classList.add('badge-cold');
  }

  // Urgency
  const urg = document.getElementById('urgencyText');
  if (data.urgency) urg.textContent = 'Urgência: ' + data.urgency;
  else urg.textContent = '';

  // WhatsApp message
  const waText = data.whatsapp_message || data.message || '';
  document.getElementById('waMsgText').textContent = waText;

  // Scroll to result
  card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function scoreColor(score, bg) {
  if (score >= 7.5) return bg ? 'rgba(34,197,94,.08)' : '#22c55e';
  if (score >= 5)   return bg ? 'rgba(245,158,11,.08)' : '#f59e0b';
  return bg ? 'rgba(239,68,68,.08)' : '#ef4444';
}

// ── Google / Firebase Auth ─────────────────────────────────────────────────
let _firebaseAuth = null;

async function _initFirebase() {
  if (_firebaseAuth) return _firebaseAuth;
  const FIREBASE_API_KEY = window.__FIREBASE_API_KEY || '';
  const FIREBASE_AUTH_DOMAIN = window.__FIREBASE_AUTH_DOMAIN || '';
  if (!FIREBASE_API_KEY) return null;
  try {
    const { initializeApp } = await import('https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js');
    const { getAuth, GoogleAuthProvider, signInWithPopup } = await import('https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js');
    const app = initializeApp({ apiKey: FIREBASE_API_KEY, authDomain: FIREBASE_AUTH_DOMAIN });
    _firebaseAuth = { getAuth, GoogleAuthProvider, signInWithPopup, auth: getAuth(app) };
    return _firebaseAuth;
  } catch(e) {
    console.error('Firebase init error', e);
    return null;
  }
}

async function linkGoogleAccount() {
  const btn = document.getElementById('googleLinkBtn');
  const apiKey = document.getElementById('apiKeyDisplay').textContent.trim();
  if (!apiKey || apiKey.startsWith('ls_xxx')) {
    showToast('Chave não disponível — acesse via /checkout/success');
    return;
  }
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner" style="border-color:rgba(0,0,0,.2);border-top-color:#1a1a1a"></span> Abrindo Google…';
  try {
    const fb = await _initFirebase();
    if (!fb) { showToast('Firebase não configurado'); btn.disabled = false; btn.innerHTML = '<img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" alt="Google"/> Entrar no Dashboard com Google'; return; }
    const provider = new fb.GoogleAuthProvider();
    const result = await fb.signInWithPopup(fb.auth, provider);
    const uid = result.user.uid;
    const token = await result.user.getIdToken();
    // Try new /onboarding/link first (uid-based), fallback to /api/link-google (token-based)
    let linked = false;
    try {
      const r1 = await fetch('/onboarding/link', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ uid, api_key: apiKey })
      });
      linked = r1.ok;
    } catch(_) {}
    if (!linked) {
      const r2 = await fetch('/api/link-google', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ firebase_token: token, api_key: apiKey })
      });
      if (!r2.ok) { const d = await r2.json(); throw new Error(d.detail || 'Erro ao vincular'); }
    }
    document.getElementById('linkSuccess').style.display = 'block';
    btn.style.display = 'none';
    showToast('✓ Conta Google vinculada! Abrindo dashboard…');
    setTimeout(() => { window.location.href = '/dashboard'; }, 1500);
  } catch(e) {
    showToast('Erro: ' + (e.message || 'Tente novamente'));
    btn.disabled = false;
    btn.innerHTML = '<img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" alt="Google"/> Entrar no Dashboard com Google';
  }
}
</script>
</body>
</html>"""


@router.get("/recover-key", response_class=HTMLResponse)
async def recover_key_page():
    """Self-service API key recovery via Google login."""
    firebase_api_key = os.getenv("FIREBASE_WEB_API_KEY", "")
    firebase_auth_domain = os.getenv("FIREBASE_AUTH_DOMAIN", "")
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Recuperar chave — LeadSolar</title>
<link rel="icon" type="image/png" href="/static/favicon.png"/>
<script>window.__FIREBASE_API_KEY='{firebase_api_key}';window.__FIREBASE_AUTH_DOMAIN='{firebase_auth_domain}';</script>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#060c18;color:#f1f5f9;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:2rem}}
.card{{background:#0d1825;border:1px solid #1a2e48;border-radius:1.5rem;padding:2.5rem;max-width:480px;width:100%;box-shadow:0 24px 64px rgba(0,0,0,.4)}}
.logo{{font-size:1.1rem;font-weight:900;color:#f59e0b;text-align:center;margin-bottom:2rem;letter-spacing:-.02em}}
.logo span{{color:#f1f5f9;font-weight:400}}
h1{{font-size:1.4rem;font-weight:800;margin-bottom:.4rem;letter-spacing:-.03em;text-align:center}}
p{{color:#6b85a0;font-size:.88rem;margin-bottom:2rem;line-height:1.6;text-align:center}}
.google-btn{{display:flex;align-items:center;justify-content:center;gap:.7rem;background:#fff;color:#1a1a1a;font-weight:600;padding:.8rem 1.5rem;border-radius:.65rem;border:none;cursor:pointer;font-size:.95rem;width:100%;font-family:inherit;transition:all .2s;box-shadow:0 2px 8px rgba(0,0,0,.18)}}
.google-btn:hover{{box-shadow:0 4px 16px rgba(0,0,0,.28);transform:translateY(-1px)}}
.google-btn:disabled{{opacity:.5;cursor:not-allowed;transform:none}}
.google-btn img{{width:20px;height:20px}}
.key-card{{background:#0a1f12;border:1px solid rgba(34,197,94,.25);border-radius:1rem;padding:1.25rem;margin-top:1.5rem;display:none}}
.key-label{{font-size:.72rem;font-weight:700;color:#22c55e;text-transform:uppercase;letter-spacing:.06em;margin-bottom:.6rem}}
.key-box{{font-family:'Courier New',monospace;font-size:.85rem;color:#fbbf24;background:#060c18;border:1px solid #1a2e48;border-radius:.5rem;padding:.85rem 1rem;word-break:break-all;margin-bottom:.75rem}}
.copy-btn{{background:#22c55e;color:#000;font-weight:700;border:none;padding:.5rem 1.1rem;border-radius:.45rem;cursor:pointer;font-size:.82rem;font-family:inherit;transition:background .2s;width:100%}}
.copy-btn:hover{{background:#16a34a}}
.err{{color:#ef4444;font-size:.83rem;text-align:center;margin-top:.75rem;display:none}}
.actions{{display:flex;gap:.75rem;margin-top:1.5rem;flex-wrap:wrap}}
.btn-primary{{flex:1;background:linear-gradient(135deg,#f59e0b,#d97706);color:#000;font-weight:700;padding:.8rem;border-radius:.6rem;text-decoration:none;text-align:center;font-size:.88rem}}
.btn-secondary{{flex:1;background:transparent;border:1px solid #1a2e48;color:#6b85a0;padding:.8rem;border-radius:.6rem;text-decoration:none;text-align:center;font-size:.88rem}}
.btn-secondary:hover{{border-color:#6b85a0;color:#f1f5f9}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
</style>
</head>
<body>
<div class="card">
  <div class="logo">Lead<span>Solar</span></div>
  <h1>Recuperar minha chave</h1>
  <p>Entre com a conta Google vinculada no momento da assinatura para recuperar sua chave de API.</p>
  <button class="google-btn" id="googleBtn" onclick="recoverWithGoogle()">
    <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" alt="Google"/>
    Entrar com Google
  </button>
  <div class="err" id="err"></div>
  <div class="key-card" id="keyCard">
    <div class="key-label">🔑 Sua chave de API</div>
    <div class="key-box" id="keyDisplay"></div>
    <button class="copy-btn" onclick="copyKey()">Copiar chave</button>
  </div>
  <div class="actions">
    <a href="/dashboard" class="btn-primary">Acessar dashboard →</a>
    <a href="/" class="btn-secondary">← Início</a>
  </div>
</div>
<script type="module">
async function recoverWithGoogle() {{
  const btn = document.getElementById('googleBtn');
  const err = document.getElementById('err');
  err.style.display = 'none';
  btn.disabled = true;
  btn.innerHTML = '<span style="display:inline-block;width:16px;height:16px;border:2px solid #ccc;border-top-color:#333;border-radius:50%;animation:spin .7s linear infinite;vertical-align:middle;margin-right:.5rem"></span> Abrindo Google…';
  try {{
    const {{ initializeApp }} = await import('https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js');
    const {{ getAuth, GoogleAuthProvider, signInWithPopup }} = await import('https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js');
    const app = initializeApp({{ apiKey: window.__FIREBASE_API_KEY, authDomain: window.__FIREBASE_AUTH_DOMAIN }});
    const auth = getAuth(app);
    const result = await signInWithPopup(auth, new GoogleAuthProvider());
    const token = await result.user.getIdToken();
    const resp = await fetch('/api/recover-key', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{ firebase_token: token }})
    }});
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.detail || 'Conta não encontrada');
    document.getElementById('keyDisplay').textContent = data.api_key;
    document.getElementById('keyCard').style.display = 'block';
    btn.style.display = 'none';
  }} catch(e) {{
    err.textContent = e.message;
    err.style.display = 'block';
    btn.disabled = false;
    btn.innerHTML = '<img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" alt="Google" style="width:20px"/> Tentar novamente';
  }}
}}
window.recoverWithGoogle = recoverWithGoogle;
function copyKey() {{
  navigator.clipboard.writeText(document.getElementById('keyDisplay').textContent)
    .then(() => {{ const b = document.querySelector('.copy-btn'); b.textContent = '✓ Copiado!'; setTimeout(() => b.textContent = 'Copiar chave', 2000); }});
}}
window.copyKey = copyKey;
</script>
</body>
</html>"""
    return HTMLResponse(content=html)


@router.get("/onboarding")
async def onboarding(
    session_id: Optional[str] = Query(default=None),
    plan: Optional[str] = Query(default=None),
    api_key: Optional[str] = Query(default=None),
):
    """
    Onboarding wizard served after Stripe checkout.

    Query params:
      - session_id: Stripe checkout session ID (optional, for future fulfillment lookup)
      - plan: subscribed plan slug (optional)
      - api_key: the newly issued API key to display to the user (optional)
    """
    _PROD_URL = "https://lead-intelligence-production.up.railway.app"
    html = _HTML.replace(_PROD_URL, _BASE_URL) if _BASE_URL != _PROD_URL else _HTML

    # Inject Firebase config so the Google login button works
    firebase_api_key = os.getenv("FIREBASE_WEB_API_KEY", "")
    firebase_auth_domain = os.getenv("FIREBASE_AUTH_DOMAIN", "")
    config_script = (
        f"<script>window.__FIREBASE_API_KEY='{firebase_api_key}';"
        f"window.__FIREBASE_AUTH_DOMAIN='{firebase_auth_domain}';</script>"
    )
    html = html.replace("</head>", config_script + "</head>", 1)

    return HTMLResponse(content=html)
