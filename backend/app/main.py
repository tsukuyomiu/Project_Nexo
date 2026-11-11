"""
Entrypoint Principal do Back-End do Projeto Nexo (FastAPI).

Orquestra:
- Inicialização automática do Banco SQL (Tabelas, Índices, Views, Triggers e Seeds)
- Middleware de Auditoria e Tráfego HTTP (`AuditAccessMiddleware`)
- Configuração de CORS para integração com o Front-End React/Vite
- Tratamento global de exceções padronizado
- Documentação interativa Swagger UI (`/docs`) e ReDoc (`/redoc`)
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.middlewares.audit_middleware import AuditAccessMiddleware
from app.api.routers import auth, dashboard, logs, transactions, users
from app.core.config import settings
from app.core.exceptions import (
    NexoException,
    nexo_exception_handler,
    validation_exception_handler,
)
from app.core.security import now_brazil_iso, now_utc_iso
from app.db.scripts.init_db import initialize_database


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Inicializa os schemas SQL, Triggers, Views e Seeds automaticamente ao subir a API."""
    initialize_database()
    yield


app = FastAPI(
    title=settings.NEXO_APP_NAME,
    version=settings.NEXO_VERSION,
    description=(
        "API REST oficial do **Projeto Nexo** — Gestão Financeira & Plataforma com "
        "Auditoria 360° Imutável (Python + SQL Triggers)."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# 1. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Middleware de Auditoria e Tráfego HTTP 360°
app.add_middleware(AuditAccessMiddleware)

# 3. Exception Handlers Globais
app.add_exception_handler(NexoException, nexo_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]

# 4. Registro dos Routers sob /api/v1
api_prefix = settings.NEXO_API_V1_PREFIX
app.include_router(auth.router, prefix=api_prefix)
app.include_router(users.router, prefix=api_prefix)
app.include_router(transactions.router, prefix=api_prefix)
app.include_router(dashboard.router, prefix=api_prefix)
app.include_router(logs.router, prefix=api_prefix)


@app.get("/", tags=["Health & Status"])
def root() -> Dict[str, Any]:
    """Rota raiz informativa da API do Projeto Nexo."""
    return {
        "ok": True,
        "service": settings.NEXO_APP_NAME,
        "version": settings.NEXO_VERSION,
        "environment": settings.NEXO_ENV,
        "timestamp_brasilia": now_brazil_iso(),
        "timestamp_utc": now_utc_iso(),
        "docs_swagger": "/docs",
        "audit_timeline_endpoint": f"{api_prefix}/logs/timeline",
        "audit_full_endpoint": f"{api_prefix}/logs/audit",
    }


@app.get("/health", tags=["Health & Status"])
def healthcheck() -> Dict[str, Any]:
    """Healthcheck de monitoramento da aplicação."""
    return {
        "status": "healthy",
        "timestamp_brasilia": now_brazil_iso(),
    }
