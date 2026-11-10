import { z } from "zod";

// Identificação de protótipo, NÃO autenticação. O hash só evita gravar o e-mail
// em texto puro; não prova identidade nem protege contra acesso neste navegador.
const scopeSchema = z.string().regex(/^local-[a-f0-9]{64}$/);
const KEY = "nexo:local-session";
export function loadLocalScope(): string | null {
  try {
    const result = scopeSchema.safeParse(sessionStorage.getItem(KEY));
    return result.success ? result.data : null;
  } catch {
    return null;
  }
}
export async function startLocalScope(email: string): Promise<string> {
  const normalized = z.string().trim().email().max(255).parse(email).toLowerCase();
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(normalized));
  const scope = `local-${Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("")}`;
  sessionStorage.setItem(KEY, scope);
  return scope;
}
export function endLocalScope(): void {
  try {
    sessionStorage.removeItem(KEY);
  } catch {
    /* sem persistência disponível */
  }
}
export function validLocalScope(scope: string): boolean {
  return scopeSchema.safeParse(scope).success;
}
