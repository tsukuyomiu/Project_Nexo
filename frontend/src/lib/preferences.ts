import { z } from "zod";

export const currencySchema = z.enum(["BRL", "USD", "EUR", "GBP"]);
export type Currency = z.infer<typeof currencySchema>;
export const CURRENCIES: { value: Currency; label: string }[] = [
  { value: "BRL", label: "Real brasileiro (R$)" },
  { value: "USD", label: "Dólar americano (US$)" },
  { value: "EUR", label: "Euro (€)" },
  { value: "GBP", label: "Libra esterlina (£)" },
];
// Provisório por navegador, não por conta. Substituir estes adaptadores pela
// preferência vinculada ao usuário quando houver autenticação e Back-End.
const KEY = "nexo:preferences:prototype";
export function loadCurrency(): Currency {
  try {
    const parsed = currencySchema.safeParse(
      JSON.parse(localStorage.getItem(KEY) ?? "null")?.currency,
    );
    return parsed.success ? parsed.data : "BRL";
  } catch {
    return "BRL";
  }
}
export function saveCurrency(currency: Currency): boolean {
  try {
    localStorage.setItem(KEY, JSON.stringify({ currency: currencySchema.parse(currency) }));
    return true;
  } catch {
    return false;
  }
}
