"""HTML dashboard for browsing and managing leads."""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>LeadSolar — Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#080e1a;color:#e2e8f0;min-height:100vh}
header{background:#0f1929;padding:1.1rem 2rem;border-bottom:1px solid #1a3050;display:flex;align-items:center;justify-content:space-between}
header h1{font-size:1.2rem;font-weight:800;color:#f59e0b}
header h1 span{color:#f8fafc;font-weight:400}
.header-right{display:flex;gap:.75rem;align-items:center}
.export-btn{background:#1a3050;color:#94a3b8;border:1px solid #1a3050;padding:.4rem 1rem;border-radius:.5rem;cursor:pointer;font-size:.82rem;text-decoration:none;transition:all .15s}
.export-btn:hover{background:#0ea5e9;color:#fff;border-color:#0ea5e9}
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
.pill-count{display:inline-block;background:#1a3050;color:#94a3b8;font-size:.68rem;padding:.1rem .5rem;border-radius:999px;margin-left:.4rem}
@media(max-width:768px){.charts-row{grid-template-columns:1fr}.stats{grid-template-columns:1fr 1fr}.table-wrap{padding:0 1rem 1.5rem}.filters{padding:.75rem 1rem}}
</style>
</head>
<body>
<header>
  <h1>Lead<span>Solar</span> <span style="font-size:.75rem;color:#64748b;font-weight:400;margin-left:.5rem">Dashboard</span></h1>
  <div class="header-right">
    <a href="/leads/export" class="export-btn">⬇ Exportar CSV</a>
  </div>
</header>

<div class="stats" id="stats-row">
  <div class="card"><div class="label">Total Leads</div><div class="value" id="s-total">—</div></div>
  <div class="card"><div class="label">Score Médio</div><div class="value" id="s-avg">—</div><div class="sub">/10</div></div>
  <div class="card"><div class="label">Alta Qualidade</div><div class="value" id="s-high">—</div><div class="sub">score ≥ 7</div></div>
  <div class="card"><div class="label">Conversão</div><div class="value" id="s-conv">—</div><div class="sub">fechados</div></div>
</div>

<div class="charts-row">
  <div class="chart-box">
    <h3>Distribuição de score</h3>
    <canvas id="chart-score"></canvas>
  </div>
  <div class="chart-box">
    <h3>Urgência dos leads</h3>
    <canvas id="chart-urgency"></canvas>
  </div>
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
let scoreChart, urgencyChart;

function initCharts() {
  const chartDefaults = {
    plugins: { legend: { display: false } },
    scales: { x: { ticks: { color: '#64748b', font: { size: 11 } }, grid: { color: '#1a3050' } }, y: { ticks: { color: '#64748b', font: { size: 11 } }, grid: { color: '#1a3050' } } },
  };

  scoreChart = new Chart(document.getElementById('chart-score'), {
    type: 'bar',
    data: {
      labels: ['0-3 Baixo', '4-6 Médio', '7-10 Alto'],
      datasets: [{ data: [0, 0, 0], backgroundColor: ['#dc2626', '#d97706', '#16a34a'], borderRadius: 6, borderSkipped: false }]
    },
    options: { ...chartDefaults, responsive: true, maintainAspectRatio: true },
  });

  urgencyChart = new Chart(document.getElementById('chart-urgency'), {
    type: 'doughnut',
    data: {
      labels: ['Alta', 'Média', 'Baixa'],
      datasets: [{ data: [0, 0, 0], backgroundColor: ['#dc2626', '#f59e0b', '#16a34a'], borderWidth: 2, borderColor: '#0f1929' }]
    },
    options: {
      responsive: true, maintainAspectRatio: true,
      plugins: { legend: { display: true, position: 'right', labels: { color: '#94a3b8', font: { size: 11 }, boxWidth: 12 } } },
    },
  });
}

async function loadStats() {
  try {
    const r = await fetch('/stats');
    if (!r.ok) return;
    const d = await r.json();
    document.getElementById('s-total').textContent = d.total_leads;
    document.getElementById('s-avg').textContent = d.average_score;
    document.getElementById('s-high').textContent = d.high_quality_leads;
    document.getElementById('s-conv').textContent = d.conversion_rate + '%';

    if (scoreChart && d.breakdown_by_urgency !== undefined) {
      const all = await fetch('/leads?limit=500').then(r => r.json()).catch(() => []);
      const low = all.filter(l => l.score <= 3).length;
      const mid = all.filter(l => l.score >= 4 && l.score <= 6).length;
      const high = all.filter(l => l.score >= 7).length;
      scoreChart.data.datasets[0].data = [low, mid, high];
      scoreChart.update();

      const urg = d.breakdown_by_urgency || {};
      urgencyChart.data.datasets[0].data = [urg.alta||0, urg.media||0, urg.baixa||0];
      urgencyChart.update();
    }
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
    const r = await fetch('/leads?' + params);
    if (!r.ok) { tbody.innerHTML = '<tr><td colspan="9" class="empty">Erro ao carregar leads.</td></tr>'; return; }
    const leads = await r.json();
    document.getElementById('leads-count').textContent = leads.length + ' lead' + (leads.length !== 1 ? 's' : '');
    if (!leads.length) { tbody.innerHTML = '<tr><td colspan="9" class="empty">Nenhum lead encontrado.</td></tr>'; return; }
    tbody.innerHTML = leads.map(row).join('');
  } catch(e) {
    tbody.innerHTML = '<tr><td colspan="9" class="empty">API indisponível.</td></tr>';
  }
}

function row(l) {
  const sc = l.score >= 7 ? 'score-high' : l.score >= 4 ? 'score-mid' : 'score-low';
  const urg = l.urgency || '';
  const dec = l.decision || '';
  const bill = 'R$' + Number(l.monthly_bill).toLocaleString('pt-BR');
  const outcomes = ['','closed','ghosted','not_viable','scheduled_visit','nurturing'];
  const outLabels = {'':'—','closed':'Fechado','ghosted':'Sumiu','not_viable':'Inviável','scheduled_visit':'Visita agendada','nurturing':'Nurturing'};
  const opts = outcomes.map(o => `<option value="${o}" ${l.outcome===o?'selected':''}>${outLabels[o]||o}</option>`).join('');
  const waBtn = l.whatsapp_message
    ? `<button class="wa-btn" onclick="copyWA(this,'${l.id}')">📋 Copiar</button>`
    : '<span style="color:#475569">—</span>';
  const typeIcon = {casa:'🏠',apartamento:'🏢',comercial:'🏪'}[l.property_type] || '🏗';
  return `<tr>
    <td style="font-weight:600">${esc(l.name)}</td>
    <td>${esc(l.city)}</td>
    <td style="font-weight:600">${bill}</td>
    <td>${typeIcon} ${esc(l.property_type)}</td>
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
    const r = await fetch('/leads/' + id + '/outcome', {
      method: 'PATCH',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({outcome})
    });
    if (r.ok) { toast('✓ Outcome salvo!'); loadStats(); }
    else toast('Erro ao salvar.', true);
  } catch(e) { toast('Erro de rede.', true); }
}

async function copyWA(btn, id) {
  try {
    const r = await fetch('/leads/' + id);
    if (!r.ok) return;
    const lead = await r.json();
    if (lead.whatsapp_message) {
      await navigator.clipboard.writeText(lead.whatsapp_message);
      btn.textContent = '✓ Copiado!';
      setTimeout(() => btn.textContent = '📋 Copiar', 2000);
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

initCharts();
loadStats();
loadLeads();
</script>
</body>
</html>"""


@router.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def dashboard() -> HTMLResponse:
    return HTMLResponse(content=_HTML)
