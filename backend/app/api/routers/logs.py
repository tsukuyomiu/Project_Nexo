"""
Central de Retorno e Monitoramento de Logs & Auditoria 360° (`/api/v1/logs`):
Acesso restrito a Administradores (`role == 'admin'`), mas retorna as atividades
de TODOS os usuários do site (Administradores, Usuários Comuns e Visitantes).

Inclui:
  - GET  `/audit`: Consulta completa e filtrável da tabela `audit_logs`
  - GET  `/timeline`: Linha do tempo humana ("Quem fez, a que horas fez e o que fez")
  - GET  `/access`: Histórico de todas as requisições HTTP (`access_logs`)
  - GET  `/stats`: Painel consolidado de métricas de auditoria, usuários mais ativos e alertas
  - GET  `/export`: Download imediato de todos os logs em CSV (Excel formatado pt-BR) ou JSON
  - POST `/send-email`: Gera a planilha Excel (.csv) dos logs e envia direto para o Gmail!
  - GET/POST `/smtp-config`: Configuração rápida de Gmail SMTP e visualização da Caixa de Saída
  - POST `/frontend-event`: Recebe eventos de interface do Front-End React
"""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import PlainTextResponse, Response
from pydantic import BaseModel, EmailStr
from sqlalchemy import func, or_, text
from sqlalchemy.orm import Session

from app.api.deps import (
    AuditContext,
    get_audit_context,
    get_current_user_optional,
)
from app.core.audit_logger import record_audit_event
from app.core.email_service import (
    get_smtp_config,
    list_outbox_emails,
    save_smtp_config,
    send_audit_logs_excel_email,
)
from app.core.exceptions import NexoException
from app.core.security import decode_access_token
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


class SendLogsEmailRequest(BaseModel):
    to_email: EmailStr
    incluir_triggers_sql: bool = False


class SmtpConfigPayload(BaseModel):
    gmail_user: EmailStr
    gmail_app_password: str
    default_to: Optional[EmailStr] = None


def format_br_datetime(iso_str: str) -> str:
    """Converte '2026-11-10T23:35:12.123-03:00' para '10/11/2026 23:35:12'."""
    if not iso_str:
        return ""
    try:
        clean = iso_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean)
        return dt.strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        if "T" in iso_str and len(iso_str) >= 19:
            date_part, time_part = iso_str[:10], iso_str[11:19]
            parts = date_part.split("-")
            if len(parts) == 3:
                return f"{parts[2]}/{parts[1]}/{parts[0]} {time_part}"
        return iso_str


def _check_log_access(
    user: Optional[User],
    db: Optional[Session] = None,
    token_query: Optional[str] = None,
) -> User:
    """
    Exige estritamente que o usuário esteja autenticado e possua `role = 'admin'` (ou 'auditor').
    """
    resolved_user = user
    if not resolved_user and token_query and db is not None:
        payload = decode_access_token(token_query)
        if payload and payload.get("sub"):
            resolved_user = (
                db.query(User)
                .filter(User.id == payload["sub"], User.ativo == 1)
                .first()
            )

    if not resolved_user:
        raise NexoException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticação de Administrador necessária para acessar os logs.",
            error_code="UNAUTHORIZED",
        )
    if resolved_user.role not in ("admin", "auditor"):
        raise NexoException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito exclusivamente a Administradores do Nexo.",
            error_code="FORBIDDEN_AUDIT_ACCESS",
        )
    return resolved_user


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
        quando_fez_brasilia=format_br_datetime(row.data_hora_local),
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


def _build_csv_bytes(rows: list[AuditLog]) -> bytes:
    output = io.StringIO()
    output.write("\ufeff")  # UTF-8 BOM para Excel pt-BR
    writer = csv.writer(output, delimiter=";")
    writer.writerow(
        [
            "Data e Hora (Brasília)",
            "Quem Fez (Nome)",
            "Quem Fez (E-mail)",
            "O Que Fez (Descrição Completa)",
            "Módulo",
            "Código da Ação",
            "Severidade",
            "IP de Origem",
            "Entidade Afetada",
            "Estado Anterior (Antes)",
            "Novo Estado (Depois)",
            "Origem do Log",
            "ID do Log",
            "Hash SHA-256 de Integridade",
        ]
    )
    for r in rows:
        writer.writerow(
            [
                format_br_datetime(r.data_hora_local),
                r.usuario_nome,
                r.usuario_email,
                r.resumo_humano,
                r.categoria_evento,
                r.acao,
                r.severidade,
                r.ip_origem,
                r.entidade_afetada,
                r.dados_anteriores or "-",
                r.dados_novos or "-",
                r.origem_registro,
                r.id,
                r.hash_integridade,
            ]
        )
    return output.getvalue().encode("utf-8")


@router.get("/audit", response_model=AuditLogListResponse)
def list_audit_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    usuario_id: Optional[str] = Query(default=None),
    email: Optional[str] = Query(default=None),
    acao: Optional[str] = Query(default=None),
    categoria: Optional[str] = Query(default=None),
    origem: Optional[str] = Query(default=None),
    severidade: Optional[str] = Query(default=None),
    data_inicio: Optional[str] = Query(default=None),
    data_fim: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None),
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> AuditLogListResponse:
    """Retorna a trilha completa de auditoria de todos os usuários (restrito a Admin)."""
    _check_log_access(user, db=db)

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
        default=False, description="Se True, inclui também os logs internos de gatilhos SQL"
    ),
    email: Optional[str] = Query(default=None, description="Filtrar por e-mail de usuário"),
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Retorna a linha do tempo de TODOS os usuários para o painel de Administrador.
    Por padrão oculta os logs redundantes de `SQL_TRIGGER` para focar nas ações reais do site.
    """
    _check_log_access(user, db=db)

    query = db.query(AuditLog)
    if not incluir_triggers_sql:
        query = query.filter(AuditLog.origem_registro != "SQL_TRIGGER")
    if email:
        query = query.filter(AuditLog.usuario_email.ilike(f"%{email.strip()}%"))

    rows = query.order_by(AuditLog.data_hora_utc.desc()).limit(limit).all()

    timeline = [
        {
            "log_id": r.id,
            "quando_fez": format_br_datetime(r.data_hora_local),
            "quando_iso": r.data_hora_local,
            "quem_fez": f"{r.usuario_nome} ({r.usuario_email})",
            "quem_nome": r.usuario_nome,
            "quem_email": r.usuario_email,
            "o_que_fez": r.resumo_humano,
            "acao": r.acao,
            "modulo": r.categoria_evento,
            "severidade": r.severidade,
            "ip": r.ip_origem,
            "origem": r.origem_registro,
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
    metodo: Optional[str] = Query(default=None),
    status_code: Optional[int] = Query(default=None),
    rota: Optional[str] = Query(default=None),
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> AccessLogListResponse:
    """Lista todas as requisições HTTP recebidas pela API com latência em ms."""
    _check_log_access(user, db=db)

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
                quando_brasilia=format_br_datetime(r.data_hora_local),
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
    _check_log_access(user, db=db)

    total_audit = (
        db.query(func.count(AuditLog.id))
        .filter(AuditLog.origem_registro != "SQL_TRIGGER")
        .scalar()
        or 0
    )
    total_sql_triggers = (
        db.query(func.count(AuditLog.id))
        .filter(AuditLog.origem_registro == "SQL_TRIGGER")
        .scalar()
        or 0
    )
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
    top_actors = (
        db.query(
            AuditLog.usuario_email,
            AuditLog.usuario_nome,
            func.count(AuditLog.id).label("total"),
        )
        .filter(AuditLog.origem_registro != "SQL_TRIGGER")
        .group_by(AuditLog.usuario_email, AuditLog.usuario_nome)
        .order_by(text("total DESC"))
        .limit(10)
        .all()
    )
    avg_latency = db.query(func.avg(AccessLog.tempo_resposta_ms)).scalar() or 0.0

    return {
        "ok": True,
        "total_audit_events": total_audit,
        "total_sql_trigger_events": total_sql_triggers,
        "total_http_requests": total_access,
        "average_http_latency_ms": round(float(avg_latency), 2),
        "events_by_category": {cat: count for cat, count in by_category},
        "events_by_severity": {sev: count for sev, count in by_severity},
        "most_active_users": [
            {"email": email, "name": name, "actions_count": count}
            for email, name, count in top_actors
        ],
    }


@router.get("/export")
def export_audit_logs(
    format: str = Query(default="csv", description="'csv' ou 'json'"),
    incluir_triggers_sql: bool = Query(default=False),
    limit: int = Query(default=2000, ge=1, le=10000),
    token: Optional[str] = Query(default=None),
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> Response:
    """Exporta os logs de auditoria em formato CSV (pronto para Excel pt-BR) ou JSON."""
    _check_log_access(user, db=db, token_query=token)

    query = db.query(AuditLog)
    if not incluir_triggers_sql:
        query = query.filter(AuditLog.origem_registro != "SQL_TRIGGER")
    rows = query.order_by(AuditLog.data_hora_utc.desc()).limit(limit).all()

    if format.lower() == "json":
        payload = [_row_to_audit_item(r).model_dump() for r in rows]
        return Response(
            content=json.dumps(payload, ensure_ascii=False, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": 'attachment; filename="nexo_audit_logs.json"'},
        )

    csv_bytes = _build_csv_bytes(rows)
    return Response(
        content=csv_bytes,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="nexo_audit_logs.csv"'},
    )


@router.post("/send-email")
def send_logs_excel_by_email(
    payload: SendLogsEmailRequest,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
    audit: AuditContext = Depends(get_audit_context),
) -> Dict[str, Any]:
    """
    Gera a planilha Excel (.csv) com todos os logs de auditoria e envia por e-mail (Gmail)
    para o endereço solicitado pelo Administrador.
    """
    admin_user = _check_log_access(user, db=db)

    query = db.query(AuditLog)
    if not payload.incluir_triggers_sql:
        query = query.filter(AuditLog.origem_registro != "SQL_TRIGGER")
    rows = query.order_by(AuditLog.data_hora_utc.desc()).limit(2000).all()

    csv_bytes = _build_csv_bytes(rows)
    email_res = send_audit_logs_excel_email(
        to_email=payload.to_email,
        admin_name=admin_user.nome,
        csv_bytes=csv_bytes,
        total_events=len(rows),
    )

    record_audit_event(
        db,
        action="AUDIT_LOGS_EMAILED_EXCEL",
        category="REPORT",
        severity="INFO",
        entity_affected="audit_logs",
        actor_id=admin_user.id,
        actor_email=admin_user.email,
        actor_name=admin_user.nome,
        ip_address=audit.ip_address,
        user_agent=audit.user_agent,
        http_method=audit.http_method,
        http_route=audit.http_route,
        request_id=audit.request_id,
        summary=(
            f"Administrador '{admin_user.nome}' enviou a planilha Excel com {len(rows)} logs "
            f"para o e-mail {payload.to_email}."
        ),
        after_data={
            "to_email": payload.to_email,
            "events_exported": len(rows),
            "sent_via_smtp": email_res["sent_via_smtp"],
        },
    )

    return {
        "ok": True,
        "to_email": payload.to_email,
        "events_count": len(rows),
        "sent_via_smtp": email_res["sent_via_smtp"],
        "smtp_error": email_res["smtp_error"],
        "message": (
            f"Planilha Excel enviada com sucesso para o Gmail {payload.to_email}!"
            if email_res["sent_via_smtp"]
            else f"Planilha preparada e registrada na Caixa de Saída para {payload.to_email} (configure sua Senha de App do Gmail no botão 'Configurar Gmail' para envio SMTP externo)."
        ),
    }


@router.get("/smtp-config")
def read_smtp_settings(
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Retorna o status da configuração SMTP do Gmail e os últimos e-mails na Caixa de Saída."""
    _check_log_access(user, db=db)
    cfg = get_smtp_config()
    return {
        "ok": True,
        "smtp_user": cfg.get("user", ""),
        "default_to": cfg.get("default_to", ""),
        "is_configured": bool(cfg.get("user") and cfg.get("password")),
        "outbox": list_outbox_emails(limit=20),
    }


@router.post("/smtp-config")
def update_smtp_settings(
    payload: SmtpConfigPayload,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
    audit: AuditContext = Depends(get_audit_context),
) -> Dict[str, Any]:
    """Configura em tempo real o Gmail e a Senha de App para envio real de e-mails e planilhas."""
    admin_user = _check_log_access(user, db=db)
    saved = save_smtp_config(
        user=payload.gmail_user,
        password=payload.gmail_app_password,
        default_to=payload.default_to,
    )
    record_audit_event(
        db,
        action="SMTP_GMAIL_CONFIG_UPDATED",
        category="SYSTEM",
        severity="INFO",
        entity_affected="smtp_config",
        actor_id=admin_user.id,
        actor_email=admin_user.email,
        actor_name=admin_user.nome,
        ip_address=audit.ip_address,
        user_agent=audit.user_agent,
        http_method=audit.http_method,
        http_route=audit.http_route,
        request_id=audit.request_id,
        summary=f"Administrador '{admin_user.nome}' configurou a conta Gmail SMTP ({payload.gmail_user}).",
    )
    return {
        "ok": True,
        "message": f"Conta Gmail ({payload.gmail_user}) configurada com sucesso para disparo de e-mails!",
        "config": saved,
    }


@router.post("/frontend-event", status_code=status.HTTP_201_CREATED)
def log_frontend_event(
    payload: FrontendEventPayload,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
    audit: AuditContext = Depends(get_audit_context),
) -> Dict[str, Any]:
    """Recebe eventos diretamente do Front-End e grava na trilha central `audit_logs`."""
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
