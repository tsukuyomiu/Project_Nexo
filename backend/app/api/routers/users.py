"""
Rotas de Perfil e Preferências do Usuário (`/api/v1/users`):
- GET  `/me`: Retorna dados completos do perfil e preferências
- PUT  `/me/profile`: Atualiza nome, e-mail, telefone, data de nascimento e endereço
- PUT  `/me/preferences`: Atualiza moeda preferida (`BRL`, `USD`, `EUR`, `GBP`) e 2FA
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import AuditContext, get_audit_context, get_current_user
from app.core.audit_logger import record_audit_event
from app.core.exceptions import NexoException
from app.core.security import now_utc_iso
from app.db.models import User, UserProfilePreference
from app.db.session import get_db
from app.schemas.user import PreferencesPayload, ProfilePayload, UserProfileResponse

router = APIRouter(prefix="/users", tags=["Perfil & Preferências"])


def _ensure_profile(db: Session, user: User) -> UserProfilePreference:
    if not user.profile:
        prof = UserProfilePreference(
            usuario_id=user.id,
            telefone="",
            data_nascimento="",
            endereco="",
            moeda_preferida="BRL",
            dois_fatores_ativo=0,
            atualizado_em=now_utc_iso(),
        )
        db.add(prof)
        db.commit()
        db.refresh(user)
        return prof
    return user.profile


def _build_user_response(user: User, prof: UserProfilePreference) -> UserProfileResponse:
    return UserProfileResponse(
        id=user.id,
        name=user.nome,
        email=user.email,
        phone=prof.telefone or "",
        birthDate=prof.data_nascimento or "",
        address=prof.endereco or "",
        currency=prof.moeda_preferida or "BRL",  # type: ignore[arg-type]
        twoFactorEnabled=bool(prof.dois_fatores_ativo),
        role=user.role,
        createdAt=user.criado_em,
        updatedAt=prof.atualizado_em,
    )


@router.get("/me", response_model=UserProfileResponse)
def get_my_profile(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserProfileResponse:
    """Retorna os dados pessoais e preferências do usuário autenticado."""
    prof = _ensure_profile(db, user)
    return _build_user_response(user, prof)


@router.put("/me/profile", response_model=UserProfileResponse)
def update_my_profile(
    payload: ProfilePayload,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    audit: AuditContext = Depends(get_audit_context),
) -> UserProfileResponse:
    """Atualiza as informações pessoais do usuário e registra o diff completo em `audit_logs`."""
    prof = _ensure_profile(db, user)
    email_norm = payload.email.strip().lower()

    if email_norm != user.email:
        conflict = db.query(User).filter(User.email == email_norm, User.id != user.id).first()
        if conflict:
            raise NexoException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Este e-mail já está em uso por outra conta.",
                error_code="EMAIL_IN_USE",
            )

    before_snapshot = {
        "name": user.nome,
        "email": user.email,
        "phone": prof.telefone,
        "birthDate": prof.data_nascimento,
        "address": prof.endereco,
    }

    ts = now_utc_iso()
    user.nome = payload.name.strip()
    user.email = email_norm
    user.atualizado_em = ts

    prof.telefone = payload.phone
    prof.data_nascimento = payload.birthDate
    prof.endereco = payload.address
    prof.atualizado_em = ts

    db.commit()
    db.refresh(user)
    db.refresh(prof)

    after_snapshot = {
        "name": user.nome,
        "email": user.email,
        "phone": prof.telefone,
        "birthDate": prof.data_nascimento,
        "address": prof.endereco,
    }

    record_audit_event(
        db,
        action="PROFILE_UPDATED",
        category="PROFILE",
        severity="INFO",
        entity_affected="perfis_preferencias",
        entity_id=user.id,
        actor_id=user.id,
        actor_email=user.email,
        actor_name=user.nome,
        ip_address=audit.ip_address,
        user_agent=audit.user_agent,
        http_method=audit.http_method,
        http_route=audit.http_route,
        request_id=audit.request_id,
        summary=f"Usuário '{user.nome}' ({user.email}) atualizou suas informações pessoais de perfil.",
        before_data=before_snapshot,
        after_data=after_snapshot,
    )

    return _build_user_response(user, prof)


@router.put("/me/preferences", response_model=UserProfileResponse)
def update_my_preferences(
    payload: PreferencesPayload,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    audit: AuditContext = Depends(get_audit_context),
) -> UserProfileResponse:
    """Atualiza moeda preferida (`BRL`, `USD`, `EUR`, `GBP`) e status de autenticação em 2 etapas."""
    prof = _ensure_profile(db, user)

    before_snapshot = {
        "currency": prof.moeda_preferida,
        "twoFactorEnabled": bool(prof.dois_fatores_ativo),
    }

    prof.moeda_preferida = payload.currency
    if payload.twoFactorEnabled is not None:
        prof.dois_fatores_ativo = 1 if payload.twoFactorEnabled else 0
    prof.atualizado_em = now_utc_iso()

    db.commit()
    db.refresh(prof)

    after_snapshot = {
        "currency": prof.moeda_preferida,
        "twoFactorEnabled": bool(prof.dois_fatores_ativo),
    }

    record_audit_event(
        db,
        action="PREFERENCES_UPDATED",
        category="PREFERENCES",
        severity="INFO",
        entity_affected="perfis_preferencias",
        entity_id=user.id,
        actor_id=user.id,
        actor_email=user.email,
        actor_name=user.nome,
        ip_address=audit.ip_address,
        user_agent=audit.user_agent,
        http_method=audit.http_method,
        http_route=audit.http_route,
        request_id=audit.request_id,
        summary=(
            f"Usuário '{user.nome}' ({user.email}) alterou preferências: "
            f"moeda {before_snapshot['currency']} -> {after_snapshot['currency']}."
        ),
        before_data=before_snapshot,
        after_data=after_snapshot,
    )

    return _build_user_response(user, prof)
