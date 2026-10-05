import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.auth import router as auth_router
from routes.health import router as health_router
from routes.predict import router as predict_router
from security.headers import SecurityHeadersMiddleware

app = FastAPI(
    title="Customer Support Intent API",
    description="API de classificação de intenção de tickets de suporte ao cliente.",
    version="1.0.0",
)

# ── Configuração de CORS com Allowlist Explícita ───────────────────────────
# Origens permitidas explícitas (sem wildcard "*")
DEFAULT_ALLOWED_ORIGINS = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:3000",
    "https://supportdesk-api.marcosryan.com",
]

env_origins = os.getenv("ALLOWED_ORIGINS")
if env_origins:
    allowed_origins = [o.strip() for o in env_origins.split(",") if o.strip()]
else:
    allowed_origins = DEFAULT_ALLOWED_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# ── Middleware de Headers de Segurança HTTP (OWASP Top 10) ──────────────────
app.add_middleware(SecurityHeadersMiddleware)

# ── Inclusão de Rotas Modulares ────────────────────────────────────────────
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(predict_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
