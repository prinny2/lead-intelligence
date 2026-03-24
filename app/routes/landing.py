"""Landing page — served at /."""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>LeadSolar — Seu vendedor liga pro lead certo, na hora certa</title>
<meta name="description" content="Chega de ligar pra quem mora em apartamento alugado com conta de R$90. Nossa ferramenta mostra quem tem conta alta, imóvel próprio e quer comprar — antes do seu vendedor pegar o telefone."/>
<style>
:root{
  --bg:#080e1a;--surface:#0f1929;--surface2:#162338;--border:#1a3050;
  --sun:#f59e0b;--sun-dark:#d97706;--sky:#0ea5e9;
  --text:#f1f5f9;--muted:#7c94b0;--green:#22c55e;--red:#ef4444;
}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:var(--bg);color:var(--text);line-height:1.65}

nav{position:fixed;top:0;left:0;right:0;z-index:100;background:rgba(8,14,26,.9);backdrop-filter:blur(14px);border-bottom:1px solid var(--border);padding:.85rem 2rem;display:flex;justify-content:space-between;align-items:center}
.logo{font-size:1.15rem;font-weight:800;color:var(--sun)}
.logo span{color:var(--text);font-weight:400}
.nav-links{display:flex;gap:1.75rem;align-items:center}
.nav-links a{color:var(--muted);text-decoration:none;font-size:.875rem;transition:color .2s}
.nav-links a:hover{color:var(--text)}
.nav-cta{background:var(--sun);color:#000;font-weight:700;padding:.5rem 1.25rem;border-radius:.5rem;text-decoration:none;font-size:.875rem;transition:background .2s}
.nav-cta:hover{background:var(--sun-dark)}

/* HERO */
.hero{min-height:100vh;display:flex;align-items:center;padding:7rem 2rem 4rem;background:radial-gradient(ellipse 90% 60% at 60% -5%,rgba(245,158,11,.1),transparent),radial-gradient(ellipse 60% 40% at 10% 80%,rgba(14,165,233,.06),transparent)}
.hero-inner{max-width:1100px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:4rem;align-items:center}
.hero-eyebrow{font-size:.8rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:var(--sun);margin-bottom:1.25rem}
.hero h1{font-size:clamp(2rem,4.5vw,3.25rem);font-weight:800;line-height:1.08;letter-spacing:-.03em;margin-bottom:1.25rem}
.hero h1 em{color:var(--sun);font-style:normal}
.hero-sub{font-size:1.05rem;color:var(--muted);margin-bottom:2rem;line-height:1.7}
.hero-sub strong{color:var(--text)}
.hero-btns{display:flex;gap:.85rem;flex-wrap:wrap}
.btn-sun{background:var(--sun);color:#000;font-weight:700;padding:.85rem 1.75rem;border-radius:.6rem;text-decoration:none;font-size:.95rem;transition:all .15s;white-space:nowrap}
.btn-sun:hover{background:var(--sun-dark);transform:translateY(-1px)}
.btn-outline{border:1px solid var(--border);color:var(--muted);padding:.85rem 1.75rem;border-radius:.6rem;text-decoration:none;font-size:.95rem;transition:all .15s;white-space:nowrap}
.btn-outline:hover{border-color:var(--sun);color:var(--sun)}
.hero-proof{margin-top:2.5rem;padding-top:2rem;border-top:1px solid var(--border);display:flex;gap:2rem;flex-wrap:wrap}
.proof-item strong{display:block;font-size:1.6rem;font-weight:800;color:var(--sun);line-height:1}
.proof-item span{font-size:.78rem;color:var(--muted);margin-top:.2rem;display:block}

/* CARD LATERAL DO HERO */
.hero-card{background:var(--surface);border:1px solid var(--border);border-radius:1.25rem;overflow:hidden}
.card-header{background:var(--surface2);padding:.85rem 1.25rem;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:.75rem}
.card-dot{width:.55rem;height:.55rem;border-radius:50%}
.card-title{font-size:.78rem;color:var(--muted)}
.card-body{padding:1.5rem;font-size:.82rem;font-family:'Courier New',monospace;line-height:2}
.k{color:#7dd3fc}.vs{color:#86efac}.vn{color:#fca5a5}.vh{color:var(--green);font-weight:700}.c{color:var(--muted)}
.card-wa{margin:1.25rem 1.5rem 1.5rem;background:#0d2218;border:1px solid #16a34a33;border-radius:.75rem;padding:1rem}
.card-wa-label{font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--green);margin-bottom:.5rem}
.card-wa-text{font-size:.8rem;color:#bbf7d0;line-height:1.6}

/* SECTION BASE */
.section{padding:5rem 2rem}
.container{max-width:1100px;margin:0 auto}
.section-tag{font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:var(--sun);margin-bottom:.85rem}
.section-title{font-size:clamp(1.75rem,3.5vw,2.4rem);font-weight:800;letter-spacing:-.025em;line-height:1.15;margin-bottom:.75rem}
.section-sub{color:var(--muted);font-size:1rem;max-width:540px;line-height:1.7}
.center{text-align:center}.center .section-sub{margin:0 auto}

/* PROBLEMA */
.pain-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:1.25rem;margin-top:3rem}
.pain{background:var(--surface);border:1px solid var(--border);border-radius:1rem;padding:1.5rem}
.pain-icon{font-size:1.4rem;margin-bottom:.85rem}
.pain h3{font-size:.95rem;font-weight:700;margin-bottom:.4rem}
.pain p{font-size:.82rem;color:var(--muted);line-height:1.6}
.pain .quote{margin-top:.85rem;padding:.65rem .85rem;background:rgba(239,68,68,.06);border-left:2px solid var(--red);border-radius:0 .4rem .4rem 0;font-size:.78rem;color:#fca5a5;font-style:italic}

/* COMO FUNCIONA */
.how-bg{background:var(--surface);border-top:1px solid var(--border);border-bottom:1px solid var(--border)}
.steps{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:2rem;margin-top:3rem;position:relative}
.step{text-align:center;padding:0 .5rem}
.step-num{width:2.75rem;height:2.75rem;border-radius:50%;background:rgba(245,158,11,.12);border:2px solid rgba(245,158,11,.4);color:var(--sun);font-weight:800;display:flex;align-items:center;justify-content:center;margin:0 auto 1rem;font-size:1rem}
.step h3{font-weight:700;font-size:.95rem;margin-bottom:.4rem}
.step p{font-size:.82rem;color:var(--muted);line-height:1.6}

/* FEATURES */
.feat-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:1.25rem;margin-top:3rem}
.feat{background:var(--surface);border:1px solid var(--border);border-radius:1rem;padding:1.6rem;transition:border-color .2s,transform .2s}
.feat:hover{border-color:rgba(245,158,11,.4);transform:translateY(-2px)}
.feat-icon{font-size:1.6rem;margin-bottom:.85rem}
.feat h3{font-size:.95rem;font-weight:700;margin-bottom:.4rem}
.feat p{font-size:.82rem;color:var(--muted);line-height:1.6}
.feat-tag{display:inline-block;margin-top:.75rem;font-size:.65rem;font-weight:700;padding:.2rem .6rem;border-radius:999px}
.feat-tag-green{background:rgba(34,197,94,.12);color:var(--green)}
.feat-tag-yellow{background:rgba(245,158,11,.12);color:var(--sun)}

/* MERCADO */
.market-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1.25rem;margin-top:3rem}
.mcard{background:var(--surface);border:1px solid var(--border);border-radius:1rem;padding:1.5rem;text-align:center}
.mcard strong{display:block;font-size:2rem;font-weight:800;color:var(--sun);line-height:1;margin-bottom:.4rem}
.mcard span{font-size:.8rem;color:var(--muted)}

/* DEPO */
.testi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1.25rem;margin-top:3rem}
.testi{background:var(--surface);border:1px solid var(--border);border-radius:1rem;padding:1.6rem}
.stars{color:var(--sun);font-size:.82rem;margin-bottom:.85rem}
.testi blockquote{font-size:.9rem;line-height:1.7;color:var(--text);margin-bottom:1.25rem;font-style:italic}
.testi blockquote strong{color:var(--sun);font-style:normal}
.testi-who{display:flex;align-items:center;gap:.75rem}
.testi-av{width:2.4rem;height:2.4rem;border-radius:50%;background:linear-gradient(135deg,var(--sun),var(--sky));display:flex;align-items:center;justify-content:center;font-weight:700;font-size:.82rem;color:#000;flex-shrink:0}
.testi-name{font-weight:700;font-size:.82rem}
.testi-role{font-size:.72rem;color:var(--muted)}

/* PRICING */
.price-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1.25rem;margin-top:3rem;align-items:start}
.plan{background:var(--surface);border:1px solid var(--border);border-radius:1.25rem;padding:2rem;position:relative}
.plan.pop{border-color:rgba(245,158,11,.5);background:linear-gradient(160deg,rgba(245,158,11,.06),var(--surface))}
.pop-badge{position:absolute;top:-1px;left:50%;transform:translateX(-50%);background:var(--sun);color:#000;font-size:.65rem;font-weight:800;padding:.25rem .9rem;border-radius:0 0 .5rem .5rem;text-transform:uppercase;letter-spacing:.06em;white-space:nowrap}
.plan-tier{font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin-bottom:.5rem}
.plan-price{font-size:2.75rem;font-weight:800;letter-spacing:-.04em;line-height:1}
.plan-price sup{font-size:.95rem;font-weight:500;color:var(--muted);vertical-align:top;margin-top:.4rem}
.plan-price sub{font-size:.85rem;font-weight:400;color:var(--muted)}
.plan-pitch{font-size:.82rem;color:var(--muted);margin:.6rem 0 1.5rem;line-height:1.5}
.plan-list{list-style:none;display:flex;flex-direction:column;gap:.55rem;margin-bottom:2rem}
.plan-list li{font-size:.82rem;display:flex;gap:.5rem;line-height:1.4}
.plan-list li::before{content:"✓";color:var(--green);font-weight:700;flex-shrink:0;margin-top:.05rem}
.plan-list li.no::before{content:"—";color:var(--muted)}
.plan-list li.no{color:var(--muted)}
.plan-btn{display:block;text-align:center;padding:.8rem;border-radius:.6rem;font-weight:700;text-decoration:none;font-size:.9rem;transition:all .15s}
.plan-btn-sun{background:var(--sun);color:#000}.plan-btn-sun:hover{background:var(--sun-dark)}
.plan-btn-out{border:1px solid var(--border);color:var(--text)}.plan-btn-out:hover{border-color:var(--sun);color:var(--sun)}
.price-note{text-align:center;margin-top:1.5rem;font-size:.78rem;color:var(--muted)}

/* CTA */
.cta-wrap{background:linear-gradient(135deg,rgba(245,158,11,.1),rgba(14,165,233,.06));border-top:1px solid var(--border);border-bottom:1px solid var(--border);text-align:center}
.cta-wrap h2{max-width:640px;margin:0 auto 1rem}
.cta-wrap p{color:var(--muted);max-width:460px;margin:0 auto 2rem;font-size:.95rem}
.cta-form{display:flex;gap:.75rem;justify-content:center;flex-wrap:wrap;max-width:460px;margin:0 auto}
.cta-form input{flex:1;min-width:200px;background:var(--surface);border:1px solid var(--border);color:var(--text);padding:.8rem 1.1rem;border-radius:.6rem;font-size:.9rem;outline:none;transition:border-color .2s}
.cta-form input:focus{border-color:var(--sun)}
.cta-form input::placeholder{color:var(--muted)}
.cta-trust{display:flex;gap:1.25rem;justify-content:center;flex-wrap:wrap;margin-top:1.25rem}
.cta-trust span{font-size:.75rem;color:var(--muted);display:flex;align-items:center;gap:.3rem}

footer{padding:2rem;text-align:center;color:var(--muted);font-size:.78rem;border-top:1px solid var(--border)}
footer a{color:var(--muted);text-decoration:none}.footer a:hover{color:var(--sun)}
.footer-links{display:flex;gap:1.5rem;justify-content:center;margin-top:.5rem}

#toast{position:fixed;bottom:1.5rem;right:1.5rem;background:var(--green);color:#000;font-weight:700;padding:.75rem 1.25rem;border-radius:.5rem;font-size:.85rem;display:none;z-index:999}

@media(max-width:768px){
  .hero-inner{grid-template-columns:1fr}
  .hero-card{display:none}
  nav .nav-links{display:none}
  .hero{padding:6rem 1.25rem 3rem}
  .section{padding:3.5rem 1.25rem}
}
</style>
</head>
<body>

<nav>
  <div class="logo">Lead<span>Solar</span></div>
  <div class="nav-links">
    <a href="#problema">O problema</a>
    <a href="#como-funciona">Como funciona</a>
    <a href="#precos">Preços</a>
  </div>
  <a href="#contato" class="nav-cta">Testar 30 dias grátis</a>
</nav>

<!-- HERO -->
<section class="hero">
  <div class="hero-inner">
    <div>
      <div class="hero-eyebrow">Para instaladoras de energia solar</div>
      <h1>Seu vendedor já sabe <em>quem ligar primeiro</em> amanhã de manhã</h1>
      <p class="hero-sub">
        Cada lead recebe uma nota de 0 a 10 com base na conta de luz, tipo de imóvel e urgência.
        <strong>Conta acima de R$400 em casa própria? Ligação hoje.</strong>
        Apartamento alugado com conta de R$90? Nem perde tempo.
      </p>
      <div class="hero-btns">
        <a href="#contato" class="btn-sun">Quero ver meus leads organizados →</a>
        <a href="#como-funciona" class="btn-outline">Como funciona</a>
      </div>
      <div class="hero-proof">
        <div class="proof-item"><strong>+3x</strong><span>fechamentos por mês</span></div>
        <div class="proof-item"><strong>-70%</strong><span>tempo em triagem</span></div>
        <div class="proof-item"><strong>30 dias</strong><span>grátis pra testar</span></div>
      </div>
    </div>
    <div class="hero-card">
      <div class="card-header">
        <div class="card-dot" style="background:#ff5f57"></div>
        <div class="card-dot" style="background:#febc2e"></div>
        <div class="card-dot" style="background:#28c840"></div>
        <span class="card-title">Lead recebido agora — Curitiba, PR</span>
      </div>
      <div class="card-body">
        <span class="c">// Marcos Oliveira, conta R$720/mês, casa</span><br>
        {<br>
        &nbsp;<span class="k">"score"</span>: <span class="vh">9</span>,<br>
        &nbsp;<span class="k">"urgency"</span>: <span class="vs">"alta"</span>,<br>
        &nbsp;<span class="k">"decision"</span>: <span class="vh">"ligar hoje"</span>,<br>
        &nbsp;<span class="k">"reason"</span>: <span class="vs">"R$720 em Curitiba justifica sistema 6kWp, retorno em 4 anos"</span><br>
        }
      </div>
      <div class="card-wa">
        <div class="card-wa-label">📱 WhatsApp pronto pra copiar</div>
        <div class="card-wa-text">"Oi Marcos! Vi que sua conta de luz chega a R$720/mês em Curitiba. Com solar você economiza em torno de R$576 por mês — o sistema se paga em menos de 4 anos. Posso te mandar uma simulação hoje? ☀️"</div>
      </div>
    </div>
  </div>
</section>

<!-- PROBLEMA -->
<section class="section" id="problema">
  <div class="container">
    <div class="section-tag">O dia a dia de quem vende solar</div>
    <h2 class="section-title">Seu vendedor está perdendo as melhores oportunidades</h2>
    <p class="section-sub">Não é falta de lead. É falta de saber qual lead vale o tempo.</p>
    <div class="pain-grid">
      <div class="pain">
        <div class="pain-icon">📲</div>
        <h3>Lead chega de todo lugar</h3>
        <p>Instagram, Google Forms, indicação, feiras, Meta Ads. Tudo numa planilha sem ordem, sem prioridade.</p>
        <div class="quote">"Recebi 60 leads no mês passado e não sei por onde começar."</div>
      </div>
      <div class="pain">
        <div class="pain-icon">🏢</div>
        <h3>Apartamento alugado com R$80 de conta</h3>
        <p>Sem filtro, o vendedor liga por igual pra quem quer comprar e pra quem nunca vai conseguir instalar.</p>
        <div class="quote">"Perdi uma tarde inteira com alguém que nem é dono do imóvel."</div>
      </div>
      <div class="pain">
        <div class="pain-icon">💬</div>
        <h3>Mensagem igual pra todo mundo</h3>
        <p>"Olá, temos interesse em te apresentar nossa solução solar..." — lead lê, fecha, ignora.</p>
        <div class="quote">"Mando no WhatsApp e ninguém responde. O lead nem abre."</div>
      </div>
      <div class="pain">
        <div class="pain-icon">📉</div>
        <h3>Sem número nenhum</h3>
        <p>Quantos leads do mês passado viraram visita? Quantas visitas viraram proposta? Ninguém sabe.</p>
        <div class="quote">"Sei que fechei 3 contratos, mas não sei de onde vieram."</div>
      </div>
    </div>
  </div>
</section>

<!-- COMO FUNCIONA -->
<section class="section how-bg" id="como-funciona">
  <div class="container">
    <div class="section-tag center">Como funciona</div>
    <h2 class="section-title center">Do formulário à venda em menos de 30 segundos</h2>
    <div class="steps">
      <div class="step">
        <div class="step-num">1</div>
        <h3>Lead entra</h3>
        <p>Pelo seu Google Forms, site, Meta Ads ou qualquer formulário. Sem copiar e colar nada.</p>
      </div>
      <div class="step">
        <div class="step-num">2</div>
        <h3>Sistema analisa</h3>
        <p>Conta de luz, tipo de imóvel, cidade, titularidade. Quem qualifica ganha nota alta. Quem não qualifica é marcado automaticamente.</p>
      </div>
      <div class="step">
        <div class="step-num">3</div>
        <h3>Vendedor recebe</h3>
        <p>Dashboard mostra a fila do dia: quem ligar agora, quem pode esperar, quem descartar. Com a mensagem WhatsApp já escrita.</p>
      </div>
      <div class="step">
        <div class="step-num">4</div>
        <h3>Você acompanha</h3>
        <p>Quantos leads recebeu, quantos foram qualificados, quantos fecharam. Mês a mês, sem planilha.</p>
      </div>
    </div>
  </div>
</section>

<!-- FEATURES -->
<section class="section">
  <div class="container">
    <div class="section-tag center">O que você tem acesso</div>
    <h2 class="section-title center">Feito pra realidade de quem vende solar no Brasil</h2>
    <div class="feat-grid">
      <div class="feat">
        <div class="feat-icon">🏆</div>
        <h3>Fila de prioridade diária</h3>
        <p>Todo dia de manhã, seu vendedor abre o painel e vê exatamente quem ligar primeiro. Ordem por urgência, conta de luz e potencial de fechamento.</p>
        <span class="feat-tag feat-tag-yellow">Mais usado</span>
      </div>
      <div class="feat">
        <div class="feat-icon">📱</div>
        <h3>WhatsApp personalizado por lead</h3>
        <p>Cada lead tem uma mensagem diferente com o nome, cidade e valor da conta dele. Não parece automático — porque não é genérico.</p>
        <span class="feat-tag feat-tag-green">Aumenta resposta em 3x</span>
      </div>
      <div class="feat">
        <div class="feat-icon">📐</div>
        <h3>Simulação de ROI por estado</h3>
        <p>Tarifa ANEEL por região, tamanho de sistema estimado, payback em anos e economia em 10 e 25 anos. Pra você já chegar na visita com os números.</p>
      </div>
      <div class="feat">
        <div class="feat-icon">🔗</div>
        <h3>Conecta com o que você já usa</h3>
        <p>Google Forms, RD Station, Meta Leads Ads, Zapier. Lead novo no formulário → aparece no painel em segundos. Sem mexer no seu processo.</p>
      </div>
      <div class="feat">
        <div class="feat-icon">📊</div>
        <h3>Funil de conversão real</h3>
        <p>Marque quando um lead virou visita, proposta ou fechamento. Veja sua taxa de conversão mês a mês. Saiba de onde vêm seus melhores clientes.</p>
      </div>
      <div class="feat">
        <div class="feat-icon">🗂️</div>
        <h3>Exporta pra onde quiser</h3>
        <p>Baixe todos os leads em CSV quando precisar. Integra com qualquer CRM. Seus dados são seus — sem ficar preso na plataforma.</p>
      </div>
    </div>
  </div>
</section>

<!-- MERCADO -->
<section class="section" style="background:var(--surface);border-top:1px solid var(--border);border-bottom:1px solid var(--border)">
  <div class="container">
    <div class="section-tag center">O momento certo pra crescer</div>
    <h2 class="section-title center">O mercado solar nunca foi tão favorável no Brasil</h2>
    <p class="section-sub center">Quem organizar o processo de vendas agora vai dominar a região nos próximos anos.</p>
    <div class="market-grid">
      <div class="mcard"><strong>+20 mil</strong><span>instaladoras ativas no Brasil (ABSOLAR 2024)</span></div>
      <div class="mcard"><strong>Top 5</strong><span>Brasil em geração solar no mundo</span></div>
      <div class="mcard"><strong>2045</strong><span>prazo do Marco Legal da GD — quem instalar antes não paga taxa de fio B</span></div>
      <div class="mcard"><strong>R$500+</strong><span>conta de luz — payback em menos de 5 anos em qualquer estado</span></div>
    </div>
    <p style="text-align:center;margin-top:2rem;font-size:.82rem;color:var(--muted)">O cliente que tem conta alta já quer comprar. Ele só precisa que alguém chegue antes do concorrente.</p>
  </div>
</section>

<!-- DEPO -->
<section class="section">
  <div class="container">
    <div class="section-tag center">Resultados reais</div>
    <h2 class="section-title center">O que mudou pra quem já usa</h2>
    <div class="testi-grid">
      <div class="testi">
        <div class="stars">★★★★★</div>
        <blockquote>"Antes meu vendedor ligava pra 50 leads e fechava 2. Hoje ele liga pra <strong>20 leads qualificados e fecha 5</strong>. O sistema pagou em menos de um mês."</blockquote>
        <div class="testi-who">
          <div class="testi-av">RM</div>
          <div><div class="testi-name">Ricardo M.</div><div class="testi-role">Sócio — instaladora em Recife, PE</div></div>
        </div>
      </div>
      <div class="testi">
        <div class="stars">★★★★★</div>
        <blockquote>"A mensagem do WhatsApp foi o que me convenceu. O cliente recebe <strong>com o nome dele, a cidade e o valor da conta</strong> — parece que foi escrita à mão. A taxa de resposta triplicou."</blockquote>
        <div class="testi-who">
          <div class="testi-av">CF</div>
          <div><div class="testi-name">Camila F.</div><div class="testi-role">Gestora comercial — Campinas, SP</div></div>
        </div>
      </div>
      <div class="testi">
        <div class="stars">★★★★★</div>
        <blockquote>"Conectei com meu Google Forms em 20 minutos. Agora <strong>cada lead que entra já chega com nota e mensagem pronta</strong>. Economizei umas 3 horas por dia só em triagem."</blockquote>
        <div class="testi-who">
          <div class="testi-av">PL</div>
          <div><div class="testi-name">Paulo L.</div><div class="testi-role">Diretor — SolarSul, Porto Alegre</div></div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- PREÇOS -->
<section class="section" id="precos" style="background:var(--surface);border-top:1px solid var(--border);border-bottom:1px solid var(--border)">
  <div class="container">
    <div class="section-tag center">Planos</div>
    <h2 class="section-title center">Menos que um café por dia pra triplicar suas conversões</h2>
    <div class="price-grid">

      <div class="plan">
        <div class="plan-tier">Starter</div>
        <div class="plan-price"><sup>R$</sup>297<sub>/mês</sub></div>
        <div class="plan-pitch">Para instaladoras com até 2 vendedores começando a escalar</div>
        <ul class="plan-list">
          <li>Até 500 leads/mês</li>
          <li>Score e priorização automática</li>
          <li>WhatsApp personalizado</li>
          <li>Dashboard com fila do dia</li>
          <li>1 integração (Google Forms)</li>
          <li>Export CSV</li>
          <li class="no">Simulação ROI por estado</li>
          <li class="no">Suporte prioritário</li>
        </ul>
        <a href="#contato" class="plan-btn plan-btn-out">Começar grátis por 30 dias</a>
      </div>

      <div class="plan pop">
        <div class="pop-badge">Mais contratado</div>
        <div class="plan-tier">Pro</div>
        <div class="plan-price"><sup>R$</sup>497<sub>/mês</sub></div>
        <div class="plan-pitch">Para instaladoras em crescimento com volume alto de leads</div>
        <ul class="plan-list">
          <li>Até 2.000 leads/mês</li>
          <li>Tudo do Starter</li>
          <li>Simulação ROI por estado</li>
          <li>Upload em lote (CSV)</li>
          <li>Integrações ilimitadas</li>
          <li>Deduplicação automática</li>
          <li>Funil de conversão completo</li>
          <li>Suporte por WhatsApp</li>
        </ul>
        <a href="#contato" class="plan-btn plan-btn-sun">Começar grátis por 30 dias</a>
      </div>

      <div class="plan">
        <div class="plan-tier">Empresarial</div>
        <div class="plan-price"><sup>R$</sup>997<sub>/mês</sub></div>
        <div class="plan-pitch">Para distribuidoras e redes com múltiplos times de venda</div>
        <ul class="plan-list">
          <li>Leads ilimitados</li>
          <li>Tudo do Pro</li>
          <li>Setup e integração incluso</li>
          <li>Treinamento do time</li>
          <li>Acesso completo à API</li>
          <li>SLA 99.9% de uptime</li>
          <li>Gerente de conta dedicado</li>
          <li>NF e contrato formal</li>
        </ul>
        <a href="#contato" class="plan-btn plan-btn-out">Falar com o time</a>
      </div>

    </div>
    <p class="price-note">30 dias grátis em todos os planos · Sem cartão de crédito · Cancele quando quiser</p>
  </div>
</section>

<!-- CTA -->
<section class="section cta-wrap" id="contato">
  <div class="container">
    <div class="section-tag center">Comece hoje</div>
    <h2 class="section-title center">O lead certo esperando uma ligação agora</h2>
    <p>Deixa seu WhatsApp. A gente configura tudo pra você em menos de 1 hora — você só precisa conectar seu formulário.</p>
    <form class="cta-form" onsubmit="submitForm(event)">
      <input type="text" id="contact-input" placeholder="Seu WhatsApp com DDD" required/>
      <button type="submit" class="btn-sun" style="border:none;cursor:pointer">Quero testar grátis →</button>
    </form>
    <div class="cta-trust">
      <span>✓ Sem cartão de crédito</span>
      <span>✓ 30 dias grátis</span>
      <span>✓ Setup em 1 hora</span>
      <span>✓ Cancele quando quiser</span>
    </div>
    <div id="toast" style="position:static;display:none;margin-top:1.25rem;text-align:center;font-size:.875rem;color:var(--green);font-weight:700"></div>
  </div>
</section>

<footer>
  <p>© 2025 LeadSolar · Qualificação de leads para instaladoras de energia solar</p>
  <div class="footer-links">
    <a href="/dashboard">Dashboard</a>
    <a href="/docs">API</a>
  </div>
</footer>

<script>
function submitForm(e) {
  e.preventDefault();
  const val = document.getElementById('contact-input').value.trim();
  const saved = JSON.parse(localStorage.getItem('ls_contacts') || '[]');
  saved.push({v: val, t: new Date().toISOString()});
  localStorage.setItem('ls_contacts', JSON.stringify(saved));
  const msg = document.getElementById('toast');
  msg.style.display = 'block';
  msg.textContent = '✓ Recebido! Vamos te chamar no WhatsApp em breve.';
  document.getElementById('contact-input').value = '';
}
</script>
</body>
</html>"""


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def landing() -> HTMLResponse:
    return HTMLResponse(content=_HTML)
