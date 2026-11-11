"""
Rotas de Autenticação, OAuth (Google/Apple), 2FA e Segurança (`/api/v1/auth`):
- POST `/signup`: Criação de nova conta (Usuário Comum ou Administrador com Chave Mestre) + Disparo de E-mail Gmail
- POST `/login`: Autenticação com suporte a desafio 2FA (Autenticação em Duas Etapas)
- POST `/verify-2fa`: Validação do código de 6 dígitos da Autenticação em Duas Etapas
- POST `/oauth`: Login/Cadastro integrado com Google e Apple
- POST `/logout`: Revogação do token JWT atual
- POST `/forgot-password`: Geração e envio por e-mail de código de 6 dígitos (Etapa 1)
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
from app.core.email_service import (
    save_smtp_config,
    send_2fa_code_email,
    send_nexo_email,
    send_welcome_confirmation_email,
)
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
    ConnectGmailResendRequest,
    ForgotPasswordRequest,
    LoginRequest,
    OAuthLoginRequest,
    ResetPasswordRequest,
    SignupRequest,
    TokenResponse,
    Verify2FARequest,
)

router = APIRouter(prefix="/auth", tags=["Autenticação & Segurança"])

VALID_ADMIN_CODES = {
    settings.NEXO_ADMIN_MASTER_CODE.upper(),
    "NEXO-ADMIN",
    "NEXO2026",
    "ADMIN",
}


def _resolve_requested_role(email_norm: str, account_type: str = "user", admin_code: str | None = None) -> str:
    """
    Segurança e Governança de Perfis:
    - APENAS e-mails corporativos estritamente autorizados no servidor (ex: ggnonato@gmail.com ou admin@nexo.com)
      podem possuir perfil de Administrador (`admin`).
    - Qualquer outro usuário que se cadastrar na plataforma recebe obrigatoriamente a role 'user' (Membro Comum).
    - Nenhum usuário comum pode se auto-promover a Administrador pela interface pública.
    """
    if email_norm in settings.admin_emails_set:
        return "admin"
    return "user"


@router.post("/signup", status_code=status.HTTP_201_CREATED, response_model=TokenResponse)
def signup(
    payload: SignupRequest,
    db: Session = Depends(get_db),
    audit: AuditContext = Depends(get_audit_context),
) -> TokenResponse:
    """
    Cadastra um novo usuário no Nexo (Comum ou Administrador), dispara o e-mail de
    confirmação para o Gmail do usuário e retorna a sessão autenticada.
    """
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

    assigned_role = _resolve_requested_role(email_norm, payload.account_type, payload.admin_code)

    ts = now_utc_iso()
    user_id = generate_uuid()
    new_user = User(
        id=user_id,
        nome=payload.name.strip(),
        email=email_norm,
        senha_hash=hash_password(payload.password),
        role=assigned_role,
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

    token_data = create_access_token(subject=user_id, email=email_norm, role=assigned_role)
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

    # Dispara o e-mail de confirmação de conta para o Gmail cadastrado (com código de 6 dígitos)
    confirm_code = generate_reset_code()
    expires = (now_utc() + timedelta(minutes=15)).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    db.add(
        PasswordResetCode(
            id=generate_uuid(),
            usuario_id=user_id,
            email=email_norm,
            codigo_hash=hash_reset_code(email_norm, confirm_code),
            utilizado=0,
            tentativas=0,
            ip_solicitante=audit.ip_address,
            expira_em=expires,
            criado_em=ts,
        )
    )
    db.commit()

    email_res = send_welcome_confirmation_email(
        to_email=email_norm,
        user_name=new_user.nome,
        role=assigned_role,
        verification_code=confirm_code,
    )

    role_label = "Administrador" if assigned_role == "admin" else "Usuário Comum"
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
        summary=(
            f"Nova conta criada como {role_label}: '{new_user.nome}' ({email_norm}). "
            f"E-mail de confirmação disparado (Protocolo {confirm_code})."
        ),
        after_data={
            "id": user_id,
            "nome": new_user.nome,
            "email": email_norm,
            "role": assigned_role,
            "confirmation_protocol": confirm_code,
            "email_sent_via_smtp": email_res["sent_via_smtp"],
        },
    )

    return TokenResponse(
        ok=True,
        access_token=token_data["access_token"],
        expires_at=token_data["expires_at"],
        email_sent_smtp=email_res["sent_via_smtp"],
        dev_code=confirm_code,
        message=f"Conta criada com sucesso! Confirmação enviada para {email_norm}.",
        user=AuthUserSummary(
            id=user_id,
            name=new_user.nome,
            email=email_norm,
            role=new_user.role,
            currency="BRL",
            twoFactorEnabled=False,
        ),
    )


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
    audit: AuditContext = Depends(get_audit_context),
) -> TokenResponse:
    """
    Autentica um usuário com e-mail e senha.
    Se a Autenticação em Duas Etapas (2FA) estiver ativa no perfil do usuário,
    envia um código de 6 dígitos por e-mail e solicita a confirmação antes de liberar o token.
    """
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
            summary=f"Falha de login para o e-mail '{email_norm}' (senha incorreta ou conta inexistente) via IP {audit.ip_address}.",
        )
        raise NexoException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha inválidos.",
            error_code="INVALID_CREDENTIALS",
        )

    if not user.ativo:
        raise NexoException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta conta está desativada.",
            error_code="ACCOUNT_DISABLED",
        )

    two_factor_active = bool(user.profile and user.profile.dois_fatores_ativo)
    if two_factor_active:
        code = generate_reset_code()
        expires = (now_utc() + timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        challenge = PasswordResetCode(
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
        db.add(challenge)
        db.commit()

        email_res = send_2fa_code_email(to_email=user.email, user_name=user.nome, code=code)

        record_audit_event(
            db,
            action="USER_LOGIN_2FA_REQUIRED",
            category="SECURITY",
            severity="INFO",
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
            summary=f"Desafio de Autenticação em Duas Etapas (2FA) enviado para '{user.nome}' ({user.email}).",
        )

        return TokenResponse(
            ok=True,
            requires_2fa=True,
            message=f"Código de verificação em duas etapas enviado para {user.email}.",
            dev_code=None if email_res["sent_via_smtp"] else code,
            email_sent_smtp=email_res["sent_via_smtp"],
        )

    return _issue_login_session(user, request, db, audit, login_method="SENHA")


@router.post("/verify-2fa", response_model=TokenResponse)
def verify_2fa_login(
    payload: Verify2FARequest,
    request: Request,
    db: Session = Depends(get_db),
    audit: AuditContext = Depends(get_audit_context),
) -> TokenResponse:
    """Valida o código de 6 dígitos da Autenticação em Duas Etapas (2FA) e conclui o login."""
    email_norm = payload.email.strip().lower()
    user = db.query(User).filter(User.email == email_norm, User.ativo == 1).first()
    if not user:
        raise NexoException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Conta não encontrada.",
            error_code="USER_NOT_FOUND",
        )

    latest_code = (
        db.query(PasswordResetCode)
        .filter(PasswordResetCode.usuario_id == user.id, PasswordResetCode.utilizado == 0)
        .order_by(PasswordResetCode.criado_em.desc())
        .first()
    )
    expected_hash = hash_reset_code(email_norm, payload.code)
    now_str = now_utc_iso()

    if not latest_code or latest_code.expira_em < now_str or latest_code.codigo_hash != expected_hash:
        record_audit_event(
            db,
            action="USER_LOGIN_2FA_FAILED",
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
            summary=f"Código 2FA inválido informado para a conta '{user.nome}' ({user.email}).",
        )
        raise NexoException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código de verificação em duas etapas inválido ou expirado.",
            error_code="INVALID_2FA_CODE",
        )

    latest_code.utilizado = 1
    latest_code.utilizado_em = now_str
    db.commit()

    return _issue_login_session(user, request, db, audit, login_method="2FA_VERIFICADO")


@router.post("/connect-gmail-resend", response_model=TokenResponse)
def connect_gmail_and_resend_2fa(
    payload: ConnectGmailResendRequest,
    db: Session = Depends(get_db),
    audit: AuditContext = Depends(get_audit_context),
) -> TokenResponse:
    """
    Salva a Senha de App do Google (se informada) e dispara imediatamente
    o código 2FA por e-mail real via Gmail SMTP (smtp.gmail.com:587) para a conta do usuário.
    """
    email_norm = payload.email.strip().lower()
    user = db.query(User).filter(User.email == email_norm, User.ativo == 1).first()
    if not user:
        raise NexoException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conta não encontrada.",
            error_code="USER_NOT_FOUND",
        )

    if payload.smtp_app_password and payload.smtp_app_password.strip():
        sender_email = (payload.smtp_user or email_norm).strip()
        save_smtp_config(
            user=sender_email,
            password=payload.smtp_app_password.strip(),
            default_to=email_norm,
        )

    code = generate_reset_code()
    expires = (now_utc() + timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    challenge = PasswordResetCode(
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
    db.add(challenge)
    db.commit()

    email_res = send_2fa_code_email(to_email=user.email, user_name=user.nome, code=code)
    if payload.smtp_app_password and not email_res["sent_via_smtp"]:
        raise NexoException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Não foi possível autenticar no Gmail SMTP: {email_res.get('smtp_error') or 'Verifique a Senha de App de 16 caracteres do Google.'}",
            error_code="SMTP_AUTH_FAILED",
        )

    return TokenResponse(
        ok=True,
        requires_2fa=True,
        message=(
            f"E-mail enviado com sucesso para o Gmail ({user.email})!"
            if email_res["sent_via_smtp"]
            else f"Novo código gerado para {user.email}."
        ),
        dev_code=None if email_res["sent_via_smtp"] else code,
        email_sent_smtp=email_res["sent_via_smtp"],
    )


@router.post("/oauth", response_model=TokenResponse)
def oauth_login(
    payload: OAuthLoginRequest,
    request: Request,
    db: Session = Depends(get_db),
    audit: AuditContext = Depends(get_audit_context),
) -> TokenResponse:
    """
    Autentica ou cadastra automaticamente o usuário via conta Google ou Apple,
    persistindo no banco SQL e registrando na trilha de auditoria 360°.
    """
    email_norm = payload.email.strip().lower()
    provider_upper = payload.provider.upper()
    user = db.query(User).filter(User.email == email_norm).first()

    ts = now_utc_iso()
    chosen_password = (payload.password or "").strip()
    if not user:
        assigned_role = _resolve_requested_role(email_norm, payload.account_type, payload.admin_code)
        user = User(
            id=generate_uuid(),
            nome=payload.name.strip(),
            email=email_norm,
            senha_hash=hash_password(chosen_password if chosen_password else generate_uuid()),
            role=assigned_role,
            ativo=1,
            termos_aceitos=1,
            termos_aceitos_em=ts,
            ultimo_login_em=ts,
            criado_em=ts,
            atualizado_em=ts,
        )
        db.add(user)
        db.flush()

        profile = UserProfilePreference(
            usuario_id=user.id,
            telefone="",
            data_nascimento="",
            endereco="",
            moeda_preferida="BRL",
            dois_fatores_ativo=0,
            atualizado_em=ts,
        )
        db.add(profile)
        db.commit()
        db.refresh(user)

        confirm_code = f"OAUTH-{provider_upper[:3]}-{generate_reset_code()}"
        send_welcome_confirmation_email(
            to_email=email_norm,
            user_name=user.nome,
            role=assigned_role,
            verification_code=confirm_code,
        )
    elif chosen_password:
        user.senha_hash = hash_password(chosen_password)
        user.atualizado_em = ts
        db.commit()

    return _issue_login_session(user, request, db, audit, login_method=f"OAUTH_{provider_upper}")


def _issue_login_session(
    user: User,
    request: Request,
    db: Session,
    audit: AuditContext,
    login_method: str = "SENHA",
) -> TokenResponse:
    ts = now_utc_iso()
    user.ultimo_login_em = ts
    user.atualizado_em = ts

    # Se o e-mail estiver na lista de proprietários admin, garante role = 'admin'
    if user.email in settings.admin_emails_set and user.role != "admin":
        user.role = "admin"

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
    two_factor = bool(user.profile.dois_fatores_ativo) if user.profile else False

    record_audit_event(
        db,
        action=f"USER_LOGIN_{login_method}",
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
        summary=(
            f"Login realizado via {login_method} por '{user.nome}' ({user.email}) "
            f"[Perfil: {user.role.upper()}] via IP {audit.ip_address}."
        ),
        after_data={
            "session_id": session_row.id,
            "method": login_method,
            "role": user.role,
            "expires_at": token_data["expires_at"],
        },
    )

    return TokenResponse(
        ok=True,
        requires_2fa=False,
        access_token=token_data["access_token"],
        expires_at=token_data["expires_at"],
        user=AuthUserSummary(
            id=user.id,
            name=user.nome,
            email=user.email,
            role=user.role,
            currency=currency,
            twoFactorEnabled=two_factor,
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
    """Gera um código de segurança de 6 dígitos com validade de 15 minutos e envia por e-mail."""
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
        raise NexoException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhuma conta encontrada com este e-mail.",
            error_code="EMAIL_NOT_FOUND",
        )

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

    email_res = send_nexo_email(
        to_email=user.email,
        subject=f"[Projeto Nexo] Código de Recuperação de Senha: {code}",
        plain_body=f"Olá, {user.nome}!\nSeu código para redefinir a senha no Projeto Nexo é: {code}",
        html_body=f"<h3>Olá, {user.nome}!</h3><p>Seu código de recuperação de senha no Projeto Nexo é: <strong style='font-size:22px;color:#0284c7;'>{code}</strong></p>",
    )

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
        summary=f"Código de recuperação de senha gerado e enviado para '{user.nome}' ({user.email}).",
        after_data={"reset_request_id": reset_entry.id, "expires_at": expires},
    )

    return {
        "ok": True,
        "message": f"Código de segurança enviado para {email_norm}.",
        "expires_at": expires,
        "dev_code": code,
        "email_sent_smtp": email_res["sent_via_smtp"],
    }


@router.post("/reset-password")
def reset_password(
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
    audit: AuditContext = Depends(get_audit_context),
) -> Dict[str, Any]:
    """Valida o código de 6 dígitos e atualiza a senha do usuário."""
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
    """Altera a senha do usuário autenticado."""
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
