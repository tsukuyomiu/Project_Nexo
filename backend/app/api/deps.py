"""
Injeção de Dependências do FastAPI:
- Extração de Usuário Autenticado (JWT Bearer)
- Construção automática do Contexto de Auditoria (Quem, IP, User-Agent, Rota, Request ID)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import NexoException
from app.core.security import decode_access_token
from app.db.models import SessionToken, User
from app.db.session import get_db

bearer_scheme = HTTPBearer(auto_error=False)


def extract_client_ip(request: Request) -> str:
    """Extrai o IP real do cliente considerando proxies reversos."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    if request.client and request.client.host:
        return request.client.host
    return "127.0.0.1"


@dataclass
class AuditContext:
    """Contexto completo da requisição atual para alimentar o motor de logs."""

    request_id: str
    ip_address: str
    user_agent: str
    http_method: str
    http_route: str
    actor_id: Optional[str] = None
    actor_email: str = "anonimo@nexo.local"
    actor_name: str = "Visitante / Não Autenticado"


def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Tenta resolver o usuário logado a partir do header `Authorization: Bearer <token>`.
    Se não houver token válido, retorna `None` sem lançar erro.
    """
    if not credentials or not credentials.credentials:
        return None

    payload = decode_access_token(credentials.credentials)
    if not payload:
        return None

    user_id = payload.get("sub")
    jti = payload.get("jti")
    if not user_id:
        return None

    # Verifica se a sessão foi revogada no banco
    if jti:
        session_record = (
            db.query(SessionToken)
            .filter(SessionToken.token_jti == jti, SessionToken.revogado == 1)
            .first()
        )
        if session_record:
            return None

    user = db.query(User).filter(User.id == user_id, User.ativo == 1).first()
    if user:
        request.state.user_id = user.id
        request.state.user_email = user.email
        request.state.user_name = user.nome
    return user


def get_current_user(
    user: Optional[User] = Depends(get_current_user_optional),
) -> User:
    """Exige um usuário autenticado válido, retornando 401 caso contrário."""
    if not user:
        raise NexoException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão inválida ou expirada. Faça login novamente.",
            error_code="UNAUTHORIZED",
        )
    return user


def get_audit_context(
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional),
) -> AuditContext:
    """Constrói o contexto de auditoria enriquecido com os dados do usuário e da requisição."""
    req_id = getattr(request.state, "request_id", "req-internal")
    ip_addr = extract_client_ip(request)
    ua = request.headers.get("user-agent", "Unknown-Client")
    return AuditContext(
        request_id=req_id,
        ip_address=ip_addr,
        user_agent=ua,
        http_method=request.method,
        http_route=request.url.path,
        actor_id=user.id if user else None,
        actor_email=user.email if user else "anonimo@nexo.local",
        actor_name=user.nome if user else "Visitante / Não Autenticado",
    )
