import { useEffect, useState } from "react";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useTransactions } from "@/hooks/useTransactions";
import { FieldLabel } from "@/components/FieldLabel";
import { Button } from "@/components/ui/button";
import {
  EXPENSE_CATEGORIES,
  INCOME_CATEGORIES,
  parseBRValue,
  todayISO,
  currencySymbol,
  type Transaction,
  type TransactionStatus,
  type TransactionType,
} from "@/lib/transactions";

interface TransactionModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  type: TransactionType;
  editing?: Transaction | null;
}

type Errors = Partial<Record<"description" | "amount" | "date" | "category", string | undefined>>;

const inputClass =
  "h-9 w-full rounded-lg border border-border bg-background px-3 text-sm text-foreground shadow-field outline-none focus:ring-2 focus:ring-secondary";

/* Modal ÚNICO de lançamento: usado por "Nova Receita", "Nova Despesa" e pela
   edição. O tipo é definido pelo botão que abriu o modal e não é editável. */
export function TransactionModal({ open, onOpenChange, type, editing }: TransactionModalProps) {
  const { add, update, currency } = useTransactions();
  const [description, setDescription] = useState("");
  const [amount, setAmount] = useState("");
  const [date, setDate] = useState(todayISO());
  const [category, setCategory] = useState("");
  const [status, setStatus] = useState<TransactionStatus>("confirmado");
  const [errors, setErrors] = useState<Errors>({});
  const [submitting, setSubmitting] = useState(false);

  const categories = type === "income" ? INCOME_CATEGORIES : EXPENSE_CATEGORIES;
  const title = editing ? "Editar Lançamento" : type === "income" ? "Nova Receita" : "Nova Despesa";

  // Ao abrir: pré-preenche na edição ou limpa tudo para um novo lançamento.
  useEffect(() => {
    if (!open) return;
    setDescription(editing?.description ?? "");
    setAmount(editing ? String(editing.amount).replace(".", ",") : "");
    setDate(editing?.date ?? todayISO());
    setCategory(editing?.category ?? "");
    setStatus(editing?.status ?? "confirmado");
    setErrors({});
    setSubmitting(false);
  }, [open, editing]);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (submitting) return; // evita duplo envio
    const next: Errors = {};
    const value = parseBRValue(amount);
    if (!description.trim()) next.description = "Informe uma descrição.";
    if (!amount.trim()) next.amount = "Campo obrigatório.";
    else if (value === null) next.amount = "Informe um valor maior que zero.";
    if (!date) next.date = "Informe uma data válida.";
    if (!category) next.category = "Selecione uma categoria.";
    setErrors(next);
    if (Object.keys(next).length > 0 || value === null) {
      const first = Object.keys(next)[0];
      if (first) e.currentTarget.querySelector<HTMLElement>(`#tx-${first}`)?.focus();
      return;
    }

    setSubmitting(true);
    const data = { description: description.trim(), amount: value, date, category, type, status };
    if (editing) {
      update(editing.id, data);
      toast.success("Lançamento atualizado com sucesso!");
    } else {
      add(data);
      toast.success(
        type === "income" ? "Receita adicionada com sucesso!" : "Despesa adicionada com sucesso!",
      );
    }
    onOpenChange(false);
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>
            Preencha as informações abaixo para registrar uma nova movimentação financeira
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <FieldLabel htmlFor="tx-date" required>
                Data
              </FieldLabel>
              <input
                id="tx-date"
                type="date"
                value={date}
                onChange={(e) => {
                  setDate(e.target.value);
                  setErrors((current) => ({ ...current, date: undefined }));
                }}
                aria-required="true"
                aria-describedby={errors.date ? "tx-date-error" : undefined}
                aria-invalid={!!errors.date}
                className={inputClass}
              />
              {errors.date && (
                <p id="tx-date-error" className="mt-1 text-xs text-destructive">
                  {errors.date}
                </p>
              )}
            </div>
            <div>
              <FieldLabel htmlFor="tx-amount" required>
                Valor
              </FieldLabel>
              <div
                className={`flex items-center rounded-lg border border-border shadow-field focus-within:ring-2 focus-within:ring-secondary ${errors.amount ? "ring-1 ring-destructive" : ""}`}
              >
                <span className="border-r border-border px-3 text-sm text-muted-foreground">
                  {currencySymbol(currency)}
                </span>
                <input
                  id="tx-amount"
                  inputMode="decimal"
                  placeholder="0,00"
                  value={amount}
                  onChange={(e) => {
                    setAmount(e.target.value);
                    if (parseBRValue(e.target.value) !== null)
                      setErrors((current) => ({ ...current, amount: undefined }));
                  }}
                  aria-invalid={!!errors.amount}
                  aria-required="true"
                  aria-describedby={errors.amount ? "tx-amount-error" : undefined}
                  className="h-9 min-w-0 flex-1 rounded-r-lg bg-background px-3 text-sm outline-none"
                />
              </div>
              {errors.amount && (
                <p id="tx-amount-error" className="mt-1 text-xs text-destructive">
                  {errors.amount}
                </p>
              )}
            </div>
          </div>

          <div>
            <FieldLabel htmlFor="tx-description" required>
              Descrição
            </FieldLabel>
            <input
              id="tx-description"
              value={description}
              maxLength={100}
              onChange={(e) => {
                setDescription(e.target.value);
                if (e.target.value.trim())
                  setErrors((current) => ({ ...current, description: undefined }));
              }}
              aria-invalid={!!errors.description}
              aria-required="true"
              aria-describedby={errors.description ? "tx-description-error" : undefined}
              className={inputClass}
            />
            <div className="mt-1 flex items-center justify-between">
              {errors.description ? (
                <p id="tx-description-error" className="text-xs text-destructive">
                  {errors.description}
                </p>
              ) : (
                <span />
              )}
              <span className="text-[10px] text-muted-foreground">{description.length}/100</span>
            </div>
          </div>

          <div>
            <FieldLabel htmlFor="tx-category" required>
              Categoria
            </FieldLabel>
            <Select
              value={category}
              onValueChange={(value) => {
                setCategory(value);
                setErrors((current) => ({ ...current, category: undefined }));
              }}
            >
              <SelectTrigger
                id="tx-category"
                aria-required="true"
                aria-describedby={errors.category ? "tx-category-error" : undefined}
                aria-invalid={!!errors.category}
                className="w-full"
              >
                <SelectValue placeholder="Selecione uma categoria" />
              </SelectTrigger>
              <SelectContent>
                {categories.map((c) => (
                  <SelectItem key={c} value={c}>
                    {c}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.category && (
              <p id="tx-category-error" className="mt-1 text-xs text-destructive">
                {errors.category}
              </p>
            )}
          </div>

          <div>
            <label htmlFor="tx-type" className="mb-1 block text-xs font-bold text-foreground">
              Tipo
            </label>
            <input
              id="tx-type"
              value={type === "income" ? "Receita" : "Despesa"}
              disabled
              className={`${inputClass} opacity-60`}
            />
          </div>

          <div>
            <label htmlFor="tx-status" className="mb-1 block text-xs font-bold text-foreground">
              Status
            </label>
            <Select value={status} onValueChange={(v) => setStatus(v as TransactionStatus)}>
              <SelectTrigger id="tx-status" className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="confirmado">Confirmado</SelectItem>
                <SelectItem value="pendente">Pendente</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="mt-2 grid grid-cols-2 gap-4">
            <Button
              type="button"
              onClick={() => onOpenChange(false)}
              className="h-10 rounded-lg border border-border bg-background text-sm font-bold text-foreground shadow-btn hover:bg-muted"
            >
              Cancelar
            </Button>
            <Button
              type="submit"
              disabled={submitting}
              className={`h-10 rounded-lg text-sm font-bold shadow-btn hover:brightness-110 disabled:opacity-50 ${type === "income" ? "bg-income text-income-foreground" : "bg-expense text-expense-foreground"}`}
            >
              Salvar Lançamento
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
