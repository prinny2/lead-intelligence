"""
Lead Intelligence MVP - FastAPI application.
Solar lead qualification with hybrid AI + rules and local JSONL storage.
"""

import logging
import os
import sys
import time

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

load_dotenv()

# --- Sentry error tracking (optional — set SENTRY_DSN env var) ---
_sentry_dsn = os.getenv("SENTRY_DSN", "").strip()
if _sentry_dsn:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.starlette import StarletteIntegration
    sentry_sdk.init(
        dsn=_sentry_dsn,
        integrations=[StarletteIntegration(), FastApiIntegration()],
        traces_sample_rate=0.2,
        environment=os.getenv("RAILWAY_ENVIRONMENT", "production"),
    )

# --- Structured logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)

from app.routes import api_router
from app.services.audit_service import log_event

app = FastAPI(
    title="Lead Intelligence MVP",
    description="Qualify solar energy leads via AI + rules. POST /lead, GET /stats.",
    version="0.2.0",
)

# --- CORS ---
_cors = os.getenv("CORS_ORIGINS", "").strip()
if _cors:
    _origins = ["*"] if _cors == "*" else [o.strip() for o in _cors.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# --- Audit middleware ---
@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000)

    # Only audit non-trivial endpoints
    path = request.url.path
    skip = {"/", "/health", "/favicon.ico", "/docs", "/openapi.json", "/redoc"}
    if path not in skip and not path.startswith("/static"):
        ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (
            request.client.host if request.client else "unknown"
        )
        log_event(
            "http_request",
            ip=ip,
            endpoint=path,
            method=request.method,
            status_code=response.status_code,
            extra={"duration_ms": duration_ms},
        )

    return response


_static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.isdir(_static_dir):
    app.mount("/static", StaticFiles(directory=_static_dir), name="static")

app.include_router(api_router)
