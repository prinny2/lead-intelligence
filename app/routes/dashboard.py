"""Simple HTML dashboard for browsing leads."""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Lead Intelligence — Dashboard</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0f172a;color:#e2e8f0;min-height:100vh}
  header{background:#1e293b;padding:1.25rem 2rem;border-bottom:1px solid #334155;display:flex;align-items:center;gap:.75rem}
  header h1{font-size:1.25rem;font-weight:700;color:#f8fafc}
  header span{font-size:.75rem;background:#0ea5e9;color:#fff;padding:.2rem .6rem;border-radius:999px}
  .stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:1rem;padding:1.5rem 2rem}
  .card{background:#1e293b;border:1px solid #334155;border-radius:.75rem;padding:1.25rem}
  .card .label{font-size:.7rem;text-transform:uppercase;letter-spacing:.05em;color:#94a3b8;margin-bottom:.4rem}
  .card .value{font-size:1.75rem;font-weight:700;color:#f8fafc}
  .card .sub{font-size:.75rem;color:#64748b;margin-top:.25rem}
  .filters{padding:0 2rem 1rem;display:flex;gap:.75rem;flex-wrap:wrap;align-items:center}
  .filters select,.filters input{background:#1e293b;border:1px solid #334155;color:#e2e8f0;padding:.4rem .75rem;border-radius:.5rem;font-size:.85rem}
  .filters button{background:#0ea5e9;color:#fff;border:none;padding:.4rem 1rem;border-radius:.5rem;cursor:pointer;font-size:.85rem}
  .filters button:hover{background:#0284c7}
  table{width:100%;border-collapse:collapse}
  .table-wrap{overflow-x:auto;padding:0 2rem 2rem}
  th{text-align:left;font-size:.7rem;text-transform:uppercase;letter-spacing:.05em;color:#64748b;padding:.6rem .75rem;border-bottom:1px solid #334155}
  td{padding:.65rem .75rem;border-bottom:1px solid #1e293b;font-size:.85rem;vertical-align:middle}
  tr:hover td{background:#1e293b}
  .badge{display:inline-block;padding:.15rem .5rem;border-radius:999px;font-size:.7rem;font-weight:600}
  .badge-alta{background:#dc2626;color:#fff}
  .badge-media{background:#f59e0b;color:#000}
  .badge-baixa{background:#22c55e;color:#000}
  .badge-accept{background:#16a34a;color:#fff}
  .badge-review{background:#d97706;color:#fff}
  .badge-reject{background:#dc2626;color:#fff}
  .score{display:inline-block;width:2rem;height:2rem;border-radius:50%;background:#334155;text-align:center;line-height:2rem;font-weight:700;font-size:.85rem}
  .score-high{background:#16a34a;color:#fff}
  .score-mid{background:#d97706;color:#000}
  .score-low{background:#dc2626;color:#fff}
  .wa-btn{background:#25d366;color:#fff;border:none;padding:.3rem .6rem;border-radius:.4rem;cursor:pointer;font-size:.75rem}
  .wa-btn:hover{background:#128c7e}
  .outcome-sel{background:#1e293b;border:1px solid #334155;color:#e2e8f0;padding:.2rem .4rem;border-radius:.4rem;font-size:.75rem}
  #toast{position:fixed;bottom:1.5rem;right:1.5rem;background:#0ea5e9;color:#fff;padding:.75rem 1.25rem;border-radius:.5rem;font-size:.85rem;display:none;z-index:999}
  .empty{text-align:center;padding:3rem;color:#64748b}
</style>
</head>
<body>
<header>
  <h1>⚡ Lead Intelligence</h1>
  <span>Solar</span>
</header>

<div class="stats" id="stats-row">
  <div class="card"><div class="label">Total Leads</div><div class="value" id="s-total">—</div></div>
  <div class="card"><div class="label">Score Médio</div><div class="value" id="s-avg">—</div></div>
  <div class="card"><div class="label">Alta Qualidade</div><div class="value" id="s-high">—</div><div class="sub">score ≥ 7</div></div>
  <div class="card"><div class="label">Taxa de Conversão</div><div class="value" id="s-conv">—</div><div class="sub">fechados</div></div>
</div>

<div class="filters">
  <select id="f-urgency"><option value="">Urgência</option><option>alta</option><option>media</option><option>baixa</option></select>
  <select id="f-decision"><option value="">Decisão</option><option>accept</option><option>review</option><option>reject</option></select>
  <input id="f-city" placeholder="Cidade..." style="width:140px"/>
  <input id="f-score-min" type="number" min="0" max="10" placeholder="Score min" style="width:100px"/>
  <button onclick="loadLeads()">Filtrar</button>
  <button onclick="clearFilters()" style="background:#334155">Limpar</button>
</div>

<div class="table-wrap">
<table>
  <thead>
    <tr>
      <th>Nome</th><th>Cidade</th><th>Conta</th><th>Tipo</th>
      <th>Score</th><th>Urgência</th><th>Decisão</th><th>Outcome</th><th>WhatsApp</th>
    </tr>
  </thead>
  <tbody id="leads-body">
    <tr><td colspan="9" class="empty">Carregando...</td></tr>
  </tbody>
</table>
</div>

<div id="toast"></div>

<script>
const API = '';

async function loadStats() {
  try {
    const r = await fetch(API + '/stats');
    if (!r.ok) return;
    const d = await r.json();
    document.getElementById('s-total').textContent = d.total_leads;
    document.getElementById('s-avg').textContent = d.average_score;
    document.getElementById('s-high').textContent = d.high_quality_leads;
    document.getElementById('s-conv').textContent = d.conversion_rate + '%';
  } catch(e) {}
}

async function loadLeads() {
  const urgency = document.getElementById('f-urgency').value;
  const decision = document.getElementById('f-decision').value;
  const city = document.getElementById('f-city').value.trim();
  const scoreMin = document.getElementById('f-score-min').value;
  const params = new URLSearchParams();
  if (urgency) params.set('urgency', urgency);
  if (decision) params.set('decision', decision);
  if (city) params.set('city', city);
  if (scoreMin) params.set('score_min', scoreMin);
  params.set('limit', '100');

  const tbody = document.getElementById('leads-body');
  tbody.innerHTML = '<tr><td colspan="9" class="empty">Carregando...</td></tr>';
  try {
    const r = await fetch(API + '/leads?' + params);
    if (!r.ok) { tbody.innerHTML = '<tr><td colspan="9" class="empty">Erro ao carregar leads.</td></tr>'; return; }
    const leads = await r.json();
    if (!leads.length) { tbody.innerHTML = '<tr><td colspan="9" class="empty">Nenhum lead encontrado.</td></tr>'; return; }
    tbody.innerHTML = leads.map(row).join('');
  } catch(e) {
    tbody.innerHTML = '<tr><td colspan="9" class="empty">API indisponível.</td></tr>';
  }
}

function row(l) {
  const sc = l.score >= 7 ? 'score-high' : l.score >= 5 ? 'score-mid' : 'score-low';
  const urg = l.urgency || '';
  const dec = l.decision || '';
  const bill = 'R$' + Number(l.monthly_bill).toLocaleString('pt-BR');
  const outcomes = ['','closed','ghosted','not_viable','scheduled_visit','nurturing'];
  const opts = outcomes.map(o => `<option value="${o}" ${l.outcome===o?'selected':''}>${o||'—'}</option>`).join('');
  const waBtn = l.whatsapp_message
    ? `<button class="wa-btn" onclick="copyWA(this,'${l.id}')">Copiar</button>`
    : '<span style="color:#475569">—</span>';
  return `<tr>
    <td>${esc(l.name)}</td>
    <td>${esc(l.city)}</td>
    <td>${bill}</td>
    <td>${esc(l.property_type)}</td>
    <td><span class="score ${sc}">${l.score}</span></td>
    <td><span class="badge badge-${urg}">${urg}</span></td>
    <td><span class="badge badge-${dec}">${dec||'—'}</span></td>
    <td><select class="outcome-sel" data-id="${l.id}" onchange="setOutcome(this)">${opts}</select></td>
    <td>${waBtn}</td>
  </tr>`;
}

function esc(s){ const d=document.createElement('div');d.textContent=s||'';return d.innerHTML; }

async function setOutcome(sel) {
  const id = sel.dataset.id;
  const outcome = sel.value;
  if (!outcome) return;
  try {
    const r = await fetch(API + '/leads/' + id + '/outcome', {
      method: 'PATCH',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({outcome})
    });
    if (r.ok) { toast('Outcome salvo!'); loadStats(); }
    else toast('Erro ao salvar outcome.', true);
  } catch(e) { toast('Erro de rede.', true); }
}

async function copyWA(btn, id) {
  try {
    const r = await fetch(API + '/leads/' + id);
    if (!r.ok) return;
    const lead = await r.json();
    if (lead.whatsapp_message) {
      await navigator.clipboard.writeText(lead.whatsapp_message);
      toast('Mensagem copiada!');
    }
  } catch(e) { toast('Erro ao copiar.', true); }
}

function clearFilters() {
  ['f-urgency','f-decision'].forEach(id => document.getElementById(id).value='');
  ['f-city','f-score-min'].forEach(id => document.getElementById(id).value='');
  loadLeads();
}

function toast(msg, err=false) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.style.background = err ? '#dc2626' : '#0ea5e9';
  t.style.display = 'block';
  setTimeout(() => t.style.display='none', 2500);
}

loadStats();
loadLeads();
</script>
</body>
</html>"""


@router.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def dashboard() -> HTMLResponse:
    return HTMLResponse(content=_HTML)
