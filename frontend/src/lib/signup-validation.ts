import { isEmail } from "@/components/NexoLayout";

export type SignupForm = { name: string; email: string; password: string; confirm: string };
export type SignupErrors = Partial<Record<keyof SignupForm | "terms", string>>;

export function validateSignup(form: SignupForm, terms: boolean): SignupErrors {
  const next: SignupErrors = {};
  if (!form.name.trim()) next.name = "Informe seu nome.";
  if (!form.email.trim()) next.email = "Campo obrigatório.";
  else if (!isEmail(form.email)) next.email = "Informe um email válido.";
  if (!form.password.trim()) next.password = "Campo obrigatório.";
  else if (form.password.length < 6) next.password = "A senha deve ter ao menos 6 caracteres.";
  if (!form.confirm.trim()) next.confirm = "Campo obrigatório.";
  else if (form.confirm !== form.password) next.confirm = "As senhas não coincidem.";
  if (!terms) next.terms = "Aceite os termos para continuar.";
  return next;
}
