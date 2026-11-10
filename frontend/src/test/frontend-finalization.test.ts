import { beforeEach, describe, expect, it, vi } from "vitest";
import { emptyProfile, prepareProfile, profileSchema } from "@/lib/profile";
import { loadCurrency, saveCurrency, type Currency } from "@/lib/preferences";
import { calcTotals, currencySymbol, formatBRL, saveTransactions } from "@/lib/transactions";

describe("perfil temporário", () => {
  it("inicia sem dados pessoais fictícios", () => {
    expect(emptyProfile).toEqual({ name: "", email: "", phone: "", birthDate: "", address: "" });
  });
  it("valida e normaliza nome e e-mail sem gravar dados pessoais", () => {
    localStorage.clear();
    const result = prepareProfile({
      ...emptyProfile,
      name: " Luann ",
      email: " teste@exemplo.com ",
    });
    expect(result.name).toBe("Luann");
    expect(result.email).toBe("teste@exemplo.com");
    expect(localStorage.length).toBe(0);
  });
  it.each(["name", "email"] as const)("bloqueia %s vazio ou só espaços", (field) => {
    expect(
      profileSchema.safeParse({
        ...emptyProfile,
        name: "Luann",
        email: "teste@exemplo.com",
        [field]: "   ",
      }).success,
    ).toBe(false);
  });
  it("rejeita e-mail inválido", () => {
    expect(profileSchema.shape.email.safeParse("invalido").success).toBe(false);
  });
  it("mantém endereço opcional", () => {
    expect(profileSchema.shape.address.safeParse("").success).toBe(true);
  });
  it("limita nome a 100 caracteres", () => {
    expect(profileSchema.shape.name.safeParse("a".repeat(101)).success).toBe(false);
  });
  it("valida telefone e data quando preenchidos", () => {
    expect(profileSchema.shape.phone.safeParse("telefone").success).toBe(false);
    expect(profileSchema.shape.birthDate.safeParse("2026-02-31").success).toBe(false);
  });
});

describe("moeda provisória", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });
  it("usa BRL sem preferência", () => {
    expect(loadCurrency()).toBe("BRL");
  });
  it("usa BRL para dados inválidos", () => {
    localStorage.setItem("nexo:preferences:prototype", JSON.stringify({ currency: "JPY" }));
    expect(loadCurrency()).toBe("BRL");
    localStorage.setItem("nexo:preferences:prototype", "{");
    expect(loadCurrency()).toBe("BRL");
  });
  it.each(["BRL", "USD", "EUR", "GBP"] as Currency[])(
    "persiste %s sem alterar valores financeiros",
    (currency) => {
      const list = [
        {
          id: "real",
          description: "Receita",
          amount: 1234.56,
          date: "2026-11-08",
          category: "Salário",
          type: "income" as const,
          status: "confirmado" as const,
        },
      ];
      saveTransactions(list);
      const before = localStorage.getItem("nexo:transactions");
      expect(saveCurrency(currency)).toBe(true);
      expect(loadCurrency()).toBe(currency);
      expect(localStorage.getItem("nexo:transactions")).toBe(before);
      expect(calcTotals(list).income).toBe(1234.56);
    },
  );
  it.each([
    ["BRL", "R$"],
    ["USD", "US$"],
    ["EUR", "€"],
    ["GBP", "£"],
  ] as const)("formata %s com separadores pt-BR e sem conversão", (currency, symbol) => {
    expect(formatBRL(1234.56, currency)).toBe(`${symbol}\u00A01.234,56`);
    expect(currencySymbol(currency)).toBe(symbol);
  });
  it("informa falha de persistência", () => {
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("indisponível");
    });
    expect(saveCurrency("EUR")).toBe(false);
  });
});
