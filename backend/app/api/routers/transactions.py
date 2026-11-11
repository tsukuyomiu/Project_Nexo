"""
Rotas de Lançamentos Financeiros (`/api/v1/transactions`):
- GET    `/`: Lista lançamentos do usuário com filtros combináveis (`month`, `type`, `category`, `status`)
- GET    `/categories`: Lista categorias oficiais de Receita e Despesa do banco
- POST   `/`: Cria novo lançamento (Receita ou Despesa) + Auditoria completa
- PUT    `/{tx_id}`: Edita lançamento existente + Auditoria com diff Antes/Depois
- DELETE `/{tx_id}`: Exclui lançamento + Auditoria preservando snapshot original
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import AuditContext, get_audit_context, get_current_user
from app.core.audit_logger import record_audit_event
from app.core.exceptions import NexoException
from app.core.security import generate_uuid, now_utc_iso
from app.db.models import TransactionModel, User
from app.db.session import get_db
from app.schemas.transaction import (
    TransactionCreate,
    TransactionResponse,
    TransactionUpdate,
)

router = APIRouter(prefix="/transactions", tags=["Lançamentos Financeiros"])


def _to_response(tx: TransactionModel) -> TransactionResponse:
    return TransactionResponse(
        id=tx.id,
        description=tx.descricao,
        amount=round(float(tx.valor), 2),
        date=tx.data_lancamento,
        category=tx.categoria,
        type=tx.tipo,  # type: ignore[arg-type]
        status=tx.status,  # type: ignore[arg-type]
        createdAt=tx.criado_em,
        updatedAt=tx.atualizado_em,
    )


def _snapshot(tx: TransactionModel) -> Dict[str, Any]:
    return {
        "id": tx.id,
        "description": tx.descricao,
        "amount": round(float(tx.valor), 2),
        "date": tx.data_lancamento,
        "category": tx.categoria,
        "type": tx.tipo,
        "status": tx.status,
    }


@router.get("/categories")
def list_categories(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Retorna o catálogo oficial de categorias de Receitas e Despesas do banco SQL."""
    rows = db.execute(
        text(
            "SELECT nome, tipo, descricao FROM categorias_padrao WHERE ativo = 1 ORDER BY id ASC"
        )
    ).fetchall()
    income_cats = [r[0] for r in rows if r[1] == "income"]
    expense_cats = [r[0] for r in rows if r[1] == "expense"]
    return {
        "ok": True,
        "income": income_cats,
        "expense": expense_cats,
    }


@router.get("", response_model=List[TransactionResponse])
def list_transactions(
    month: Optional[str] = Query(default=None, description="Filtro YYYY-MM ou 'all'"),
    type: Optional[str] = Query(default=None, description="'income', 'expense' ou 'all'"),
    category: Optional[str] = Query(default=None, description="Categoria ou 'all'"),
    status_filter: Optional[str] = Query(
        default=None, alias="status", description="'confirmado' ou 'pendente'"
    ),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[TransactionResponse]:
    """
    Lista os lançamentos do usuário autenticado ordenados por data decrescente
    e ordem de inserção (`criado_em DESC`), idêntico a `sortTransactions` do Front-End.
    """
    query = db.query(TransactionModel).filter(TransactionModel.usuario_id == user.id)

    if month and month != "all":
        query = query.filter(TransactionModel.data_lancamento.like(f"{month}%"))
    if type and type != "all":
        query = query.filter(TransactionModel.tipo == type)
    if category and category != "all":
        query = query.filter(TransactionModel.categoria == category)
    if status_filter and status_filter != "all":
        query = query.filter(TransactionModel.status == status_filter)

    items = query.order_by(
        TransactionModel.data_lancamento.desc(),
        TransactionModel.criado_em.desc(),
    ).all()
    return [_to_response(item) for item in items]


@router.post("", status_code=status.HTTP_201_CREATED, response_model=TransactionResponse)
def create_transaction(
    payload: TransactionCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    audit: AuditContext = Depends(get_audit_context),
) -> TransactionResponse:
    """Cria uma nova Receita (`income`) ou Despesa (`expense`) e registra em `audit_logs`."""
    ts = now_utc_iso()
    tx = TransactionModel(
        id=generate_uuid(),
        usuario_id=user.id,
        descricao=payload.description,
        valor=round(float(payload.amount), 2),
        data_lancamento=payload.date,
        categoria=payload.category,
        tipo=payload.type,
        status=payload.status,
        criado_em=ts,
        atualizado_em=ts,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)

    tipo_label = "Receita" if tx.tipo == "income" else "Despesa"
    record_audit_event(
        db,
        action="TRANSACTION_CREATED",
        category="TRANSACTION",
        severity="INFO",
        entity_affected="lancamentos",
        entity_id=tx.id,
        actor_id=user.id,
        actor_email=user.email,
        actor_name=user.nome,
        ip_address=audit.ip_address,
        user_agent=audit.user_agent,
        http_method=audit.http_method,
        http_route=audit.http_route,
        request_id=audit.request_id,
        summary=(
            f"{user.nome} ({user.email}) cadastrou nova {tipo_label}: "
            f"'{tx.descricao}' no valor de R$ {tx.valor:.2f} (Categoria: {tx.categoria}, Data: {tx.data_lancamento})."
        ),
        after_data=_snapshot(tx),
    )

    return _to_response(tx)


@router.put("/{tx_id}", response_model=TransactionResponse)
def update_transaction(
    tx_id: str,
    payload: TransactionUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    audit: AuditContext = Depends(get_audit_context),
) -> TransactionResponse:
    """Atualiza um lançamento existente do usuário e grava o estado Antes e Depois no log."""
    tx = (
        db.query(TransactionModel)
        .filter(TransactionModel.id == tx_id, TransactionModel.usuario_id == user.id)
        .first()
    )
    if not tx:
        raise NexoException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lançamento não encontrado.",
            error_code="TRANSACTION_NOT_FOUND",
        )

    before_snap = _snapshot(tx)

    tx.descricao = payload.description
    tx.valor = round(float(payload.amount), 2)
    tx.data_lancamento = payload.date
    tx.categoria = payload.category
    tx.tipo = payload.type
    tx.status = payload.status
    tx.atualizado_em = now_utc_iso()

    db.commit()
    db.refresh(tx)

    after_snap = _snapshot(tx)

    record_audit_event(
        db,
        action="TRANSACTION_UPDATED",
        category="TRANSACTION",
        severity="INFO",
        entity_affected="lancamentos",
        entity_id=tx.id,
        actor_id=user.id,
        actor_email=user.email,
        actor_name=user.nome,
        ip_address=audit.ip_address,
        user_agent=audit.user_agent,
        http_method=audit.http_method,
        http_route=audit.http_route,
        request_id=audit.request_id,
        summary=(
            f"{user.nome} ({user.email}) editou o lançamento '{before_snap['description']}' -> "
            f"'{after_snap['description']}' (Valor: {before_snap['amount']:.2f} -> {after_snap['amount']:.2f})."
        ),
        before_data=before_snap,
        after_data=after_snap,
    )

    return _to_response(tx)


@router.delete("/{tx_id}")
def delete_transaction(
    tx_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    audit: AuditContext = Depends(get_audit_context),
) -> Dict[str, Any]:
    """Exclui um lançamento financeiro e preserva os dados originais em `audit_logs`."""
    tx = (
        db.query(TransactionModel)
        .filter(TransactionModel.id == tx_id, TransactionModel.usuario_id == user.id)
        .first()
    )
    if not tx:
        raise NexoException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lançamento não encontrado.",
            error_code="TRANSACTION_NOT_FOUND",
        )

    before_snap = _snapshot(tx)
    db.delete(tx)
    db.commit()

    record_audit_event(
        db,
        action="TRANSACTION_DELETED",
        category="TRANSACTION",
        severity="WARNING",
        entity_affected="lancamentos",
        entity_id=tx_id,
        actor_id=user.id,
        actor_email=user.email,
        actor_name=user.nome,
        ip_address=audit.ip_address,
        user_agent=audit.user_agent,
        http_method=audit.http_method,
        http_route=audit.http_route,
        request_id=audit.request_id,
        summary=(
            f"{user.nome} ({user.email}) excluiu o lançamento '{before_snap['description']}' "
            f"(Valor: R$ {before_snap['amount']:.2f}, Data: {before_snap['date']})."
        ),
        before_data=before_snap,
    )

    return {"ok": True, "id": tx_id, "message": "Lançamento excluído com sucesso!"}
