"""Custom error pages."""

from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse, Response

_404_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Página não encontrada — LeadSolar</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#060c18;color:#f1f5f9;min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:2rem;text-align:center}
.logo{font-size:1.4rem;font-weight:900;color:#f59e0b;letter-spacing:-.02em;margin-bottom:3rem;display:flex;align-items:center;gap:.5rem}
.logo span{color:#f1f5f9;font-weight:400}
.code{font-size:6rem;font-weight:900;line-height:1;background:linear-gradient(135deg,#f59e0b,#d97706);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:1rem}
h1{font-size:1.5rem;font-weight:800;margin-bottom:.75rem}
p{color:#6b85a0;font-size:.95rem;max-width:380px;line-height:1.7;margin-bottom:2.5rem}
.btns{display:flex;gap:.85rem;flex-wrap:wrap;justify-content:center}
.btn-sun{background:linear-gradient(135deg,#f59e0b,#d97706);color:#000;font-weight:800;padding:.85rem 1.75rem;border-radius:.65rem;text-decoration:none;font-size:.95rem;transition:transform .2s}
.btn-sun:hover{transform:translateY(-2px)}
.btn-wa{background:#25d366;color:#fff;font-weight:700;padding:.85rem 1.75rem;border-radius:.65rem;text-decoration:none;font-size:.95rem;display:flex;align-items:center;gap:.5rem;transition:transform .2s}
.btn-wa:hover{transform:translateY(-2px)}
</style>
</head>
<body>
<div class="logo">
  <svg width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="14" cy="14" r="14" fill="#1a2e48"/>
    <circle cx="14" cy="14" r="7" fill="#f59e0b"/>
    <line x1="14" y1="2" x2="14" y2="5" stroke="#f59e0b" stroke-width="2" stroke-linecap="round"/>
    <line x1="14" y1="23" x2="14" y2="26" stroke="#f59e0b" stroke-width="2" stroke-linecap="round"/>
    <line x1="2" y1="14" x2="5" y2="14" stroke="#f59e0b" stroke-width="2" stroke-linecap="round"/>
    <line x1="23" y1="14" x2="26" y2="14" stroke="#f59e0b" stroke-width="2" stroke-linecap="round"/>
  </svg>
  Lead<span>Solar</span>
</div>
<div class="code">404</div>
<h1>Essa página não existe</h1>
<p>O link que você acessou pode ter expirado ou nunca existiu. Volte para o início e continue de onde parou.</p>
<div class="btns">
  <a href="/" class="btn-sun">← Voltar para o início</a>
  <a href="https://wa.me/5591985156690" target="_blank" rel="noopener" class="btn-wa">
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/><path d="M12 0C5.373 0 0 5.373 0 12c0 2.121.554 4.112 1.523 5.837L0 24l6.335-1.505A11.942 11.942 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0zm0 21.818a9.818 9.818 0 01-5.006-1.371l-.36-.214-3.727.885.916-3.618-.235-.372A9.818 9.818 0 1112 21.818z"/></svg>
    Falar no WhatsApp
  </a>
</div>
</body>
</html>"""


async def not_found_handler(request: Request, exc: Exception) -> Response:
    # Browsers get the branded page; API clients keep FastAPI's JSON {"detail": ...}.
    if "text/html" not in request.headers.get("accept", ""):
        return JSONResponse({"detail": getattr(exc, "detail", "Not Found")}, status_code=404)
    return HTMLResponse(content=_404_HTML, status_code=404)
