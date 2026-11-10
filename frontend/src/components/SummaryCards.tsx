import { ArrowDown, ArrowUp, Wallet } from "lucide-react";
import { calcTotals, formatBRL, type Transaction } from "@/lib/transactions";
import { useTransactions } from "@/hooks/useTransactions";

function pctChange(current: number, previous: number): number | null {
  if (previous <= 0) return null;
  return Math.round(((current - previous) / previous) * 100);
}

/* Cards de resumo (Entrada / Saídas / Total). Usados no Dashboard, em
   Lançamentos e no Perfil, sempre com a mesma função de cálculo. */
export function SummaryCards({
  current,
  previous,
}: {
  current: Transaction[];
  previous?: Transaction[];
}) {
  const { currency } = useTransactions();
  const totals = calcTotals(current);
  const prev = previous ? calcTotals(previous) : null;

  const cards = [
    {
      label: "Entrada",
      hint: "Total de receitas no mês",
      value: totals.income,
      icon: <ArrowUp className="h-5 w-5" />,
      iconClass: "bg-income-soft text-income",
      pct: prev ? pctChange(totals.income, prev.income) : null,
    },
    {
      label: "Saídas",
      hint: "Total de despesas no mês",
      value: totals.expense,
      icon: <ArrowDown className="h-5 w-5" />,
      iconClass: "bg-expense-soft text-expense",
      pct: prev ? pctChange(totals.expense, prev.expense) : null,
    },
    {
      label: "Total",
      hint: "Saldo do mês",
      value: totals.balance,
      icon: <Wallet className="h-5 w-5" />,
      iconClass: "bg-primary-soft text-primary",
      pct: prev ? pctChange(totals.balance, prev.balance) : null,
    },
  ];

  return (
    <div className="grid gap-4 sm:grid-cols-3">
      {cards.map((card) => (
        <section
          key={card.label}
          className="nexo-enter rounded-xl border border-primary/40 bg-card p-5 shadow-sm"
        >
          <div className="flex items-center gap-3">
            <span className={`grid h-10 w-10 place-items-center rounded-full ${card.iconClass}`}>
              {card.icon}
            </span>
            <div>
              <h3 className="text-sm font-bold text-foreground">{card.label}</h3>
              <p className="text-[10px] text-muted-foreground">{card.hint}</p>
            </div>
          </div>
          <p
            key={`${card.value}-${currency}`}
            className="nexo-enter mt-3 break-words text-2xl font-bold text-foreground"
          >
            {formatBRL(card.value, currency)}
          </p>
          {card.pct !== null && (
            <p
              className={`mt-1 flex items-center gap-1 text-[10px] ${card.pct >= 0 ? "text-income" : "text-expense"}`}
            >
              {card.pct >= 0 ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />}
              {Math.abs(card.pct)}% em relação ao mês anterior
            </p>
          )}
        </section>
      ))}
    </div>
  );
}
