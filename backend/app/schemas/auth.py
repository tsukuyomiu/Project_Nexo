"""
Schemas de Autenticação, Cadastro, OAuth (Google/Apple), 2FA, Redefinição e Troca de Senha.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class SignupRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Nome completo do usuário")
    email: EmailStr = Field(..., description="E-mail único do usuário")
    password: str = Field(..., min_length=6, max_length=128, description="Senha (mínimo 6 caracteres)")
    confirm: Optional[str] = Field(default=None, description="Confirmação da senha")
    terms: bool = Field(default=True, description="Aceite dos termos de uso")
    account_type: Literal["user", "admin"] = Field(default="user", description="'user' ou 'admin'")
    admin_code: Optional[str] = Field(default=None, description="Chave Corporativa para criação de Administrador")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Informe seu nome.")
        return cleaned

    @field_validator("terms")
    @classmethod
    def validate_terms(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Aceite os termos para continuar.")
        return v


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="E-mail cadastrado")
    password: str = Field(..., min_length=1, description="Senha do usuário")


class Verify2FARequest(BaseModel):
    email: EmailStr = Field(..., description="E-mail da conta")
    code: str = Field(..., min_length=4, max_length=12, description="Código 2FA de 6 dígitos")


class ConnectGmailResendRequest(BaseModel):
    email: EmailStr = Field(..., description="E-mail da conta que receberá o código")
    smtp_user: Optional[str] = Field(default=None, description="E-mail Gmail remetente")
    smtp_app_password: Optional[str] = Field(default=None, description="Senha de App de 16 caracteres do Google")


class OAuthLoginRequest(BaseModel):
    provider: Literal["google", "apple"] = Field(..., description="Provedor OAuth: google ou apple")
    email: EmailStr = Field(..., description="E-mail da conta Google ou Apple")
    name: str = Field(..., min_length=1, max_length=100, description="Nome do titular da conta")
    password: Optional[str] = Field(default=None, description="Senha escolhida pelo usuário no cadastro social")
    account_type: Literal["user", "admin"] = Field(default="user")
    admin_code: Optional[str] = Field(default=None)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(..., description="E-mail para envio do código de recuperação")


class ResetPasswordRequest(BaseModel):
    email: EmailStr = Field(..., description="E-mail da conta")
    code: str = Field(..., min_length=4, max_length=12, description="Código recebido por e-mail")
    new_password: str = Field(..., min_length=6, max_length=128, description="Nova senha")
    confirm_password: Optional[str] = Field(default=None, description="Confirmação da nova senha")


class ChangePasswordRequest(BaseModel):
    current: str = Field(..., min_length=1, description="Senha atual")
    next: str = Field(..., min_length=6, max_length=128, description="Nova senha (mínimo 6 caracteres)")
    confirm: Optional[str] = Field(default=None, description="Confirmação da nova senha")


class ChangePasswordResponse(BaseModel):
    ok: bool
    message: str


class AuthUserSummary(BaseModel):
    id: str
    name: str
    email: str
    role: str
    currency: str = "BRL"
    twoFactorEnabled: bool = False


class TokenResponse(BaseModel):
    ok: bool = True
    requires_2fa: bool = False
    access_token: Optional[str] = None
    token_type: str = "bearer"
    expires_at: Optional[str] = None
    user: Optional[AuthUserSummary] = None
    message: Optional[str] = None
    dev_code: Optional[str] = None
    email_sent_smtp: Optional[bool] = None
