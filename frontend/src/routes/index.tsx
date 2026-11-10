import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { Eye, EyeOff, Lock, Mail } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import {
  IconField,
  isEmail,
  NexoLayout,
  SocialButtons,
  WelcomePanel,
} from "@/components/NexoLayout";
import { useTransactions } from "@/hooks/useTransactions";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Login | Nexo" },
      { name: "description", content: "Entre na sua conta Nexo." },
      { property: "og:title", content: "Login | Nexo" },
      { property: "og:description", content: "Entre na sua conta Nexo." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: LoginPage,
});

function LoginPage() {
  const navigate = useNavigate();
  const { startLocalSession } = useTransactions();
  const [submitting, setSubmitting] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [show, setShow] = useState(false);
  const [errors, setErrors] = useState<{ email?: string; password?: string }>({});

  // Validação simples dos campos
  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (submitting) return;
    const next: typeof errors = {};
    if (!isEmail(email)) next.email = "Informe um email válido.";
    if (!password) next.password = "Informe sua senha.";
    setErrors(next);
    if (Object.keys(next).length === 0) {
      setSubmitting(true);
      try {
        await startLocalSession(email);
        toast.success("Espaço local aberto neste navegador.");
        navigate({ to: "/dashboard" });
      } catch {
        toast.error("Não foi possível abrir o espaço local neste navegador.");
      } finally {
        setSubmitting(false);
      }
    }
  }

  return (
    <NexoLayout useLogoImage hideFooter>
      <div className="grid w-full max-w-4xl min-h-[440px] overflow-hidden rounded-2xl border border-primary shadow-card md:grid-cols-2">
        <form
          method="post"
          onSubmit={handleSubmit}
          noValidate
          className="nexo-enter flex flex-col gap-3 bg-background p-8"
        >
          <h1 className="mb-4 text-center text-3xl font-bold text-foreground">Login</h1>
          <IconField
            autoComplete="username"
            id="email"
            label="Email"
            type="email"
            icon={<Mail className="h-4 w-4" />}
            value={email}
            onChange={setEmail}
            error={errors.email}
          />
          <IconField
            autoComplete="current-password"
            id="password"
            label="Senha"
            type={show ? "text" : "password"}
            icon={<Lock className="h-4 w-4" />}
            value={password}
            onChange={setPassword}
            error={errors.password}
            trailing={
              <button
                type="button"
                onClick={() => setShow(!show)}
                aria-label={show ? "Ocultar senha" : "Mostrar senha"}
                className="text-muted-foreground hover:text-primary"
              >
                {show ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            }
          />
          <Link
            to="/redefinir-senha"
            className="-mt-2 self-end text-[10px] text-foreground hover:underline"
          >
            Esqueceu sua senha?
          </Link>
          <button
            type="submit"
            disabled={submitting}
            className="mx-auto h-7 w-24 rounded-lg bg-secondary text-sm font-bold text-secondary-foreground shadow-btn hover:brightness-110 disabled:opacity-50"
          >
            Entrar
          </button>
          <SocialButtons appleIcon />
          <Link to="/cadastro" className="mt-6 text-center text-link hover:underline">
            Criar uma conta!
          </Link>
        </form>
        <WelcomePanel useLogoImage>
          <p className="max-w-[220px] text-[10px]">
            Para desfrutar de nossos serviços entre com sua conta já cadastrada ou cadastre sua
            conta.
          </p>
        </WelcomePanel>
      </div>
    </NexoLayout>
  );
}
