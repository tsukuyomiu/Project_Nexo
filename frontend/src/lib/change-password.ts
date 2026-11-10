// PONTO ÚNICO DE INTEGRAÇÃO da alteração de senha do usuário logado.
// Hoje o projeto NÃO possui serviço de autenticação capaz de efetivar a
// troca (o login é apenas de interface). Quando o Back-End estiver
// disponível, implemente aqui a chamada real e retorne o resultado do
// serviço. Nunca armazene senhas em estado global, localStorage ou logs.

export interface ChangePasswordResult {
  ok: boolean;
  message?: string;
}

export async function changePassword(
  _current: string,
  _next: string,
): Promise<ChangePasswordResult> {
  return {
    ok: false,
    message:
      "A alteração efetiva de senha depende da integração com o serviço de autenticação e ainda não está disponível.",
  };
}
