"""HTML dashboard — Google Sign-In + per-tenant lead management."""

import os

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import HTMLResponse

from app.auth import _verify_firebase_token

router = APIRouter()


@router.get("/me")
async def me(authorization: str | None = Header(default=None)):
    """Return current user info (requires Firebase Bearer token)."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token ausente")
    token = authorization[7:].strip()
    client = _verify_firebase_token(token)
    if not client:
        raise HTTPException(status_code=401, detail="Token inválido")
    # Fetch api_key from Firestore for self-service recovery
    api_key = None
    try:
        from app.auth import _get_firestore
        db = _get_firestore()
        if db:
            docs = db.collection("customers").where("org_id", "==", client.client_id).limit(1).get()
            for doc in docs:
                api_key = doc.to_dict().get("api_key")
    except Exception:
        pass

    return {
        "email": client.email,
        "name": client.client_name,
        "tier": client.tier,
        "org_id": client.client_id,
        "api_key": api_key,
    }


def _dashboard_html() -> str:
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    firebase_api_key = os.getenv("FIREBASE_WEB_API_KEY", "")
    auth_domain = os.getenv("FIREBASE_AUTH_DOMAIN", f"{project_id}.firebaseapp.com" if project_id else "")

    # Build config block safely (no f-string for JS object literals)
    fb_config = (
        '{"apiKey":"' + firebase_api_key + '",'
        '"authDomain":"' + auth_domain + '",'
        '"projectId":"' + project_id + '"}'
    )
    no_config_msg = "" if firebase_api_key else "Firebase não configurado. Adicione FIREBASE_WEB_API_KEY nas variáveis de ambiente."

    return """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>LeadSolar — Dashboard</title>
<link rel="icon" type="image/png" href="/static/favicon.png"/>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#080e1a;color:#e2e8f0;min-height:100vh}
header{background:#0f1929;padding:1.1rem 2rem;border-bottom:1px solid #1a3050;display:flex;align-items:center;justify-content:space-between}
header h1{font-size:1.2rem;font-weight:800;color:#f59e0b}
header h1 span{color:#f8fafc;font-weight:400}
.header-right{display:flex;gap:.75rem;align-items:center}
.user-chip{display:flex;align-items:center;gap:.5rem;background:#132030;border:1px solid #1a3050;padding:.35rem .85rem;border-radius:999px;font-size:.8rem;color:#94a3b8}
.user-chip img{width:1.4rem;height:1.4rem;border-radius:50%}
.tier-badge{font-size:.65rem;font-weight:700;padding:.1rem .45rem;border-radius:999px;background:rgba(245,158,11,.15);color:#f59e0b;border:1px solid rgba(245,158,11,.3);text-transform:uppercase}
.export-btn,.logout-btn{padding:.4rem 1rem;border-radius:.5rem;font-size:.82rem;cursor:pointer;text-decoration:none;transition:all .15s;border:1px solid #1a3050}
.export-btn{background:#1a3050;color:#94a3b8}
.export-btn:hover{background:#0ea5e9;color:#fff;border-color:#0ea5e9}
.logout-btn{background:transparent;color:#64748b}
.logout-btn:hover{color:#ef4444;border-color:#ef4444}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1rem;padding:1.5rem 2rem 0}
.card{background:#0f1929;border:1px solid #1a3050;border-radius:.75rem;padding:1.25rem}
.card .label{font-size:.68rem;text-transform:uppercase;letter-spacing:.05em;color:#64748b;margin-bottom:.4rem}
.card .value{font-size:1.75rem;font-weight:700;color:#f8fafc}
.card .sub{font-size:.72rem;color:#64748b;margin-top:.2rem}
.charts-row{display:grid;grid-template-columns:1fr 1fr;gap:1rem;padding:1.25rem 2rem 0}
.chart-box{background:#0f1929;border:1px solid #1a3050;border-radius:.75rem;padding:1.25rem}
.chart-box h3{font-size:.75rem;text-transform:uppercase;letter-spacing:.06em;color:#64748b;margin-bottom:1rem}
.chart-box canvas{max-height:160px}
.filters{padding:1.25rem 2rem .75rem;display:flex;gap:.75rem;flex-wrap:wrap;align-items:center}
.filters select,.filters input{background:#0f1929;border:1px solid #1a3050;color:#e2e8f0;padding:.4rem .75rem;border-radius:.5rem;font-size:.82rem;outline:none}
.filters select:focus,.filters input:focus{border-color:#0ea5e9}
.filters button{background:#0ea5e9;color:#fff;border:none;padding:.4rem 1rem;border-radius:.5rem;cursor:pointer;font-size:.82rem}
.filters button:hover{background:#0284c7}
.filters .clear-btn{background:#1a3050;color:#94a3b8}
.filters .clear-btn:hover{background:#334155}
table{width:100%;border-collapse:collapse}
.table-wrap{overflow-x:auto;padding:0 2rem 2rem}
th{text-align:left;font-size:.68rem;text-transform:uppercase;letter-spacing:.05em;color:#64748b;padding:.6rem .75rem;border-bottom:1px solid #1a3050}
td{padding:.65rem .75rem;border-bottom:1px solid #0f1929;font-size:.82rem;vertical-align:middle}
tr:hover td{background:#0f1929}
.badge{display:inline-block;padding:.15rem .5rem;border-radius:999px;font-size:.68rem;font-weight:700}
.badge-alta{background:#dc2626;color:#fff}
.badge-media{background:#f59e0b;color:#000}
.badge-baixa{background:#16a34a;color:#fff}
.badge-accept{background:#16a34a;color:#fff}
.badge-review{background:#d97706;color:#fff}
.badge-reject{background:#dc2626;color:#fff}
.score{display:inline-flex;width:2.1rem;height:2.1rem;border-radius:50%;align-items:center;justify-content:center;font-weight:800;font-size:.82rem}
.score-high{background:#16a34a;color:#fff}
.score-mid{background:#d97706;color:#000}
.score-low{background:#dc2626;color:#fff}
.wa-btn{background:#25d366;color:#fff;border:none;padding:.28rem .6rem;border-radius:.4rem;cursor:pointer;font-size:.72rem;white-space:nowrap}
.wa-btn:hover{background:#128c7e}
.outcome-sel{background:#0f1929;border:1px solid #1a3050;color:#e2e8f0;padding:.2rem .4rem;border-radius:.4rem;font-size:.72rem}
#toast{position:fixed;bottom:1.5rem;right:1.5rem;background:#0ea5e9;color:#fff;padding:.75rem 1.25rem;border-radius:.5rem;font-size:.82rem;display:none;z-index:999;font-weight:600}
.empty{text-align:center;padding:3rem;color:#64748b}
/* Breakdown panel */
#breakdown-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:1000;backdrop-filter:blur(2px)}
#breakdown-panel{position:fixed;top:0;right:-440px;width:420px;max-width:95vw;height:100vh;background:#0d1825;border-left:1px solid #1a3050;z-index:1001;padding:1.75rem 1.5rem;overflow-y:auto;transition:right .28s cubic-bezier(.4,0,.2,1)}
#breakdown-panel.open{right:0}
.bp-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:1.5rem}
.bp-title{font-size:1rem;font-weight:800;color:#f1f5f9}
.bp-close{background:none;border:none;color:#64748b;font-size:1.4rem;cursor:pointer;line-height:1;padding:.2rem}
.bp-close:hover{color:#ef4444}
.bp-lead-name{font-size:.8rem;color:#64748b;margin-top:.15rem}
.bp-score-big{display:flex;align-items:center;gap:1rem;background:#132030;border:1px solid #1a3050;border-radius:.85rem;padding:1rem 1.25rem;margin-bottom:1.25rem}
.bp-score-circle{width:3.5rem;height:3.5rem;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:1.5rem;font-weight:900;flex-shrink:0}
.bp-score-info{flex:1}
.bp-score-label{font-size:.68rem;text-transform:uppercase;letter-spacing:.06em;color:#64748b;margin-bottom:.2rem}
.bp-score-desc{font-size:.82rem;color:#e2e8f0}
.bp-factors-title{font-size:.68rem;text-transform:uppercase;letter-spacing:.06em;color:#64748b;margin-bottom:.75rem}
.bp-factor{display:flex;gap:.85rem;align-items:flex-start;background:#132030;border:1px solid #1a3050;border-radius:.75rem;padding:.85rem 1rem;margin-bottom:.6rem}
.bp-factor-icon{font-size:1.25rem;flex-shrink:0;margin-top:.05rem}
.bp-factor-body{flex:1;min-width:0}
.bp-factor-label{font-size:.78rem;font-weight:700;color:#e2e8f0;margin-bottom:.15rem;display:flex;align-items:center;gap:.5rem}
.bp-impact{font-size:.7rem;font-weight:800;padding:.1rem .4rem;border-radius:.3rem}
.impact-pos{background:rgba(22,163,74,.15);color:#22c55e}
.impact-neg{background:rgba(220,38,38,.15);color:#ef4444}
.impact-neu{background:rgba(100,116,139,.12);color:#64748b}
.bp-factor-desc{font-size:.75rem;color:#64748b;line-height:1.5}
.bp-reco{background:#0a1f12;border:1px solid rgba(34,197,94,.15);border-radius:.75rem;padding:1rem;margin-top:1rem}
.bp-reco-title{font-size:.68rem;font-weight:700;color:#22c55e;text-transform:uppercase;letter-spacing:.06em;margin-bottom:.5rem}
.bp-reco-text{font-size:.8rem;color:#94a3b8;line-height:1.6}
/* Login */
#login-screen{display:flex;align-items:center;justify-content:center;min-height:100vh;background:#060c18}
.login-card{background:#0d1825;border:1px solid #1a2e48;border-radius:1.5rem;padding:2.5rem;max-width:420px;width:100%;text-align:center}
.login-logo{font-size:1.6rem;font-weight:900;color:#f59e0b;margin-bottom:.25rem}
.login-logo em{color:#f1f5f9;font-style:normal}
.login-sub{color:#6b85a0;font-size:.9rem;margin-bottom:2rem;line-height:1.5}
.google-btn{display:inline-flex;align-items:center;gap:.75rem;background:#fff;color:#1e293b;font-weight:700;font-size:.9rem;padding:.85rem 1.75rem;border-radius:.65rem;border:none;cursor:pointer;width:100%;justify-content:center;transition:box-shadow .2s}
.google-btn:hover{box-shadow:0 4px 20px rgba(0,0,0,.2)}
.google-btn svg{width:1.2rem;height:1.2rem;flex-shrink:0}
.login-note{margin-top:1.25rem;font-size:.75rem;color:#4b5563}
#app-screen{display:none}
@media(max-width:768px){.charts-row{grid-template-columns:1fr}.stats{grid-template-columns:1fr 1fr}.table-wrap{padding:0 1rem 1.5rem}.filters{padding:.75rem 1rem}}
</style>
</head>
<body>

<div id="login-screen">
  <div class="login-card">
    <div class="login-logo">Lead<em>Solar</em></div>
    <p class="login-sub">Seu painel de qualificação de leads.<br>Entre com a conta Google usada no cadastro.</p>
    <button class="google-btn" id="google-btn">
      <svg viewBox="0 0 24 24"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/></svg>
      Entrar com Google
    </button>
    <p class="login-note">Apenas clientes LeadSolar com conta ativa.</p>
    <div id="login-error" style="display:none;margin-top:1rem;color:#ef4444;font-size:.8rem">""" + no_config_msg + """</div>
  </div>
</div>

<div id="app-screen">
<header>
  <h1 style="display:flex;align-items:center;gap:.55rem"><img src="/static/logo.png" alt="LeadSolar" style="width:2rem;height:2rem;border-radius:.4rem"/>Lead<span>Solar</span> <span style="font-size:.75rem;color:#64748b;font-weight:400;margin-left:.5rem">Dashboard</span></h1>
  <div class="header-right">
    <div class="user-chip">
      <img id="user-photo" src="" alt="" style="display:none"/>
      <span id="user-name">—</span>
      <span class="tier-badge" id="user-tier">—</span>
    </div>
    <a href="/leads/export" class="export-btn" id="export-link">⬇ Exportar CSV</a>
    <button class="logout-btn" id="logout-btn">Sair</button>
  </div>
</header>
<div class="stats">
  <div class="card"><div class="label">Total Leads</div><div class="value" id="s-total">—</div></div>
  <div class="card"><div class="label">Score Médio</div><div class="value" id="s-avg">—</div><div class="sub">/10</div></div>
  <div class="card"><div class="label">Alta Qualidade</div><div class="value" id="s-high">—</div><div class="sub">score ≥ 7</div></div>
  <div class="card"><div class="label">Conversão</div><div class="value" id="s-conv">—</div><div class="sub">fechados</div></div>
</div>
<div class="charts-row">
  <div class="chart-box"><h3>Distribuição de score</h3><canvas id="chart-score"></canvas></div>
  <div class="chart-box"><h3>Urgência dos leads</h3><canvas id="chart-urgency"></canvas></div>
</div>
<div class="filters">
  <select id="f-urgency"><option value="">Urgência</option><option>alta</option><option>media</option><option>baixa</option></select>
  <select id="f-decision"><option value="">Decisão</option><option>accept</option><option>review</option><option>reject</option></select>
  <input id="f-city" placeholder="Cidade..." style="width:130px"/>
  <input id="f-score-min" type="number" min="0" max="10" placeholder="Score min" style="width:100px"/>
  <button onclick="loadLeads()">Filtrar</button>
  <button class="clear-btn" onclick="clearFilters()">Limpar</button>
  <span id="leads-count" style="font-size:.78rem;color:#64748b"></span>
</div>
<div class="table-wrap">
<table>
  <thead><tr><th>Nome</th><th>Cidade</th><th>Conta</th><th>Tipo</th><th>Score</th><th>Urgência</th><th>Decisão</th><th>Outcome</th><th>WhatsApp</th></tr></thead>
  <tbody id="leads-body"><tr><td colspan="9" class="empty">Carregando...</td></tr></tbody>
</table>
</div>
</div>

<div id="toast"></div>

<!-- Score Breakdown Panel -->
<div id="breakdown-overlay" onclick="closeBreakdown()"></div>
<div id="breakdown-panel">
  <div class="bp-header">
    <div>
      <div class="bp-title">Análise detalhada do lead</div>
      <div class="bp-lead-name" id="bp-name"></div>
    </div>
    <button class="bp-close" onclick="closeBreakdown()">✕</button>
  </div>
  <div class="bp-score-big" id="bp-score-big"></div>
  <div class="bp-factors-title">Fatores que influenciaram o score</div>
  <div id="bp-factors"></div>
  <div class="bp-reco" id="bp-reco" style="display:none">
    <div class="bp-reco-title">Recomendação</div>
    <div class="bp-reco-text" id="bp-reco-text"></div>
  </div>
</div>

<script type="module">
import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js';
import { getAuth, GoogleAuthProvider, signInWithPopup, onAuthStateChanged, signOut } from 'https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js';

const FB_CONFIG = """ + fb_config + """;
let currentToken = null;
let scoreChart = null, urgencyChart = null;

const app = initializeApp(FB_CONFIG);
const auth = getAuth(app);

// Auth state
onAuthStateChanged(auth, async (user) => {
  if (user) {
    currentToken = await user.getIdToken();
    await showApp(user);
  } else {
    showLogin();
  }
});

// Buttons
document.getElementById('google-btn').addEventListener('click', async () => {
  const errEl = document.getElementById('login-error');
  errEl.style.display = 'none';
  try {
    const provider = new GoogleAuthProvider();
    provider.setCustomParameters({ prompt: 'select_account' });
    await signInWithPopup(auth, provider);
  } catch(e) {
    errEl.textContent = e.code === 'auth/popup-closed-by-user' ? 'Login cancelado.' : 'Erro: ' + e.message;
    errEl.style.display = 'block';
  }
});

document.getElementById('logout-btn').addEventListener('click', async () => {
  await signOut(auth);
  currentToken = null;
  showLogin();
});

function showLogin() {
  document.getElementById('login-screen').style.display = 'flex';
  document.getElementById('app-screen').style.display = 'none';
}

async function showApp(user) {
  document.getElementById('login-screen').style.display = 'none';
  document.getElementById('app-screen').style.display = 'block';
  const photo = document.getElementById('user-photo');
  if (user.photoURL) { photo.src = user.photoURL; photo.style.display = 'block'; }
  document.getElementById('user-name').textContent = user.displayName || user.email;
  try {
    const r = await authFetch('/me');
    if (r.ok) {
      const data = await r.json();
      document.getElementById('user-tier').textContent = data.tier;
    }
  } catch(e) {}
  initCharts();
  loadStats();
  loadLeads();
}

async function authFetch(url, opts = {}) {
  if (!currentToken && auth.currentUser) {
    currentToken = await auth.currentUser.getIdToken();
  }
  return fetch(url, {
    ...opts,
    headers: { ...(opts.headers || {}), 'Authorization': 'Bearer ' + (currentToken || '') },
  });
}

function initCharts() {
  const C = window.Chart;
  if (!C || scoreChart) return;
  const cd = {
    plugins: { legend: { display: false } },
    scales: { x: { ticks: { color:'#64748b', font:{size:11} }, grid:{color:'#1a3050'} }, y: { ticks:{color:'#64748b',font:{size:11}}, grid:{color:'#1a3050'} } }
  };
  scoreChart = new C(document.getElementById('chart-score'), {
    type:'bar',
    data:{ labels:['0-3','4-6','7-10'], datasets:[{data:[0,0,0],backgroundColor:['#dc2626','#d97706','#16a34a'],borderRadius:6,borderSkipped:false}] },
    options:{...cd,responsive:true,maintainAspectRatio:true},
  });
  urgencyChart = new C(document.getElementById('chart-urgency'), {
    type:'doughnut',
    data:{ labels:['Alta','Média','Baixa'], datasets:[{data:[0,0,0],backgroundColor:['#dc2626','#f59e0b','#16a34a'],borderWidth:2,borderColor:'#0f1929'}] },
    options:{responsive:true,maintainAspectRatio:true,plugins:{legend:{display:true,position:'right',labels:{color:'#94a3b8',font:{size:11},boxWidth:12}}}},
  });
}

async function loadStats() {
  try {
    const r = await authFetch('/stats');
    if (!r.ok) return;
    const d = await r.json();
    document.getElementById('s-total').textContent = d.total_leads;
    document.getElementById('s-avg').textContent = d.average_score;
    document.getElementById('s-high').textContent = d.high_quality_leads;
    document.getElementById('s-conv').textContent = d.conversion_rate + '%';
    if (scoreChart) {
      const all = await authFetch('/leads?limit=500').then(r=>r.json()).catch(()=>[]);
      scoreChart.data.datasets[0].data = [
        all.filter(l=>l.score<=3).length,
        all.filter(l=>l.score>=4&&l.score<=6).length,
        all.filter(l=>l.score>=7).length
      ];
      scoreChart.update();
      const urg = d.breakdown_by_urgency || {};
      urgencyChart.data.datasets[0].data = [urg.alta||0, urg.media||0, urg.baixa||0];
      urgencyChart.update();
    }
  } catch(e) {}
}

window.loadLeads = async function() {
  const params = new URLSearchParams();
  const urgency = document.getElementById('f-urgency').value;
  const decision = document.getElementById('f-decision').value;
  const city = document.getElementById('f-city').value.trim();
  const scoreMin = document.getElementById('f-score-min').value;
  if (urgency) params.set('urgency', urgency);
  if (decision) params.set('decision', decision);
  if (city) params.set('city', city);
  if (scoreMin) params.set('score_min', scoreMin);
  params.set('limit', '100');
  const tbody = document.getElementById('leads-body');
  tbody.innerHTML = '<tr><td colspan="9" class="empty">Carregando...</td></tr>';
  try {
    const r = await authFetch('/leads?' + params);
    if (!r.ok) { tbody.innerHTML = '<tr><td colspan="9" class="empty">Erro ao carregar leads.</td></tr>'; return; }
    const leads = await r.json();
    document.getElementById('leads-count').textContent = leads.length + ' lead' + (leads.length !== 1 ? 's' : '');
    tbody.innerHTML = leads.length ? leads.map(renderRow).join('') : '<tr><td colspan="9" class="empty">Nenhum lead encontrado.</td></tr>';
  } catch(e) {
    tbody.innerHTML = '<tr><td colspan="9" class="empty">API indisponível.</td></tr>';
  }
};

function renderRow(l) {
  const sc = l.score>=7?'score-high':l.score>=4?'score-mid':'score-low';
  const urg = l.urgency||'', dec = l.decision||'';
  const bill = 'R$' + Number(l.monthly_bill).toLocaleString('pt-BR');
  const outcomes = ['','closed','ghosted','not_viable','scheduled_visit','nurturing'];
  const outLabels = {'':'—','closed':'Fechado','ghosted':'Sumiu','not_viable':'Inviável','scheduled_visit':'Visita agendada','nurturing':'Nurturing'};
  const opts = outcomes.map(o=>`<option value="${o}" ${l.outcome===o?'selected':''}>${outLabels[o]||o}</option>`).join('');
  const typeIcon = {casa:'🏠',apartamento:'🏢',comercial:'🏪'}[l.property_type]||'🏗';
  const waBtn = l.whatsapp_message ? `<button class="wa-btn" onclick="copyWA(this,'${l.id}')">📋 Copiar</button>` : '<span style="color:#475569">—</span>';
  return `<tr>
    <td style="font-weight:600">${esc(l.name)}</td>
    <td>${esc(l.city)}</td>
    <td style="font-weight:600">${bill}</td>
    <td>${typeIcon} ${esc(l.property_type)}</td>
    <td><span class="score ${sc}" onclick="showBreakdown('${l.id}','${esc(l.name)}')" style="cursor:pointer" title="Ver análise detalhada">${l.score}</span></td>
    <td><span class="badge badge-${urg}">${urg}</span></td>
    <td><span class="badge badge-${dec}">${dec||'—'}</span></td>
    <td><select class="outcome-sel" data-id="${l.id}" onchange="setOutcome(this)">${opts}</select></td>
    <td>${waBtn}</td>
  </tr>`;
}

function esc(s) { const d=document.createElement('div'); d.textContent=s||''; return d.innerHTML; }

window.setOutcome = async function(sel) {
  const id = sel.dataset.id, outcome = sel.value;
  if (!outcome) return;
  try {
    const r = await authFetch('/leads/'+id+'/outcome', {
      method:'PATCH', headers:{'Content-Type':'application/json'}, body:JSON.stringify({outcome})
    });
    if (r.ok) { toast('✓ Outcome salvo!'); loadStats(); } else toast('Erro ao salvar.', true);
  } catch(e) { toast('Erro de rede.', true); }
};

window.copyWA = async function(btn, id) {
  try {
    const r = await authFetch('/leads/'+id);
    if (!r.ok) return;
    const lead = await r.json();
    if (lead.whatsapp_message) {
      await navigator.clipboard.writeText(lead.whatsapp_message);
      btn.textContent='✓ Copiado!'; setTimeout(()=>btn.textContent='📋 Copiar',2000);
      toast('Mensagem copiada!');
    }
  } catch(e) { toast('Erro ao copiar.', true); }
};

window.clearFilters = function() {
  ['f-urgency','f-decision'].forEach(id=>document.getElementById(id).value='');
  ['f-city','f-score-min'].forEach(id=>document.getElementById(id).value='');
  loadLeads();
};

function toast(msg, err=false) {
  const t = document.getElementById('toast');
  t.textContent = msg; t.style.background = err ? '#dc2626' : '#0ea5e9';
  t.style.display = 'block'; setTimeout(()=>t.style.display='none', 2500);
}

// ── Breakdown panel ──────────────────────────────────────────────────────────

window.showBreakdown = async function(id, name) {
  document.getElementById('bp-name').textContent = name || '';
  document.getElementById('bp-factors').innerHTML = '<div style="color:#64748b;font-size:.82rem;padding:.5rem 0">Carregando...</div>';
  document.getElementById('bp-score-big').innerHTML = '';
  document.getElementById('bp-reco').style.display = 'none';

  document.getElementById('breakdown-overlay').style.display = 'block';
  const panel = document.getElementById('breakdown-panel');
  requestAnimationFrame(() => panel.classList.add('open'));

  try {
    const r = await authFetch('/leads/' + id);
    if (!r.ok) { document.getElementById('bp-factors').innerHTML = '<div style="color:#ef4444;font-size:.82rem">Erro ao carregar.</div>'; return; }
    const lead = await r.json();
    _renderBreakdown(lead);
  } catch(e) {
    document.getElementById('bp-factors').innerHTML = '<div style="color:#ef4444;font-size:.82rem">Erro de rede.</div>';
  }
};

window.closeBreakdown = function() {
  const panel = document.getElementById('breakdown-panel');
  panel.classList.remove('open');
  setTimeout(() => { document.getElementById('breakdown-overlay').style.display = 'none'; }, 280);
};

function _renderBreakdown(lead) {
  const sc = lead.score >= 7 ? 'score-high' : lead.score >= 4 ? 'score-mid' : 'score-low';
  const scColors = {'score-high':'#16a34a','score-mid':'#d97706','score-low':'#dc2626'};
  const scLabels = {'score-high':'Alta qualidade','score-mid':'Qualidade média','score-low':'Baixa qualidade'};
  const col = scColors[sc];
  document.getElementById('bp-score-big').innerHTML = `
    <div class="bp-score-circle" style="background:${col}20;color:${col};border:2px solid ${col}40">${lead.score}</div>
    <div class="bp-score-info">
      <div class="bp-score-label">Score final</div>
      <div class="bp-score-desc" style="font-weight:700;color:${col}">${scLabels[sc]}</div>
      ${lead.ai_raw_score != null ? '<div class="bp-score-desc" style="margin-top:.2rem">IA base: ' + lead.ai_raw_score + '/10' + (lead.rule_delta !== 0 ? ' · Ajuste regras: ' + (lead.rule_delta > 0 ? '+' : '') + lead.rule_delta : '') + '</div>' : ''}
    </div>`;

  const factors = lead.score_breakdown;
  const container = document.getElementById('bp-factors');
  if (!factors || factors.length === 0) {
    container.innerHTML = '<div style="color:#64748b;font-size:.82rem;padding:.5rem 0">Detalhamento não disponível para este lead.</div>';
  } else {
    container.innerHTML = factors.filter(f => f.factor !== 'ai_base').map(f => {
      const impClass = f.impact > 0 ? 'impact-pos' : f.impact < 0 ? 'impact-neg' : 'impact-neu';
      const impText = f.impact > 0 ? '+' + f.impact : f.impact < 0 ? String(f.impact) : '±0';
      return `<div class="bp-factor">
        <div class="bp-factor-icon">${f.icon || '📊'}</div>
        <div class="bp-factor-body">
          <div class="bp-factor-label">${esc(f.label)} <span class="bp-impact ${impClass}">${impText}</span></div>
          <div class="bp-factor-desc">${esc(f.description)}</div>
        </div>
      </div>`;
    }).join('');
  }

  if (lead.recommendation) {
    document.getElementById('bp-reco-text').textContent = lead.recommendation;
    document.getElementById('bp-reco').style.display = 'block';
  }
}

document.addEventListener('keydown', e => { if (e.key === 'Escape') window.closeBreakdown(); });
</script>
</body>
</html>"""


@router.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def dashboard() -> HTMLResponse:
    return HTMLResponse(content=_dashboard_html())
