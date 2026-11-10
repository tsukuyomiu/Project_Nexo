import { Pencil, Trash2 } from "lucide-react";
import { formatBRL, formatDate, type Transaction } from "@/lib/transactions";
import { useTransactions } from "@/hooks/useTransactions";

interface TransactionTableProps {
  transactions: Transaction[];
  onEdit?: (t: Transaction) => void;
  onDelete?: (t: Transaction) => void;
  emptyMessage?: string;
}

/* Tabela de lançamentos compartilhada pelo Dashboard (recentes) e pela tela
   de Lançamentos (com ações de editar/excluir). */
export function TransactionTable({
  transactions,
  onEdit,
  onDelete,
  emptyMessage = "Nenhum lançamento encontrado.",
}: TransactionTableProps) {
  const { lastAddedId, currency } = useTransactions();
  if (transactions.length === 0) {
    return (
      <p className="rounded-lg border border-dashed border-primary/40 p-6 text-center text-sm text-muted-foreground">
        {emptyMessage}
      </p>
    );
  }

  const hasActions = !!onEdit || !!onDelete;

  return (
    <div className="max-h-[420px] overflow-auto rounded-lg border border-border">
      <table className="w-full text-sm">
        <thead className="sticky top-0 bg-muted text-left text-xs text-muted-foreground">
          <tr>
            <th className="px-3 py-2 font-bold">Data</th>
            <th className="px-3 py-2 font-bold">Descrição</th>
            <th className="px-3 py-2 font-bold">Categoria</th>
            <th className="px-3 py-2 font-bold">Tipo</th>
            <th className="px-3 py-2 text-right font-bold">Valor</th>
            <th className="px-3 py-2 font-bold">Status</th>
            {hasActions && <th className="px-3 py-2 text-right font-bold">Ações</th>}
          </tr>
        </thead>
        <tbody>
          {transactions.map((t) => (
            <tr
              key={t.id}
              className={`border-t border-border ${lastAddedId === t.id ? "nexo-enter" : ""}`}
            >
              <td className="whitespace-nowrap px-3 py-2">{formatDate(t.date)}</td>
              <td className="max-w-[180px] truncate px-3 py-2 font-bold" title={t.description}>
                {t.description}
              </td>
              <td className="px-3 py-2">{t.category}</td>
              <td className="px-3 py-2">
                <span
                  className={`rounded-full px-2 py-0.5 text-xs font-bold ${t.type === "income" ? "bg-income-soft text-income" : "bg-expense-soft text-expense"}`}
                >
                  {t.type === "income" ? "Entrada" : "Saída"}
                </span>
              </td>
              <td
                className={`whitespace-nowrap px-3 py-2 text-right font-bold ${t.type === "income" ? "text-income" : "text-expense"}`}
              >
                {t.type === "income" ? "+" : "−"} {formatBRL(t.amount, currency)}
              </td>
              <td className="px-3 py-2">
                <span
                  className={`rounded-full px-2 py-0.5 text-xs font-bold ${t.status === "confirmado" ? "bg-income-soft text-income" : "bg-muted text-muted-foreground"}`}
                >
                  {t.status === "confirmado" ? "Confirmado" : "Pendente"}
                </span>
              </td>
              {hasActions && (
                <td className="px-3 py-2">
                  <div className="flex justify-end gap-1">
                    {onEdit && (
                      <button
                        type="button"
                        onClick={() => onEdit(t)}
                        aria-label={`Editar ${t.description}`}
                        className="rounded p-1 text-muted-foreground hover:bg-primary-soft hover:text-primary"
                      >
                        <Pencil className="h-4 w-4" />
                      </button>
                    )}
                    {onDelete && (
                      <button
                        type="button"
                        onClick={() => onDelete(t)}
                        aria-label={`Excluir ${t.description}`}
                        className="rounded p-1 text-muted-foreground hover:bg-expense-soft hover:text-expense"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
