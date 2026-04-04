"""Landing page — served at /."""

import os

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

_BASE_URL = os.getenv("BASE_URL", "https://lead-intelligence-production.up.railway.app")

_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>LeadSolar — Pare de ligar pra quem nunca vai fechar</title>
<meta name="description" content="Cada lead do seu formulário recebe um score de 0 a 10 e uma mensagem de WhatsApp pronta em segundos. Seu vendedor liga só pra quem tem potencial real."/>
<meta property="og:title" content="LeadSolar — Pare de ligar pra quem nunca vai fechar"/>
<meta property="og:description" content="Score automático 0–10 por conta de luz, imóvel e urgência. WhatsApp personalizado pronto. Fila de prioridade diária. 30 dias grátis."/>
<meta property="og:type" content="website"/>
<meta property="og:url" content="https://leadsolarintelligence.com.br/"/>
<meta property="og:image" content="https://leadsolarintelligence.com.br/static/og-image.png"/>
<meta name="twitter:card" content="summary_large_image"/>
<meta name="twitter:title" content="LeadSolar — Score automático de leads solares"/>
<meta name="twitter:description" content="Seu vendedor já sabe quem ligar primeiro amanhã de manhã. 30 dias grátis, sem cartão."/>
<link rel="icon" type="image/png" href="/static/favicon.png"/>
<link rel="apple-touch-icon" href="/static/logo.png"/>
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-MEHL0VK5XD"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments)}gtag('js',new Date());gtag('config','G-MEHL0VK5XD');</script>
<!-- Meta Pixel -->
<script>!function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');fbq('init','1230863952146253');fbq('track','PageView');</script>
<noscript><img height="1" width="1" style="display:none" src="https://www.facebook.com/tr?id=1230863952146253&ev=PageView&noscript=1"/></noscript>
<style>
:root{
  --bg:#060c18;--surface:#0d1825;--surface2:#132030;--border:#1a2e48;
  --sun:#f59e0b;--sun-dark:#d97706;--sun-light:#fbbf24;--sky:#0ea5e9;
  --text:#f1f5f9;--muted:#6b85a0;--green:#22c55e;--red:#ef4444;
  --glow:rgba(245,158,11,.18);
}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:var(--bg);color:var(--text);line-height:1.65}

nav{position:fixed;top:0;left:0;right:0;z-index:100;background:rgba(6,12,24,.92);backdrop-filter:blur(16px);border-bottom:1px solid var(--border);padding:.85rem 2rem;display:flex;justify-content:space-between;align-items:center}
.logo{font-size:1.2rem;font-weight:900;color:var(--sun);letter-spacing:-.02em}
.logo span{color:var(--text);font-weight:400}
.nav-links{display:flex;gap:1.75rem;align-items:center}
.nav-links a{color:var(--muted);text-decoration:none;font-size:.875rem;transition:color .2s}
.nav-links a:hover{color:var(--text)}
.nav-cta{background:var(--sun);color:#000;font-weight:700;padding:.5rem 1.25rem;border-radius:.5rem;text-decoration:none;font-size:.875rem;transition:all .2s;box-shadow:0 0 16px var(--glow)}
.nav-cta:hover{background:var(--sun-dark);box-shadow:0 0 24px var(--glow)}

/* HERO */
.hero{min-height:100vh;display:flex;align-items:center;padding:7rem 2rem 4rem;background:radial-gradient(ellipse 80% 55% at 65% -10%,rgba(245,158,11,.12),transparent),radial-gradient(ellipse 55% 45% at 5% 85%,rgba(14,165,233,.07),transparent),radial-gradient(ellipse 40% 35% at 95% 95%,rgba(245,158,11,.05),transparent)}
.hero-inner{max-width:1140px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:4.5rem;align-items:center}
.hero-eyebrow{display:inline-flex;align-items:center;gap:.5rem;font-size:.75rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:var(--sun);margin-bottom:1.5rem;background:rgba(245,158,11,.08);border:1px solid rgba(245,158,11,.2);padding:.3rem .85rem;border-radius:999px}
.hero h1{font-size:clamp(2.2rem,4.8vw,3.5rem);font-weight:900;line-height:1.05;letter-spacing:-.035em;margin-bottom:1.35rem}
.hero h1 em{color:var(--sun);font-style:normal;position:relative}
.hero-sub{font-size:1.05rem;color:var(--muted);margin-bottom:2.25rem;line-height:1.75}
.hero-sub strong{color:var(--text)}
.hero-btns{display:flex;gap:.85rem;flex-wrap:wrap;align-items:center}
.btn-sun{background:linear-gradient(135deg,var(--sun),var(--sun-dark));color:#000;font-weight:800;padding:.9rem 2rem;border-radius:.65rem;text-decoration:none;font-size:.95rem;transition:all .2s;white-space:nowrap;box-shadow:0 4px 20px rgba(245,158,11,.3)}
.btn-sun:hover{transform:translateY(-2px);box-shadow:0 8px 28px rgba(245,158,11,.4)}
.btn-outline{border:1px solid var(--border);color:var(--muted);padding:.85rem 1.75rem;border-radius:.6rem;text-decoration:none;font-size:.95rem;transition:all .2s;white-space:nowrap}
.btn-outline:hover{border-color:var(--sun);color:var(--sun)}
.hero-no-risk{font-size:.78rem;color:var(--muted);display:flex;align-items:center;gap:.35rem;margin-top:.75rem}
.hero-no-risk span{color:var(--green)}
.hero-proof{margin-top:2.5rem;padding-top:2rem;border-top:1px solid var(--border);display:flex;gap:2rem;flex-wrap:wrap}
.proof-item strong{display:block;font-size:1.6rem;font-weight:800;color:var(--sun);line-height:1}
.proof-item span{font-size:.78rem;color:var(--muted);margin-top:.2rem;display:block}

/* CARD LATERAL DO HERO */
.hero-card{background:var(--surface);border:1px solid var(--border);border-radius:1.25rem;overflow:hidden}
.card-header{background:var(--surface2);padding:.85rem 1.25rem;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:.65rem}
.card-status-dot{width:.55rem;height:.55rem;border-radius:50%;background:#22c55e;flex-shrink:0;box-shadow:0 0 6px #22c55e88;animation:pulse-dot 2s ease-in-out infinite}
@keyframes pulse-dot{0%,100%{opacity:1}50%{opacity:.5}}
.card-title{font-size:.78rem;color:var(--muted);flex:1}
.card-time{font-size:.7rem;color:var(--muted);opacity:.6}
.lead-info{display:flex;align-items:center;gap:.85rem;padding:1.1rem 1.25rem .9rem}
.lead-avatar{width:2.4rem;height:2.4rem;border-radius:50%;background:linear-gradient(135deg,#b45309,#92400e);color:#fff;font-weight:800;font-size:.85rem;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.lead-name{font-weight:700;font-size:.9rem;margin-bottom:.15rem}
.lead-meta{font-size:.75rem;color:var(--muted)}
.lead-score-section{padding:.1rem 1.25rem 1rem}
.score-row{display:flex;align-items:center;justify-content:space-between;margin-bottom:.5rem}
.score-label-sm{font-size:.7rem;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}
.score-badge-pill{font-size:.72rem;font-weight:800;background:rgba(34,197,94,.15);color:var(--green);border:1px solid rgba(34,197,94,.3);padding:.2rem .65rem;border-radius:999px}
.score-track{height:.45rem;background:rgba(255,255,255,.06);border-radius:999px;overflow:hidden;margin-bottom:.5rem}
.score-fill{height:100%;background:linear-gradient(90deg,var(--sun),var(--green));border-radius:999px;transition:width 1s ease}
.score-detail{font-size:.73rem;color:var(--muted);line-height:1.5}
.card-wa{margin:1.25rem 1.5rem 1.5rem;background:#0d2218;border:1px solid #16a34a33;border-radius:.75rem;padding:1rem}
.card-wa-label{font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--green);margin-bottom:.5rem}
.card-wa-text{font-size:.8rem;color:#bbf7d0;line-height:1.6}

/* SECTION BASE */
.section{padding:5rem 2rem}
.container{max-width:1140px;margin:0 auto}
.section-tag{display:inline-block;font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.12em;color:var(--sun);margin-bottom:1rem;background:rgba(245,158,11,.08);border:1px solid rgba(245,158,11,.18);padding:.28rem .85rem;border-radius:999px}
.section-title{font-size:clamp(1.85rem,3.8vw,2.6rem);font-weight:900;letter-spacing:-.03em;line-height:1.1;margin-bottom:.85rem}
.section-sub{color:var(--muted);font-size:1rem;max-width:560px;line-height:1.75}
.center{text-align:center}.center .section-sub{margin:0 auto}

/* HERO GRID TEXTURE */
.hero{position:relative;overflow:hidden}
.hero::before{content:'';position:absolute;inset:0;background-image:radial-gradient(circle at 1px 1px,rgba(245,158,11,.05) 1px,transparent 0);background-size:36px 36px;pointer-events:none;z-index:0}
.hero-inner{position:relative;z-index:1}

/* STEP NUMBERS — upgraded */
.step-num{width:3rem;height:3rem;border-radius:50%;background:linear-gradient(135deg,rgba(245,158,11,.15),rgba(245,158,11,.05));border:2px solid rgba(245,158,11,.4);color:var(--sun);font-weight:900;display:flex;align-items:center;justify-content:center;margin:0 auto 1.1rem;font-size:1.1rem;box-shadow:0 0 16px rgba(245,158,11,.12)}

/* PROOF ITEMS — number counter */
.proof-item strong{display:block;font-size:2rem;font-weight:900;color:var(--sun);line-height:1;background:linear-gradient(135deg,var(--sun-light),var(--sun));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.proof-item span{font-size:.78rem;color:var(--muted);margin-top:.25rem;display:block}

/* FEATURE CARD — upgraded */
.feat{background:var(--surface);border:1px solid var(--border);border-radius:1.1rem;padding:1.75rem;transition:border-color .25s,transform .25s,box-shadow .25s}
.feat:hover{border-color:rgba(245,158,11,.35);transform:translateY(-3px);box-shadow:0 12px 32px rgba(0,0,0,.25)}
.feat-icon{font-size:1.8rem;margin-bottom:1rem;display:block}

/* PAIN CARD — upgraded */
.pain{background:var(--surface);border:1px solid var(--border);border-radius:1.1rem;padding:1.6rem;transition:border-color .2s}
.pain:hover{border-color:rgba(239,68,68,.25)}

/* GUARANTEE — fix layout */
.guarantee-wrap{background:linear-gradient(135deg,rgba(34,197,94,.07),rgba(14,165,233,.03));border:1px solid rgba(34,197,94,.25);border-radius:1.5rem;padding:2.5rem 2.5rem;margin-top:2.5rem;display:flex;gap:2rem;align-items:flex-start}
.guarantee-icon{font-size:2.5rem;flex-shrink:0;width:3.5rem;height:3.5rem;background:rgba(34,197,94,.1);border:1px solid rgba(34,197,94,.2);border-radius:50%;display:flex;align-items:center;justify-content:center;line-height:1}
.guarantee-title{font-size:1.15rem;font-weight:800;color:var(--green);margin-bottom:.5rem}
.guarantee-text{color:var(--muted);font-size:.88rem;line-height:1.75}
@media(max-width:768px){.guarantee-wrap{flex-direction:column;align-items:center;text-align:center;padding:1.75rem}}

/* CTA BUTTON — pulse glow */
@keyframes glow{0%,100%{box-shadow:0 4px 20px rgba(245,158,11,.3)}50%{box-shadow:0 4px 32px rgba(245,158,11,.6)}}
.btn-sun-pulse{animation:glow 2.5s ease-in-out infinite}

/* SECTION ACCENT LINE */
.section-accent{width:3rem;height:.2rem;background:linear-gradient(90deg,var(--sun),transparent);border-radius:999px;margin:.75rem auto 0}
.center .section-accent{margin-left:auto;margin-right:auto}

/* ROI WIZARD */
#roi-wizard.open{display:flex!important}
.wz-chip{background:#132030;border:1px solid #1a2e48;color:#e2e8f0;text-align:left;padding:.85rem 1.1rem;border-radius:.75rem;font-size:.9rem;cursor:pointer;font-family:inherit;transition:all .15s;width:100%}
.wz-chip:hover{border-color:#f59e0b;color:#f59e0b;background:rgba(245,158,11,.06)}

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
.testi-av{width:3rem;height:3rem;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:1rem;flex-shrink:0;color:#fff;border:2px solid rgba(255,255,255,.15)}
.testi-name{font-weight:700;font-size:.85rem}
.testi-role{font-size:.72rem;color:var(--muted)}
.testi-result{display:inline-block;margin-top:.75rem;background:rgba(34,197,94,.1);border:1px solid rgba(34,197,94,.2);color:var(--green);font-size:.72rem;font-weight:700;padding:.25rem .65rem;border-radius:999px}

/* DEMO AO VIVO */
.demo-wrap{display:grid;grid-template-columns:1fr 1fr;gap:2.5rem;margin-top:3rem;align-items:start}
.demo-form-box{background:var(--surface);border:1px solid var(--border);border-radius:1.25rem;padding:2rem}
.demo-form-box h3{font-size:1.05rem;font-weight:700;margin-bottom:1.5rem}
.demo-field{display:flex;flex-direction:column;gap:.35rem;margin-bottom:1rem}
.demo-field label{font-size:.75rem;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}
.demo-field input,.demo-field select{background:var(--surface2);border:1px solid var(--border);color:var(--text);padding:.65rem .9rem;border-radius:.55rem;font-size:.9rem;outline:none;font-family:inherit;transition:border-color .2s}
.demo-field input:focus,.demo-field select:focus{border-color:var(--sun)}
.demo-field select option{background:var(--surface2)}
.demo-row{display:grid;grid-template-columns:1fr 1fr;gap:.75rem}
.demo-submit{width:100%;background:var(--sun);color:#000;font-weight:700;padding:.9rem;border-radius:.6rem;border:none;font-size:.95rem;cursor:pointer;margin-top:.5rem;transition:all .15s;font-family:inherit}
.demo-submit:hover{background:var(--sun-dark)}
.demo-submit:disabled{opacity:.6;cursor:not-allowed}
.demo-result-box{background:var(--surface);border:1px solid var(--border);border-radius:1.25rem;padding:2rem;min-height:300px;display:flex;flex-direction:column;justify-content:center}
.demo-placeholder{text-align:center;color:var(--muted)}
.demo-placeholder .arrow{font-size:2rem;margin-bottom:.75rem;opacity:.4}
.demo-placeholder p{font-size:.875rem;line-height:1.6}
.demo-result{display:none;flex-direction:column;gap:1.25rem}
.demo-score-row{display:flex;align-items:center;gap:1.25rem}
.demo-score-circle{width:5rem;height:5rem;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:2rem;font-weight:800;flex-shrink:0;border:3px solid}
.demo-score-high{background:rgba(34,197,94,.12);border-color:var(--green);color:var(--green)}
.demo-score-mid{background:rgba(245,158,11,.12);border-color:var(--sun);color:var(--sun)}
.demo-score-low{background:rgba(239,68,68,.1);border-color:var(--red);color:var(--red)}
.demo-score-label{font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin-bottom:.35rem}
.demo-score-dec{font-size:1rem;font-weight:700}
.demo-score-urg{font-size:.8rem;color:var(--muted);margin-top:.15rem}
.demo-rec{background:var(--surface2);border:1px solid var(--border);border-radius:.75rem;padding:1rem}
.demo-rec-label{font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--sky);margin-bottom:.5rem}
.demo-rec-text{font-size:.82rem;color:var(--text);line-height:1.65}
.demo-wa{background:#0d2218;border:1px solid #16a34a33;border-radius:.75rem;padding:1rem}
.demo-wa-label{font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--green);margin-bottom:.5rem;display:flex;justify-content:space-between;align-items:center}
.demo-wa-copy{background:none;border:1px solid rgba(34,197,94,.3);color:var(--green);padding:.15rem .55rem;border-radius:.35rem;font-size:.65rem;cursor:pointer;font-family:inherit}
.demo-wa-copy:hover{background:rgba(34,197,94,.1)}
.demo-wa-text{font-size:.8rem;color:#bbf7d0;line-height:1.65}
.demo-error{color:var(--red);font-size:.82rem;text-align:center;padding:.75rem;background:rgba(239,68,68,.08);border-radius:.5rem;border:1px solid rgba(239,68,68,.2)}
@media(max-width:768px){.demo-wrap{grid-template-columns:1fr}.demo-row{grid-template-columns:1fr}}

/* FAQ */
.faq-list{margin-top:2.5rem;display:flex;flex-direction:column;gap:.75rem;max-width:720px;margin-left:auto;margin-right:auto}
.faq-item{background:var(--surface);border:1px solid var(--border);border-radius:.85rem;overflow:hidden}
.faq-q{width:100%;background:none;border:none;color:var(--text);text-align:left;padding:1.1rem 1.4rem;font-size:.92rem;font-weight:600;cursor:pointer;display:flex;justify-content:space-between;align-items:center;gap:1rem;font-family:inherit}
.faq-q:hover{color:var(--sun)}
.faq-icon{color:var(--sun);font-size:1.1rem;flex-shrink:0;transition:transform .2s}
.faq-a{font-size:.85rem;color:var(--muted);line-height:1.7;padding:0 1.4rem 1.1rem;display:none}
.faq-item.open .faq-a{display:block}
.faq-item.open .faq-icon{transform:rotate(45deg)}

/* BILLING TOGGLE */
.billing-toggle{display:flex;align-items:center;justify-content:center;gap:1rem;margin-bottom:2.5rem}
.toggle-label{font-size:.9rem;font-weight:600;color:var(--muted);transition:color .2s}
.toggle-label.active{color:var(--text)}
.toggle-wrap{position:relative;width:3rem;height:1.6rem;cursor:pointer}
.toggle-wrap input{opacity:0;width:0;height:0;position:absolute}
.toggle-slider{position:absolute;inset:0;background:var(--border);border-radius:999px;transition:.3s}
.toggle-slider:before{content:"";position:absolute;width:1.2rem;height:1.2rem;left:.2rem;bottom:.2rem;background:#fff;border-radius:50%;transition:.3s}
.toggle-wrap input:checked+.toggle-slider{background:var(--sun)}
.toggle-wrap input:checked+.toggle-slider:before{transform:translateX(1.4rem)}
.save-badge{background:rgba(34,197,94,.12);border:1px solid rgba(34,197,94,.25);color:var(--green);font-size:.7rem;font-weight:700;padding:.2rem .65rem;border-radius:999px;white-space:nowrap}

/* PRICING */
.price-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1.5rem;margin-top:1.5rem;align-items:start}
.plan{background:var(--surface);border:1px solid var(--border);border-radius:1.5rem;padding:2rem;position:relative;transition:border-color .25s,box-shadow .25s}
.plan:hover{border-color:rgba(245,158,11,.25);box-shadow:0 8px 32px rgba(0,0,0,.3)}
.plan.pop{border-color:rgba(245,158,11,.45);background:linear-gradient(160deg,rgba(245,158,11,.07),var(--surface));box-shadow:0 0 32px rgba(245,158,11,.08)}
.plan.pop:hover{border-color:rgba(245,158,11,.7);box-shadow:0 0 40px rgba(245,158,11,.15)}
.pop-badge{position:absolute;top:-1px;left:50%;transform:translateX(-50%);background:linear-gradient(90deg,var(--sun),var(--sun-dark));color:#000;font-size:.65rem;font-weight:800;padding:.28rem 1rem;border-radius:0 0 .6rem .6rem;text-transform:uppercase;letter-spacing:.08em;white-space:nowrap}
.plan-tier{font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin-bottom:.5rem}
.plan-price{font-size:2.9rem;font-weight:900;letter-spacing:-.04em;line-height:1;transition:all .25s}
.plan-price sup{font-size:.95rem;font-weight:500;color:var(--muted);vertical-align:top;margin-top:.45rem}
.plan-price sub{font-size:.85rem;font-weight:400;color:var(--muted)}
.plan-annual-note{font-size:.72rem;color:var(--green);font-weight:600;margin-top:.3rem;display:none}
.plan-pitch{font-size:.82rem;color:var(--muted);margin:.65rem 0 1.5rem;line-height:1.55}
.plan-list{list-style:none;display:flex;flex-direction:column;gap:.6rem;margin-bottom:2rem}
.plan-list li{font-size:.83rem;display:flex;gap:.5rem;line-height:1.45}
.plan-list li::before{content:"✓";color:var(--green);font-weight:700;flex-shrink:0;margin-top:.05rem}
.plan-list li.no::before{content:"—";color:var(--muted)}
.plan-list li.no{color:var(--muted)}
.plan-btn{display:block;text-align:center;padding:.85rem;border-radius:.65rem;font-weight:700;text-decoration:none;font-size:.9rem;transition:all .2s;cursor:pointer;border:none;font-family:inherit;width:100%}
.plan-btn-sun{background:linear-gradient(135deg,var(--sun),var(--sun-dark));color:#000;box-shadow:0 4px 16px rgba(245,158,11,.25)}
.plan-btn-sun:hover{transform:translateY(-1px);box-shadow:0 6px 24px rgba(245,158,11,.4)}
.plan-btn-out{border:1px solid var(--border);color:var(--text);background:transparent}
.plan-btn-out:hover{border-color:var(--sun);color:var(--sun)}
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

/* ANNOUNCEMENT BAR */
.ann-bar{background:linear-gradient(90deg,#92400e,#b45309,#d97706);color:#fff;text-align:center;padding:.55rem 1rem;font-size:.82rem;font-weight:600;position:relative;z-index:101}
.ann-bar span{color:#fde68a}
.ann-bar a{color:#fde68a;text-decoration:underline;margin-left:.5rem}

/* INTEGRATION LOGOS */
.logos-section{padding:2.5rem 2rem;border-bottom:1px solid var(--border)}
.logos-inner{max-width:1100px;margin:0 auto;text-align:center}
.logos-label{font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin-bottom:1.5rem}
.logos-row{display:flex;gap:2rem;justify-content:center;flex-wrap:wrap;align-items:center}
.logo-chip{background:var(--surface);border:1px solid var(--border);border-radius:.6rem;padding:.55rem 1.1rem;font-size:.82rem;font-weight:600;color:var(--muted);display:flex;align-items:center;gap:.5rem;transition:border-color .2s}
.logo-chip:hover{border-color:rgba(245,158,11,.4);color:var(--text)}

/* BEFORE / AFTER */
.ba-table{margin-top:2.5rem;display:grid;grid-template-columns:1fr 1fr;border-radius:1rem;overflow:hidden;border:1px solid var(--border)}
.ba-col{display:flex;flex-direction:column}
.ba-header{padding:1rem 1.5rem;font-weight:700;font-size:.88rem;text-align:center}
.ba-header.bad{background:rgba(239,68,68,.12);color:#fca5a5;border-bottom:1px solid rgba(239,68,68,.15)}
.ba-header.good{background:rgba(34,197,94,.1);color:var(--green);border-bottom:1px solid rgba(34,197,94,.15)}
.ba-row{display:flex;align-items:center;gap:.65rem;padding:.9rem 1.5rem;font-size:.84rem;border-top:1px solid var(--border)}
.ba-col.bad-col .ba-row{color:#fca5a5}
.ba-col.bad-col .ba-row::before{content:"✗";color:var(--red);font-weight:700;flex-shrink:0}
.ba-col.good-col .ba-row{color:#bbf7d0}
.ba-col.good-col .ba-row::before{content:"✓";color:var(--green);font-weight:700;flex-shrink:0}

/* COUNTER */
.counter-live{display:inline-flex;align-items:center;gap:.5rem;background:rgba(34,197,94,.08);border:1px solid rgba(34,197,94,.2);border-radius:999px;padding:.3rem .9rem;font-size:.75rem;color:var(--green);font-weight:700;margin-top:1.25rem}
.counter-dot{width:.5rem;height:.5rem;border-radius:50%;background:var(--green);animation:pulse 1.5s infinite}
@keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.5;transform:scale(1.3)}}

/* SCROLL ANIMATIONS — only animate if JS enabled */
body.js-ready .anim{opacity:0;transform:translateY(24px);transition:opacity .5s ease,transform .5s ease}
body.js-ready .anim.visible{opacity:1;transform:none}
body.js-ready .anim-left{opacity:0;transform:translateX(-24px);transition:opacity .5s ease,transform .5s ease}
body.js-ready .anim-left.visible{opacity:1;transform:none}
/* delay helpers */
.d1{transition-delay:.08s}.d2{transition-delay:.16s}.d3{transition-delay:.24s}.d4{transition-delay:.32s}

/* STICKY MOBILE CTA */
.sticky-cta{display:none;position:fixed;bottom:0;left:0;right:0;z-index:400;background:var(--bg);border-top:1px solid var(--border);padding:.75rem 1.25rem;gap:.75rem;align-items:center;justify-content:space-between}
.sticky-cta p{font-size:.78rem;color:var(--muted);line-height:1.3}
.sticky-cta p strong{color:var(--text);display:block}
.sticky-cta a{background:var(--sun);color:#000;font-weight:700;padding:.65rem 1.1rem;border-radius:.5rem;text-decoration:none;font-size:.82rem;white-space:nowrap;flex-shrink:0}
@media(max-width:768px){.sticky-cta{display:flex}body{padding-bottom:70px}}

/* TRUST BADGES */
.trust-row{display:flex;gap:1rem;flex-wrap:wrap;justify-content:center;margin-top:1.5rem}
.trust-badge{display:flex;align-items:center;gap:.4rem;background:var(--surface);border:1px solid var(--border);border-radius:.5rem;padding:.4rem .85rem;font-size:.72rem;color:var(--muted)}
.trust-badge svg{width:.9rem;height:.9rem;color:var(--green);flex-shrink:0}

/* FLOATING WA */
.wa-float{position:fixed;bottom:1.75rem;right:1.75rem;z-index:500;display:flex;align-items:center;gap:.65rem;background:#25d366;color:#fff;font-weight:700;font-size:.85rem;padding:.75rem 1.25rem;border-radius:3rem;box-shadow:0 4px 20px rgba(37,211,102,.35);text-decoration:none;transition:transform .2s,box-shadow .2s}
.wa-float:hover{transform:translateY(-2px);box-shadow:0 6px 28px rgba(37,211,102,.45)}
.wa-float svg{width:1.25rem;height:1.25rem;flex-shrink:0}

/* HAMBURGER */
.nav-ham{display:none;background:none;border:none;cursor:pointer;padding:.25rem;color:var(--text);font-size:1.4rem}
.mobile-menu{display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:var(--bg);z-index:200;flex-direction:column;align-items:center;justify-content:center;gap:2rem}
.mobile-menu.open{display:flex}
.mobile-menu a{color:var(--text);text-decoration:none;font-size:1.25rem;font-weight:600}
.mobile-menu-close{position:absolute;top:1.5rem;right:1.5rem;background:none;border:none;cursor:pointer;color:var(--muted);font-size:1.5rem}

@media(max-width:768px){
  .hero-inner{grid-template-columns:1fr}
  .hero-card{display:none}
  nav .nav-links{display:none}
  .nav-ham{display:block}
  .hero{padding:6rem 1.25rem 3rem}
  .section{padding:3.5rem 1.25rem}
  .ba-table{grid-template-columns:1fr}
  .ba-col.bad-col{border-bottom:1px solid var(--border)}
  .wa-float span{display:none}
  /* ── Botões mobile ── */
  .hero-btns{flex-direction:column;align-items:stretch;gap:.7rem}
  .hero-btns .btn-sun,.hero-btns .btn-outline,.hero-btns button{
    width:100%!important;box-sizing:border-box!important;text-align:center!important;
    white-space:normal!important;padding:.9rem 1rem!important}
  /* ── CTA form mobile ── */
  .cta-form{flex-direction:column;align-items:stretch}
  .cta-form input{min-width:unset;width:100%}
  .cta-form .btn-sun,.cta-form button{width:100%;box-sizing:border-box}
  /* ── Announcement bar ── */
  .ann-bar{font-size:.72rem;padding:.4rem .75rem;line-height:1.5}
  .ann-bar span{display:block}
  /* ── Proof items ── */
  .hero-proof{gap:1rem}
  /* ── Price grid força coluna única em telas muito pequenas ── */
  .price-grid{grid-template-columns:1fr}
  /* ── Steps ── */
  .steps{grid-template-columns:1fr}
}
</style>
</head>
<body>

<!-- ANNOUNCEMENT BAR -->
<div class="ann-bar">
  🎉 <span>Lançamento — 40% OFF com código LANCAMENTO40</span> · Primeiras 50 vagas
</div>

<!-- MOBILE MENU -->
<div class="mobile-menu" id="mobile-menu">
  <button class="mobile-menu-close" onclick="closeMobileMenu()">✕</button>
  <a href="#problema" onclick="closeMobileMenu()">O problema</a>
  <a href="#como-funciona" onclick="closeMobileMenu()">Como funciona</a>
  <a href="#precos" onclick="closeMobileMenu()">Preços</a>
  <button onclick="closeMobileMenu();startCheckout('pro')" style="color:var(--sun);background:none;border:none;cursor:pointer;font-family:inherit;font-size:1rem;text-align:left;padding:0">Testar grátis →</button>
</div>

<nav>
  <a href="/" class="logo" style="display:flex;align-items:center;gap:.5rem;text-decoration:none"><svg width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg" style="flex-shrink:0"><circle cx="14" cy="14" r="14" fill="#1a2e48"/><circle cx="14" cy="14" r="7" fill="#f59e0b"/><line x1="14" y1="2" x2="14" y2="5" stroke="#f59e0b" stroke-width="2" stroke-linecap="round"/><line x1="14" y1="23" x2="14" y2="26" stroke="#f59e0b" stroke-width="2" stroke-linecap="round"/><line x1="2" y1="14" x2="5" y2="14" stroke="#f59e0b" stroke-width="2" stroke-linecap="round"/><line x1="23" y1="14" x2="26" y2="14" stroke="#f59e0b" stroke-width="2" stroke-linecap="round"/><line x1="5.5" y1="5.5" x2="7.5" y2="7.5" stroke="#f59e0b" stroke-width="2" stroke-linecap="round"/><line x1="20.5" y1="20.5" x2="22.5" y2="22.5" stroke="#f59e0b" stroke-width="2" stroke-linecap="round"/><line x1="22.5" y1="5.5" x2="20.5" y2="7.5" stroke="#f59e0b" stroke-width="2" stroke-linecap="round"/><line x1="7.5" y1="20.5" x2="5.5" y2="22.5" stroke="#f59e0b" stroke-width="2" stroke-linecap="round"/></svg>Lead<span>Solar</span></a>
  <div class="nav-links">
    <a href="#problema">O problema</a>
    <a href="#como-funciona">Como funciona</a>
    <a href="#precos">Preços</a>
  </div>
  <div style="display:flex;align-items:center;gap:.75rem">
    <button onclick="startCheckout('pro')" class="nav-cta" style="border:none;cursor:pointer;font-family:inherit">Testar grátis →</button>
    <button class="nav-ham" onclick="document.getElementById('mobile-menu').classList.add('open')" aria-label="Menu">☰</button>
  </div>
</nav>

<!-- HERO -->
<section class="hero">
  <div class="hero-inner">
    <div>
      <div class="hero-eyebrow">⚡ Inteligência de leads para energia solar</div>
      <h1>Pare de ligar pra quem <em>nunca vai fechar</em></h1>
      <p class="hero-sub">Cada lead do seu formulário recebe um score de 0 a 10 e uma mensagem de WhatsApp pronta em segundos.</p>
      <div class="hero-btns">
        <button onclick="startCheckout('pro')" class="btn-sun" style="border:none;cursor:pointer;font-family:inherit">Começar grátis por 30 dias →</button>
        <button onclick="openWizard()" class="btn-outline" style="background:none;border:1px solid var(--border);cursor:pointer;font-family:inherit;color:var(--muted);padding:.85rem 1.75rem;border-radius:.6rem;font-size:.95rem">Calcular meu ROI →</button>
      </div>
      <div class="hero-no-risk"><span>✓</span> Sem cartão de crédito &nbsp;·&nbsp; <span>✓</span> Cancele quando quiser &nbsp;·&nbsp; <span>✓</span> Setup em 1 hora</div>
      <div class="hero-proof anim">
        <div class="proof-item"><strong>+3x</strong><span>fechamentos com mesma equipe</span></div>
        <div class="proof-item"><strong>30s</strong><span>do formulário ao score</span></div>
        <div class="proof-item"><strong>30 dias</strong><span>grátis pra testar</span></div>
      </div>
    </div>
    <div class="hero-card">
      <div class="card-header">
        <span class="card-status-dot"></span>
        <span class="card-title">Lead recebido agora · Curitiba, PR</span>
        <span class="card-time">há 12s</span>
      </div>
      <div class="lead-info">
        <div class="lead-avatar">MO</div>
        <div>
          <div class="lead-name">Marcos Oliveira</div>
          <div class="lead-meta">Casa própria · R$720/mês · Curitiba, PR</div>
        </div>
      </div>
      <div class="lead-score-section">
        <div class="score-row">
          <span class="score-label-sm">Potencial de fechamento</span>
          <span class="score-badge-pill">9/10 — Ligar hoje ↑</span>
        </div>
        <div class="score-track"><div class="score-fill" style="width:90%"></div></div>
        <div class="score-detail">R$720/mês em Curitiba → sistema 6kWp, payback em 4 anos</div>
      </div>
      <div class="card-wa">
        <div class="card-wa-label">📱 Mensagem pronta para enviar</div>
        <div class="card-wa-text">"Oi Marcos! Vi que sua conta de luz chega a R$720/mês em Curitiba. Com solar você economiza em torno de R$576 por mês — o sistema se paga em menos de 4 anos. Posso te mandar uma simulação hoje? ☀️"</div>
      </div>
    </div>
  </div>
</section>

<!-- DOR -->
<section class="section" id="problema">
  <div class="container">
    <div class="section-tag center">O problema</div>
    <h2 class="section-title center">Você já tem leads. O problema é saber quem ligar primeiro.</h2>
    <div class="pain-grid" style="grid-template-columns:repeat(auto-fit,minmax(260px,1fr));margin-top:3rem">
      <div class="pain">
        <div class="pain-icon">⏱️</div>
        <h3>Lead esquentou e esfriou</h3>
        <p>Você ligou 2 dias depois. O concorrente ligou em 20 minutos.</p>
      </div>
      <div class="pain">
        <div class="pain-icon">🎯</div>
        <h3>Vendedor atira pra todo lado</h3>
        <p>50 ligações por semana, 2 fechamentos. Por falta de filtro, não de esforço.</p>
      </div>
      <div class="pain">
        <div class="pain-icon">💬</div>
        <h3>Mensagem igual pra todo mundo</h3>
        <p>Apartamento alugado com R$80 de conta recebe a mesma abordagem que casa própria R$700.</p>
      </div>
    </div>
  </div>
</section>

<!-- COMO FUNCIONA -->
<section class="section how-bg" id="como-funciona">
  <div class="container">
    <div class="section-tag center">Como funciona</div>
    <h2 class="section-title center">De formulário a lead qualificado em 30 segundos</h2>
    <div class="steps">
      <div class="step">
        <div class="step-num">1</div>
        <h3>Conecta</h3>
        <p>Google Forms, RD Station ou qualquer formulário. Sem mexer no seu processo atual.</p>
      </div>
      <div class="step">
        <div class="step-num">2</div>
        <h3>Qualifica</h3>
        <p>IA analisa conta de luz, imóvel, cidade e urgência. Score 0 a 10 na hora.</p>
      </div>
      <div class="step">
        <div class="step-num">3</div>
        <h3>Vende</h3>
        <p>Seu vendedor recebe a fila do dia: quem ligar primeiro e o WhatsApp pronto pra mandar.</p>
      </div>
    </div>
  </div>
</section>

<!-- DEMO AO VIVO -->
<section class="section" id="demo" style="background:var(--surface);border-top:1px solid var(--border);border-bottom:1px solid var(--border)">
  <div class="container">
    <div class="section-tag center">Demo ao vivo</div>
    <h2 class="section-title center">Teste agora com um lead real</h2>
    <p class="section-sub center">Preencha os dados de qualquer lead e veja o score, a decisão e a mensagem WhatsApp pronta — em segundos.</p>
    <div class="demo-wrap">
      <div class="demo-form-box">
        <h3>Dados do lead</h3>
        <form id="demo-form" onsubmit="runDemo(event)">
          <div class="demo-field">
            <label>Nome</label>
            <input id="d-name" placeholder="Ex: João Silva" required maxlength="80"/>
          </div>
          <div class="demo-row">
            <div class="demo-field">
              <label>Cidade</label>
              <input id="d-city" placeholder="Ex: Curitiba" required maxlength="80"/>
            </div>
            <div class="demo-field">
              <label>Conta de luz (R$)</label>
              <input id="d-bill" type="number" placeholder="450" min="50" max="5000" required/>
            </div>
          </div>
          <div class="demo-row">
            <div class="demo-field">
              <label>Tipo de imóvel</label>
              <select id="d-type" required>
                <option value="">Selecione...</option>
                <option value="casa">Casa própria</option>
                <option value="apartamento">Apartamento</option>
                <option value="comercial">Comercial</option>
              </select>
            </div>
            <div class="demo-field">
              <label>Objetivo</label>
              <select id="d-goal">
                <option value="reduzir conta de luz">Reduzir conta de luz</option>
                <option value="instalar energia solar">Instalar energia solar</option>
                <option value="só pesquisando">Só pesquisando</option>
                <option value="investimento">Investimento</option>
              </select>
            </div>
          </div>
          <button type="submit" class="demo-submit" id="demo-btn">Ver resultado e mensagem →</button>
        </form>
      </div>
      <div class="demo-result-box" id="demo-result-box">
        <div class="demo-placeholder" id="demo-placeholder">
          <div class="arrow">←</div>
          <p>Preencha os dados e clique em <strong>"Ver score e mensagem"</strong> para ver o resultado.</p>
        </div>
        <div class="demo-result" id="demo-result">
          <div class="demo-score-row">
            <div class="demo-score-circle" id="demo-score-circle">—</div>
            <div>
              <div class="demo-score-label">Pontuação do lead</div>
              <div class="demo-score-dec" id="demo-decision">—</div>
              <div class="demo-score-urg" id="demo-urgency">—</div>
            </div>
          </div>
          <div class="demo-rec">
            <div class="demo-rec-label">Recomendação para o vendedor</div>
            <div class="demo-rec-text" id="demo-rec-text">—</div>
          </div>
          <div class="demo-wa">
            <div class="demo-wa-label">
              Mensagem WhatsApp pronta
              <button class="demo-wa-copy" onclick="copyDemoWA()">Copiar</button>
            </div>
            <div class="demo-wa-text" id="demo-wa-text">—</div>
          </div>
        </div>
        <div class="demo-error" id="demo-error" style="display:none"></div>
      </div>
    </div>
  </div>
</section>

<!-- DEPOIMENTOS -->
<section class="section">
  <div class="container">
    <div class="section-tag center">Resultados reais</div>
    <h2 class="section-title center">O que mudou pra quem já usa</h2>
    <div class="testi-grid" style="grid-template-columns:repeat(auto-fit,minmax(300px,1fr));max-width:780px;margin:3rem auto 0">
      <div class="testi">
        <div class="stars">★★★★★</div>
        <blockquote>"Antes eu ligava pra todo lead. Hoje meu vendedor liga só pros quentes. Em 3 meses triplicamos os fechamentos sem contratar ninguém."</blockquote>
        <div class="testi-who">
          <div class="testi-av" style="background:linear-gradient(135deg,#b45309,#92400e)">PA</div>
          <div>
            <div class="testi-name">Pedro Alves</div>
            <div class="testi-role">Instaladora solar — Curitiba, PR</div>
            <span class="testi-result">↑ 3x fechamentos</span>
          </div>
        </div>
      </div>
      <div class="testi">
        <div class="stars">★★★★★</div>
        <blockquote>"Setup foi 1 hora. No mesmo dia já tinha a fila organizada. Parece que finalmente tenho um sistema."</blockquote>
        <div class="testi-who">
          <div class="testi-av" style="background:linear-gradient(135deg,#0369a1,#075985)">AF</div>
          <div>
            <div class="testi-name">Ana Ferreira</div>
            <div class="testi-role">Gestora comercial — São Paulo, SP</div>
            <span class="testi-result">Setup em 1 hora</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- FAQ -->
<section class="section" style="background:var(--surface);border-top:1px solid var(--border);border-bottom:1px solid var(--border)">
  <div class="container">
    <div class="section-tag center">Dúvidas frequentes</div>
    <h2 class="section-title center">Antes de falar com a gente</h2>
    <div class="faq-list">
      <div class="faq-item">
        <button class="faq-q" onclick="toggleFaq(this)">
          Funciona com o Google Forms que eu já uso?
          <span class="faq-icon">+</span>
        </button>
        <div class="faq-a">Sim. Você conecta seu formulário existente via Zapier ou Make em menos de 20 minutos — sem mudar nada no seu processo atual. Todo lead novo que chegar já aparece qualificado no painel.</div>
      </div>
      <div class="faq-item">
        <button class="faq-q" onclick="toggleFaq(this)">
          Preciso de equipe técnica pra configurar?
          <span class="faq-icon">+</span>
        </button>
        <div class="faq-a">Não. A gente configura tudo pra você em até 1 hora por chamada. Você não precisa saber programar nada — só nos dar acesso ao seu formulário e definir qual número de WhatsApp recebe as notificações.</div>
      </div>
      <div class="faq-item">
        <button class="faq-q" onclick="toggleFaq(this)">
          Quanto tempo até ver resultado?
          <span class="faq-icon">+</span>
        </button>
        <div class="faq-a">Na maioria dos casos, o primeiro lead qualificado aparece no mesmo dia do setup. Resultados concretos em fechamentos costumam aparecer na primeira semana — quando o vendedor para de ligar pra leads frios.</div>
      </div>
      <div class="faq-item">
        <button class="faq-q" onclick="toggleFaq(this)">
          Posso cancelar quando quiser?
          <span class="faq-icon">+</span>
        </button>
        <div class="faq-a">Sim, sem multa e sem burocracia. Você cancela pelo painel ou nos chama no WhatsApp. Os 30 dias grátis não pedem cartão de crédito — você só paga se decidir continuar.</div>
      </div>
    </div>
  </div>
</section>

<!-- PREÇOS -->
<section class="section" id="precos" style="background:var(--surface);border-top:1px solid var(--border);border-bottom:1px solid var(--border)">
  <div class="container">
    <div class="section-tag center anim">Planos</div>
    <h2 class="section-title center anim">Menos que um vendedor, resultado de 10</h2>
    <p class="section-sub center anim" style="margin-bottom:2rem">30 dias grátis em todos os planos. Cancele quando quiser, sem burocracia.</p>

    <!-- BILLING TOGGLE -->
    <div class="billing-toggle anim">
      <span class="toggle-label active" id="label-monthly">Mensal</span>
      <label class="toggle-wrap">
        <input type="checkbox" id="billing-switch" onchange="toggleBilling(this.checked)"/>
        <span class="toggle-slider"></span>
      </label>
      <span class="toggle-label" id="label-annual">Anual</span>
      <span class="save-badge">Economize 20%</span>
    </div>

    <div class="price-grid">

      <div class="plan anim">
        <div class="plan-tier">Starter</div>
        <div class="plan-price" id="price-starter"><sup>R$</sup>297<sub>/mês</sub></div>
        <div class="plan-annual-note" id="note-starter">R$ 2.856 cobrado anualmente — economia de R$ 708</div>
        <div class="plan-pitch">Para instaladoras que qualificam até 500 leads/mês</div>
        <ul class="plan-list">
          <li>Até 500 leads/mês</li>
          <li>Score e priorização automática</li>
          <li>WhatsApp personalizado por lead</li>
          <li>Dashboard com fila do dia</li>
          <li>1 integração (Google Forms)</li>
          <li>Export CSV</li>
          <li class="no">Simulação ROI por estado</li>
          <li class="no">Suporte prioritário</li>
        </ul>
        <button onclick="startCheckout('starter')" class="plan-btn plan-btn-out">Começar grátis por 30 dias</button>
      </div>

      <div class="plan pop anim">
        <div class="pop-badge">⭐ Mais popular</div>
        <div class="plan-tier">Pro</div>
        <div class="plan-price" id="price-pro"><sup>R$</sup>497<sub>/mês</sub></div>
        <div class="plan-annual-note" id="note-pro">R$ 4.776 cobrado anualmente — economia de R$ 1.188</div>
        <div class="plan-pitch">Para times que querem escalar sem contratar mais vendedores</div>
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
        <button onclick="startCheckout('pro')" class="plan-btn plan-btn-sun">Começar grátis por 30 dias</button>
      </div>

      <div class="plan anim">
        <div class="plan-tier">Empresarial</div>
        <div class="plan-price" id="price-enterprise"><sup>R$</sup>997<sub>/mês</sub></div>
        <div class="plan-annual-note" id="note-enterprise">R$ 9.576 cobrado anualmente — economia de R$ 2.388</div>
        <div class="plan-pitch">Para redes e franquias com múltiplas operações</div>
        <ul class="plan-list">
          <li>Leads ilimitados</li>
          <li>Tudo do Pro</li>
          <li>Setup e integração incluso</li>
          <li>Treinamento do time</li>
          <li>Integração com qualquer sistema</li>
          <li>Disponibilidade garantida 24/7</li>
          <li>Gerente de conta dedicado</li>
          <li>NF e contrato formal</li>
        </ul>
        <a href="#contato" class="plan-btn plan-btn-out">Falar com o time →</a>
      </div>

    </div>
    <p class="price-note">30 dias grátis em todos os planos · Sem cartão · Cancele quando quiser</p>

    <!-- GARANTIA -->
    <div class="guarantee-wrap anim">
      <div class="guarantee-icon">🛡️</div>
      <div>
        <div class="guarantee-title">Garantia de 30 dias — ou devolvemos tudo</div>
        <div class="guarantee-text">Teste sem risco. Se em 30 dias você não ver resultado, devolvemos 100% do valor pago. Sem perguntas, sem burocracia. Você não perde nada — só ganha tempo.</div>
      </div>
    </div>
  </div>
</section>

<!-- CTA -->
<section class="section cta-wrap" id="contato">
  <div class="container">
    <div class="section-tag center">Comece hoje</div>
    <h2 class="section-title center">Seu próximo fechamento começa com o lead certo</h2>
    <p>30 dias grátis. Sem cartão. Se não funcionar, você não paga nada.</p>
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
    <div id="form-feedback" style="display:none;margin-top:1.25rem;text-align:center;font-size:.875rem;font-weight:700"></div>
    <div class="trust-row">
      <div class="trust-badge"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>Dados protegidos · LGPD</div>
      <div class="trust-badge"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>Cobrança transparente via Stripe</div>
      <div class="trust-badge"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>Suporte via WhatsApp</div>
    </div>
  </div>
</section>

<footer>
  <p>© 2026 LeadSolar · Qualificação de leads para instaladoras de energia solar</p>
  <div class="footer-links">
    <a href="/dashboard">Dashboard</a>
    <a href="/docs">API</a>
    <a href="/privacidade">Privacidade</a>
    <a href="/termos">Termos</a>
  </div>
</footer>

<!-- STICKY MOBILE CTA -->
<div class="sticky-cta" id="sticky-cta">
  <p><strong>30 dias grátis</strong>Sem cartão de crédito</p>
  <a href="#contato" onclick="document.getElementById('sticky-cta').style.display='none'">Testar agora →</a>
</div>

<!-- FLOATING WA BUTTON -->
<a class="wa-float" href="https://wa.me/message/J3P2VWIXM5RKL1" target="_blank" rel="noopener">
  <svg viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/><path d="M12 0C5.373 0 0 5.373 0 12c0 2.121.554 4.112 1.523 5.837L0 24l6.335-1.505A11.942 11.942 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0zm0 21.818a9.818 9.818 0 01-5.006-1.371l-.36-.214-3.727.885.916-3.618-.235-.372A9.818 9.818 0 1112 21.818z"/></svg>
  <span>Falar no WhatsApp</span>
</a>

<!-- ROI WIZARD MODAL -->
<div id="roi-wizard" style="display:none;position:fixed;inset:0;z-index:900;background:rgba(6,12,24,.88);backdrop-filter:blur(8px);align-items:center;justify-content:center;padding:1.5rem">
  <div style="background:#0d1825;border:1px solid #1a2e48;border-radius:1.5rem;max-width:520px;width:100%;padding:2rem;position:relative;box-shadow:0 24px 64px rgba(0,0,0,.5)">
    <button onclick="closeWizard()" style="position:absolute;top:1rem;right:1rem;background:none;border:none;color:#6b85a0;font-size:1.2rem;cursor:pointer;line-height:1;padding:.25rem">✕</button>
    <!-- STEP 1 -->
    <div id="wz-step-1">
      <div style="font-size:.7rem;font-weight:700;color:#f59e0b;text-transform:uppercase;letter-spacing:.1em;margin-bottom:.5rem">Passo 1 de 3</div>
      <div style="font-size:1.2rem;font-weight:800;margin-bottom:.35rem">Quantos leads chegam por mês?</div>
      <div style="font-size:.85rem;color:#6b85a0;margin-bottom:1.5rem">Todos os canais somados: formulário, Meta Ads, indicação...</div>
      <div style="display:flex;flex-direction:column;gap:.65rem">
        <button class="wz-chip" onclick="wzNext(1,'lt100','Menos de 100 leads')">Menos de 100 leads</button>
        <button class="wz-chip" onclick="wzNext(1,'100to500','100 a 500 leads')">100 a 500 leads</button>
        <button class="wz-chip" onclick="wzNext(1,'500to2000','500 a 2.000 leads')">500 a 2.000 leads</button>
        <button class="wz-chip" onclick="wzNext(1,'gt2000','Mais de 2.000 leads')">Mais de 2.000 leads</button>
      </div>
    </div>
    <!-- STEP 2 -->
    <div id="wz-step-2" style="display:none">
      <div style="font-size:.7rem;font-weight:700;color:#f59e0b;text-transform:uppercase;letter-spacing:.1em;margin-bottom:.5rem">Passo 2 de 3</div>
      <div style="font-size:1.2rem;font-weight:800;margin-bottom:.35rem">Qual o maior problema hoje?</div>
      <div style="font-size:.85rem;color:#6b85a0;margin-bottom:1.5rem">Escolha o que mais impacta seus resultados.</div>
      <div style="display:flex;flex-direction:column;gap:.65rem">
        <button class="wz-chip" onclick="wzNext(2,'waste','Vendedor perde tempo com leads que não compram')">Vendedor perde tempo com leads que não compram</button>
        <button class="wz-chip" onclick="wzNext(2,'priority','Não sei quais leads ligar primeiro')">Não sei quais leads ligar primeiro</button>
        <button class="wz-chip" onclick="wzNext(2,'message','As mensagens não geram resposta')">As mensagens não geram resposta</button>
      </div>
    </div>
    <!-- STEP 3 -->
    <div id="wz-step-3" style="display:none">
      <div style="font-size:.7rem;font-weight:700;color:#f59e0b;text-transform:uppercase;letter-spacing:.1em;margin-bottom:.5rem">Passo 3 de 3</div>
      <div style="font-size:1.2rem;font-weight:800;margin-bottom:.35rem">Qual o ticket médio por contrato?</div>
      <div style="font-size:.85rem;color:#6b85a0;margin-bottom:1.5rem">Valor médio de um contrato fechado.</div>
      <div style="display:flex;flex-direction:column;gap:.65rem">
        <button class="wz-chip" onclick="wzResult('lt15k',15000)">Até R$ 15.000</button>
        <button class="wz-chip" onclick="wzResult('15to50k',32500)">R$ 15.000 – R$ 50.000</button>
        <button class="wz-chip" onclick="wzResult('gt50k',65000)">Acima de R$ 50.000</button>
      </div>
    </div>
    <!-- RESULT -->
    <div id="wz-result" style="display:none">
      <div style="text-align:center;margin-bottom:1.5rem">
        <div style="font-size:2.2rem;margin-bottom:.5rem">💰</div>
        <div style="font-size:.8rem;color:#6b85a0;margin-bottom:.35rem">Potencial extra por mês</div>
        <div id="wz-revenue" style="font-size:2rem;font-weight:900;color:#f59e0b;line-height:1;margin-bottom:.25rem"></div>
        <div id="wz-revenue-detail" style="font-size:.82rem;color:#6b85a0"></div>
      </div>
      <div id="wz-plan-card" style="background:#132030;border:1px solid #1a3050;border-radius:1rem;padding:1.25rem;margin-bottom:1.25rem">
        <div style="font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:#f59e0b;margin-bottom:.35rem">Plano recomendado para você</div>
        <div id="wz-plan-name" style="font-size:1rem;font-weight:800;margin-bottom:.2rem"></div>
        <div id="wz-plan-pitch" style="font-size:.82rem;color:#6b85a0"></div>
      </div>
      <button id="wz-cta" onclick="" style="width:100%;background:linear-gradient(135deg,#f59e0b,#d97706);color:#000;font-weight:800;padding:.9rem;border-radius:.65rem;border:none;font-size:.95rem;cursor:pointer;font-family:inherit;margin-bottom:.75rem">Começar grátis por 30 dias →</button>
      <div style="text-align:center;font-size:.75rem;color:#6b85a0">Sem cartão · 30 dias grátis · Cancele quando quiser</div>
    </div>
  </div>
</div>

<div id="toast">✓ Copiado!</div>

<script>
async function runDemo(e) {
  e.preventDefault();
  const btn = document.getElementById('demo-btn');
  btn.disabled = true;
  btn.textContent = 'Calculando...';
  document.getElementById('demo-error').style.display = 'none';
  document.getElementById('demo-placeholder').style.display = 'none';
  document.getElementById('demo-result').style.display = 'none';

  const body = {
    name: document.getElementById('d-name').value.trim(),
    city: document.getElementById('d-city').value.trim(),
    monthly_bill: parseFloat(document.getElementById('d-bill').value),
    property_type: document.getElementById('d-type').value,
    goal: document.getElementById('d-goal').value,
  };

  try {
    const r = await fetch('/demo', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body),
    });
    if (!r.ok) {
      const err = await r.json().catch(() => ({detail: 'Erro desconhecido'}));
      throw new Error(err.detail || 'Erro ao calcular score');
    }
    const d = await r.json();

    // Score circle
    const circle = document.getElementById('demo-score-circle');
    circle.textContent = d.score;
    circle.className = 'demo-score-circle';
    if (d.score >= 7) circle.classList.add('demo-score-high');
    else if (d.score >= 4) circle.classList.add('demo-score-mid');
    else circle.classList.add('demo-score-low');

    // Decision
    const decMap = {accept: '✓ Ligar hoje', review: '~ Qualificar primeiro', reject: '✗ Baixa prioridade'};
    document.getElementById('demo-decision').textContent = decMap[d.decision] || d.decision || '—';
    const urgMap = {alta: 'Urgência alta', media: 'Urgência média', baixa: 'Urgência baixa'};
    document.getElementById('demo-urgency').textContent = urgMap[d.urgency] || d.urgency;

    document.getElementById('demo-rec-text').textContent = d.recommendation;
    document.getElementById('demo-wa-text').textContent = d.whatsapp_message;
    document.getElementById('demo-result').style.display = 'flex';
  } catch(err) {
    const errEl = document.getElementById('demo-error');
    errEl.textContent = err.message || 'Erro ao conectar. Tente novamente.';
    errEl.style.display = 'block';
    document.getElementById('demo-placeholder').style.display = 'block';
  } finally {
    btn.disabled = false;
    btn.textContent = 'Ver score e mensagem →';
  }
}

function copyDemoWA() {
  const txt = document.getElementById('demo-wa-text').textContent;
  if (!txt || txt === '—') return;
  navigator.clipboard.writeText(txt).then(() => {
    const btn = document.querySelector('.demo-wa-copy');
    btn.textContent = 'Copiado!';
    setTimeout(() => btn.textContent = 'Copiar', 2000);
  });
}

async function submitForm(e) {
  e.preventDefault();
  const btn = e.submitter || e.target.querySelector('button[type=submit]');
  const val = document.getElementById('contact-input').value.trim();
  if (!val) return;
  btn.disabled = true;
  btn.textContent = 'Enviando...';
  const msg = document.getElementById('form-feedback');
  try {
    const r = await fetch('/contact', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({contact: val, source: 'landing'})
    });
    const data = await r.json();
    msg.style.display = 'block';
    if (data.ok) {
      msg.style.color = '#22c55e';
      msg.textContent = '✓ Recebido! Vamos te chamar no WhatsApp em breve.';
      document.getElementById('contact-input').value = '';
      if (typeof fbq !== 'undefined') fbq('track', 'Lead');
    } else {
      msg.style.color = '#ef4444';
      msg.textContent = 'Algo deu errado. Tente novamente.';
    }
  } catch(err) {
    msg.style.display = 'block';
    msg.style.color = '#ef4444';
    msg.textContent = 'Erro de conexão. Tente novamente.';
  } finally {
    btn.disabled = false;
    btn.textContent = 'Quero testar grátis →';
  }
}

let _currentBilling = 'monthly';

function toggleBilling(isAnnual) {
  _currentBilling = isAnnual ? 'annual' : 'monthly';
  const prices = {
    starter: isAnnual ? '<sup>R$</sup>238<sub>/mês</sub>' : '<sup>R$</sup>297<sub>/mês</sub>',
    pro:     isAnnual ? '<sup>R$</sup>398<sub>/mês</sub>' : '<sup>R$</sup>497<sub>/mês</sub>',
    enterprise: isAnnual ? '<sup>R$</sup>798<sub>/mês</sub>' : '<sup>R$</sup>997<sub>/mês</sub>',
  };
  Object.keys(prices).forEach(plan => {
    const el = document.getElementById('price-' + plan);
    const note = document.getElementById('note-' + plan);
    if (el) el.innerHTML = prices[plan];
    if (note) note.style.display = isAnnual ? 'block' : 'none';
  });
  document.getElementById('label-monthly').classList.toggle('active', !isAnnual);
  document.getElementById('label-annual').classList.toggle('active', isAnnual);
}

async function startCheckout(plan) {
  const btns = document.querySelectorAll('.plan-btn');
  btns.forEach(b => { b.disabled = true; });
  try {
    const r = await fetch('/checkout/create', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({plan, billing: _currentBilling})
    });
    if (!r.ok) throw new Error('Erro ao iniciar pagamento');
    const data = await r.json();
    if (typeof fbq !== 'undefined') fbq('track', 'InitiateCheckout');
    window.location.href = data.checkout_url;
  } catch(err) {
    alert('Erro ao iniciar checkout. Tente novamente ou entre em contato pelo WhatsApp.');
    btns.forEach(b => { b.disabled = false; });
  }
}

function toggleFaq(btn) {
  const item = btn.closest('.faq-item');
  const isOpen = item.classList.contains('open');
  document.querySelectorAll('.faq-item.open').forEach(el => el.classList.remove('open'));
  if (!isOpen) item.classList.add('open');
}

function closeMobileMenu() {
  document.getElementById('mobile-menu').classList.remove('open');
}

// Scroll reveal — safe: only animate elements NOT already visible
(function() {
  document.body.classList.add('js-ready');

  // Auto-add anim class to card-type elements
  document.querySelectorAll('.pain, .feat, .step, .testi, .mcard, .faq-item, .plan, .ba-row, .logo-chip').forEach(el => {
    if (!el.classList.contains('anim') && !el.classList.contains('anim-left')) {
      el.classList.add('anim');
    }
  });

  const io = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) { e.target.classList.add('visible'); io.unobserve(e.target); }
    });
  }, {threshold: 0.06, rootMargin: '0px 0px -20px 0px'});

  document.querySelectorAll('.anim, .anim-left').forEach((el, idx) => {
    // Stagger siblings in same grid/flex parent
    const sibs = el.parentElement ? [...el.parentElement.children].filter(c => c.classList.contains('anim') || c.classList.contains('anim-left')) : [];
    const pos = sibs.indexOf(el);
    if (pos > 0) el.style.transitionDelay = (pos * 0.1) + 's';
    io.observe(el);
  });
})();

// Animate hero proof numbers on first view
(function() {
  const proof = document.querySelector('.hero-proof');
  if (!proof) return;
  const io = new IntersectionObserver(([e]) => {
    if (!e.isIntersecting) return;
    io.disconnect();
    proof.querySelectorAll('strong').forEach((el, i) => {
      el.style.cssText += 'opacity:0;transition:opacity .5s ease ' + (i * 0.15) + 's';
      requestAnimationFrame(() => requestAnimationFrame(() => el.style.opacity = '1'));
    });
  }, {threshold: 0.5});
  io.observe(proof);
})();

// Pulse glow on first CTA button only
const firstCTA = document.querySelector('.hero-btns .btn-sun');
if (firstCTA) firstCTA.classList.add('btn-sun-pulse');

// Hide WA float when CTA section is visible (avoid overlap)
(function() {
  const waBtn = document.querySelector('.wa-float');
  const ctaEl = document.getElementById('contato');
  if (!waBtn || !ctaEl) return;
  new IntersectionObserver(([e]) => {
    waBtn.style.display = e.isIntersecting ? 'none' : '';
  }, {threshold: 0.1}).observe(ctaEl);
})();

// ROI WIZARD
const _wzAnswers = {};

function openWizard() {
  document.getElementById('roi-wizard').classList.add('open');
  document.body.style.overflow = 'hidden';
}
function closeWizard() {
  document.getElementById('roi-wizard').classList.remove('open');
  document.body.style.overflow = '';
}
document.getElementById('roi-wizard').addEventListener('click', function(e) {
  if (e.target === this) closeWizard();
});

function wzNext(step, key, label) {
  _wzAnswers['step' + step] = {key, label};
  document.getElementById('wz-step-' + step).style.display = 'none';
  document.getElementById('wz-step-' + (step + 1)).style.display = 'block';
}

function wzResult(ticketKey, ticketVal) {
  _wzAnswers.ticket = {key: ticketKey, val: ticketVal};

  const leadsMap = {lt100: 75, '100to500': 280, '500to2000': 1100, gt2000: 2500};
  const leads = leadsMap[_wzAnswers.step1.key] || 280;
  const extraCloses = Math.round(leads * 0.03);
  const extraRevenue = extraCloses * ticketVal;

  const planMap = {lt100: {plan:'starter', name:'Starter', pitch:'Perfeito para times pequenos — até 500 leads/mês.', price:'R$297'}, '100to500': {plan:'starter', name:'Starter', pitch:'Ideal para seu volume — até 500 leads/mês com priorização automática.', price:'R$297'}, '500to2000': {plan:'pro', name:'Pro', pitch:'Feito para o seu volume — até 2.000 leads/mês com simulação de ROI.', price:'R$497'}, gt2000: {plan:'enterprise', name:'Empresarial', pitch:'Para o seu volume, precisamos conversar. Leads ilimitados + setup incluso.', price:'R$997'}};
  const rec = planMap[_wzAnswers.step1.key] || planMap['100to500'];

  document.getElementById('wz-revenue').textContent = 'R$ ' + extraRevenue.toLocaleString('pt-BR');
  document.getElementById('wz-revenue-detail').textContent = extraCloses + ' contratos a mais por mês × R$ ' + ticketVal.toLocaleString('pt-BR') + ' de ticket médio';
  document.getElementById('wz-plan-name').textContent = 'LeadSolar ' + rec.name + ' — ' + rec.price + '/mês';
  document.getElementById('wz-plan-pitch').textContent = rec.pitch;
  document.getElementById('wz-cta').onclick = function() { closeWizard(); startCheckout(rec.plan); };

  document.getElementById('wz-step-3').style.display = 'none';
  document.getElementById('wz-result').style.display = 'block';
}
</script>
</body>
</html>"""


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def landing() -> HTMLResponse:
    _PROD_URL = "https://lead-intelligence-production.up.railway.app"
    html = _HTML.replace(_PROD_URL, _BASE_URL) if _BASE_URL != _PROD_URL else _HTML
    return HTMLResponse(content=html)


_LEGAL_STYLE = """
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#060c18;color:#cbd5e1;line-height:1.7;padding:2rem 1rem}
.wrap{max-width:760px;margin:0 auto}
a.back{display:inline-block;color:#f59e0b;text-decoration:none;font-size:.9rem;margin-bottom:2rem}
a.back:hover{text-decoration:underline}
h1{font-size:1.8rem;font-weight:900;color:#f1f5f9;margin-bottom:.5rem}
.date{font-size:.8rem;color:#6b85a0;margin-bottom:2rem}
h2{font-size:1.1rem;font-weight:700;color:#f1f5f9;margin:2rem 0 .5rem}
p,li{font-size:.9rem;color:#94a3b8;margin-bottom:.75rem}
ul{padding-left:1.5rem}
a{color:#f59e0b}
</style>
"""


@router.get("/privacidade", response_class=HTMLResponse, include_in_schema=False)
async def privacy_policy() -> HTMLResponse:
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Política de Privacidade — LeadSolar</title>
{_LEGAL_STYLE}
</head>
<body><div class="wrap">
<a class="back" href="/">← Voltar</a>
<h1>Política de Privacidade</h1>
<p class="date">Última atualização: março de 2026</p>

<h2>1. Quem somos</h2>
<p>LeadSolar é uma plataforma de qualificação de leads para instaladoras de energia solar, operada por pessoa jurídica brasileira. Nosso produto analisa dados de leads fornecidos por você (o cliente) para gerar scores, priorização e mensagens de abordagem.</p>

<h2>2. Dados que coletamos</h2>
<ul>
  <li><strong>Dados do cliente (você):</strong> nome da empresa, e-mail, número de WhatsApp fornecidos ao contratar o serviço.</li>
  <li><strong>Dados dos seus leads:</strong> nome, cidade, valor de conta de luz, tipo de imóvel e objetivo — enviados por você via API ou integração.</li>
  <li><strong>Dados de uso:</strong> logs de requisições, IP de acesso e métricas de desempenho.</li>
  <li><strong>Dados de pagamento:</strong> processados integralmente pelo Stripe. Não armazenamos dados de cartão.</li>
</ul>

<h2>3. Como usamos os dados</h2>
<ul>
  <li>Qualificar e pontuar os leads enviados por você.</li>
  <li>Gerar relatórios e dashboards de uso.</li>
  <li>Processar pagamentos e emitir cobranças via Stripe.</li>
  <li>Melhorar o produto com base em padrões agregados e anonimizados.</li>
</ul>

<h2>4. Compartilhamento de dados</h2>
<p>Não vendemos nem compartilhamos seus dados com terceiros, exceto:</p>
<ul>
  <li><strong>Stripe:</strong> para processamento de pagamentos.</li>
  <li><strong>Firebase/Google Cloud:</strong> para armazenamento seguro dos dados.</li>
  <li><strong>Obrigação legal:</strong> quando exigido por lei ou autoridade competente.</li>
</ul>

<h2>5. Seus direitos (LGPD)</h2>
<p>Conforme a Lei Geral de Proteção de Dados (Lei nº 13.709/2018), você tem direito a:</p>
<ul>
  <li>Confirmar a existência de tratamento de dados.</li>
  <li>Acessar, corrigir ou excluir seus dados pessoais.</li>
  <li>Revogar o consentimento a qualquer momento.</li>
  <li>Portabilidade dos dados mediante solicitação.</li>
</ul>
<p>Para exercer seus direitos, entre em contato via WhatsApp: <a href="https://wa.me/message/J3P2VWIXM5RKL1">+55 91 8515-6690</a></p>

<h2>6. Retenção de dados</h2>
<p>Mantemos seus dados enquanto o contrato estiver ativo. Após cancelamento, excluímos os dados em até 90 dias, salvo obrigação legal.</p>

<h2>7. Segurança</h2>
<p>Utilizamos criptografia em trânsito (HTTPS/TLS), controles de acesso por chave de API e auditoria de logs para proteger seus dados.</p>

<h2>8. Alterações</h2>
<p>Podemos atualizar esta política periodicamente. Notificaremos clientes ativos sobre mudanças relevantes.</p>

<h2>9. Contato</h2>
<p>Dúvidas sobre privacidade? Fale conosco: <a href="https://wa.me/message/J3P2VWIXM5RKL1">WhatsApp</a></p>
</div></body></html>"""
    return HTMLResponse(content=html)


@router.get("/termos", response_class=HTMLResponse, include_in_schema=False)
async def terms_of_service() -> HTMLResponse:
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Termos de Uso — LeadSolar</title>
{_LEGAL_STYLE}
</head>
<body><div class="wrap">
<a class="back" href="/">← Voltar</a>
<h1>Termos de Uso</h1>
<p class="date">Última atualização: março de 2026</p>

<h2>1. Aceitação</h2>
<p>Ao contratar ou usar o LeadSolar, você concorda com estes Termos. Se não concordar, não utilize o serviço.</p>

<h2>2. O serviço</h2>
<p>O LeadSolar fornece uma API e painel para qualificação automatizada de leads de energia solar. O serviço é prestado no modelo SaaS com cobrança mensal ou anual via Stripe.</p>

<h2>3. Uso permitido</h2>
<ul>
  <li>O serviço destina-se exclusivamente a empresas e profissionais do setor de energia solar.</li>
  <li>Você é responsável pelos dados de leads que envia à plataforma.</li>
  <li>É proibido usar o serviço para fins ilegais, envio de spam ou abordagens não autorizadas.</li>
</ul>

<h2>4. Chave de API</h2>
<p>Sua chave de API é pessoal e intransferível. Não a compartilhe. Você é responsável por todo uso feito com sua chave.</p>

<h2>5. Pagamento e cancelamento</h2>
<ul>
  <li><strong>Trial:</strong> 30 dias grátis sem cartão de crédito.</li>
  <li><strong>Cobrança:</strong> Mensal ou anual, processada pelo Stripe.</li>
  <li><strong>Cancelamento:</strong> A qualquer momento pelo portal do cliente. Sem multa.</li>
  <li><strong>Garantia:</strong> Se em 30 dias você não ver resultado, devolvemos 100% do valor pago.</li>
</ul>

<h2>6. Limitação de responsabilidade</h2>
<p>O LeadSolar fornece scores e recomendações baseados em dados e regras. As decisões de negócio são sempre sua responsabilidade. Não garantimos conversão ou resultado específico de vendas.</p>

<h2>7. Disponibilidade</h2>
<p>Buscamos 99,9% de uptime, mas não garantimos disponibilidade ininterrupta. Manutenções programadas serão comunicadas com antecedência.</p>

<h2>8. Rescisão</h2>
<p>Podemos encerrar contas que violem estes termos, com aviso prévio quando possível.</p>

<h2>9. Foro</h2>
<p>Fica eleito o foro da comarca de Belém/PA para dirimir quaisquer controvérsias.</p>

<h2>10. Contato</h2>
<p>Dúvidas? <a href="https://wa.me/message/J3P2VWIXM5RKL1">WhatsApp</a></p>
</div></body></html>"""
    return HTMLResponse(content=html)
