"""
Schemas de Perfil e Preferências do Usuário.
Alinhados com `frontend/src/lib/profile.ts` e `frontend/src/lib/preferences.ts`.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

CurrencyType = Literal["BRL", "USD", "EUR", "GBP"]


class ProfilePayload(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: str = Field(default="", max_length=25)
    birthDate: str = Field(default="", max_length=10)
    address: str = Field(default="", max_length=200)

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Informe seu nome.")
        return cleaned

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            return ""
        digits = re.sub(r"\D", "", cleaned)
        if not re.match(r"^[+\d\s().-]+$", cleaned) or len(digits) < 8:
            raise ValueError("Informe um telefone válido.")
        return cleaned

    @field_validator("birthDate")
    @classmethod
    def validate_birth_date(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            return ""
        try:
            parsed = date.fromisoformat(cleaned)
            if parsed > date.today():
                raise ValueError("A data de nascimento não pode estar no futuro.")
            return cleaned
        except ValueError as exc:
            raise ValueError("Informe uma data de nascimento válida (YYYY-MM-DD).") from exc

    @field_validator("address")
    @classmethod
    def clean_address(cls, v: str) -> str:
        return v.strip()


class PreferencesPayload(BaseModel):
    currency: CurrencyType = Field(default="BRL")
    twoFactorEnabled: Optional[bool] = Field(default=False)


class UserProfileResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: str
    birthDate: str
    address: str
    currency: CurrencyType
    twoFactorEnabled: bool
    role: str
    createdAt: str
    updatedAt: str
