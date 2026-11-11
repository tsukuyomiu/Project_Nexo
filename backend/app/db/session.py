"""
Configuração da Engine SQLAlchemy 2.0 e gerenciamento de Sessão.
Habilita automaticamente `PRAGMA foreign_keys = ON` e `WAL` no SQLite
e suporta conexão direta com PostgreSQL em produção.
"""

from __future__ import annotations

from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

is_sqlite = settings.NEXO_DATABASE_URL.startswith("sqlite")

connect_args = {"check_same_thread": False} if is_sqlite else {}

engine = create_engine(
    settings.NEXO_DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)

if is_sqlite:
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute("PRAGMA journal_mode = WAL;")
        cursor.execute("PRAGMA synchronous = NORMAL;")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Classe base para todos os modelos ORM SQLAlchemy 2.0."""
    pass


def get_db() -> Generator[Session, None, None]:
    """Dependency do FastAPI para fornecer uma sessão de banco por requisição."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
