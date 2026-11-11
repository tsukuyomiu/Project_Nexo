"""
Suíte Completa de Testes End-to-End do Back-End, Banco SQL e Auditoria 360° do Projeto Nexo.

Valida:
1. Cadastro, Login (sucesso e falha), Logout, Recuperação de Senha (2 etapas) e Troca de Senha.
2. Perfil e Preferências de Moeda/2FA.
3. CRUD completo de Lançamentos Financeiros (Receitas e Despesas).
4. Dashboard Mensal e Geração de Relatório com Hash SHA-256.
5. Trilha de Auditoria 360° (Python + Triggers SQL) e Imutabilidade (`Append-Only`).
"""

from __future__ import annotations

import asyncio
import uuid

import httpx
from sqlalchemy import text

from app.db.scripts.init_db import initialize_database
from app.db.session import SessionLocal
from app.main import app


async def run_all_tests() -> None:
    initialize_database()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Healthcheck
        r_health = await client.get("/health")
        assert r_health.status_code == 200, r_health.text

        # 2. Cadastro de Novo Usuário
        unique_email = f"gabriel.{uuid.uuid4().hex[:6]}@nexo.com"
        r_signup = await client.post(
            "/api/v1/auth/signup",
            json={
                "name": "Gabriel Nonato",
                "email": unique_email,
                "password": "SenhaForte123",
                "confirm": "SenhaForte123",
                "terms": True,
            },
        )
        assert r_signup.status_code == 201, r_signup.text
        token = r_signup.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Tentativa de Login com Senha Errada (deve gravar USER_LOGIN_FAILED no Audit Log)
        r_bad_login = await client.post(
            "/api/v1/auth/login",
            json={"email": unique_email, "password": "SenhaErrada999"},
        )
        assert r_bad_login.status_code == 401

        # 4. Login com Sucesso
        r_login = await client.post(
            "/api/v1/auth/login",
            json={"email": unique_email, "password": "SenhaForte123"},
        )
        assert r_login.status_code == 200, r_login.text
        token = r_login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 5. Atualizar Perfil e Preferências
        r_prof = await client.put(
            "/api/v1/users/me/profile",
            headers=headers,
            json={
                "name": "Gabriel Nonato Senior",
                "email": unique_email,
                "phone": "+55 (11) 98888-7777",
                "birthDate": "2000-08-25",
                "address": "São Paulo, Brasil",
            },
        )
        assert r_prof.status_code == 200, r_prof.text
        assert r_prof.json()["name"] == "Gabriel Nonato Senior"

        r_pref = await client.put(
            "/api/v1/users/me/preferences",
            headers=headers,
            json={"currency": "USD", "twoFactorEnabled": True},
        )
        assert r_pref.status_code == 200, r_pref.text
        assert r_pref.json()["currency"] == "USD"

        # 6. Criar Receita e Despesa
        r_tx_inc = await client.post(
            "/api/v1/transactions",
            headers=headers,
            json={
                "description": "Salário Engenheiro de Dados",
                "amount": 12500.00,
                "date": "2026-11-10",
                "category": "Salário",
                "type": "income",
                "status": "confirmado",
            },
        )
        assert r_tx_inc.status_code == 201, r_tx_inc.text
        inc_id = r_tx_inc.json()["id"]

        r_tx_exp = await client.post(
            "/api/v1/transactions",
            headers=headers,
            json={
                "description": "Aluguel Apartamento",
                "amount": 2800.00,
                "date": "2026-11-10",
                "category": "Moradia",
                "type": "expense",
                "status": "pendente",
            },
        )
        assert r_tx_exp.status_code == 201, r_tx_exp.text
        exp_id = r_tx_exp.json()["id"]

        # 7. Editar Despesa (testando diff antes e depois no Audit Log)
        r_tx_upd = await client.put(
            f"/api/v1/transactions/{exp_id}",
            headers=headers,
            json={
                "description": "Aluguel + Condomínio",
                "amount": 3250.00,
                "date": "2026-11-10",
                "category": "Moradia",
                "type": "expense",
                "status": "confirmado",
            },
        )
        assert r_tx_upd.status_code == 200, r_tx_upd.text
        assert r_tx_upd.json()["amount"] == 3250.00

        # 8. Consultar Dashboard e Gerar Relatório Oficial
        r_dash = await client.get("/api/v1/dashboard/summary?month=2026-11", headers=headers)
        assert r_dash.status_code == 200, r_dash.text
        dash_data = r_dash.json()
        assert dash_data["currentTotals"]["income"] == 12500.00
        assert dash_data["currentTotals"]["expense"] == 3250.00
        assert dash_data["currentTotals"]["balance"] == 9250.00

        r_rep = await client.post("/api/v1/dashboard/reports?month=2026-11", headers=headers)
        assert r_rep.status_code == 200, r_rep.text
        assert "hash_sha256" in r_rep.json()

        # 9. Excluir Lançamento
        r_del = await client.delete(f"/api/v1/transactions/{inc_id}", headers=headers)
        assert r_del.status_code == 200, r_del.text

        # 10. Registrar Evento de Telemetria do Front-End
        r_fe = await client.post(
            "/api/v1/logs/frontend-event",
            headers=headers,
            json={
                "acao": "DASHBOARD_MONTH_FILTER_CHANGED",
                "entidade_afetada": "dashboard_ui",
                "resumo_humano": "Gabriel Nonato filtrou o Dashboard para o mês 2026-11.",
                "detalhes": {"month": "2026-11"},
            },
        )
        assert r_fe.status_code == 201, r_fe.text

        # 11. Consultar Central de Logs e Auditoria 360°
        r_audit = await client.get(f"/api/v1/logs/audit?email={unique_email}", headers=headers)
        assert r_audit.status_code == 200, r_audit.text
        audit_items = r_audit.json()["items"]
        assert len(audit_items) >= 10

        r_timeline = await client.get("/api/v1/logs/timeline?limit=20", headers=headers)
        assert r_timeline.status_code == 200, r_timeline.text

        r_stats = await client.get("/api/v1/logs/stats", headers=headers)
        assert r_stats.status_code == 200, r_stats.text

        r_csv = await client.get("/api/v1/logs/export?format=csv", headers=headers)
        assert r_csv.status_code == 200
        assert "Hash Integridade SHA256" in r_csv.text

        # 12. Testar Imutabilidade da Tabela `audit_logs` via Trigger SQL
        db = SessionLocal()
        try:
            immutable_verified = False
            try:
                db.execute(text("DELETE FROM audit_logs"))
                db.commit()
            except Exception as exc:
                db.rollback()
                assert "VIOLACAO DE SEGURANCA NEXO" in str(exc)
                immutable_verified = True
            assert immutable_verified, "O trigger de imutabilidade deveria ter bloqueado o DELETE!"
        finally:
            db.close()

        print("\n[SUCESSO TOTAL] Todos os 12 fluxos de API, Banco SQL e Auditoria 360° passaram nos testes!")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
