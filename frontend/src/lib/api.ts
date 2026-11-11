// Cliente oficial de integração com o Back-End FastAPI (http://localhost:8000/api/v1)

export const API_BASE_URL = "http://localhost:8000/api/v1";

const TOKEN_KEY = "nexo:auth-token";
const USER_KEY = "nexo:auth-user";

export interface StoredAuthUser {
  id: string;
  name: string;
  email: string;
  role: "user" | "admin" | "auditor";
  currency: "BRL" | "USD" | "EUR" | "GBP";
  twoFactorEnabled?: boolean;
}

export function getAuthToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function getStoredAuthUser(): StoredAuthUser | null {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as StoredAuthUser) : null;
  } catch {
    return null;
  }
}

export function setAuthSession(token: string, user: StoredAuthUser): void {
  try {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  } catch {
    // ignore storage errors
  }
}

export function clearAuthSession(): void {
  try {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  } catch {
    // ignore
  }
}

async function requestJson<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getAuthToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg = data?.detail || data?.message || `Erro na comunicação com o servidor (${res.status}).`;
    throw new Error(msg);
  }
  return data as T;
}

export interface AuthApiResponse {
  ok: boolean;
  requires_2fa?: boolean;
  access_token?: string;
  expires_at?: string;
  user?: StoredAuthUser;
  message?: string;
  dev_code?: string;
  email_sent_smtp?: boolean;
}

export async function apiSignup(payload: {
  name: string;
  email: string;
  password: string;
  confirm: string;
  terms: boolean;
  account_type?: "user" | "admin";
  admin_code?: string;
}): Promise<AuthApiResponse> {
  return requestJson<AuthApiResponse>("/auth/signup", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function apiLogin(payload: {
  email: string;
  password: string;
}): Promise<AuthApiResponse> {
  return requestJson<AuthApiResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function apiVerify2FA(payload: {
  email: string;
  code: string;
}): Promise<AuthApiResponse> {
  return requestJson<AuthApiResponse>("/auth/verify-2fa", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function apiConnectGmailAndResend2FA(payload: {
  email: string;
  smtp_user?: string | undefined;
  smtp_app_password?: string | undefined;
}): Promise<AuthApiResponse> {
  return requestJson<AuthApiResponse>("/auth/connect-gmail-resend", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function apiOAuthLogin(payload: {
  provider: "google" | "apple";
  email: string;
  name: string;
  password?: string | undefined;
  account_type?: "user" | "admin" | undefined;
  admin_code?: string | undefined;
}): Promise<AuthApiResponse> {
  return requestJson<AuthApiResponse>("/auth/oauth", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function apiLogout(): Promise<void> {
  try {
    if (getAuthToken()) {
      await requestJson("/auth/logout", { method: "POST" });
    }
  } catch {
    // ignore
  } finally {
    clearAuthSession();
  }
}

export async function apiForgotPassword(email: string): Promise<{
  ok: boolean;
  message: string;
  dev_code?: string;
  email_sent_smtp?: boolean;
}> {
  return requestJson("/auth/forgot-password", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export async function apiResetPassword(payload: {
  email: string;
  code: string;
  new_password: string;
  confirm_password: string;
}): Promise<{ ok: boolean; message: string }> {
  return requestJson("/auth/reset-password", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export interface UserProfileApi {
  id: string;
  name: string;
  email: string;
  phone: string;
  birthDate: string;
  address: string;
  currency: "BRL" | "USD" | "EUR" | "GBP";
  twoFactorEnabled: boolean;
  role: "user" | "admin" | "auditor";
}

export async function apiGetMyProfile(): Promise<UserProfileApi> {
  return requestJson<UserProfileApi>("/users/me");
}

export async function apiUpdateMyProfile(payload: {
  name: string;
  email: string;
  phone: string;
  birthDate: string;
  address: string;
}): Promise<UserProfileApi> {
  return requestJson<UserProfileApi>("/users/me/profile", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function apiUpdateMyPreferences(payload: {
  currency: "BRL" | "USD" | "EUR" | "GBP";
  twoFactorEnabled?: boolean;
}): Promise<UserProfileApi> {
  return requestJson<UserProfileApi>("/users/me/preferences", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export interface TransactionApi {
  id: string;
  description: string;
  amount: number;
  date: string;
  category: string;
  type: "income" | "expense";
  status: "confirmado" | "pendente";
}

export async function apiListTransactions(): Promise<TransactionApi[]> {
  return requestJson<TransactionApi[]>("/transactions");
}

export async function apiCreateTransaction(
  payload: Omit<TransactionApi, "id">,
): Promise<TransactionApi> {
  return requestJson<TransactionApi>("/transactions", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function apiUpdateTransaction(
  id: string,
  payload: Omit<TransactionApi, "id">,
): Promise<TransactionApi> {
  return requestJson<TransactionApi>(`/transactions/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function apiDeleteTransaction(id: string): Promise<void> {
  await requestJson(`/transactions/${id}`, {
    method: "DELETE",
  });
}

export async function apiLogFrontendEvent(
  acao: string,
  resumo_humano: string,
  detalhes?: Record<string, unknown>,
): Promise<void> {
  try {
    await requestJson("/logs/frontend-event", {
      method: "POST",
      body: JSON.stringify({
        acao,
        resumo_humano,
        severidade: "INFO",
        detalhes,
      }),
    });
  } catch {
    // ignore telemetry errors
  }
}
