"""
Schemas do Sistema de Auditoria 360° e Logs de Acesso.
Permitem consultar e receber em detalhes:
  - QUEM fez (usuário, e-mail, nome, IP, navegador)
  - QUANDO fez (horário de Brasília -03:00 e UTC)
  - O QUE fez (ação, resumo humano, antes e depois em JSON, hash SHA-256)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AuditLogItem(BaseModel):
    id: str
    quando_fez_brasilia: str = Field(..., description="Timestamp ISO no horário de Brasília (-03:00)")
    quando_fez_utc: str = Field(..., description="Timestamp ISO em UTC")
    quem_fez_id: Optional[str] = None
    quem_fez_nome: str
    quem_fez_email: str
    ip_origem: str
    user_agent: str
    metodo_http: Optional[str] = None
    rota_http: Optional[str] = None
    request_id: Optional[str] = None
    acao: str
    categoria_evento: str
    severidade: str
    entidade_afetada: str
    entidade_id: Optional[str] = None
    o_que_fez: str = Field(..., description="Resumo legível em português da ação realizada")
    dados_anteriores: Optional[Dict[str, Any]] = None
    dados_novos: Optional[Dict[str, Any]] = None
    metadados_extras: Optional[Dict[str, Any]] = None
    origem_registro: str
    hash_anterior: Optional[str] = None
    hash_integridade: str


class AuditLogListResponse(BaseModel):
    ok: bool = True
    total: int
    page: int
    page_size: int
    items: List[AuditLogItem]


class AccessLogItem(BaseModel):
    id: str
    quando_brasilia: str
    quando_utc: str
    request_id: str
    usuario_id: Optional[str] = None
    usuario_email: Optional[str] = None
    metodo_http: str
    rota: str
    query_params: Optional[str] = None
    status_code: int
    tempo_resposta_ms: float
    ip_origem: str
    user_agent: Optional[str] = None
    erro_detalhe: Optional[str] = None


class AccessLogListResponse(BaseModel):
    ok: bool = True
    total: int
    page: int
    page_size: int
    items: List[AccessLogItem]


class FrontendEventPayload(BaseModel):
    """Permite que o Front-End envie eventos de navegação, clique ou erro para o log central."""

    acao: str = Field(..., min_length=2, max_length=80, description="Ex: PAGE_VIEW, MODAL_OPENED, FILTER_APPLIED")
    entidade_afetada: str = Field(default="frontend_ui", max_length=60)
    entidade_id: Optional[str] = None
    resumo_humano: str = Field(..., min_length=3, max_length=500)
    severidade: str = Field(default="INFO")
    detalhes: Optional[Dict[str, Any]] = None
