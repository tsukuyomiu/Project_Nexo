"""
Rotas de Autenticação e Segurança (`/api/v1/auth`):
- POST `/signup`: Criação de nova conta ("Faça parte da Nexo")
- POST `/login`: Autenticação com emissão de JWT e registro de sessão
- POST `/logout`: Revogação do token JWT atual
- POST `/forgot-password`: Geração de código de segurança de 6 dígitos (Etapa 1)
- POST `/reset-password`: Validação do código e redefinição de senha (Etapa 2)
- POST `/change-password`: Troca de senha do usuário logado (`/perfil`)
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any, Dict

from fastapi import APIRouter, Depends, Request, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.api.deps import (
    AuditContext,
    bearer_scheme,
    get_audit_context,
    get_current_user,
)
from app.core.audit_logger import record_audit_event
from app.core.config import settings
from app.core.exceptions import NexoException
from app.core.security import (
    create_access_token,
    decode_access_token,
    generate_reset_code,
    generate_uuid,
    hash_password,
    hash_reset_code,
    now_utc,
    now_utc_iso,
    verify_password,
)
from app.db.models import PasswordResetCode, SessionToken, User, UserProfilePreference
from app.db.session import get_db
from app.schemas.auth import (
    AuthUserSummary,
    ChangePasswordRequest,
    ChangePasswordResponse,
    ForgotPasswordRequest,
    LoginRequest,
    ResetPasswordRequest,
    SignupRequest,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["Autenticação & Segurança"])


@router.post("/signup", status_code=status.HTTP_201_CREATED, response_model=TokenResponse)
def signup(
    payload: SignupRequest,
    db: Session = Depends(get_db),
    audit: AuditContext = Depends(get_audit_context),
) -> TokenResponse:
    """Cadastra um novo usuário no Nexo, cria seu perfil padrão e já retorna a sessão autenticada."""
    email_norm = payload.email.strip().lower()
    if payload.confirm is not None and payload.confirm != payload.password:
        raise NexoException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="As senhas não coincidem.",
            error_code="PASSWORD_MISMATCH",
        )

    existing = db.query(User).filter(User.email == email_norm).first()
    if existing:
        record_audit_event(
            db,
            action="USER_SIGNUP_DUPLICATE_EMAIL",
            category="AUTH",
            severity="WARNING",
            entity_affected="usuarios",
            actor_email=email_norm,
            actor_name=payload.name,
            ip_address=audit.ip_address,
            user_agent=audit.user_agent,
            http_method=audit.http_method,
            http_route=audit.http_route,
            request_id=audit.request_id,
            summary=f"Tentativa de cadastro com e-mail já existente: {email_norm} (IP: {audit.ip_address}).",
        )
        raise NexoException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este e-mail já está cadastrado na Nexo.",
            error_code="EMAIL_ALREADY_EXISTS",
        )

    ts = now_utc_iso()
    user_id = generate_uuid()
    new_user = User(
        id=user_id,
        nome=payload.name.strip(),
        email=email_norm,
        senha_hash=hash_password(payload.password),
        role="user",
        ativo=1,
        termos_aceitos=1 if payload.terms else 0,
        termos_aceitos_em=ts,
        ultimo_login_em=ts,
        criado_em=ts,
        atualizado_em=ts,
    )
    db.add(new_user)
    db.flush()

    profile = UserProfilePreference(
        usuario_id=user_id,
        telefone="",
        data_nascimento="",
        endereco="",
        moeda_preferida="BRL",
        dois_fatores_ativo=0,
        atualizado_em=ts,
    )
    db.add(profile)

    token_data = create_access_token(subject=user_id, email=email_norm, role="user")
    session_row = SessionToken(
        id=generate_uuid(),
        usuario_id=user_id,
        token_jti=token_data["jti"],
        ip_origem=audit.ip_address,
        user_agent=audit.user_agent,
        revogado=0,
        expira_em=token_data["expires_at"],
        criado_em=ts,
    )
    db.add(session_row)
    db.commit()

    record_audit_event(
        db,
        action="USER_SIGNUP_SUCCESS",
        category="AUTH",
        severity="INFO",
        entity_affected="usuarios",
        entity_id=user_id,
        actor_id=user_id,
        actor_email=email_norm,
        actor_name=new_user.nome,
        ip_address=audit.ip_address,
        user_agent=audit.user_agent,
        http_method=audit.http_method,
        http_route=audit.http_route,
        request_id=audit.request_id,
        summary=f"Novo usuário cadastrado: '{new_user.nome}' ({email_norm}) a partir do IP {audit.ip_address}.",
        after_data={
            "id": user_id,
            "nome": new_user.nome,
            "email": email_norm,
            "role": "user",
            "termos_aceitos": True,
        },
    )

    return TokenResponse(
        ok=True,
        access_token=token_data["access_token"],
        expires_at=token_data["expires_at"],
        user=AuthUserSummary(
            id=user_id,
            name=new_user.nome,
            email=email_norm,
            role=new_user.role,
            currency="BRL",
        ),
    )


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
    audit: AuditContext = Depends(get_audit_context),
) -> TokenResponse:
    """Autentica um usuário com e-mail e senha e registra o evento de login."""
    email_norm = payload.email.strip().lower()
    user = db.query(User).filter(User.email == email_norm).first()

    if not user or not verify_password(payload.password, user.senha_hash):
        record_audit_event(
            db,
            action="USER_LOGIN_FAILED",
            category="AUTH",
            severity="WARNING",
            entity_affected="usuarios",
            entity_id=user.id if user else None,
            actor_id=user.id if user else None,
            actor_email=email_norm,
            actor_name=user.nome if user else "Tentativa de Login",
            ip_address=audit.ip_address,
            user_agent=audit.user_agent,
            http_method=audit.http_method,
            http_route=audit.http_route,
            request_id=audit.request_id,
            summary=f"Falha de login para o e-mail '{email_norm}' (credenciais inválidas) via IP {audit.ip_address}.",
        )
        raise NexoException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha inválidos.",
            error_code="INVALID_CREDENTIALS",
        )

    if not user.ativo:
        record_audit_event(
            db,
            action="USER_LOGIN_BLOCKED_INACTIVE",
            category="SECURITY",
            severity="WARNING",
            entity_affected="usuarios",
            entity_id=user.id,
            actor_id=user.id,
            actor_email=user.email,
            actor_name=user.nome,
            ip_address=audit.ip_address,
            user_agent=audit.user_agent,
            http_method=audit.http_method,
            http_route=audit.http_route,
            request_id=audit.request_id,
            summary=f"Tentativa de login em conta inativa: '{user.nome}' ({user.email}).",
        )
        raise NexoException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta conta está desativada.",
            error_code="ACCOUNT_DISABLED",
        )

    ts = now_utc_iso()
    user.ultimo_login_em = ts
    user.atualizado_em = ts

    token_data = create_access_token(subject=user.id, email=user.email, role=user.role)
    session_row = SessionToken(
        id=generate_uuid(),
        usuario_id=user.id,
        token_jti=token_data["jti"],
        ip_origem=audit.ip_address,
        user_agent=audit.user_agent,
        revogado=0,
        expira_em=token_data["expires_at"],
        criado_em=ts,
    )
    db.add(session_row)
    db.commit()

    request.state.user_id = user.id
    request.state.user_email = user.email

    currency = user.profile.moeda_preferida if user.profile else "BRL"

    record_audit_event(
        db,
        action="USER_LOGIN_SUCCESS",
        category="AUTH",
        severity="INFO",
        entity_affected="sessoes_tokens",
        entity_id=session_row.id,
        actor_id=user.id,
        actor_email=user.email,
        actor_name=user.nome,
        ip_address=audit.ip_address,
        user_agent=audit.user_agent,
        http_method=audit.http_method,
        http_route=audit.http_route,
        request_id=audit.request_id,
        summary=f"Login realizado com sucesso por '{user.nome}' ({user.email}) via IP {audit.ip_address}.",
        after_data={"session_id": session_row.id, "jti": token_data["jti"], "expires_at": token_data["expires_at"]},
    )

    return TokenResponse(
        ok=True,
        access_token=token_data["access_token"],
        expires_at=token_data["expires_at"],
        user=AuthUserSummary(
            id=user.id,
            name=user.nome,
            email=user.email,
            role=user.role,
            currency=currency,
        ),
    )


@router.post("/logout")
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    audit: AuditContext = Depends(get_audit_context),
) -> Dict[str, Any]:
    """Encerra a sessão atual revogando o JTI do token JWT no banco."""
    payload = decode_access_token(credentials.credentials) if credentials else None
    jti = payload.get("jti") if payload else None
    if jti:
        session_row = db.query(SessionToken).filter(SessionToken.token_jti == jti).first()
        if session_row:
            session_row.revogado = 1
            session_row.revogado_em = now_utc_iso()
            db.commit()

    record_audit_event(
        db,
        action="USER_LOGOUT",
        category="AUTH",
        severity="INFO",
        entity_affected="sessoes_tokens",
        entity_id=jti,
        actor_id=user.id,
        actor_email=user.email,
        actor_name=user.nome,
        ip_address=audit.ip_address,
        user_agent=audit.user_agent,
        http_method=audit.http_method,
        http_route=audit.http_route,
        request_id=audit.request_id,
        summary=f"Usuário '{user.nome}' ({user.email}) encerrou a sessão (Logout).",
    )
    return {"ok": True, "message": "Sessão encerrada com sucesso."}


@router.post("/forgot-password")
def forgot_password(
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db),
    audit: AuditContext = Depends(get_audit_context),
) -> Dict[str, Any]:
    """
    Etapa 1 da Redefinição de Senha (`/redefinir-senha`):
    Gera um código de segurança de 6 dígitos com validade de 15 minutos.
    Em ambiente de desenvolvimento (`development`), retorna `dev_code` para facilitar testes.
    """
    email_norm = payload.email.strip().lower()
    user = db.query(User).filter(User.email == email_norm).first()

    if not user:
        record_audit_event(
            db,
            action="PASSWORD_RESET_UNKNOWN_EMAIL",
            category="SECURITY",
            severity="WARNING",
            entity_affected="codigos_recuperacao",
            actor_email=email_norm,
            ip_address=audit.ip_address,
            user_agent=audit.user_agent,
            http_method=audit.http_method,
            http_route=audit.http_route,
            request_id=audit.request_id,
            summary=f"Solicitação de recuperação de senha para e-mail não cadastrado: '{email_norm}'.",
        )
        # Resposta genérica para evitar enumeração de contas, mantendo UX amigável
        return {
            "ok": True,
            "message": f"Se o e-mail {email_norm} estiver cadastrado, um código de segurança foi enviado.",
        }

    code = generate_reset_code()
    expires = (now_utc() + timedelta(minutes=settings.NEXO_RESET_CODE_EXPIRE_MINUTES)).strftime(
        "%Y-%m-%dT%H:%M:%S.%f"
    )[:-3] + "Z"

    reset_entry = PasswordResetCode(
        id=generate_uuid(),
        usuario_id=user.id,
        email=email_norm,
        codigo_hash=hash_reset_code(email_norm, code),
        utilizado=0,
        tentativas=0,
        ip_solicitante=audit.ip_address,
        expira_em=expires,
        criado_em=now_utc_iso(),
    )
    db.add(reset_entry)
    db.commit()

    record_audit_event(
        db,
        action="PASSWORD_RESET_CODE_GENERATED",
        category="SECURITY",
        severity="INFO",
        entity_affected="codigos_recuperacao",
        entity_id=reset_entry.id,
        actor_id=user.id,
        actor_email=user.email,
        actor_name=user.nome,
        ip_address=audit.ip_address,
        user_agent=audit.user_agent,
        http_method=audit.http_method,
        http_route=audit.http_route,
        request_id=audit.request_id,
        summary=f"Código de recuperação de senha gerado para '{user.nome}' ({user.email}). Expira em {expires}.",
        after_data={"reset_request_id": reset_entry.id, "expires_at": expires},
    )

    resp: Dict[str, Any] = {
        "ok": True,
        "message": f"Código de segurança gerado e enviado para {email_norm}.",
        "expires_at": expires,
    }
    if settings.NEXO_ENV == "development":
        resp["dev_code"] = code
    return resp


@router.post("/reset-password")
def reset_password(
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
    audit: AuditContext = Depends(get_audit_context),
) -> Dict[str, Any]:
    """
    Etapa 2 da Redefinição de Senha (`/redefinir-senha`):
    Valida o código de 6 dígitos e atualiza a senha do usuário, revogando sessões antigas.
    """
    email_norm = payload.email.strip().lower()
    if payload.confirm_password is not None and payload.confirm_password != payload.new_password:
        raise NexoException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="As senhas não coincidem.",
            error_code="PASSWORD_MISMATCH",
        )

    user = db.query(User).filter(User.email == email_norm).first()
    if not user:
        raise NexoException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código inválido ou expirado.",
            error_code="INVALID_RESET_CODE",
        )

    latest_code = (
        db.query(PasswordResetCode)
        .filter(
            PasswordResetCode.usuario_id == user.id,
            PasswordResetCode.utilizado == 0,
        )
        .order_by(PasswordResetCode.criado_em.desc())
        .first()
    )

    expected_hash = hash_reset_code(email_norm, payload.code)
    now_str = now_utc_iso()

    if not latest_code or latest_code.expira_em < now_str or latest_code.codigo_hash != expected_hash:
        if latest_code:
            latest_code.tentativas += 1
            db.commit()
        record_audit_event(
            db,
            action="PASSWORD_RESET_CODE_INVALID",
            category="SECURITY",
            severity="WARNING",
            entity_affected="codigos_recuperacao",
            entity_id=latest_code.id if latest_code else None,
            actor_id=user.id,
            actor_email=user.email,
            actor_name=user.nome,
            ip_address=audit.ip_address,
            user_agent=audit.user_agent,
            http_method=audit.http_method,
            http_route=audit.http_route,
            request_id=audit.request_id,
            summary=f"Tentativa inválida de código de recuperação de senha para '{user.email}'.",
        )
        raise NexoException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código de segurança inválido ou expirado.",
            error_code="INVALID_RESET_CODE",
        )

    latest_code.utilizado = 1
    latest_code.utilizado_em = now_str
    user.senha_hash = hash_password(payload.new_password)
    user.atualizado_em = now_str

    # Revoga todas as sessões anteriores por segurança
    db.query(SessionToken).filter(
        SessionToken.usuario_id == user.id, SessionToken.revogado == 0
    ).update({"revogado": 1, "revogado_em": now_str})
    db.commit()

    record_audit_event(
        db,
        action="PASSWORD_RESET_COMPLETED",
        category="SECURITY",
        severity="WARNING",
        entity_affected="usuarios",
        entity_id=user.id,
        actor_id=user.id,
        actor_email=user.email,
        actor_name=user.nome,
        ip_address=audit.ip_address,
        user_agent=audit.user_agent,
        http_method=audit.http_method,
        http_route=audit.http_route,
        request_id=audit.request_id,
        summary=f"Senha redefinida com sucesso via código de segurança por '{user.nome}' ({user.email}).",
    )

    return {"ok": True, "message": "Senha redefinida com sucesso! Faça seu login."}


@router.post("/change-password", response_model=ChangePasswordResponse)
def change_password_endpoint(
    payload: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    audit: AuditContext = Depends(get_audit_context),
) -> ChangePasswordResponse:
    """
    Altera a senha do usuário autenticado (integração direta com `frontend/src/lib/change-password.ts`).
    """
    if not verify_password(payload.current, user.senha_hash):
        record_audit_event(
            db,
            action="PASSWORD_CHANGE_FAILED_WRONG_CURRENT",
            category="SECURITY",
            severity="WARNING",
            entity_affected="usuarios",
            entity_id=user.id,
            actor_id=user.id,
            actor_email=user.email,
            actor_name=user.nome,
            ip_address=audit.ip_address,
            user_agent=audit.user_agent,
            http_method=audit.http_method,
            http_route=audit.http_route,
            request_id=audit.request_id,
            summary=f"Falha ao alterar senha de '{user.nome}' ({user.email}): senha atual incorreta.",
        )
        raise NexoException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A senha atual informada está incorreta.",
            error_code="WRONG_CURRENT_PASSWORD",
        )

    if payload.current == payload.next:
        raise NexoException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A nova senha deve ser diferente da atual.",
            error_code="SAME_PASSWORD",
        )

    if payload.confirm is not None and payload.confirm != payload.next:
        raise NexoException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="As senhas não coincidem.",
            error_code="PASSWORD_MISMATCH",
        )

    user.senha_hash = hash_password(payload.next)
    user.atualizado_em = now_utc_iso()
    db.commit()

    record_audit_event(
        db,
        action="PASSWORD_CHANGED_SUCCESS",
        category="SECURITY",
        severity="WARNING",
        entity_affected="usuarios",
        entity_id=user.id,
        actor_id=user.id,
        actor_email=user.email,
        actor_name=user.nome,
        ip_address=audit.ip_address,
        user_agent=audit.user_agent,
        http_method=audit.http_method,
        http_route=audit.http_route,
        request_id=audit.request_id,
        summary=f"Usuário '{user.nome}' ({user.email}) alterou sua senha de acesso na tela de Perfil.",
    )

    return ChangePasswordResponse(ok=True, message="Senha alterada com sucesso!")
