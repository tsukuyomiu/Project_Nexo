import { beforeEach, describe, expect, it } from "vitest";
import { loadTransactions, saveTransactions, type Transaction } from "@/lib/transactions";
import { validateSignup } from "@/lib/signup-validation";

const valid = { name: "Luann", email: "teste@exemplo.com", password: "123456", confirm: "123456" };

describe("cadastro obrigatório", () => {
  it.each(["name", "email", "password", "confirm"] as const)(
    "bloqueia %s composto apenas por espaços",
    (key) => {
      expect(validateSignup({ ...valid, [key]: "   " }, true)[key]).toBeTruthy();
    },
  );
  it("mantém validação do formato de e-mail", () => {
    expect(validateSignup({ ...valid, email: "invalido" }, true).email).toBe(
      "Informe um email válido.",
    );
  });
  it("mantém mínimo de seis caracteres de senha", () => {
    expect(validateSignup({ ...valid, password: "12345" }, true).password).toBe(
      "A senha deve ter ao menos 6 caracteres.",
    );
  });
  it("mantém confirmação igual à senha", () => {
    expect(validateSignup({ ...valid, confirm: "654321" }, true).confirm).toBe(
      "As senhas não coincidem.",
    );
  });
  it("exige o aceite dos termos", () => {
    expect(validateSignup(valid, false).terms).toBeTruthy();
  });
  it("permite formulário válido", () => {
    expect(validateSignup(valid, true)).toEqual({});
  });
});

describe("preservação dos lançamentos", () => {
  beforeEach(() => localStorage.clear());
  it("não cria exemplos quando não há armazenamento", () => {
    expect(loadTransactions()).toEqual([]);
    expect(localStorage.getItem("nexo:transactions")).toBeNull();
  });
  it("preserva todos os campos e valores dos registros existentes", () => {
    const list: Transaction[] = [
      {
        id: "real-1",
        description: "Receita real",
        amount: 1234.56,
        date: "2026-11-07",
        category: "Serviços",
        type: "income",
        status: "confirmado",
      },
    ];
    saveTransactions(list);
    const before = localStorage.getItem("nexo:transactions");
    expect(loadTransactions()).toEqual(list);
    expect(localStorage.getItem("nexo:transactions")).toBe(before);
  });
  it("mantém lista vazia depois de excluir todos os registros", () => {
    saveTransactions([]);
    expect(loadTransactions()).toEqual([]);
  });
});
