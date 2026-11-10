import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { AppLayout } from "@/components/AppLayout";
import { MonthSelect } from "@/components/MonthSelect";
import { SummaryCards } from "@/components/SummaryCards";
import { TransactionTable } from "@/components/TransactionTable";
import { useTransactions } from "@/hooks/useTransactions";
import { Handshake, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  calcTotals,
  currentMonthKey,
  expensesByCategory,
  filterByMonth,
  formatBRL,
  monthOptions,
  prevMonthKey,
} from "@/lib/transactions";

export const Route = createFileRoute("/dashboard")({
  head: () => ({
    meta: [
      { title: "Dashboard | Nexo" },
      { name: "description", content: "Acompanhe seu desempenho financeiro na Nexo." },
      { property: "og:title", content: "Dashboard | Nexo" },
      { property: "og:description", content: "Acompanhe seu desempenho financeiro na Nexo." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: DashboardPage,
});

// Paleta do gráfico: variações de azul da identidade Nexo.
const CHART_COLORS = [
  "var(--nexo-chart-1)",
  "var(--nexo-chart-2)",
  "var(--nexo-chart-3)",
  "var(--nexo-chart-4)",
  "var(--nexo-chart-5)",
  "var(--nexo-chart-6)",
];

function DashboardPage() {
  const { transactions, loaded, currency, profile } = useTransactions();
  const [month, setMonth] = useState(currentMonthKey());
  const [reduceMotion, setReduceMotion] = useState(true);
  useEffect(() => {
    const query = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => setReduceMotion(query.matches);
    update();
    query.addEventListener("change", update);
    return () => query.removeEventListener("change", update);
  }, []);

  const filtered = filterByMonth(transactions, month);
  const previous = filterByMonth(transactions, prevMonthKey(month));
  const byCategory = expensesByCategory(filtered);
  const totalExpense = calcTotals(filtered).expense;

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
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="break-words text-2xl font-bold text-foreground">
              Seja Bem vindo, {profile.name || "Usuário"}!
            </h1>
            <p className="text-sm text-muted-foreground">
              Aqui você acompanha o seu desempenho financeiro
            </p>
          </div>
          <MonthSelect value={month} onChange={setMonth} options={monthOptions(transactions)} />
        </div>

        <SummaryCards current={filtered} previous={previous} />
        {transactions.length === 0 && (
          <section
            className="nexo-enter flex flex-col items-center gap-4 border-y border-border py-8 text-center"
            aria-labelledby="welcome-title"
          >
            <Handshake className="h-7 w-7 text-primary" aria-hidden="true" />
            <h2 id="welcome-title" className="text-xl font-bold text-foreground">
              Seja bem-vindo ao Nexo!
            </h2>
            <p className="max-w-2xl text-sm text-muted-foreground">
              Você ainda não possui lançamentos. Registre sua primeira receita ou despesa para
              começar a acompanhar sua vida financeira.
            </p>
            <Button
              asChild
              variant="secondary"
              className="h-auto min-h-10 w-full max-w-2xl whitespace-normal"
            >
              <Link to="/lancamentos">
                Fazer meu primeiro lançamento <ArrowRight />
              </Link>
            </Button>
          </section>
        )}

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <section className="min-w-0 rounded-xl border border-primary/40 bg-card p-5 shadow-sm">
            <div className="flex items-start justify-between gap-2">
              <div>
                <h2 className="font-bold text-foreground">Despesas por categoria</h2>
                <p className="text-xs text-muted-foreground">Percentual gasto por categoria</p>
              </div>
            </div>
            {byCategory.length === 0 ? (
              <p className="mt-6 rounded-lg border border-dashed border-primary/40 p-6 text-center text-sm text-muted-foreground">
                Nenhuma despesa registrada neste período.
              </p>
            ) : (
              <div className="mt-4 flex flex-col items-center gap-4 pt-14 sm:flex-row">
                <div className="relative h-48 w-48 shrink-0">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={byCategory}
                        dataKey="total"
                        nameKey="category"
                        innerRadius={55}
                        outerRadius={85}
                        strokeWidth={0}
                        isAnimationActive={!reduceMotion}
                        animationDuration={220}
                      >
                        {byCategory.map((entry, i) => (
                          <Cell key={entry.category} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip
                        position={{ x: 0, y: -52 }}
                        allowEscapeViewBox={{ x: true, y: true }}
                        animationDuration={220}
                        isAnimationActive={!reduceMotion}
                        content={({ active, payload }) =>
                          active && payload?.[0] ? (
                            <div className="pointer-events-none max-w-48 rounded border border-border bg-popover px-3 py-2 text-xs text-popover-foreground shadow-sm">
                              <span className="block truncate font-bold">{payload[0].name}</span>
                              {formatBRL(Number(payload[0].value), currency)}
                            </div>
                          ) : null
                        }
                      />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center text-center">
                    <span className="max-w-[90px] text-[9px] text-muted-foreground">
                      Total gasto no período
                    </span>
                    <span className="text-sm font-bold text-foreground">
                      {formatBRL(totalExpense, currency)}
                    </span>
                  </div>
                </div>
                <ul className="flex w-full flex-col gap-2 text-xs">
                  {byCategory.map((entry, i) => (
                    <li key={entry.category} className="flex items-center gap-2">
                      <span
                        className="h-2.5 w-2.5 shrink-0 rounded-full"
                        style={{ backgroundColor: CHART_COLORS[i % CHART_COLORS.length] }}
                      />
                      <span className="flex-1 truncate text-foreground">{entry.category}</span>
                      <span className="text-muted-foreground">
                        {formatBRL(entry.total, currency)}
                      </span>
                      <span className="w-10 text-right font-bold text-foreground">
                        {Math.round(entry.percent)}%
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </section>

          <section className="min-w-0 rounded-xl border border-primary/40 bg-card p-5 shadow-sm">
            <div className="flex items-start justify-between gap-2">
              <div>
                <h2 className="font-bold text-foreground">Últimos Lançamentos</h2>
                <p className="text-xs text-muted-foreground">
                  Veja as movimentações mais recentes do seu negócio
                </p>
              </div>
              <Link to="/lancamentos" className="text-xs font-bold text-link hover:underline">
                Ver todos
              </Link>
            </div>
            <div className="mt-4">
              <TransactionTable
                transactions={filtered.slice(0, 6)}
                emptyMessage="Nenhum lançamento recente neste período."
              />
            </div>
          </section>
        </div>
      </div>
    </AppLayout>
  );
}
