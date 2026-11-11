"""
Central de Retorno e Monitoramento de Logs & Auditoria 360° (`/api/v1/logs`):
Retorna exatamente TUDO o que acontece no site (em Python e em SQL):
  - QUEM fez (`quem_fez_nome`, `quem_fez_email`, `quem_fez_id`, `ip_origem`, `user_agent`)
  - QUANDO fez (`quando_fez_brasilia`, `quando_fez_utc`)
  - O QUE fez (`o_que_fez`, `acao`, `categoria_evento`, `entidade_afetada`, `dados_anteriores`, `dados_novos`)

Rotas disponíveis:
  - GET  `/audit`: Consulta completa e filtrável da tabela `audit_logs`
  - GET  `/timeline`: Linha do tempo humana ("Quem fez, a que horas fez e o que fez")
  - GET  `/access`: Histórico de todas as requisições HTTP (`access_logs`)
  - GET  `/stats`: Painel consolidado de métricas de auditoria, usuários mais ativos e alertas
  - GET  `/export`: Download imediato de todos os logs em CSV (Excel) ou JSON
  - POST `/frontend-event`: Recebe eventos de interface do Front-End React (cliques, telas, erros)
"""

from __future__ import annotations

import csv
import io
import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import PlainTextResponse, Response
from sqlalchemy import func, or_, text
from sqlalchemy.orm import Session

from app.api.deps import (
    AuditContext,
    get_audit_context,
    get_current_user_optional,
)
from app.core.audit_logger import record_audit_event
from app.core.config import settings
from app.core.exceptions import NexoException
from app.db.models import AccessLog, AuditLog, User
from app.db.session import get_db
from app.schemas.audit import (
    AccessLogItem,
    AccessLogListResponse,
    AuditLogItem,
    AuditLogListResponse,
    FrontendEventPayload,
)

router = APIRouter(prefix="/logs", tags=["Auditoria 360° & Logs do Sistema"])


def _check_log_access(user: Optional[User]) -> None:
    """
    Em desenvolvimento (`NEXO_LOGS_PUBLIC_IN_DEV=true`), permite consultar os logs
    diretamente pelo navegador/Swagger para inspeção imediata.
    Em produção, exige usuário autenticado com role 'admin' ou 'auditor'.
    """
    if settings.NEXO_ENV == "development" and settings.NEXO_LOGS_PUBLIC_IN_DEV:
        return
    if not user:
        raise NexoException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticação necessária para consultar os logs de auditoria.",
            error_code="UNAUTHORIZED",
        )
    if user.role not in ("admin", "auditor"):
        raise NexoException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a Administradores e Auditores.",
            error_code="FORBIDDEN_AUDIT_ACCESS",
        )


def _parse_json_safe(raw: Optional[str]) -> Optional[Dict[str, Any]]:
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {"value": parsed}
    except Exception:
        return {"raw": raw}


def _row_to_audit_item(row: AuditLog) -> AuditLogItem:
    return AuditLogItem(
        id=row.id,
        quando_fez_brasilia=row.data_hora_local,
        quando_fez_utc=row.data_hora_utc,
        quem_fez_id=row.usuario_id,
        quem_fez_nome=row.usuario_nome,
        quem_fez_email=row.usuario_email,
        ip_origem=row.ip_origem,
        user_agent=row.user_agent,
        metodo_http=row.metodo_http,
        rota_http=row.rota_http,
        request_id=row.request_id,
        acao=row.acao,
        categoria_evento=row.categoria_evento,
        severidade=row.severidade,
        entidade_afetada=row.entidade_afetada,
        entidade_id=row.entidade_id,
        o_que_fez=row.resumo_humano,
        dados_anteriores=_parse_json_safe(row.dados_anteriores),
        dados_novos=_parse_json_safe(row.dados_novos),
        metadados_extras=_parse_json_safe(row.metadados_extras),
        origem_registro=row.origem_registro,
        hash_anterior=row.hash_anterior,
        hash_integridade=row.hash_integridade,
    )


@router.get("/audit", response_model=AuditLogListResponse)
def list_audit_logs(
    page: int = Query(default=1, ge=1, description="Página atual"),
    page_size: int = Query(default=50, ge=1, le=500, description="Itens por página"),
    usuario_id: Optional[str] = Query(default=None, description="Filtrar por ID do usuário"),
    email: Optional[str] = Query(default=None, description="Filtrar por e-mail de quem fez"),
    acao: Optional[str] = Query(default=None, description="Ex: TRANSACTION_CREATED, USER_LOGIN_SUCCESS"),
    categoria: Optional[str] = Query(
        default=None, description="AUTH | TRANSACTION | PROFILE | PREFERENCES | SECURITY | DATABASE"
    ),
    origem: Optional[str] = Query(
        default=None, description="API_PYTHON | SQL_TRIGGER | FRONTEND_TELEMETRY | SYSTEM"
    ),
    severidade: Optional[str] = Query(default=None, description="INFO | WARNING | ERROR | CRITICAL"),
    data_inicio: Optional[str] = Query(default=None, description="Data inicial YYYY-MM-DD"),
    data_fim: Optional[str] = Query(default=None, description="Data final YYYY-MM-DD"),
    q: Optional[str] = Query(default=None, description="Busca livre no resumo, nome, e-mail ou dados"),
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> AuditLogListResponse:
    """
    Retorna a trilha completa de auditoria com filtros combináveis.
    Mostra exatamente QUEM fez, a HORA que fez, O QUE fez e os dados ANTES/DEPOIS.
    """
    _check_log_access(user)

    query = db.query(AuditLog)
    if usuario_id:
        query = query.filter(AuditLog.usuario_id == usuario_id)
    if email:
        query = query.filter(AuditLog.usuario_email.ilike(f"%{email.strip()}%"))
    if acao:
        query = query.filter(AuditLog.acao.ilike(f"%{acao.strip()}%"))
    if categoria:
        query = query.filter(AuditLog.categoria_evento == categoria.upper())
    if origem:
        query = query.filter(AuditLog.origem_registro == origem.upper())
    if severidade:
        query = query.filter(AuditLog.severidade == severidade.upper())
    if data_inicio:
        query = query.filter(AuditLog.data_hora_local >= data_inicio)
    if data_fim:
        query = query.filter(AuditLog.data_hora_local <= f"{data_fim}T23:59:59")
    if q:
        term = f"%{q.strip()}%"
        query = query.filter(
            or_(
                AuditLog.resumo_humano.ilike(term),
                AuditLog.usuario_nome.ilike(term),
                AuditLog.usuario_email.ilike(term),
                AuditLog.acao.ilike(term),
                AuditLog.dados_anteriores.ilike(term),
                AuditLog.dados_novos.ilike(term),
            )
        )

    total = query.count()
    rows = (
        query.order_by(AuditLog.data_hora_utc.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return AuditLogListResponse(
        ok=True,
        total=total,
        page=page,
        page_size=page_size,
        items=[_row_to_audit_item(r) for r in rows],
    )


@router.get("/timeline")
def get_human_timeline(
    limit: int = Query(default=100, ge=1, le=500),
    incluir_triggers_sql: bool = Query(
        default=True, description="Se True, inclui também os logs de gatilhos nativos SQL"
    ),
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Retorna uma linha do tempo direta e super legível respondendo:
    'Quem fez, a que horas fez, de onde fez e o que fez'.
    """
    _check_log_access(user)

    query = db.query(AuditLog)
    if not incluir_triggers_sql:
        query = query.filter(AuditLog.origem_registro != "SQL_TRIGGER")

    rows = query.order_by(AuditLog.data_hora_utc.desc()).limit(limit).all()

    timeline = [
        {
            "log_id": r.id,
            "quando_fez": r.data_hora_local,
            "quem_fez": f"{r.usuario_nome} <{r.usuario_email}>",
            "o_que_fez": r.resumo_humano,
            "acao": r.acao,
            "modulo": r.categoria_evento,
            "severidade": r.severidade,
            "ip": r.ip_origem,
            "rota": f"{r.metodo_http or ''} {r.rota_http or ''}".strip() or r.origem_registro,
            "antes": _parse_json_safe(r.dados_anteriores),
            "depois": _parse_json_safe(r.dados_novos),
        }
        for r in rows
    ]
    return {
        "ok": True,
        "count": len(timeline),
        "timeline": timeline,
    }


@router.get("/access", response_model=AccessLogListResponse)
def list_access_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    metodo: Optional[str] = Query(default=None, description="GET, POST, PUT, DELETE"),
    status_code: Optional[int] = Query(default=None, description="Ex: 200, 201, 401, 422, 500"),
    rota: Optional[str] = Query(default=None, description="Filtro de rota"),
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> AccessLogListResponse:
    """Lista todas as requisições HTTP recebidas pela API com latência em ms."""
    _check_log_access(user)

    query = db.query(AccessLog)
    if metodo:
        query = query.filter(AccessLog.metodo_http == metodo.upper())
    if status_code:
        query = query.filter(AccessLog.status_code == status_code)
    if rota:
        query = query.filter(AccessLog.rota.ilike(f"%{rota.strip()}%"))

    total = query.count()
    rows = (
        query.order_by(AccessLog.data_hora_utc.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return AccessLogListResponse(
        ok=True,
        total=total,
        page=page,
        page_size=page_size,
        items=[
            AccessLogItem(
                id=r.id,
                quando_brasilia=r.data_hora_local,
                quando_utc=r.data_hora_utc,
                request_id=r.request_id,
                usuario_id=r.usuario_id,
                usuario_email=r.usuario_email,
                metodo_http=r.metodo_http,
                rota=r.rota,
                query_params=r.query_params,
                status_code=r.status_code,
                tempo_resposta_ms=r.tempo_resposta_ms,
                ip_origem=r.ip_origem,
                user_agent=r.user_agent,
                erro_detalhe=r.erro_detalhe,
            )
            for r in rows
        ],
    )


@router.get("/stats")
def get_logs_statistics(
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Retorna métricas agregadas sobre tudo o que ocorreu no sistema."""
    _check_log_access(user)

    total_audit = db.query(func.count(AuditLog.id)).scalar() or 0
    total_access = db.query(func.count(AccessLog.id)).scalar() or 0

    by_category = (
        db.query(AuditLog.categoria_evento, func.count(AuditLog.id))
        .group_by(AuditLog.categoria_evento)
        .all()
    )
    by_severity = (
        db.query(AuditLog.severidade, func.count(AuditLog.id))
        .group_by(AuditLog.severidade)
        .all()
    )
    by_origin = (
        db.query(AuditLog.origem_registro, func.count(AuditLog.id))
        .group_by(AuditLog.origem_registro)
        .all()
    )
    top_actors = (
        db.query(AuditLog.usuario_email, AuditLog.usuario_nome, func.count(AuditLog.id).label("total"))
        .group_by(AuditLog.usuario_email, AuditLog.usuario_nome)
        .order_by(text("total DESC"))
        .limit(10)
        .all()
    )
    avg_latency = db.query(func.avg(AccessLog.tempo_resposta_ms)).scalar() or 0.0

    return {
        "ok": True,
        "total_audit_events": total_audit,
        "total_http_requests": total_access,
        "average_http_latency_ms": round(float(avg_latency), 2),
        "events_by_category": {cat: count for cat, count in by_category},
        "events_by_severity": {sev: count for sev, count in by_severity},
        "events_by_origin": {orig: count for orig, count in by_origin},
        "most_active_users": [
            {"email": email, "name": name, "actions_count": count}
            for email, name, count in top_actors
        ],
    }


@router.get("/export")
def export_audit_logs(
    format: str = Query(default="csv", description="'csv' ou 'json'"),
    limit: int = Query(default=1000, ge=1, le=10000),
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> Response:
    """Exporta os logs de auditoria em formato CSV (pronto para Excel) ou JSON."""
    _check_log_access(user)

    rows = db.query(AuditLog).order_by(AuditLog.data_hora_utc.desc()).limit(limit).all()

    if format.lower() == "json":
        payload = [_row_to_audit_item(r).model_dump() for r in rows]
        return Response(
            content=json.dumps(payload, ensure_ascii=False, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": 'attachment; filename="nexo_audit_logs.json"'},
        )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "ID Log",
            "Data/Hora (Brasilia)",
            "Data/Hora (UTC)",
            "Quem Fez (Nome)",
            "Quem Fez (Email)",
            "Quem Fez (ID)",
            "IP Origem",
            "Acao",
            "Modulo",
            "Severidade",
            "O Que Fez (Resumo)",
            "Entidade Afetada",
            "ID Entidade",
            "Dados Anteriores (JSON)",
            "Dados Novos (JSON)",
            "Origem Registro",
            "Hash Integridade SHA256",
        ]
    )
    for r in rows:
        writer.writerow(
            [
                r.id,
                r.data_hora_local,
                r.data_hora_utc,
                r.usuario_nome,
                r.usuario_email,
                r.usuario_id or "",
                r.ip_origem,
                r.acao,
                r.categoria_evento,
                r.severidade,
                r.resumo_humano,
                r.entidade_afetada,
                r.entidade_id or "",
                r.dados_anteriores or "",
                r.dados_novos or "",
                r.origem_registro,
                r.hash_integridade,
            ]
        )

    return PlainTextResponse(
        content=output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="nexo_audit_logs.csv"'},
    )


@router.post("/frontend-event", status_code=status.HTTP_201_CREATED)
def log_frontend_event(
    payload: FrontendEventPayload,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
    audit: AuditContext = Depends(get_audit_context),
) -> Dict[str, Any]:
    """
    Recebe eventos diretamente do Front-End (ex.: abertura de tela, clique em botão,
    aplicação de filtro ou erro de cliente) e grava na trilha central `audit_logs`.
    """
    sev = payload.severidade.upper()
    if sev not in ("INFO", "WARNING", "ERROR", "CRITICAL"):
        sev = "INFO"

    record = record_audit_event(
        db,
        action=payload.acao.upper(),
        category="FRONTEND",
        severity=sev,
        entity_affected=payload.entidade_afetada,
        entity_id=payload.entidade_id,
        actor_id=user.id if user else audit.actor_id,
        actor_email=user.email if user else audit.actor_email,
        actor_name=user.nome if user else audit.actor_name,
        ip_address=audit.ip_address,
        user_agent=audit.user_agent,
        http_method=audit.http_method,
        http_route=audit.http_route,
        request_id=audit.request_id,
        summary=payload.resumo_humano,
        after_data=payload.detalhes,
        origin="FRONTEND_TELEMETRY",
    )
    return {"ok": True, "log_id": record["id"], "recorded_at": record["data_hora_local"]}
