"""
Schemas de Autenticação, Cadastro, Redefinição e Troca de Senha.
Alinhados com `signup-validation.ts`, `change-password.ts` e `redefinir-senha.tsx`.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class SignupRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Nome completo do usuário")
    email: EmailStr = Field(..., description="E-mail único do usuário")
    password: str = Field(..., min_length=6, max_length=128, description="Senha (mínimo 6 caracteres)")
    confirm: Optional[str] = Field(default=None, description="Confirmação da senha")
    terms: bool = Field(default=True, description="Aceite dos termos de uso")

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


class TokenResponse(BaseModel):
    ok: bool = True
    access_token: str
    token_type: str = "bearer"
    expires_at: str
    user: AuthUserSummary
