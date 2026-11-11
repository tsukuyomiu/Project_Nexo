import { Link, useNavigate } from "@tanstack/react-router";
import { ChevronDown, User } from "lucide-react";
import type { ReactNode } from "react";
import { useTransactions } from "@/hooks/useTransactions";

/* Layout das telas internas:
   - Exibe "Logs" SOMENTE para Administradores (role === "admin").
   - Exibe o NOME REAL e a foto de perfil da pessoa logada. */
export function AppLayout({ children }: { children: ReactNode }) {
  const navigate = useNavigate();
  const { profile, avatarUrl, role, endLocalSession } = useTransactions();
  const isAdmin = role === "admin" || role === "auditor";

  const navItems = [
    { to: "/dashboard", label: "Dashboard", show: true },
    { to: "/lancamentos", label: "Lançamentos", show: true },
    { to: "/logs", label: "Logs", show: isAdmin },
    { to: "/perfil", label: "Perfil", show: true },
    { to: "/sobre", label: "Sobre nós", show: true },
  ] as const;

  const displayName = profile.name?.trim() || profile.email?.split("@")[0] || "Membro Nexo";

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
          <ul className="flex items-center gap-4 text-xs sm:gap-7">
            {navItems
              .filter((item) => item.show)
              .map((item) => (
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
          <Link to="/perfil" className="flex items-center gap-2 text-xs hover:underline">
            <span className="grid h-7 w-7 overflow-hidden place-items-center rounded-full bg-muted text-muted-foreground">
              {avatarUrl ? (
                <img
                  src={avatarUrl}
                  alt={`Foto de ${displayName}`}
                  className="h-full w-full object-cover"
                />
              ) : (
                <User className="h-4 w-4" />
              )}
            </span>
            <span className="hidden max-w-40 truncate font-bold sm:inline">{displayName}</span>
            <ChevronDown className="h-3 w-3" />
          </Link>
        </nav>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8">{children}</main>
    </div>
  );
}
