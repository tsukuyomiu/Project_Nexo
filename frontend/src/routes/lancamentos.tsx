import { createFileRoute } from "@tanstack/react-router";
import { Calendar, FilterX, Plus, Tag, ArrowDownUp } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { AppLayout } from "@/components/AppLayout";
import { MonthSelect } from "@/components/MonthSelect";
import { SummaryCards } from "@/components/SummaryCards";
import { TransactionModal } from "@/components/TransactionModal";
import { TransactionTable } from "@/components/TransactionTable";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useTransactions } from "@/hooks/useTransactions";
import {
  EXPENSE_CATEGORIES,
  INCOME_CATEGORIES,
  monthKey,
  monthOptions,
  type Transaction,
  type TransactionType,
} from "@/lib/transactions";

export const Route = createFileRoute("/lancamentos")({
  head: () => ({
    meta: [
      { title: "Lançamentos | Nexo" },
      {
        name: "description",
        content: "Registre, visualize e gerencie suas movimentações financeiras.",
      },
      { property: "og:title", content: "Lançamentos | Nexo" },
      {
        property: "og:description",
        content: "Registre, visualize e gerencie suas movimentações financeiras.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: TransactionsPage,
});

const ALL_CATEGORIES = [...new Set([...INCOME_CATEGORIES, ...EXPENSE_CATEGORIES])];

function TransactionsPage() {
  const { transactions, remove, loaded } = useTransactions();
  const [month, setMonth] = useState("all");
  const [type, setType] = useState<"all" | TransactionType>("all");
  const [category, setCategory] = useState("all");
  const [modal, setModal] = useState<{
    open: boolean;
    type: TransactionType;
    editing: Transaction | null;
  }>({
    open: false,
    type: "income",
    editing: null,
  });
  const [deleting, setDeleting] = useState<Transaction | null>(null);

  // Filtros combináveis (AND): atualizam lista e resumo imediatamente.
  const filtered = transactions.filter(
    (t) =>
      (month === "all" || monthKey(t.date) === month) &&
      (type === "all" || t.type === type) &&
      (category === "all" || t.category === category),
  );

  function clearFilters() {
    setMonth("all");
    setType("all");
    setCategory("all");
  }

  function confirmDelete() {
    if (!deleting) return;
    remove(deleting.id);
    toast.success("Lançamento excluído com sucesso!");
    setDeleting(null);
  }

  if (!loaded)
    return (
      <AppLayout>
        <p role="status" className="text-sm text-muted-foreground">
          Carregando lançamentos…
        </p>
      </AppLayout>
    );

  return (
    <AppLayout>
      <div className="flex flex-col gap-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-foreground">Lançamentos!</h1>
            <p className="text-sm text-muted-foreground">
              Registre, visualize e gerencie todas as suas movimentações financeiras.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => setModal({ open: true, type: "income", editing: null })}
              className="flex h-11 items-center gap-2 rounded-xl bg-income px-5 text-sm font-bold text-income-foreground shadow-btn hover:brightness-110"
            >
              <span className="grid h-6 w-6 place-items-center rounded-full bg-income-foreground/20">
                <Plus className="h-4 w-4" />
              </span>
              Nova Receita
            </button>
            <button
              type="button"
              onClick={() => setModal({ open: true, type: "expense", editing: null })}
              className="flex h-11 items-center gap-2 rounded-xl bg-expense px-5 text-sm font-bold text-expense-foreground shadow-btn hover:brightness-110"
            >
              <span className="grid h-6 w-6 place-items-center rounded-full bg-expense-foreground/20">
                <Plus className="h-4 w-4" />
              </span>
              Nova Despesa
            </button>
          </div>
        </div>

        <section className="flex flex-wrap items-end gap-4 rounded-xl border border-primary/40 bg-card p-4 shadow-sm">
          <div>
            <span className="mb-1 flex items-center gap-1 text-xs font-bold text-foreground">
              <Calendar className="h-3 w-3" /> Mês
            </span>
            <MonthSelect
              value={month}
              onChange={setMonth}
              options={monthOptions(transactions)}
              allowAll
            />
          </div>
          <div>
            <span className="mb-1 flex items-center gap-1 text-xs font-bold text-foreground">
              <ArrowDownUp className="h-3 w-3" /> Tipo
            </span>
            <Select value={type} onValueChange={(v) => setType(v as typeof type)}>
              <SelectTrigger className="w-[150px] bg-background" aria-label="Filtrar por tipo">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos</SelectItem>
                <SelectItem value="income">Receita</SelectItem>
                <SelectItem value="expense">Despesa</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <span className="mb-1 flex items-center gap-1 text-xs font-bold text-foreground">
              <Tag className="h-3 w-3" /> Categoria
            </span>
            <Select value={category} onValueChange={setCategory}>
              <SelectTrigger className="w-[170px] bg-background" aria-label="Filtrar por categoria">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todas</SelectItem>
                {ALL_CATEGORIES.map((c) => (
                  <SelectItem key={c} value={c}>
                    {c}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <button
            type="button"
            onClick={clearFilters}
            className="flex h-9 items-center gap-2 rounded-lg border border-border bg-background px-4 text-xs font-bold text-foreground shadow-btn hover:bg-muted"
          >
            <FilterX className="h-3.5 w-3.5" /> Limpar Filtros
          </button>
        </section>

        {/* O resumo reflete os filtros aplicados, com a mesma função de cálculo do Dashboard */}
        <SummaryCards current={filtered} />

        <TransactionTable
          transactions={filtered}
          onEdit={(t) => setModal({ open: true, type: t.type, editing: t })}
          onDelete={setDeleting}
          emptyMessage={
            transactions.length === 0
              ? "Você ainda não possui lançamentos. Adicione sua primeira movimentação em Nova Receita ou Nova Despesa."
              : "Nenhum resultado encontrado para os filtros aplicados."
          }
        />
      </div>

      <TransactionModal
        open={modal.open}
        onOpenChange={(open) => setModal((cur) => ({ ...cur, open }))}
        type={modal.type}
        editing={modal.editing}
      />

      <AlertDialog open={!!deleting} onOpenChange={(open) => !open && setDeleting(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Excluir lançamento?</AlertDialogTitle>
            <AlertDialogDescription>
              Esta ação não pode ser desfeita. O lançamento &quot;{deleting?.description}&quot; será
              removido permanentemente.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmDelete}
              className="bg-expense text-expense-foreground hover:bg-expense/90"
            >
              Excluir
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </AppLayout>
  );
}
