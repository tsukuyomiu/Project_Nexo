// PONTO ÚNICO DE INTEGRAÇÃO da alteração de senha do usuário logado.
// Conectado diretamente ao Back-End FastAPI (/api/v1/auth/change-password).

import { API_BASE_URL, getAuthToken } from "@/lib/api";

export interface ChangePasswordResult {
  ok: boolean;
  message?: string;
}

export async function changePassword(
  current: string,
  next: string,
): Promise<ChangePasswordResult> {
  const token = getAuthToken();
  if (!token) {
    return {
      ok: false,
      message: "Faça login novamente para alterar sua senha.",
    };
  }
  try {
    const res = await fetch(`${API_BASE_URL}/auth/change-password`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ current, next, confirm: next }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      return {
        ok: false,
        message: data?.detail || data?.message || "Não foi possível alterar a senha.",
      };
    }
    return {
      ok: true,
      message: data?.message || "Senha alterada com sucesso!",
    };
  } catch {
    return {
      ok: false,
      message: "Não foi possível conectar ao servidor Back-End na porta 8000.",
    };
  }
}
