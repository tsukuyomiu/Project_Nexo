import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { Lock, Mail, User } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { IconField, NexoLayout, SocialButtons, WelcomePanel } from "@/components/NexoLayout";
import { validateSignup } from "@/lib/signup-validation";
import { useTransactions } from "@/hooks/useTransactions";

export const Route = createFileRoute("/cadastro")({
  head: () => ({
    meta: [
      { title: "Cadastro | Nexo" },
      { name: "description", content: "Crie sua conta e faça parte da Nexo." },
      { property: "og:title", content: "Cadastro | Nexo" },
      { property: "og:description", content: "Crie sua conta e faça parte da Nexo." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: SignupPage,
});

type Errors = Partial<
  Record<"name" | "email" | "password" | "confirm" | "terms", string | undefined>
>;

function SignupPage() {
  const navigate = useNavigate();
  const { endLocalSession } = useTransactions();
  const [form, setForm] = useState({ name: "", email: "", password: "", confirm: "" });
  const [terms, setTerms] = useState(false);
  const [errors, setErrors] = useState<Errors>({});
  const set = (key: keyof typeof form) => (v: string) => {
    const updated = { ...form, [key]: v };
    setForm(updated);
    setErrors((current) => ({
      ...current,
      [key]: current[key] ? validateSignup(updated, terms)[key] : undefined,
    }));
  };

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const next = validateSignup(form, terms);
    setErrors(next);
    const first = Object.keys(next)[0];
    if (first) e.currentTarget.querySelector<HTMLElement>(`#${first}`)?.focus();
    if (Object.keys(next).length === 0) {
      endLocalSession(); // novo cadastro nunca herda a identificação anterior
      toast.success("Formulário validado. Entre com seu e-mail para abrir um espaço local.");
      navigate({ to: "/" });
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
        <form
          method="post"
          onSubmit={handleSubmit}
          noValidate
          className="nexo-enter flex flex-col gap-4 bg-background p-10"
        >
          <h1 className="mb-6 text-center text-2xl font-bold text-foreground sm:text-3xl">
            Faça parte da Nexo
          </h1>
          <IconField
            autoComplete="name"
            required
            id="name"
            label="Nome"
            icon={<User className="h-4 w-4" />}
            value={form.name}
            onChange={set("name")}
            error={errors.name}
          />
          <IconField
            autoComplete="email"
            required
            id="email"
            label="Email"
            type="email"
            icon={<Mail className="h-4 w-4" />}
            value={form.email}
            onChange={set("email")}
            error={errors.email}
          />
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
              className="h-7 w-24 rounded-lg bg-secondary text-sm font-bold text-secondary-foreground shadow-btn hover:brightness-110"
            >
              Continue
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
      </div>
    </NexoLayout>
  );
}
