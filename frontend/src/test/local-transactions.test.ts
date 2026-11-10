import { beforeEach, describe, expect, it } from "vitest";
import { endLocalScope, loadLocalScope, startLocalScope } from "@/lib/local-identity";
import { loadTransactions, saveTransactions, type Transaction } from "@/lib/transactions";

const a = `local-${"a".repeat(64)}`;
const b = `local-${"b".repeat(64)}`;
const real: Transaction = {
  id: "real",
  description: "Receita cadastrada",
  amount: 500,
  date: "2026-11-09",
  category: "Salário",
  type: "income",
  status: "confirmado",
};

describe("lançamentos locais separados", () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
  });
  it("novo escopo começa vazio mesmo com legado salvo", () => {
    saveTransactions([real]);
    expect(loadTransactions(a)).toEqual([]);
    expect(loadTransactions()).toEqual([real]);
  });
  it("não lê legado quando não há identificação", () => {
    saveTransactions([real]);
    expect(loadTransactions(null)).toEqual([]);
  });
  it("separa dois escopos sem copiar dados", () => {
    saveTransactions([real], a);
    expect(loadTransactions(b)).toEqual([]);
    saveTransactions([{ ...real, id: "outro", amount: 100 }], b);
    expect(loadTransactions(a)).toEqual([real]);
    expect(loadTransactions(b)[0]?.amount).toBe(100);
  });
  it("preserva o legado byte a byte", () => {
    saveTransactions([real]);
    const before = localStorage.getItem("nexo:transactions");
    saveTransactions([], a);
    expect(localStorage.getItem("nexo:transactions")).toBe(before);
  });
  it("recarga/reentrada mantêm registros e exclusão não recria exemplos", () => {
    saveTransactions([real], a);
    expect(loadTransactions(a)).toEqual([real]);
    saveTransactions([], a);
    expect(loadTransactions(a)).toEqual([]);
  });
  it("escopo inválido não lê nem grava", () => {
    saveTransactions([real], "invalido");
    expect(loadTransactions("invalido")).toEqual([]);
    expect(localStorage.length).toBe(0);
  });
  it("normaliza e-mail, restaura sessão e não armazena credenciais", async () => {
    const scope = await startLocalScope(" Teste@exemplo.com ");
    expect(await startLocalScope("teste@exemplo.com")).toBe(scope);
    expect(loadLocalScope()).toBe(scope);
    expect(sessionStorage.getItem("nexo:local-session")).not.toContain("@");
    endLocalScope();
    expect(loadLocalScope()).toBeNull();
  });
});
