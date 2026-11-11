"""
Middleware HTTP de Auditoria e Rastreabilidade (Audit & Access Middleware).

Intercepta 100% das chamadas que chegam ao Back-End:
1. Gera um `X-Request-ID` único por chamada.
2. Identifica automaticamente quem está fazendo a requisição (se houver JWT).
3. Cronometra o tempo de execução em milissegundos (`X-Process-Time-Ms`).
4. Grava o registro completo na tabela SQL `access_logs` e em `nexo_access.jsonl`.
5. Em caso de erro interno (500), registra automaticamente um alerta `CRITICAL` em `audit_logs`.
"""

from __future__ import annotations

import time
import traceback

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.deps import extract_client_ip
from app.core.audit_logger import record_access_log, record_audit_event
from app.core.security import decode_access_token, generate_uuid
from app.db.session import SessionLocal


class AuditAccessMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start_perf = time.perf_counter()
        request_id = request.headers.get("x-request-id") or generate_uuid()
        request.state.request_id = request_id

        ip_address = extract_client_ip(request)
        user_agent = request.headers.get("user-agent", "Unknown-Client")
        route = request.url.path
        query_params = str(request.url.query) if request.url.query else None

        # Tenta extrair identidade do token JWT mesmo antes da rota executar
        user_id = getattr(request.state, "user_id", None)
        user_email = getattr(request.state, "user_email", None)
        auth_header = request.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            token_str = auth_header.split(" ", 1)[1].strip()
            payload = decode_access_token(token_str)
            if payload:
                user_id = payload.get("sub")
                user_email = payload.get("email")

        error_detail = None
        try:
            response: Response = await call_next(request)
            status_code = response.status_code
        except Exception as exc:
            status_code = 500
            error_detail = f"{type(exc).__name__}: {exc}"
            elapsed_ms = (time.perf_counter() - start_perf) * 1000.0

            db = SessionLocal()
            try:
                record_access_log(
                    db,
                    request_id=request_id,
                    http_method=request.method,
                    route=route,
                    query_params=query_params,
                    status_code=500,
                    response_time_ms=elapsed_ms,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    user_id=user_id,
                    user_email=user_email,
                    error_detail=error_detail,
                )
                record_audit_event(
                    db,
                    action="UNHANDLED_SERVER_EXCEPTION",
                    category="SYSTEM",
                    severity="CRITICAL",
                    entity_affected="http_server",
                    entity_id=request_id,
                    actor_id=user_id,
                    actor_email=user_email or "anonimo@nexo.local",
                    ip_address=ip_address,
                    user_agent=user_agent,
                    http_method=request.method,
                    http_route=route,
                    request_id=request_id,
                    summary=f"Erro interno não tratado em {request.method} {route}: {error_detail}",
                    extra_metadata={"traceback": traceback.format_exc()[-1500:]},
                )
            finally:
                db.close()
            raise

        elapsed_ms = (time.perf_counter() - start_perf) * 1000.0

        # Atualiza caso a rota tenha preenchido request.state
        user_id = getattr(request.state, "user_id", user_id)
        user_email = getattr(request.state, "user_email", user_email)

        # Grava no access_logs (ignorando apenas healthcheck estático se desejado, mas aqui gravamos tudo!)
        db = SessionLocal()
        try:
            record_access_log(
                db,
                request_id=request_id,
                http_method=request.method,
                route=route,
                query_params=query_params,
                status_code=status_code,
                response_time_ms=elapsed_ms,
                ip_address=ip_address,
                user_agent=user_agent,
                user_id=user_id,
                user_email=user_email,
            )
        finally:
            db.close()

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.2f}"
        return response
