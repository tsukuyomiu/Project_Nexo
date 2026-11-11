const isEmail = (v: string) => /^\S+@\S+\.\S+$/.test(v);

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

export interface PasswordStrengthInfo {
  level: "empty" | "weak" | "medium" | "strong";
  score: 0 | 1 | 2 | 3;
  label: string;
  hasMinLength: boolean;
  hasUpperAndLower: boolean;
  hasNumber: boolean;
  hasSpecial: boolean;
}

export function evaluatePasswordStrength(password: string): PasswordStrengthInfo {
  const hasMinLength = password.length >= 6;
  const hasUpperAndLower = /[a-z]/.test(password) && /[A-Z]/.test(password);
  const hasNumber = /\d/.test(password);
  const hasSpecial = /[^A-Za-z0-9]/.test(password);

  if (!password) {
    return {
      level: "empty",
      score: 0,
      label: "",
      hasMinLength: false,
      hasUpperAndLower: false,
      hasNumber: false,
      hasSpecial: false,
    };
  }

  const points =
    (hasMinLength ? 1 : 0) +
    (hasUpperAndLower ? 1 : 0) +
    (hasNumber ? 1 : 0) +
    (hasSpecial ? 1 : 0) +
    (password.length >= 8 ? 1 : 0);

  if (!hasMinLength || points <= 2) {
    return {
      level: "weak",
      score: 1,
      label: "Fraca",
      hasMinLength,
      hasUpperAndLower,
      hasNumber,
      hasSpecial,
    };
  }

  if (points <= 3) {
    return {
      level: "medium",
      score: 2,
      label: "Média",
      hasMinLength,
      hasUpperAndLower,
      hasNumber,
      hasSpecial,
    };
  }

  return {
    level: "strong",
    score: 3,
    label: "Forte",
    hasMinLength,
    hasUpperAndLower,
    hasNumber,
    hasSpecial,
  };
}
