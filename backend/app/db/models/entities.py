"""
Modelos ORM SQLAlchemy 2.0 mapeados 1:1 com os schemas SQL em `database/sql/`.
"""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.security import generate_uuid, now_brazil_iso, now_utc_iso
from app.db.session import Base


class User(Base):
    """Mapeamento da tabela `usuarios` (schema_usuarios.sql)."""

    __tablename__ = "usuarios"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    senha_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="user")
    ativo: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    termos_aceitos: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    termos_aceitos_em: Mapped[str] = mapped_column(String(40), nullable=False, default=now_utc_iso)
    ultimo_login_em: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    criado_em: Mapped[str] = mapped_column(String(40), nullable=False, default=now_utc_iso)
    atualizado_em: Mapped[str] = mapped_column(String(40), nullable=False, default=now_utc_iso)

    profile: Mapped[Optional["UserProfilePreference"]] = relationship(
        "UserProfilePreference",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    transactions: Mapped[List["TransactionModel"]] = relationship(
        "TransactionModel",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class UserProfilePreference(Base):
    """Mapeamento da tabela `perfis_preferencias` (schema_usuarios.sql)."""

    __tablename__ = "perfis_preferencias"

    usuario_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        primary_key=True,
    )
    telefone: Mapped[str] = mapped_column(String(25), nullable=False, default="")
    data_nascimento: Mapped[str] = mapped_column(String(10), nullable=False, default="")
    endereco: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    moeda_preferida: Mapped[str] = mapped_column(String(3), nullable=False, default="BRL")
    dois_fatores_ativo: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default="")
    atualizado_em: Mapped[str] = mapped_column(String(40), nullable=False, default=now_utc_iso)

    user: Mapped["User"] = relationship("User", back_populates="profile")


class SessionToken(Base):
    """Mapeamento da tabela `sessoes_tokens` (schema_usuarios.sql)."""

    __tablename__ = "sessoes_tokens"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    usuario_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_jti: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    ip_origem: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    revogado: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    revogado_em: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    expira_em: Mapped[str] = mapped_column(String(40), nullable=False)
    criado_em: Mapped[str] = mapped_column(String(40), nullable=False, default=now_utc_iso)


class PasswordResetCode(Base):
    """Mapeamento da tabela `codigos_recuperacao` (schema_usuarios.sql)."""

    __tablename__ = "codigos_recuperacao"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    usuario_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    codigo_hash: Mapped[str] = mapped_column(Text, nullable=False)
    utilizado: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tentativas: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ip_solicitante: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    expira_em: Mapped[str] = mapped_column(String(40), nullable=False)
    utilizado_em: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    criado_em: Mapped[str] = mapped_column(String(40), nullable=False, default=now_utc_iso)


class TransactionModel(Base):
    """Mapeamento da tabela `lancamentos` (schema_projetos.sql)."""

    __tablename__ = "lancamentos"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    usuario_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    descricao: Mapped[str] = mapped_column(String(100), nullable=False)
    valor: Mapped[float] = mapped_column(Float, nullable=False)
    data_lancamento: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    categoria: Mapped[str] = mapped_column(String(60), nullable=False)
    tipo: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(String(15), nullable=False, default="confirmado")
    criado_em: Mapped[str] = mapped_column(String(40), nullable=False, default=now_utc_iso)
    atualizado_em: Mapped[str] = mapped_column(String(40), nullable=False, default=now_utc_iso)

    user: Mapped["User"] = relationship("User", back_populates="transactions")


class ExportedReport(Base):
    """Mapeamento da tabela `relatorios_exportados` (schema_relatorios.sql)."""

    __tablename__ = "relatorios_exportados"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    usuario_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    titulo: Mapped[str] = mapped_column(String(150), nullable=False)
    tipo_relatorio: Mapped[str] = mapped_column(String(40), nullable=False)
    periodo_referencia: Mapped[str] = mapped_column(String(20), nullable=False)
    formato: Mapped[str] = mapped_column(String(10), nullable=False, default="JSON")
    filtros_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    resumo_metricas: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    hash_integridade: Mapped[str] = mapped_column(String(64), nullable=False)
    ip_solicitante: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    criado_em: Mapped[str] = mapped_column(String(40), nullable=False, default=now_utc_iso)


class AuditLog(Base):
    """Mapeamento da tabela imutável `audit_logs` (schema_logs.sql)."""

    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    data_hora_utc: Mapped[str] = mapped_column(String(40), nullable=False, default=now_utc_iso)
    data_hora_local: Mapped[str] = mapped_column(String(40), nullable=False, default=now_brazil_iso)
    usuario_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    usuario_email: Mapped[str] = mapped_column(String(255), nullable=False, default="anonimo@nexo.local")
    usuario_nome: Mapped[str] = mapped_column(String(100), nullable=False, default="Visitante / Sistema")
    ip_origem: Mapped[str] = mapped_column(String(64), nullable=False, default="127.0.0.1")
    user_agent: Mapped[str] = mapped_column(Text, nullable=False, default="Unknown")
    metodo_http: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    rota_http: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    request_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    acao: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    categoria_evento: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    severidade: Mapped[str] = mapped_column(String(15), nullable=False, default="INFO")
    entidade_afetada: Mapped[str] = mapped_column(String(60), nullable=False)
    entidade_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    resumo_humano: Mapped[str] = mapped_column(Text, nullable=False)
    dados_anteriores: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    dados_novos: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadados_extras: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    origem_registro: Mapped[str] = mapped_column(String(30), nullable=False, default="API_PYTHON")
    hash_anterior: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    hash_integridade: Mapped[str] = mapped_column(String(64), nullable=False)


class AccessLog(Base):
    """Mapeamento da tabela `access_logs` (schema_logs.sql)."""

    __tablename__ = "access_logs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=generate_uuid)
    data_hora_utc: Mapped[str] = mapped_column(String(40), nullable=False, default=now_utc_iso)
    data_hora_local: Mapped[str] = mapped_column(String(40), nullable=False, default=now_brazil_iso)
    request_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    usuario_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    usuario_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    metodo_http: Mapped[str] = mapped_column(String(10), nullable=False)
    rota: Mapped[str] = mapped_column(Text, nullable=False)
    query_params: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    tempo_resposta_ms: Mapped[float] = mapped_column(Float, nullable=False)
    ip_origem: Mapped[str] = mapped_column(String(64), nullable=False)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    erro_detalhe: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
