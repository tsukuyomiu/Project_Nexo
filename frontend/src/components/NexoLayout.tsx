import { Link } from "@tanstack/react-router";
import {
  Facebook,
  Instagram,
  Linkedin,
  MessageCircle,
  Music2,
  Twitter,
  Youtube,
} from "lucide-react";
import type { ReactNode } from "react";
import logoAsset from "@/assets/Logo.png.asset.json";
import { FieldLabel } from "@/components/FieldLabel";

/* Logo "N" da Nexo */
export function NexoLogo({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true">
      <path d="M4 36V6l14 18V6h6v30L10 18v18z" fill="currentColor" />
      <path d="M26 30V10l4-6v26z" fill="currentColor" />
      <path d="M32 26V4l4-2v20z" className="fill-secondary" />
    </svg>
  );
}

const navItems = [
  { to: "/", label: "Início" },
  { to: "/", label: "Entrar" },
  { to: "/", label: "Sobre nós" },
] as const;

const socials = [
  { icon: Instagram, label: "Instagram" },
  { icon: Linkedin, label: "LinkedIn" },
  { icon: Twitter, label: "X" },
  { icon: MessageCircle, label: "WhatsApp" },
  { icon: Youtube, label: "YouTube" },
  { icon: Music2, label: "TikTok" },
  { icon: Facebook, label: "Facebook" },
];

/* useLogoImage/hideFooter: valem para todas as telas; ligue/desligue por página se precisar */
export function NexoLayout({
  children,
  useLogoImage = true,
  hideFooter = true,
}: {
  children: ReactNode;
  useLogoImage?: boolean;
  hideFooter?: boolean;
}) {
  return (
    <div className="flex min-h-screen flex-col bg-background">
      <header className="bg-primary text-primary-foreground shadow-btn">
        <nav className="mx-auto flex h-11 items-center justify-between px-4" aria-label="Principal">
          <Link to="/" className="flex items-center gap-1 font-bold">
            {useLogoImage ? (
              <img src="/imagens/logo.png" alt="Logo Nexo" className="h-5 w-5 object-contain" />
            ) : (
              <NexoLogo />
            )}{" "}
            Nexo
          </Link>
          <ul className="flex items-center gap-3 text-xs sm:gap-8">
            {navItems.map((item) => (
              <li key={item.label} className="hidden sm:block">
                <Link to={item.to} className="hover:underline focus-visible:underline">
                  {item.label}
                </Link>
              </li>
            ))}
            <li>
              <Link
                to="/cadastro"
                className="rounded-full bg-secondary px-3 py-1 transition hover:brightness-110"
                activeProps={{ className: "ring-1 ring-primary-foreground" }}
              >
                Cadastre-se
              </Link>
            </li>
          </ul>
        </nav>
      </header>

      <main className="flex flex-1 items-center justify-center px-4 py-12">{children}</main>

      {!hideFooter && (
        <footer className="flex flex-col gap-3 px-4 pb-4 text-sm sm:flex-row sm:items-end sm:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-3">
              <span className="font-bold text-primary">Siga a Nexo</span>
              {socials.map(({ icon: Icon, label }) => (
                <a
                  key={label}
                  href="#"
                  aria-label={label}
                  className="grid h-5 w-5 place-items-center rounded-full bg-primary text-primary-foreground hover:bg-secondary"
                >
                  <Icon className="h-3 w-3" />
                </a>
              ))}
            </div>
            <p className="mt-1 max-w-sm italic text-muted-foreground">
              Garantir a estabilidade do poder de compra da moeda, zelar por um sistema financeiro
              sólido, eficiente e competitivo, e fomentar o bem-estar econômico
            </p>
          </div>
          <div className="text-muted-foreground sm:text-right">
            <p>Atendimento : 145 (custo de ligação local)</p>
            <div className="flex flex-wrap gap-4 text-link">
              <a href="#" className="hover:underline">
                Fale conosco
              </a>
              <a href="#" className="hover:underline">
                Política de privacidade
              </a>
              <a href="#" className="hover:underline">
                Política de acessibilidade
              </a>
            </div>
          </div>
        </footer>
      )}
    </div>
  );
}

/* Painel azul de boas-vindas (Login e Cadastro) */
export function WelcomePanel({
  children,
  useLogoImage = true,
}: {
  children?: ReactNode;
  useLogoImage?: boolean;
}) {
  return (
    <section className="flex flex-col items-center justify-center gap-2 rounded-2xl bg-primary p-10 text-center text-primary-foreground">
      {useLogoImage ? (
        <img src="/imagens/logo.png" alt="Logo Nexo" className="h-17 w-17 object-contain" />
      ) : (
        <NexoLogo className="h-17 w-17" />
      )}
      <h2 className="mt-8 text-xl">Bem vindo ao nosso site</h2>
      {children}
    </section>
  );
}

/* Campo com ícone, no estilo do protótipo */
export function IconField({
  id,
  label,
  icon,
  type = "text",
  value,
  onChange,
  error,
  trailing,
  required = false,
  autoComplete,
}: {
  id: string;
  label: string;
  icon: ReactNode;
  type?: string;
  value: string;
  onChange: (v: string) => void;
  error?: string | undefined;
  trailing?: ReactNode;
  required?: boolean;
  autoComplete?: string;
}) {
  return (
    <div>
      {required ? (
        <FieldLabel htmlFor={id} required>
          {label}
        </FieldLabel>
      ) : (
        <label htmlFor={id} className="sr-only">
          {label}
        </label>
      )}
      <div
        className={`nexo-feedback flex items-center gap-1 rounded bg-input px-2 shadow-field focus-within:ring-2 focus-within:ring-secondary ${error ? "ring-1 ring-destructive" : ""}`}
      >
        <span className="text-muted-foreground">{icon}</span>
        <input
          id={id}
          name={id}
          autoComplete={autoComplete}
          type={type}
          value={value}
          placeholder={label}
          onChange={(e) => onChange(e.target.value)}
          aria-invalid={!!error}
          aria-required={required || undefined}
          aria-describedby={error ? `${id}-error` : undefined}
          className="h-6 min-w-0 flex-1 bg-transparent text-sm font-bold outline-none placeholder:text-muted-foreground"
        />
        {trailing}
      </div>
      {error && (
        <p id={`${id}-error`} className="nexo-enter mt-1 text-xs text-destructive">
          {error}
        </p>
      )}
    </div>
  );
}

const AppleIcon = () => (
  <svg viewBox="0 0 384 512" className="h-3.5 w-3.5" fill="currentColor" aria-hidden="true">
    <path d="M318.7 268.7c-.2-36.7 16.4-64.4 50-84.8-18.8-26.9-47.2-41.7-84.7-44.6-35.5-2.8-74.3 20.7-88.5 20.7-15 0-49.4-19.7-76.4-19.7C63.3 141.2 4 184.8 4 273.5q0 39.3 14.4 81.2c12.8 36.7 59 126.7 107.2 125.2 25.2-.6 43-17.9 75.8-17.9 31.8 0 48.3 17.9 76.4 17.9 48.6-.7 90.4-82.5 102.6-119.3-65.2-30.7-61.7-90-61.7-91.9zm-56.6-164.2c27.3-32.4 24.8-61.9 24-72.5-24.1 1.4-52 16.4-67.9 34.9-17.5 19.8-27.8 44.3-25.6 71.9 26.1 2 49.9-11.4 69.5-34.3z" />
  </svg>
);

export function SocialButtons({ appleIcon = true }: { appleIcon?: boolean }) {
  return (
    <>
      <div className="my-4 flex items-center gap-2 text-sm">
        <span className="h-px flex-1 bg-primary" /> Ou continue com{" "}
        <span className="h-px flex-1 bg-primary" />
      </div>
      <div className="flex justify-center gap-3">
        <button
          type="button"
          aria-label="Continuar com Google"
          className="h-6 w-14 rounded bg-primary text-sm font-bold text-primary-foreground shadow-btn hover:bg-secondary"
        >
          G
        </button>
        <button
          type="button"
          aria-label="Continuar com Apple"
          className="h-6 w-14 rounded bg-primary text-sm text-primary-foreground shadow-btn hover:bg-secondary inline-flex items-center justify-center"
        >
          {appleIcon && <AppleIcon />}
        </button>
      </div>
    </>
  );
}

export const isEmail = (v: string) => /^\S+@\S+\.\S+$/.test(v);
