"""Landing page — served at /."""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>LeadSolar — Qualifique leads solares com IA</title>
<meta name="description" content="Pare de perder tempo com leads ruins. Nossa IA qualifica, prioriza e já escreve a mensagem WhatsApp para o seu time fechar mais rápido."/>
<style>
:root{
  --bg:#0a0f1e;--surface:#111827;--surface2:#1e2a3a;--border:#1e3a5f;
  --primary:#f59e0b;--primary-dark:#d97706;--accent:#0ea5e9;
  --text:#f1f5f9;--muted:#94a3b8;--green:#22c55e;
}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:var(--bg);color:var(--text);line-height:1.6}

/* ── NAV ── */
nav{position:fixed;top:0;left:0;right:0;z-index:100;background:rgba(10,15,30,.85);backdrop-filter:blur(12px);border-bottom:1px solid var(--border);padding:.9rem 2rem;display:flex;justify-content:space-between;align-items:center}
.logo{font-size:1.2rem;font-weight:800;color:var(--primary);letter-spacing:-.02em}
.logo span{color:var(--text)}
.nav-cta{background:var(--primary);color:#000;font-weight:700;padding:.5rem 1.25rem;border-radius:.5rem;text-decoration:none;font-size:.9rem;transition:background .2s}
.nav-cta:hover{background:var(--primary-dark)}

/* ── HERO ── */
.hero{min-height:100vh;display:flex;align-items:center;justify-content:center;text-align:center;padding:6rem 1.5rem 4rem;background:radial-gradient(ellipse 80% 50% at 50% -10%,rgba(245,158,11,.15),transparent)}
.hero-badge{display:inline-flex;align-items:center;gap:.4rem;background:rgba(245,158,11,.1);border:1px solid rgba(245,158,11,.3);color:var(--primary);padding:.35rem .9rem;border-radius:999px;font-size:.8rem;font-weight:600;margin-bottom:1.5rem}
.hero h1{font-size:clamp(2.2rem,6vw,4rem);font-weight:800;line-height:1.1;letter-spacing:-.03em;max-width:800px;margin:0 auto 1.5rem}
.hero h1 em{color:var(--primary);font-style:normal}
.hero p{font-size:1.15rem;color:var(--muted);max-width:560px;margin:0 auto 2.5rem}
.hero-btns{display:flex;gap:1rem;justify-content:center;flex-wrap:wrap}
.btn-primary{background:var(--primary);color:#000;font-weight:700;padding:.85rem 2rem;border-radius:.6rem;text-decoration:none;font-size:1rem;transition:all .2s;display:inline-flex;align-items:center;gap:.5rem}
.btn-primary:hover{background:var(--primary-dark);transform:translateY(-1px)}
.btn-ghost{border:1px solid var(--border);color:var(--text);padding:.85rem 2rem;border-radius:.6rem;text-decoration:none;font-size:1rem;transition:all .2s}
.btn-ghost:hover{border-color:var(--primary);color:var(--primary)}
.hero-stats{display:flex;gap:2.5rem;justify-content:center;flex-wrap:wrap;margin-top:4rem;padding-top:3rem;border-top:1px solid var(--border)}
.stat strong{display:block;font-size:2rem;font-weight:800;color:var(--primary)}
.stat span{font-size:.85rem;color:var(--muted)}

/* ── PROBLEM ── */
.section{padding:5rem 1.5rem}
.container{max-width:1100px;margin:0 auto}
.tag{display:inline-block;font-size:.75rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--primary);margin-bottom:1rem}
h2{font-size:clamp(1.8rem,4vw,2.5rem);font-weight:800;letter-spacing:-.02em;line-height:1.15}
.subtitle{color:var(--muted);font-size:1.1rem;margin-top:.75rem;max-width:560px}
.problems{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:1.25rem;margin-top:3rem}
.problem-card{background:var(--surface);border:1px solid var(--border);border-radius:1rem;padding:1.5rem}
.problem-card .icon{font-size:1.5rem;margin-bottom:.75rem}
.problem-card h3{font-size:1rem;font-weight:700;margin-bottom:.4rem}
.problem-card p{font-size:.875rem;color:var(--muted)}

/* ── HOW IT WORKS ── */
.how{background:var(--surface);border-top:1px solid var(--border);border-bottom:1px solid var(--border)}
.steps{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:2rem;margin-top:3rem}
.step{text-align:center}
.step-num{width:3rem;height:3rem;border-radius:50%;background:rgba(245,158,11,.15);border:2px solid var(--primary);color:var(--primary);font-weight:800;font-size:1.1rem;display:flex;align-items:center;justify-content:center;margin:0 auto 1rem}
.step h3{font-weight:700;margin-bottom:.4rem}
.step p{font-size:.875rem;color:var(--muted)}
.step-arrow{display:none}

/* ── FEATURES ── */
.features-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:1.5rem;margin-top:3rem}
.feature{background:var(--surface);border:1px solid var(--border);border-radius:1rem;padding:1.75rem;transition:border-color .2s}
.feature:hover{border-color:var(--primary)}
.feature-icon{font-size:1.75rem;margin-bottom:1rem}
.feature h3{font-size:1.05rem;font-weight:700;margin-bottom:.5rem}
.feature p{font-size:.875rem;color:var(--muted)}
.feature .badge{display:inline-block;margin-top:.75rem;font-size:.7rem;font-weight:700;background:rgba(34,197,94,.15);color:var(--green);padding:.2rem .6rem;border-radius:999px}

/* ── DEMO ── */
.demo-wrap{background:var(--surface);border:1px solid var(--border);border-radius:1.25rem;overflow:hidden;margin-top:3rem;max-width:700px;margin-left:auto;margin-right:auto}
.demo-bar{background:var(--surface2);padding:.75rem 1.25rem;display:flex;align-items:center;gap:.5rem;border-bottom:1px solid var(--border)}
.demo-dot{width:.65rem;height:.65rem;border-radius:50%}
.demo-title{font-size:.8rem;color:var(--muted);margin-left:.5rem}
.demo-body{padding:1.5rem;font-family:'Courier New',monospace;font-size:.8rem;line-height:1.8}
.demo-body .key{color:#93c5fd}
.demo-body .val-str{color:#86efac}
.demo-body .val-num{color:#fca5a5}
.demo-body .val-high{color:var(--green);font-weight:700}
.demo-body .comment{color:var(--muted)}

/* ── PRICING ── */
.pricing-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1.5rem;margin-top:3rem;align-items:start}
.plan{background:var(--surface);border:1px solid var(--border);border-radius:1.25rem;padding:2rem;position:relative}
.plan.featured{border-color:var(--primary);background:linear-gradient(135deg,rgba(245,158,11,.08),var(--surface))}
.plan-badge{position:absolute;top:-1px;left:50%;transform:translateX(-50%);background:var(--primary);color:#000;font-size:.7rem;font-weight:800;padding:.3rem 1rem;border-radius:0 0 .5rem .5rem;text-transform:uppercase;letter-spacing:.05em}
.plan-name{font-size:.85rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin-bottom:.5rem}
.plan-price{font-size:2.5rem;font-weight:800;letter-spacing:-.03em;color:var(--text)}
.plan-price sup{font-size:1rem;vertical-align:top;margin-top:.5rem;color:var(--muted);font-weight:400}
.plan-price sub{font-size:.9rem;color:var(--muted);font-weight:400}
.plan-desc{font-size:.85rem;color:var(--muted);margin:.5rem 0 1.5rem}
.plan-features{list-style:none;display:flex;flex-direction:column;gap:.6rem;margin-bottom:2rem}
.plan-features li{font-size:.875rem;display:flex;gap:.5rem;align-items:flex-start}
.plan-features li::before{content:"✓";color:var(--green);font-weight:700;flex-shrink:0}
.plan-btn{display:block;text-align:center;padding:.85rem;border-radius:.6rem;font-weight:700;text-decoration:none;font-size:.95rem;transition:all .2s}
.plan-btn-primary{background:var(--primary);color:#000}
.plan-btn-primary:hover{background:var(--primary-dark)}
.plan-btn-ghost{border:1px solid var(--border);color:var(--text)}
.plan-btn-ghost:hover{border-color:var(--primary);color:var(--primary)}

/* ── TESTIMONIAL ── */
.testi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1.5rem;margin-top:3rem}
.testi{background:var(--surface);border:1px solid var(--border);border-radius:1rem;padding:1.5rem}
.testi p{font-size:.95rem;line-height:1.7;margin-bottom:1.25rem;color:var(--text)}
.testi-author{display:flex;align-items:center;gap:.75rem}
.testi-avatar{width:2.5rem;height:2.5rem;border-radius:50%;background:linear-gradient(135deg,var(--primary),var(--accent));display:flex;align-items:center;justify-content:center;font-weight:700;font-size:.9rem;color:#000;flex-shrink:0}
.testi-name{font-weight:700;font-size:.875rem}
.testi-role{font-size:.775rem;color:var(--muted)}
.stars{color:var(--primary);font-size:.85rem;margin-bottom:.75rem}

/* ── CTA ── */
.cta-section{background:linear-gradient(135deg,rgba(245,158,11,.12),rgba(14,165,233,.08));border-top:1px solid var(--border);border-bottom:1px solid var(--border);text-align:center}
.cta-section h2{max-width:600px;margin:0 auto 1rem}
.cta-section p{color:var(--muted);max-width:480px;margin:0 auto 2.5rem}
.cta-form{display:flex;gap:.75rem;justify-content:center;flex-wrap:wrap;max-width:480px;margin:0 auto}
.cta-form input{flex:1;min-width:200px;background:var(--surface);border:1px solid var(--border);color:var(--text);padding:.85rem 1.25rem;border-radius:.6rem;font-size:.95rem;outline:none;transition:border-color .2s}
.cta-form input:focus{border-color:var(--primary)}
.cta-form input::placeholder{color:var(--muted)}
.cta-note{font-size:.775rem;color:var(--muted);margin-top:.75rem}

/* ── FOOTER ── */
footer{padding:2rem 1.5rem;text-align:center;color:var(--muted);font-size:.825rem;border-top:1px solid var(--border)}
footer a{color:var(--muted);text-decoration:none}
footer a:hover{color:var(--primary)}

/* ── UTIL ── */
.text-center{text-align:center}
.mt-sm{margin-top:.5rem}
.mt-md{margin-top:1rem}
.highlight{color:var(--primary)}

@media(max-width:600px){
  nav{padding:.75rem 1rem}
  .hero-stats{gap:1.5rem}
  .cta-form{flex-direction:column}
  .cta-form input,.btn-primary,.btn-ghost{width:100%;text-align:center;justify-content:center}
}
</style>
</head>
<body>

<!-- NAV -->
<nav>
  <div class="logo">Lead<span>Solar</span></div>
  <a href="#contato" class="nav-cta">Começar grátis</a>
</nav>

<!-- HERO -->
<section class="hero">
  <div>
    <div class="hero-badge">⚡ Powered by IA</div>
    <h1>Pare de perder tempo com leads que <em>nunca vão fechar</em></h1>
    <p>Nossa IA qualifica, prioriza e já escreve a mensagem WhatsApp para cada lead solar. Seu time foca em quem vai comprar.</p>
    <div class="hero-btns">
      <a href="#contato" class="btn-primary">🚀 Testar grátis por 30 dias</a>
      <a href="#como-funciona" class="btn-ghost">Ver como funciona</a>
    </div>
    <div class="hero-stats">
      <div class="stat"><strong>3x</strong><span>mais conversões</span></div>
      <div class="stat"><strong>-70%</strong><span>tempo por lead</span></div>
      <div class="stat"><strong>20k+</strong><span>empresas solar no BR</span></div>
    </div>
  </div>
</section>

<!-- PROBLEMA -->
<section class="section">
  <div class="container">
    <div class="tag">O problema</div>
    <h2>Seu time está desperdiçando energia</h2>
    <p class="subtitle">Cada minuto gasto com um lead ruim é um lead bom sem atenção.</p>
    <div class="problems">
      <div class="problem-card">
        <div class="icon">📋</div>
        <h3>Planilha de Excel como CRM</h3>
        <p>Leads chegam de formulário, WhatsApp e indicação — tudo misturado, sem prioridade.</p>
      </div>
      <div class="problem-card">
        <div class="icon">📞</div>
        <h3>Ligando para todo mundo</h3>
        <p>O vendedor não sabe qual lead tem urgência real. Liga pra conta de R$120 antes do de R$800.</p>
      </div>
      <div class="problem-card">
        <div class="icon">💬</div>
        <h3>Mensagem genérica no WhatsApp</h3>
        <p>"Olá, tudo bem? Vi que você tem interesse em energia solar..." — lead ignora, vai pro concorrente.</p>
      </div>
      <div class="problem-card">
        <div class="icon">📉</div>
        <h3>Zero visibilidade</h3>
        <p>Quantos leads viraram visita? Quantos fecharam? Ninguém sabe. Decisão no chute.</p>
      </div>
    </div>
  </div>
</section>

<!-- COMO FUNCIONA -->
<section class="section how" id="como-funciona">
  <div class="container">
    <div class="tag text-center">Como funciona</div>
    <h2 class="text-center">Da chegada do lead ao WhatsApp em segundos</h2>
    <div class="steps">
      <div class="step">
        <div class="step-num">1</div>
        <h3>Lead chega</h3>
        <p>Formulário do site, Google Forms, Meta Ads ou via API. Tudo entra automaticamente.</p>
      </div>
      <div class="step">
        <div class="step-num">2</div>
        <h3>IA qualifica</h3>
        <p>Score de 0–10, urgência (baixa/média/alta) e decisão: aceitar, revisar ou descartar.</p>
      </div>
      <div class="step">
        <div class="step-num">3</div>
        <h3>WhatsApp pronto</h3>
        <p>Mensagem personalizada com cidade, conta e tipo de imóvel do lead — só copiar e enviar.</p>
      </div>
      <div class="step">
        <div class="step-num">4</div>
        <h3>Time age</h3>
        <p>Dashboard mostra quem ligar primeiro. Quando fechar, marca no sistema. IA aprende.</p>
      </div>
    </div>
  </div>
</section>

<!-- DEMO -->
<section class="section">
  <div class="container">
    <div class="tag text-center">Resultado real</div>
    <h2 class="text-center">O que sua equipe recebe para cada lead</h2>
    <div class="demo-wrap">
      <div class="demo-bar">
        <div class="demo-dot" style="background:#ff5f57"></div>
        <div class="demo-dot" style="background:#febc2e"></div>
        <div class="demo-dot" style="background:#28c840"></div>
        <span class="demo-title">POST /lead → resposta da API</span>
      </div>
      <div class="demo-body">
<span class="comment">// Lead: João Silva, São Paulo, conta R$680/mês, casa própria</span><br>
{<br>
&nbsp;&nbsp;<span class="key">"score"</span>: <span class="val-high">8</span>,<br>
&nbsp;&nbsp;<span class="key">"urgency"</span>: <span class="val-str">"alta"</span>,<br>
&nbsp;&nbsp;<span class="key">"decision"</span>: <span class="val-high">"accept"</span>,<br>
&nbsp;&nbsp;<span class="key">"recommendation"</span>: <span class="val-str">"Conta de R$680 em SP justifica simulação com retorno em ~4 anos. Contato via WhatsApp hoje — perguntar se é titular e se o telhado é próprio."</span>,<br>
&nbsp;&nbsp;<span class="key">"whatsapp_message"</span>: <span class="val-str">"Olá João! Vi que sua conta de energia chega a R$680/mês em São Paulo. Com solar, você pode economizar até R$544/mês e pagar o sistema em menos de 5 anos. Posso te mandar uma simulação rápida? 🌞"</span><br>
}
      </div>
    </div>
  </div>
</section>

<!-- FEATURES -->
<section class="section" style="background:var(--surface);border-top:1px solid var(--border);border-bottom:1px solid var(--border)">
  <div class="container">
    <div class="tag text-center">Funcionalidades</div>
    <h2 class="text-center">Tudo que seu time precisa</h2>
    <div class="features-grid">
      <div class="feature">
        <div class="feature-icon">🤖</div>
        <h3>Score por IA + regras</h3>
        <p>Combinação de GPT-4 com regras do mercado solar brasileiro. Score de 0 a 10 com justificativa.</p>
        <span class="badge">Exclusivo</span>
      </div>
      <div class="feature">
        <div class="feature-icon">💬</div>
        <h3>WhatsApp personalizado</h3>
        <p>Mensagem já escrita com os dados do lead. Diferente por urgência: alta fecha hoje, baixa educa primeiro.</p>
      </div>
      <div class="feature">
        <div class="feature-icon">📊</div>
        <h3>Dashboard em tempo real</h3>
        <p>Filtra por urgência, cidade, decisão. Marca outcome. Vê taxa de conversão. Sem planilha.</p>
      </div>
      <div class="feature">
        <div class="feature-icon">🔗</div>
        <h3>Conecta com tudo</h3>
        <p>Google Forms, Meta Ads, Zapier, Make. Lead chega, é qualificado e aparece no dashboard automaticamente.</p>
      </div>
      <div class="feature">
        <div class="feature-icon">📈</div>
        <h3>Calculadora de ROI solar</h3>
        <p>Payback, economia em 10 e 25 anos, tamanho do sistema e CO₂ evitado — por estado brasileiro.</p>
      </div>
      <div class="feature">
        <div class="feature-icon">🔒</div>
        <h3>API segura</h3>
        <p>Autenticação por API Key. Cada cliente tem acesso isolado aos próprios leads.</p>
      </div>
    </div>
  </div>
</section>

<!-- DEPOIMENTOS -->
<section class="section">
  <div class="container">
    <div class="tag text-center">Resultados</div>
    <h2 class="text-center">Quem já usa, não volta pro Excel</h2>
    <div class="testi-grid">
      <div class="testi">
        <div class="stars">★★★★★</div>
        <p>"Antes meu vendedor ligava para 40 leads e fechava 2. Agora ele liga para 15 leads qualificados e fecha 4. O sistema pagou em 3 semanas."</p>
        <div class="testi-author">
          <div class="testi-avatar">RM</div>
          <div>
            <div class="testi-name">Ricardo M.</div>
            <div class="testi-role">Diretor Comercial — Solar Nordeste</div>
          </div>
        </div>
      </div>
      <div class="testi">
        <div class="stars">★★★★★</div>
        <p>"A mensagem WhatsApp pronta foi o que mais me surpreendeu. O vendedor copia, manda, e o cliente responde porque não parece robô — é personalizada de verdade."</p>
        <div class="testi-author">
          <div class="testi-avatar">CF</div>
          <div>
            <div class="testi-name">Camila F.</div>
            <div class="testi-role">Gerente de Vendas — EnergiaSP</div>
          </div>
        </div>
      </div>
      <div class="testi">
        <div class="stars">★★★★★</div>
        <p>"Integrou com nosso Google Forms em 20 minutos. Agora todo lead que entra já chega qualificado pro time. Economizamos 3h por dia só em triagem."</p>
        <div class="testi-author">
          <div class="testi-avatar">PL</div>
          <div>
            <div class="testi-name">Paulo L.</div>
            <div class="testi-role">Sócio — SolarSul Instalações</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- PREÇOS -->
<section class="section" id="precos" style="background:var(--surface);border-top:1px solid var(--border);border-bottom:1px solid var(--border)">
  <div class="container">
    <div class="tag text-center">Preços</div>
    <h2 class="text-center">Simples. Sem surpresa.</h2>
    <p class="subtitle text-center" style="margin:0 auto 0">30 dias grátis em todos os planos. Sem cartão de crédito.</p>
    <div class="pricing-grid">

      <div class="plan">
        <div class="plan-name">Starter</div>
        <div class="plan-price"><sup>R$</sup>297<sub>/mês</sub></div>
        <div class="plan-desc">Para times pequenos começando a escalar</div>
        <ul class="plan-features">
          <li>Até 500 leads/mês</li>
          <li>Score por IA + regras</li>
          <li>WhatsApp personalizado</li>
          <li>Dashboard completo</li>
          <li>1 webhook (Google Forms)</li>
          <li>Export CSV</li>
          <li>Suporte por email</li>
        </ul>
        <a href="#contato" class="plan-btn plan-btn-ghost">Começar grátis</a>
      </div>

      <div class="plan featured">
        <div class="plan-badge">Mais popular</div>
        <div class="plan-name">Pro</div>
        <div class="plan-price"><sup>R$</sup>497<sub>/mês</sub></div>
        <div class="plan-desc">Para times em crescimento que precisam de volume</div>
        <ul class="plan-features">
          <li>Até 2.000 leads/mês</li>
          <li>Tudo do Starter</li>
          <li>Calculadora ROI por estado</li>
          <li>Ingestão em lote (CSV)</li>
          <li>Webhooks ilimitados</li>
          <li>Deduplicação automática</li>
          <li>Suporte prioritário WhatsApp</li>
        </ul>
        <a href="#contato" class="plan-btn plan-btn-primary">Começar grátis</a>
      </div>

      <div class="plan">
        <div class="plan-name">Enterprise</div>
        <div class="plan-price"><sup>R$</sup>997<sub>/mês</sub></div>
        <div class="plan-desc">Para distribuidoras e redes com múltiplos vendedores</div>
        <ul class="plan-features">
          <li>Leads ilimitados</li>
          <li>Tudo do Pro</li>
          <li>Setup e integração incluso</li>
          <li>Treinamento do time</li>
          <li>API com acesso completo</li>
          <li>SLA 99.9% uptime</li>
          <li>Gerente de conta dedicado</li>
        </ul>
        <a href="#contato" class="plan-btn plan-btn-ghost">Falar com time comercial</a>
      </div>

    </div>
  </div>
</section>

<!-- CTA FINAL -->
<section class="section cta-section" id="contato">
  <div class="container">
    <div class="tag text-center">Comece hoje</div>
    <h2>Seu próximo cliente está num lead que você ainda não abriu</h2>
    <p>Deixa seu WhatsApp ou email. A gente configura tudo pra você em menos de 1 hora.</p>
    <form class="cta-form" onsubmit="submitForm(event)">
      <input type="text" id="contact-input" placeholder="WhatsApp ou email" required/>
      <button type="submit" class="btn-primary" style="border:none;cursor:pointer;white-space:nowrap">Quero testar grátis →</button>
    </form>
    <p class="cta-note">Sem cartão de crédito · 30 dias grátis · Cancele quando quiser</p>
    <div id="form-msg" style="margin-top:1rem;font-size:.875rem;display:none"></div>
  </div>
</section>

<!-- FOOTER -->
<footer>
  <p>© 2025 LeadSolar · Qualificação inteligente de leads solares</p>
  <p class="mt-sm"><a href="/dashboard">Dashboard</a> · <a href="/docs">API Docs</a></p>
</footer>

<script>
function submitForm(e) {
  e.preventDefault();
  const val = document.getElementById('contact-input').value.trim();
  const msg = document.getElementById('form-msg');
  // Save to localStorage as simple demo; replace with real CRM/email integration
  const leads = JSON.parse(localStorage.getItem('landing_leads') || '[]');
  leads.push({contact: val, ts: new Date().toISOString()});
  localStorage.setItem('landing_leads', JSON.stringify(leads));
  msg.style.display = 'block';
  msg.style.color = '#22c55e';
  msg.textContent = '✓ Recebido! Vamos te contatar em breve.';
  document.getElementById('contact-input').value = '';
}

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', e => {
    const target = document.querySelector(a.getAttribute('href'));
    if (target) { e.preventDefault(); target.scrollIntoView({behavior:'smooth',block:'start'}); }
  });
});
</script>
</body>
</html>"""


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def landing() -> HTMLResponse:
    return HTMLResponse(content=_HTML)
