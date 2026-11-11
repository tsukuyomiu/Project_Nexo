"""
Schemas de Lançamentos Financeiros (Transactions) e Dashboard.
Alinhados 1:1 com `frontend/src/lib/transactions.ts`.
"""

from __future__ import annotations

from datetime import date
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

TransactionType = Literal["income", "expense"]
TransactionStatus = Literal["confirmado", "pendente"]


class TransactionCreate(BaseModel):
    description: str = Field(..., min_length=1, max_length=100, description="Descrição do lançamento")
    amount: float = Field(..., gt=0, description="Valor positivo maior que zero")
    date: str = Field(..., min_length=10, max_length=10, description="Data ISO YYYY-MM-DD")
    category: str = Field(..., min_length=1, max_length=60, description="Categoria do lançamento")
    type: TransactionType = Field(..., description="'income' (Receita) ou 'expense' (Despesa)")
    status: TransactionStatus = Field(default="confirmado", description="'confirmado' ou 'pendente'")

    @field_validator("description", "category")
    @classmethod
    def strip_non_empty(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("O campo não pode estar vazio.")
        return cleaned

    @field_validator("date")
    @classmethod
    def validate_iso_date(cls, v: str) -> str:
        try:
            date.fromisoformat(v)
            return v
        except ValueError as exc:
            raise ValueError("Informe uma data válida no formato YYYY-MM-DD.") from exc


class TransactionUpdate(TransactionCreate):
    """Mesmo contrato para atualização completa do lançamento."""
    pass


class TransactionResponse(BaseModel):
    id: str
    description: str
    amount: float
    date: str
    category: str
    type: TransactionType
    status: TransactionStatus
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None


class TotalsSummary(BaseModel):
    income: float
    expense: float
    balance: float


class CategoryExpenseSummary(BaseModel):
    category: str
    total: float
    percent: float
    count: int


class DashboardSummaryResponse(BaseModel):
    month: str
    previousMonth: str
    currentTotals: TotalsSummary
    previousTotals: TotalsSummary
    expensesByCategory: List[CategoryExpenseSummary]
    recentTransactions: List[TransactionResponse]
    availableMonths: List[str]
