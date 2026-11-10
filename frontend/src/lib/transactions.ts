// Camada única de dados dos lançamentos do Nexo.
// PERSISTÊNCIA TEMPORÁRIA: usa localStorage apenas para o protótipo e será
// substituída pela integração com o Back-End. Para trocar, altere apenas
// loadTransactions/saveTransactions — o restante do app não muda.
import { validLocalScope } from "@/lib/local-identity";

export type TransactionType = "income" | "expense";
export type TransactionStatus = "confirmado" | "pendente";

export interface Transaction {
  id: string;
  description: string;
  amount: number; // sempre positivo; o sinal é dado pelo tipo
  date: string; // ISO YYYY-MM-DD
  category: string;
  type: TransactionType;
  status: TransactionStatus;
}

export const INCOME_CATEGORIES = ["Salário", "Vendas", "Serviços", "Investimentos", "Outros"];
export const EXPENSE_CATEGORIES = [
  "Alimentação",
  "Transporte",
  "Moradia",
  "Saúde",
  "Lazer",
  "Educação",
  "Supermercado",
  "Serviços",
  "Outros",
];

const STORAGE_KEY = "nexo:transactions";

function newId(): string {
  return typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : `tx-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function pad(n: number) {
  return String(n).padStart(2, "0");
}

export function todayISO(): string {
  const d = new Date();
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

export function loadTransactions(scope?: string | null): Transaction[] {
  // undefined mantém o adaptador legado para inspeção/testes. O app sempre
  // fornece o escopo explícito; null significa sem identificação, nunca legado.
  if (scope === null || (scope !== undefined && !validLocalScope(scope))) return [];
  try {
    const raw = localStorage.getItem(scope === undefined ? STORAGE_KEY : `${STORAGE_KEY}:${scope}`);
    if (raw === null) return []; // não cria exemplos nem remove registros existentes
    const parsed: unknown = JSON.parse(raw);
    return Array.isArray(parsed) ? (parsed as Transaction[]) : [];
  } catch {
    return []; // JSON inválido ou armazenamento indisponível: lista vazia
  }
}

export function saveTransactions(list: Transaction[], scope?: string | null): void {
  if (scope === null || (scope !== undefined && !validLocalScope(scope))) return;
  try {
    localStorage.setItem(
      scope === undefined ? STORAGE_KEY : `${STORAGE_KEY}:${scope}`,
      JSON.stringify(list),
    );
  } catch {
    // armazenamento cheio ou indisponível: ignora sem quebrar o app
  }
}

export function createTransaction(data: Omit<Transaction, "id">): Transaction {
  return { ...data, id: newId() };
}

// Ordenação única do app: data decrescente; o desempate é a ordem de
// inserção (novos entram no início da coleção e o sort é estável).
export function sortTransactions(list: Transaction[]): Transaction[] {
  return [...list].sort((a, b) => b.date.localeCompare(a.date));
}

export interface Totals {
  income: number;
  expense: number;
  balance: number;
}

// Regra de cálculo única, usada por Dashboard, Lançamentos e Perfil.
export function calcTotals(list: Transaction[]): Totals {
  const income = list.filter((t) => t.type === "income").reduce((s, t) => s + t.amount, 0);
  const expense = list.filter((t) => t.type === "expense").reduce((s, t) => s + t.amount, 0);
  return { income, expense, balance: income - expense };
}

// Distribuição das despesas por categoria (percentual do total de despesas).
export function expensesByCategory(
  list: Transaction[],
): { category: string; total: number; percent: number }[] {
  const expenses = list.filter((t) => t.type === "expense");
  const total = expenses.reduce((s, t) => s + t.amount, 0);
  const map = new Map<string, number>();
  for (const t of expenses) map.set(t.category, (map.get(t.category) ?? 0) + t.amount);
  return [...map.entries()]
    .map(([category, value]) => ({
      category,
      total: value,
      percent: total > 0 ? (value / total) * 100 : 0,
    }))
    .sort((a, b) => b.total - a.total);
}

// Aceita formato monetário brasileiro ("1.234,56") ou ponto decimal;
// rejeita vazio, zero, negativo e não numérico.
export function parseBRValue(v: string): number | null {
  const clean = v.trim().replace(/R\$/g, "").replace(/\s/g, "");
  if (!clean) return null;
  const normalized = clean.includes(",") ? clean.replace(/\./g, "").replace(",", ".") : clean;
  const n = Number(normalized);
  return Number.isFinite(n) && n > 0 ? n : null;
}

export const formatBRL = (v: number, currency: "BRL" | "USD" | "EUR" | "GBP" = "BRL"): string =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency }).format(v);
export const currencySymbol = (currency: "BRL" | "USD" | "EUR" | "GBP"): string =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency })
    .formatToParts(0)
    .find((part) => part.type === "currency")?.value ?? "R$";

// Converte "YYYY-MM-DD" para "dd/MM/yyyy" sem new Date(iso), que pode
// retroceder um dia por causa do fuso horário.
export function formatDate(iso: string): string {
  const [y, m, d] = iso.split("-");
  return `${d}/${m}/${y}`;
}

export function monthKey(iso: string): string {
  return iso.slice(0, 7); // "YYYY-MM"
}

export function currentMonthKey(): string {
  return monthKey(todayISO());
}

export function prevMonthKey(key: string): string {
  const [y = 0, m = 1] = key.split("-").map(Number);
  const d = new Date(y, m - 2, 1);
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}`;
}

const MONTHS_PT = [
  "Janeiro",
  "Fevereiro",
  "Março",
  "Abril",
  "Maio",
  "Junho",
  "Julho",
  "Agosto",
  "Setembro",
  "Outubro",
  "Novembro",
  "Dezembro",
];

export function monthLabel(key: string): string {
  const [y, m] = key.split("-");
  return `${MONTHS_PT[Number(m) - 1]}/${y}`;
}

// Meses disponíveis para o seletor: meses presentes nos dados + mês atual.
export function monthOptions(list: Transaction[]): string[] {
  const keys = new Set(list.map((t) => monthKey(t.date)));
  keys.add(currentMonthKey());
  return [...keys].sort().reverse();
}

export function filterByMonth(list: Transaction[], key: string): Transaction[] {
  return list.filter((t) => monthKey(t.date) === key);
}
