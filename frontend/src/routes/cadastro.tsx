import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { KeyRound, Lock, Mail, ShieldCheck, User } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import {
  IconField,
  NexoLayout,
  PasswordStrengthMeter,
  SocialButtons,
  WelcomePanel,
} from "@/components/NexoLayout";
import { validateSignup } from "@/lib/signup-validation";
import { useTransactions } from "@/hooks/useTransactions";
import { apiSignup, apiVerify2FA, type StoredAuthUser } from "@/lib/api";

export const Route = createFileRoute("/cadastro")({
  head: () => ({
    meta: [
      { title: "Cadastro | Nexo" },
      { name: "description", content: "Crie sua conta e faça parte da Nexo." },
    ],
  }),
  component: SignupPage,
});

type Errors = Partial<
  Record<"name" | "email" | "password" | "confirm" | "terms" | "code", string | undefined>
>;

function SignupPage() {
  const navigate = useNavigate();
  const { authenticateSession } = useTransactions();
  const [form, setForm] = useState({ name: "", email: "", password: "", confirm: "" });
  const [terms, setTerms] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [errors, setErrors] = useState<Errors>({});

  // Etapa 2: Confirmação do Gmail ao criar a conta
  const [confirmStep, setConfirmStep] = useState(false);
  const [confirmCode, setConfirmCode] = useState("");
  const [generatedCode, setGeneratedCode] = useState<string | null>(null);
  const [sentSmtp, setSentSmtp] = useState(false);
  const [pendingSession, setPendingSession] = useState<{
    token: string;
    user: StoredAuthUser;
  } | null>(null);

  const set = (key: keyof typeof form) => (v: string) => {
    const updated = { ...form, [key]: v };
    setForm(updated);
    setErrors((current) => ({
      ...current,
      [key]: current[key] ? validateSignup(updated, terms)[key] : undefined,
    }));
  };

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (submitting) return;
    const next: Errors = validateSignup(form, terms);
    setErrors(next);
    const first = Object.keys(next)[0];
    if (first) e.currentTarget.querySelector<HTMLElement>(`#${first}`)?.focus();

    if (Object.keys(next).length === 0) {
      setSubmitting(true);
      try {
        const res = await apiSignup({
          name: form.name.trim(),
          email: form.email.trim(),
          password: form.password,
          confirm: form.confirm,
          terms,
        });

        if (res.access_token && res.user) {
          setPendingSession({ token: res.access_token, user: res.user });
          setGeneratedCode(res.dev_code ?? null);
          setSentSmtp(Boolean(res.email_sent_smtp));
          setConfirmStep(true);
          toast.info(`Enviamos um e-mail de confirmação para ${res.user.email}!`);
        }
      } catch (err) {
        toast.error(err instanceof Error ? err.message : "Não foi possível criar a conta.");
      } finally {
        setSubmitting(false);
      }
    }
  }

  async function handleConfirmEmail(e: React.FormEvent) {
    e.preventDefault();
    if (submitting) return;
    if (!confirmCode.trim()) {
      setErrors({ code: "Digite o código de 6 dígitos enviado para o seu Gmail." });
      return;
    }
    setSubmitting(true);
    try {
      const res = await apiVerify2FA({
        email: form.email.trim(),
        code: confirmCode.trim(),
      });
      if (res.access_token && res.user) {
        await authenticateSession(res.access_token, res.user);
        toast.success(`E-mail confirmado com sucesso! Bem-vindo(a), ${res.user.name}!`);
        navigate({ to: "/dashboard" });
      } else if (pendingSession) {
        await authenticateSession(pendingSession.token, pendingSession.user);
        navigate({ to: "/dashboard" });
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Código de confirmação inválido.");
    } finally {
      setSubmitting(false);
    }
  }

  const lock = <Lock className="h-4 w-4" />;
  return (
    <NexoLayout>
      <div className="grid w-full max-w-3xl overflow-hidden rounded-2xl border border-primary shadow-card md:grid-cols-[2fr_3fr]">
        <WelcomePanel>
          <p className="text-[10px]">Já faz parte da Nexo?</p>
          <Link
            to="/"
            className="rounded-full border border-primary-foreground px-4 text-[10px] hover:bg-primary-foreground hover:text-primary"
          >
            Entrar
          </Link>
        </WelcomePanel>
        {!confirmStep ? (
          <form
            method="post"
            onSubmit={handleSubmit}
            noValidate
            className="nexo-enter flex flex-col gap-3.5 bg-background p-8"
          >
            <h1 className="mb-2 text-center text-2xl font-bold text-foreground sm:text-3xl">
              Faça parte da Nexo
            </h1>

            <IconField
              autoComplete="name"
              required
              id="name"
              label="Nome completo"
              icon={<User className="h-4 w-4" />}
              value={form.name}
              onChange={set("name")}
              error={errors.name}
            />
            <IconField
              autoComplete="email"
              required
              id="email"
              label="Email (Gmail)"
              type="email"
              icon={<Mail className="h-4 w-4" />}
              value={form.email}
              onChange={set("email")}
              error={errors.email}
            />
            <div>
              <IconField
                autoComplete="new-password"
                required
                id="password"
                label="Senha"
                type="password"
                icon={lock}
                value={form.password}
                onChange={set("password")}
                error={errors.password}
              />
              <PasswordStrengthMeter password={form.password} />
            </div>
            <IconField
              autoComplete="new-password"
              required
              id="confirm"
              label="Confirmar senha"
              type="password"
              icon={lock}
              value={form.confirm}
              onChange={set("confirm")}
              error={errors.confirm}
            />
            <div>
              <label className="flex items-center justify-center gap-2 text-xs">
                <input
                  id="terms"
                  type="checkbox"
                  aria-required="true"
                  aria-invalid={!!errors.terms}
                  aria-describedby={errors.terms ? "terms-error" : undefined}
                  checked={terms}
                  onChange={(e) => {
                    setTerms(e.target.checked);
                    if (e.target.checked) setErrors((current) => ({ ...current, terms: undefined }));
                  }}
                  className="h-4 w-4 accent-primary"
                />
                Li e aceito os termos de uso e políticas de privacidade.
                <span aria-hidden="true" className="text-destructive">
                  *
                </span>
              </label>
              {errors.terms && (
                <p id="terms-error" className="mt-1 text-center text-xs text-destructive">
                  {errors.terms}
                </p>
              )}
            </div>
            <div className="flex justify-around">
              <button
                type="submit"
                disabled={submitting}
                className="h-7 w-28 rounded-lg bg-secondary text-sm font-bold text-secondary-foreground shadow-btn hover:brightness-110 disabled:opacity-50"
              >
                {submitting ? "Criando..." : "Continue"}
              </button>
              <button
                type="button"
                onClick={() => navigate({ to: "/" })}
                className="h-7 w-24 rounded-lg bg-primary text-sm font-bold text-primary-foreground shadow-btn hover:brightness-125"
              >
                Voltar
              </button>
            </div>
            <SocialButtons />
          </form>
        ) : (
          <form
            onSubmit={handleConfirmEmail}
            noValidate
            className="nexo-enter flex flex-col justify-center gap-4 bg-background p-8"
          >
            <div className="mx-auto grid h-12 w-12 place-items-center rounded-full bg-primary/15 text-secondary">
              <ShieldCheck className="h-6 w-6" />
            </div>
            <h1 className="text-center text-2xl font-bold text-foreground">
              Confirme seu e-mail
            </h1>
            <p className="text-center text-xs text-muted-foreground">
              Enviamos um e-mail de confirmação com um código de 6 dígitos para{" "}
              <strong>{form.email}</strong>. Digite o código recebido no seu Gmail para ativar sua
              conta:
            </p>
            {!sentSmtp && generatedCode && (
              <div className="rounded-lg border border-secondary/40 bg-secondary/10 px-3 py-2 text-center text-xs">
                Código de confirmação:{" "}
                <button
                  type="button"
                  onClick={() => setConfirmCode(generatedCode)}
                  className="font-mono font-bold text-secondary underline"
                >
                  {generatedCode}
                </button>{" "}
                <span className="text-[10px] text-muted-foreground">(clique para preencher)</span>
              </div>
            )}
            <IconField
              id="confirm-email-code"
              label="Código de confirmação (6 dígitos)"
              icon={<KeyRound className="h-4 w-4" />}
              value={confirmCode}
              onChange={setConfirmCode}
              error={errors.code}
            />
            <div className="mt-2 flex justify-center gap-3">
              <button
                type="submit"
                disabled={submitting}
                className="h-8 rounded-lg bg-secondary px-6 text-xs font-bold text-secondary-foreground shadow-btn hover:brightness-110 disabled:opacity-50"
              >
                {submitting ? "Confirmando..." : "Confirmar E-mail e Entrar"}
              </button>
            </div>
          </form>
        )}
      </div>
    </NexoLayout>
  );
}
