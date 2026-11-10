import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { CheckCircle2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { isEmail, NexoLayout } from "@/components/NexoLayout";

export const Route = createFileRoute("/redefinir-senha")({
  head: () => ({
    meta: [
      { title: "Redefinição de senha | Nexo" },
      { name: "description", content: "Recupere o acesso à sua conta Nexo." },
      { property: "og:title", content: "Redefinição de senha | Nexo" },
      { property: "og:description", content: "Recupere o acesso à sua conta Nexo." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: ResetPage,
});

const fieldClass =
  "h-7 w-full max-w-[190px] bg-background px-2 text-sm text-foreground shadow-field outline-none focus:ring-2 focus:ring-secondary";
const btnClass =
  "rounded-lg bg-background px-3 py-1.5 text-[10px] font-bold text-primary shadow-btn hover:bg-input";

function ResetPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState<1 | 2>(1); // etapa 1: email, etapa 2: código + nova senha
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [pass, setPass] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");

  function sendEmail(e: React.FormEvent) {
    e.preventDefault();
    if (!isEmail(email)) return setError("Informe um email válido.");
    setError("");
    setStep(2);
  }

  function resetPassword(e: React.FormEvent) {
    e.preventDefault();
    if (!code.trim()) return setError("Informe o código recebido.");
    if (pass.length < 6) return setError("A nova senha deve ter ao menos 6 caracteres.");
    if (pass !== confirm) return setError("As senhas não coincidem.");
    toast.success("Senha redefinida! Faça seu login.");
    navigate({ to: "/" });
  }

  return (
    <NexoLayout>
      <section className="flex w-full max-w-xs flex-col items-center gap-3 rounded-2xl bg-primary px-6 py-8 text-center text-primary-foreground shadow-card">
        <h1 className="text-xl font-bold">Redefinição de senha</h1>
        {step === 1 ? (
          <form onSubmit={sendEmail} noValidate className="flex w-full flex-col items-center gap-4">
            <p className="text-[10px]">
              Digite seu email no campo abaixo e<br />
              lhe enviaremos uma nova senha.
            </p>
            <label htmlFor="reset-email" className="sr-only">
              E-mail
            </label>
            <input
              id="reset-email"
              type="email"
              placeholder="E-mail"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={fieldClass}
            />
            {error && (
              <p role="alert" className="text-xs">
                {error}
              </p>
            )}
            <button type="submit" className={btnClass}>
              Redefinir senha
            </button>
            <Link to="/" className="text-[10px] font-bold hover:underline">
              Já possui cadastro? Faça seu login
            </Link>
          </form>
        ) : (
          <form
            onSubmit={resetPassword}
            noValidate
            className="flex w-full flex-col items-center gap-3"
          >
            <div className="flex items-center gap-3 rounded-xl border border-primary-foreground/30 bg-success-box px-4 py-3 text-left text-[10px]">
              <CheckCircle2 className="h-4 w-4 shrink-0" />
              Um email foi enviado para {email} para finalizar seu cadastro
            </div>
            <p className="text-[10px]">
              Por favor insira o código enviado para seu email e redefina sua senha
            </p>
            <label htmlFor="code" className="sr-only">
              Código
            </label>
            <input
              id="code"
              placeholder="Código"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className={fieldClass}
            />
            <label htmlFor="new-pass" className="sr-only">
              Nova senha
            </label>
            <input
              id="new-pass"
              type="password"
              placeholder="Nova senha"
              value={pass}
              onChange={(e) => setPass(e.target.value)}
              className={fieldClass}
            />
            <label htmlFor="confirm-pass" className="sr-only">
              Confirmar nova senha
            </label>
            <input
              id="confirm-pass"
              type="password"
              placeholder="Confirmar nova senha"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              className={fieldClass}
            />
            {error && (
              <p role="alert" className="text-xs">
                {error}
              </p>
            )}
            <button type="submit" className={btnClass}>
              Redefinir senha
            </button>
          </form>
        )}
      </section>
    </NexoLayout>
  );
}
