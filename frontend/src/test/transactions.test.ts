import { describe, expect, it } from "vitest";
import {
  calcTotals,
  expensesByCategory,
  formatBRL,
  formatDate,
  parseBRValue,
  sortTransactions,
  type Transaction,
} from "@/lib/transactions";

const tx = (over: Partial<Transaction>): Transaction => ({
  id: over.id ?? "1",
  description: "Teste",
  amount: 100,
  date: "2026-11-01",
  category: "Outros",
  type: "expense",
  status: "confirmado",
  ...over,
});

describe("calcTotals", () => {
  it("soma entradas, saídas e calcula o saldo", () => {
    const list = [
      tx({ type: "income", amount: 3450 }),
      tx({ type: "income", amount: 320 }),
      tx({ type: "expense", amount: 1980 }),
      tx({ type: "expense", amount: 99.9 }),
    ];
    const totals = calcTotals(list);
    expect(totals.income).toBeCloseTo(3770);
    expect(totals.expense).toBeCloseTo(2079.9);
    expect(totals.balance).toBeCloseTo(1690.1);
  });

  it("retorna zeros para lista vazia", () => {
    expect(calcTotals([])).toEqual({ income: 0, expense: 0, balance: 0 });
  });
});

describe("sortTransactions", () => {
  it("ordena por data decrescente e mantém estável o desempate por inserção", () => {
    const list = [
      tx({ id: "a", date: "2026-11-01" }),
      tx({ id: "b", date: "2026-11-03" }),
      tx({ id: "c", date: "2026-11-03" }),
      tx({ id: "d", date: "2026-10-30" }),
    ];
    expect(sortTransactions(list).map((t) => t.id)).toEqual(["b", "c", "a", "d"]);
  });
});

describe("expensesByCategory", () => {
  it("agrupa só despesas e calcula o percentual do total de despesas", () => {
    const list = [
      tx({ category: "Moradia", amount: 1200 }),
      tx({ category: "Lazer", amount: 400 }),
      tx({ category: "Moradia", amount: 400 }),
      tx({ type: "income", category: "Salário", amount: 5000 }),
    ];
    const result = expensesByCategory(list);
    expect(result).toHaveLength(2);
    expect(result[0]).toMatchObject({ category: "Moradia", total: 1600 });
    expect(result[0]!.percent).toBeCloseTo(80);
    expect(result[1]!.percent).toBeCloseTo(20);
  });
});

describe("parseBRValue", () => {
  it("aceita formato brasileiro com vírgula e ponto de milhar", () => {
    expect(parseBRValue("1.234,56")).toBeCloseTo(1234.56);
    expect(parseBRValue("R$ 45,90")).toBeCloseTo(45.9);
    expect(parseBRValue("100")).toBe(100);
  });

  it("rejeita vazio, zero, negativo e não numérico", () => {
    expect(parseBRValue("")).toBeNull();
    expect(parseBRValue("0")).toBeNull();
    expect(parseBRValue("-5,00")).toBeNull();
    expect(parseBRValue("abc")).toBeNull();
  });
});

describe("formatDate", () => {
  it("converte ISO para dd/MM/yyyy sem problema de fuso", () => {
    expect(formatDate("2026-11-02")).toBe("02/11/2026");
  });
});

describe("formatBRL", () => {
  it("formata em real no padrão pt-BR", () => {
    expect(formatBRL(1470)).toBe("R$ 1.470,00");
    expect(formatBRL(0)).toBe("R$ 0,00");
  });
});
