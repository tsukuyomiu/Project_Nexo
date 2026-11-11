"""
Rotas de Dashboard e Relatórios Financeiros (`/api/v1/dashboard`):
- GET  `/summary`: Consolida Receitas, Despesas, Saldo, Comparativo com Mês Anterior,
                   Despesas por Categoria e Últimos Lançamentos.
- POST `/reports`: Gera e registra na tabela `relatorios_exportados` um relatório
                   oficial com hash SHA-256 de integridade.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import AuditContext, get_audit_context, get_current_user
from app.api.routers.transactions import _to_response
from app.core.audit_logger import record_audit_event
from app.core.security import generate_uuid, now_utc_iso
from app.db.models import ExportedReport, TransactionModel, User
from app.db.session import get_db
from app.schemas.transaction import (
    CategoryExpenseSummary,
    DashboardSummaryResponse,
    TotalsSummary,
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard & Relatórios"])


def _prev_month_key(month_key: str) -> str:
    try:
        y_str, m_str = month_key.split("-")
        y, m = int(y_str), int(m_str)
        if m == 1:
            return f"{y - 1}-12"
        return f"{y:04d}-{m - 1:02d}"
    except Exception:
        today = date.today()
        return f"{today.year:04d}-{today.month:02d}"


def _calc_totals(items: List[TransactionModel]) -> TotalsSummary:
    inc = round(sum(float(t.valor) for t in items if t.tipo == "income"), 2)
    exp = round(sum(float(t.valor) for t in items if t.tipo == "expense"), 2)
    return TotalsSummary(income=inc, expense=exp, balance=round(inc - exp, 2))


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    month: Optional[str] = Query(default=None, description="Mês no formato YYYY-MM"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardSummaryResponse:
    """Retorna todas as métricas necessárias para a tela `/dashboard` e `/perfil`."""
    current_month = month or date.today().strftime("%Y-%m")
    previous_month = _prev_month_key(current_month)

    all_tx = (
        db.query(TransactionModel)
        .filter(TransactionModel.usuario_id == user.id)
        .order_by(TransactionModel.data_lancamento.desc(), TransactionModel.criado_em.desc())
        .all()
    )

    current_tx = [t for t in all_tx if t.data_lancamento.startswith(current_month)]
    prev_tx = [t for t in all_tx if t.data_lancamento.startswith(previous_month)]

    current_totals = _calc_totals(current_tx)
    prev_totals = _calc_totals(prev_tx)

    # Agrupamento de despesas por categoria (mesma regra de `expensesByCategory` do Front-End)
    cat_map: Dict[str, Dict[str, float | int]] = {}
    for t in current_tx:
        if t.tipo == "expense":
            entry = cat_map.setdefault(t.categoria, {"total": 0.0, "count": 0})
            entry["total"] = float(entry["total"]) + float(t.valor)
            entry["count"] = int(entry["count"]) + 1

    total_exp = current_totals.expense
    by_category = [
        CategoryExpenseSummary(
            category=cat,
            total=round(float(vals["total"]), 2),
            percent=round((float(vals["total"]) / total_exp) * 100.0, 2) if total_exp > 0 else 0.0,
            count=int(vals["count"]),
        )
        for cat, vals in cat_map.items()
    ]
    by_category.sort(key=lambda c: c.total, reverse=True)

    months_set = {t.data_lancamento[:7] for t in all_tx if len(t.data_lancamento) >= 7}
    months_set.add(date.today().strftime("%Y-%m"))
    available_months = sorted(months_set, reverse=True)

    return DashboardSummaryResponse(
        month=current_month,
        previousMonth=previous_month,
        currentTotals=current_totals,
        previousTotals=prev_totals,
        expensesByCategory=by_category,
        recentTransactions=[_to_response(t) for t in current_tx[:6]],
        availableMonths=available_months,
    )


@router.post("/reports")
def generate_financial_report(
    month: Optional[str] = Query(default=None, description="Mês de referência YYYY-MM ou 'ALL'"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    audit: AuditContext = Depends(get_audit_context),
) -> Dict[str, Any]:
    """
    Gera um relatório consolidado das movimentações financeiras do usuário,
    armazena na tabela `relatorios_exportados` e registra o evento de auditoria.
    """
    period = month or date.today().strftime("%Y-%m")
    summary_data = get_dashboard_summary(month=period if period != "ALL" else None, user=user, db=db)

    metrics_dict = summary_data.model_dump()
    metrics_json = json.dumps(metrics_dict, ensure_ascii=False)
    report_hash = hashlib.sha256(metrics_json.encode("utf-8")).hexdigest()

    report_row = ExportedReport(
        id=generate_uuid(),
        usuario_id=user.id,
        titulo=f"Relatório Financeiro Nexo - {period}",
        tipo_relatorio="FINANCEIRO_MENSAL",
        periodo_referencia=period,
        formato="JSON",
        filtros_json=json.dumps({"month": period}),
        resumo_metricas=metrics_json,
        hash_integridade=report_hash,
        ip_solicitante=audit.ip_address,
        criado_em=now_utc_iso(),
    )
    db.add(report_row)
    db.commit()

    record_audit_event(
        db,
        action="FINANCIAL_REPORT_GENERATED",
        category="REPORT",
        severity="INFO",
        entity_affected="relatorios_exportados",
        entity_id=report_row.id,
        actor_id=user.id,
        actor_email=user.email,
        actor_name=user.nome,
        ip_address=audit.ip_address,
        user_agent=audit.user_agent,
        http_method=audit.http_method,
        http_route=audit.http_route,
        request_id=audit.request_id,
        summary=f"{user.nome} ({user.email}) gerou o Relatório Financeiro do período {period}.",
        after_data={
            "report_id": report_row.id,
            "period": period,
            "totals": summary_data.currentTotals.model_dump(),
            "sha256": report_hash,
        },
    )

    return {
        "ok": True,
        "report_id": report_row.id,
        "title": report_row.titulo,
        "period": period,
        "hash_sha256": report_hash,
        "created_at": report_row.criado_em,
        "data": metrics_dict,
    }
