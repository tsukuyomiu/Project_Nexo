"""
Configurações tipadas e centralizadas do Back-End Nexo.
Resolve caminhos absolutos automaticamente para que o servidor possa ser
iniciado tanto da raiz do repositório quanto da pasta `backend/`.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

# Diretórios base do projeto
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT_DIR = BACKEND_DIR.parent
DATA_DIR = BACKEND_DIR / "data"
LOGS_DIR = BACKEND_DIR / "logs"
SQL_DIR = PROJECT_ROOT_DIR / "database" / "sql"
SEEDS_DIR = PROJECT_ROOT_DIR / "database" / "json_seeds"

# Garante que os diretórios de dados e logs existam
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
(DATA_DIR / "backups").mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    """Configurações globais carregadas de variáveis de ambiente ou `.env`."""

    NEXO_ENV: str = "development"
    NEXO_APP_NAME: str = "Projeto Nexo API"
    NEXO_VERSION: str = "1.0.0"
    NEXO_API_V1_PREFIX: str = "/api/v1"

    # Banco de Dados (usa caminho absoluto para o SQLite local por padrão)
    NEXO_DATABASE_URL: str = f"sqlite:///{(DATA_DIR / 'nexo.db').as_posix()}"

    # Segurança e Autenticação JWT
    NEXO_SECRET_KEY: str = "nexo-super-secret-jwt-key-change-in-production-2026"
    NEXO_JWT_ALGORITHM: str = "HS256"
    NEXO_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 horas
    NEXO_RESET_CODE_EXPIRE_MINUTES: int = 15

    # CORS
    NEXO_CORS_ORIGINS: str = (
        "http://localhost:3000,http://localhost:5173,"
        "http://127.0.0.1:3000,http://127.0.0.1:5173"
    )

    # Arquivos de Logs e Auditoria
    NEXO_AUDIT_LOG_FILE: str = str(LOGS_DIR / "nexo_audit.jsonl")
    NEXO_ACCESS_LOG_FILE: str = str(LOGS_DIR / "nexo_access.jsonl")
    NEXO_ERROR_LOG_FILE: str = str(LOGS_DIR / "nexo_errors.log")
    NEXO_LOGS_PUBLIC_IN_DEV: bool = True

    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.NEXO_CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
