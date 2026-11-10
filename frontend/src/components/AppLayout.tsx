import { Link, useNavigate } from "@tanstack/react-router";
import { ChevronDown, User } from "lucide-react";
import type { ReactNode } from "react";
import { useTransactions } from "@/hooks/useTransactions";

const navItems = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/lancamentos", label: "Lançamentos" },
  { to: "/perfil", label: "Perfil" },
] as const;

/* Layout das telas internas (Dashboard, Lançamentos, Perfil): cabeçalho azul
   com navegação e usuário. O provider de lançamentos fica na raiz do app. */
export function AppLayout({ children }: { children: ReactNode }) {
  const navigate = useNavigate();
  const { profile, endLocalSession } = useTransactions();
  return (
    <div className="min-h-screen bg-background">
      <header className="bg-primary text-primary-foreground shadow-btn">
        <nav
          className="mx-auto flex h-12 max-w-6xl items-center justify-between gap-4 px-4"
          aria-label="Principal"
        >
          <Link to="/dashboard" className="flex items-center gap-1 font-bold">
            <img src="/imagens/logo.png" alt="Logo Nexo" className="h-5 w-5 object-contain" /> Nexo
          </Link>
          <ul className="flex items-center gap-4 text-xs sm:gap-8">
            {navItems.map((item) => (
              <li key={item.to}>
                <Link
                  to={item.to}
                  className="pb-1 hover:underline focus-visible:underline"
                  activeProps={{ className: "border-b-2 border-secondary font-bold" }}
                >
                  {item.label}
                </Link>
              </li>
            ))}
            <li>
              <button
                type="button"
                onClick={() => {
                  endLocalSession();
                  navigate({ to: "/" });
                }}
                className="hover:underline focus-visible:underline"
              >
                Sair
              </button>
            </li>
          </ul>
          <Link to="/perfil" className="flex items-center gap-1 text-xs hover:underline">
            <span className="grid h-7 w-7 place-items-center rounded-full bg-muted text-muted-foreground">
              <User className="h-4 w-4" />
            </span>
            <span className="hidden max-w-36 truncate sm:inline">{profile.name || "Usuário"}</span>
            <ChevronDown className="h-3 w-3" />
          </Link>
        </nav>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8">{children}</main>
    </div>
  );
}
