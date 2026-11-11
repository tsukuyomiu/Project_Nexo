"""
Motor Central de Auditoria 360° e Logs Estruturados do Projeto Nexo (Python + SQL).

Responsável por:
1. Sanitizar automaticamente qualquer dado sensível (senhas, tokens, códigos).
2. Calcular o Hash SHA-256 encadeado (Hash Chain) para prova pericial de integridade.
3. Gravar cada evento simultaneamente na tabela SQL `audit_logs` e no arquivo
   estruturado `backend/logs/nexo_audit.jsonl`.
4. Gravar o tráfego HTTP completo na tabela SQL `access_logs` e no arquivo
   `backend/logs/nexo_access.jsonl`.
"""

from __future__ import annotations

import hashlib
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import generate_uuid, now_brazil_iso, now_utc_iso

# Campos que NUNCA devem ser gravados em texto puro nos logs
SENSITIVE_KEYS = {
    "password",
    "senha",
    "senha_hash",
    "current_password",
    "new_password",
    "confirm",
    "confirm_password",
    "current",
    "next",
    "pass",
    "token",
    "access_token",
    "authorization",
    "code",
    "codigo",
    "codigo_hash",
    "secret",
}


def _setup_file_logger(name: str, file_path: str) -> logging.Logger:
    """Configura um logger com rotação automática (10 MB por arquivo, até 5 backups)."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if not logger.handlers:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(
            filename=str(path),
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
    return logger


audit_file_logger = _setup_file_logger("nexo.audit", settings.NEXO_AUDIT_LOG_FILE)
access_file_logger = _setup_file_logger("nexo.access", settings.NEXO_ACCESS_LOG_FILE)
error_file_logger = _setup_file_logger("nexo.error", settings.NEXO_ERROR_LOG_FILE)


def sanitize_payload(data: Any) -> Any:
    """
    Percorre dicionários e listas recursivamente mascarando qualquer chave sensível
    com `[REDACTED]` para proteger credenciais nos logs.
    """
    if data is None:
        return None
    if isinstance(data, dict):
        cleaned: Dict[str, Any] = {}
        for k, v in data.items():
            key_lower = str(k).strip().lower()
            if key_lower in SENSITIVE_KEYS or "password" in key_lower or "senha" in key_lower:
                cleaned[k] = "[REDACTED]"
            else:
                cleaned[k] = sanitize_payload(v)
        return cleaned
    if isinstance(data, list):
        return [sanitize_payload(item) for item in data]
    return data


def _to_json_str(data: Any) -> Optional[str]:
    """Serializa o payload sanitizado para string JSON compacta."""
    if data is None:
        return None
    sanitized = sanitize_payload(data)
    return json.dumps(sanitized, ensure_ascii=False, default=str)


def compute_integrity_hash(
    previous_hash: Optional[str],
    timestamp_utc: str,
    actor_email: str,
    action: str,
    entity_affected: str,
    entity_id: Optional[str],
    before_json: Optional[str],
    after_json: Optional[str],
) -> str:
    """
    Calcula um hash SHA-256 encadeado (blockchain-style) combinando o hash do
    último evento com os dados do evento atual.
    """
    prev = previous_hash or "GENESIS_NEXO_AUDIT_CHAIN_0000000000000000"
    canonical = (
        f"{prev}|{timestamp_utc}|{actor_email}|{action}|"
        f"{entity_affected}|{entity_id or ''}|{before_json or ''}|{after_json or ''}"
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def record_audit_event(
    db: Session,
    *,
    action: str,
    category: str,
    entity_affected: str,
    summary: str,
    entity_id: Optional[str] = None,
    severity: str = "INFO",
    actor_id: Optional[str] = None,
    actor_email: str = "anonimo@nexo.local",
    actor_name: str = "Visitante / Sistema",
    ip_address: str = "127.0.0.1",
    user_agent: str = "Unknown",
    http_method: Optional[str] = None,
    http_route: Optional[str] = None,
    request_id: Optional[str] = None,
    before_data: Optional[Dict[str, Any]] = None,
    after_data: Optional[Dict[str, Any]] = None,
    extra_metadata: Optional[Dict[str, Any]] = None,
    origin: str = "API_PYTHON",
) -> Dict[str, Any]:
    """
    Registra um evento completo de auditoria no Banco SQL (`audit_logs`) e no
    arquivo rotativo `backend/logs/nexo_audit.jsonl`.
    Retorna o dicionário completo do evento registrado.
    """
    log_id = generate_uuid()
    ts_utc = now_utc_iso()
    ts_local = now_brazil_iso()

    before_json = _to_json_str(before_data)
    after_json = _to_json_str(after_data)
    meta_json = _to_json_str(extra_metadata)

    # Busca o último hash da cadeia no banco para encadeamento criptográfico
    prev_hash: Optional[str] = None
    try:
        row = db.execute(
            text("SELECT hash_integridade FROM audit_logs ORDER BY data_hora_utc DESC LIMIT 1")
        ).fetchone()
        if row:
            prev_hash = row[0]
    except Exception:
        prev_hash = None

    integrity_hash = compute_integrity_hash(
        previous_hash=prev_hash,
        timestamp_utc=ts_utc,
        actor_email=actor_email,
        action=action,
        entity_affected=entity_affected,
        entity_id=entity_id,
        before_json=before_json,
        after_json=after_json,
    )

    event_record = {
        "id": log_id,
        "data_hora_utc": ts_utc,
        "data_hora_local": ts_local,
        "usuario_id": actor_id,
        "usuario_email": actor_email or "anonimo@nexo.local",
        "usuario_nome": actor_name or "Visitante / Sistema",
        "ip_origem": ip_address or "127.0.0.1",
        "user_agent": user_agent or "Unknown",
        "metodo_http": http_method,
        "rota_http": http_route,
        "request_id": request_id,
        "acao": action,
        "categoria_evento": category,
        "severidade": severity,
        "entidade_afetada": entity_affected,
        "entidade_id": entity_id,
        "resumo_humano": summary,
        "dados_anteriores": sanitize_payload(before_data),
        "dados_novos": sanitize_payload(after_data),
        "metadados_extras": sanitize_payload(extra_metadata),
        "origem_registro": origin,
        "hash_anterior": prev_hash,
        "hash_integridade": integrity_hash,
    }

    # 1. Gravação no Banco SQL (audit_logs)
    try:
        db.execute(
            text(
                """
                INSERT INTO audit_logs (
                    id, data_hora_utc, data_hora_local,
                    usuario_id, usuario_email, usuario_nome,
                    ip_origem, user_agent, metodo_http, rota_http, request_id,
                    acao, categoria_evento, severidade,
                    entidade_afetada, entidade_id, resumo_humano,
                    dados_anteriores, dados_novos, metadados_extras,
                    origem_registro, hash_anterior, hash_integridade
                ) VALUES (
                    :id, :data_hora_utc, :data_hora_local,
                    :usuario_id, :usuario_email, :usuario_nome,
                    :ip_origem, :user_agent, :metodo_http, :rota_http, :request_id,
                    :acao, :categoria_evento, :severidade,
                    :entidade_afetada, :entidade_id, :resumo_humano,
                    :dados_anteriores, :dados_novos, :metadados_extras,
                    :origem_registro, :hash_anterior, :hash_integridade
                )
                """
            ),
            {
                **event_record,
                "dados_anteriores": before_json,
                "dados_novos": after_json,
                "metadados_extras": meta_json,
            },
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        error_file_logger.error(f"[{ts_local}] Falha ao gravar audit_log no SQL: {exc}")

    # 2. Gravação espelhada em arquivo JSONL (backend/logs/nexo_audit.jsonl)
    try:
        audit_file_logger.info(json.dumps(event_record, ensure_ascii=False, default=str))
    except Exception as exc:
        error_file_logger.error(f"[{ts_local}] Falha ao gravar audit_log em arquivo: {exc}")

    return event_record


def record_access_log(
    db: Session,
    *,
    request_id: str,
    http_method: str,
    route: str,
    status_code: int,
    response_time_ms: float,
    ip_address: str,
    user_agent: str,
    query_params: Optional[str] = None,
    user_id: Optional[str] = None,
    user_email: Optional[str] = None,
    error_detail: Optional[str] = None,
) -> None:
    """
    Registra os metadados de tráfego HTTP de cada requisição na tabela `access_logs`
    e no arquivo `backend/logs/nexo_access.jsonl`.
    """
    log_id = generate_uuid()
    ts_utc = now_utc_iso()
    ts_local = now_brazil_iso()

    access_record = {
        "id": log_id,
        "data_hora_utc": ts_utc,
        "data_hora_local": ts_local,
        "request_id": request_id,
        "usuario_id": user_id,
        "usuario_email": user_email,
        "metodo_http": http_method,
        "rota": route,
        "query_params": query_params,
        "status_code": status_code,
        "tempo_resposta_ms": round(response_time_ms, 2),
        "ip_origem": ip_address,
        "user_agent": user_agent,
        "erro_detalhe": error_detail,
    }

    try:
        db.execute(
            text(
                """
                INSERT INTO access_logs (
                    id, data_hora_utc, data_hora_local, request_id,
                    usuario_id, usuario_email, metodo_http, rota,
                    query_params, status_code, tempo_resposta_ms,
                    ip_origem, user_agent, erro_detalhe
                ) VALUES (
                    :id, :data_hora_utc, :data_hora_local, :request_id,
                    :usuario_id, :usuario_email, :metodo_http, :rota,
                    :query_params, :status_code, :tempo_resposta_ms,
                    :ip_origem, :user_agent, :erro_detalhe
                )
                """
            ),
            access_record,
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        error_file_logger.error(f"[{ts_local}] Falha ao gravar access_log no SQL: {exc}")

    try:
        access_file_logger.info(json.dumps(access_record, ensure_ascii=False, default=str))
    except Exception:
        pass
