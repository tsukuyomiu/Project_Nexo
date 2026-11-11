"""
Utilitário CLI Sênior para Inspeção de Logs e Auditoria 360° do Projeto Nexo.

Como usar no terminal (a partir da pasta `backend/`):
  python -m app.db.scripts.inspect_logs
  python -m app.db.scripts.inspect_logs --limit 30 --email admin@nexo.com
  python -m app.db.scripts.inspect_logs --access
"""

from __future__ import annotations

import argparse
from typing import Optional

from sqlalchemy import text

from app.db.scripts.init_db import initialize_database
from app.db.session import SessionLocal


def print_audit_logs(limit: int = 25, email: Optional[str] = None, category: Optional[str] = None) -> None:
    initialize_database()
    db = SessionLocal()
    try:
        sql = """
            SELECT
                quando_fez_brasilia,
                quem_fez_nome,
                quem_fez_email,
                de_qual_ip,
                codigo_acao,
                modulo,
                severidade,
                origem_registro,
                o_que_fez
            FROM vw_auditoria_completa
            WHERE 1=1
        """
        params = {"limit": limit}
        if email:
            sql += " AND lower(quem_fez_email) LIKE :email"
            params["email"] = f"%{email.lower()}%"
        if category:
            sql += " AND upper(modulo) = :cat"
            params["cat"] = category.upper()

        sql += " LIMIT :limit"
        rows = db.execute(text(sql), params).fetchall()

        print("=" * 120)
        print(f" PROJETO NEXO - CENTRAL DE AUDITORIA 360° (Exibindo {len(rows)} eventos mais recentes)")
        print("=" * 120)
        for idx, r in enumerate(rows, 1):
            quando, nome, mail, ip, acao, mod, sev, orig, resumo = r
            print(
                f"[{idx:02d}] DATA/HORA: {quando} | QUEM: {nome} <{mail}> (IP: {ip})\n"
                f"     AÇÃO: [{sev}] {mod} :: {acao} (Origem: {orig})\n"
                f"     O QUE FEZ: {resumo}"
            )
            print("-" * 120)
    finally:
        db.close()


def print_access_logs(limit: int = 25) -> None:
    initialize_database()
    db = SessionLocal()
    try:
        rows = db.execute(
            text(
                """
                SELECT
                    data_hora_local,
                    COALESCE(usuario_email, 'anonimo'),
                    metodo_http,
                    rota,
                    status_code,
                    tempo_resposta_ms,
                    ip_origem
                FROM access_logs
                ORDER BY data_hora_utc DESC
                LIMIT :limit
                """
            ),
            {"limit": limit},
        ).fetchall()
        print("=" * 110)
        print(f" PROJETO NEXO - LOGS DE TRÁFEGO HTTP (Últimas {len(rows)} requisições)")
        print("=" * 110)
        for r in rows:
            dt, mail, method, route, code, ms, ip = r
            print(f"{dt} | {code} | {method:<6} {route:<35} | {ms:>6.2f} ms | {mail} ({ip})")
        print("=" * 110)
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inspeciona os logs de auditoria do Projeto Nexo.")
    parser.add_argument("--limit", type=int, default=25, help="Quantidade de registros")
    parser.add_argument("--email", type=str, default=None, help="Filtrar por e-mail do usuário")
    parser.add_argument("--category", type=str, default=None, help="Filtrar por módulo (AUTH, TRANSACTION, etc.)")
    parser.add_argument("--access", action="store_true", help="Exibe os logs de tráfego HTTP (access_logs)")
    args = parser.parse_args()

    if args.access:
        print_access_logs(limit=args.limit)
    else:
        print_audit_logs(limit=args.limit, email=args.email, category=args.category)
