import { createFileRoute, Link } from "@tanstack/react-router";
import {
  ArrowLeft,
  Code2,
  Database,
  FileSpreadsheet,
  Lock,
  ShieldCheck,
  Sparkles,
  Users,
} from "lucide-react";
import { AppLayout } from "@/components/AppLayout";
import { NexoLayout } from "@/components/NexoLayout";
import { useTransactions } from "@/hooks/useTransactions";
import { getAuthToken } from "@/lib/api";

export const Route = createFileRoute("/sobre")({
  head: () => ({
    meta: [
      { title: "Sobre nós | Nexo" },
      {
        name: "description",
        content: "Conheça a história, a arquitetura e a equipe por trás do Projeto Nexo.",
      },
    ],
  }),
  component: SobrePage,
});

const TEAM_MEMBERS = [
  {
    name: "Luann Thayller",
    registration: "0023194",
    role: "Gerente de Projeto, Desenvolvedor Front-End e UI/UX Designer",
  },
  {
    name: "Gabriel Nonato",
    registration: "0020241",
    role: "Desenvolvedor FullStack, Arquiteto Back-End & Engenharia de Dados",
  },
  {
    name: "Weney Anjos da Silva",
    registration: "0023218",
    role: "Desenvolvedor Back-End e Data Engineer",
  },
  {
    name: "Luísa Damaceno",
    registration: "0016112",
    role: "Analista de Requisitos",
  },
  {
    name: "Gabryel Henrique",
    registration: "0022470",
    role: "Assistente Administrativo",
  },
  {
    name: "Érica Beatriz de A.",
    registration: "0022515",
    role: "Analista de Requisitos e UI/UX Designer",
  },
];

const PILLARS = [
  {
    icon: ShieldCheck,
    title: "Auditoria 360° Imutável",
    description:
      "Cada ação no sistema registra quem fez, a hora exata de Brasília, o IP e o estado antes/depois do dado, protegido por Triggers SQL Append-Only e Hash SHA-256.",
  },
  {
    icon: Lock,
    title: "Segurança e Autenticação 2FA",
    description:
      "Senhas criptografadas com PBKDF2-HMAC-SHA256 (600.000 iterações OWASP), sessões JWT revogáveis, login social Google/Apple e verificação em duas etapas por e-mail.",
  },
  {
    icon: Database,
    title: "Engenharia SQL de Alta Performance",
    description:
      "Modelagem relacional em 3ª Forma Normal com Views analíticas, constraints de integridade financeira e compatibilidade com SQLite (WAL) e PostgreSQL.",
  },
  {
    icon: FileSpreadsheet,
    title: "Relatórios e Exportação Inteligente",
    description:
      "Consolidação automática de receitas, despesas e saldo mensal, com exportação imediata de trilhas de auditoria em planilhas Excel (.csv) enviadas por Gmail.",
  },
];

function SobreContent() {
  const { profile } = useTransactions();
  const isLogged = Boolean(getAuthToken() || profile.email);

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-8">
      {/* Hero Banner */}
      <section className="rounded-2xl bg-primary p-8 text-primary-foreground shadow-card sm:p-10">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <span className="inline-flex items-center gap-1.5 rounded-full bg-secondary px-3 py-1 text-xs font-bold text-secondary-foreground">
            <Sparkles className="h-3.5 w-3.5" /> Plataforma Oficial Nexo
          </span>
          <Link
            to={isLogged ? "/dashboard" : "/"}
            className="inline-flex items-center gap-1.5 rounded-lg border border-primary-foreground/30 px-3 py-1.5 text-xs font-bold hover:bg-primary-foreground hover:text-primary"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            {isLogged ? "Voltar ao Dashboard" : "Voltar ao Login"}
          </Link>
        </div>
        <h1 className="mt-4 text-3xl font-bold sm:text-4xl">Sobre o Projeto Nexo</h1>
        <p className="mt-3 max-w-3xl text-sm leading-relaxed text-primary-foreground/90">
          O <strong>Projeto Nexo</strong> nasceu com a missão de unir uma experiência visual
          intuitiva de gestão financeira com uma arquitetura de engenharia de dados e rastreabilidade
          pericial. Na Nexo, cada centavo movimentado e cada operação executada possuem transparência,
          segurança criptográfica e histórico auditável em tempo real.
        </p>
      </section>

      {/* Pilares Tecnológicos */}
      <section>
        <h2 className="mb-4 flex items-center gap-2 text-xl font-bold text-foreground">
          <Code2 className="h-5 w-5 text-secondary" /> Pilares de Engenharia e Segurança
        </h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {PILLARS.map((item) => {
            const Icon = item.icon;
            return (
              <div
                key={item.title}
                className="rounded-xl border border-primary/40 bg-card p-5 shadow-sm"
              >
                <div className="flex items-center gap-3">
                  <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-primary/15 text-secondary">
                    <Icon className="h-5 w-5" />
                  </span>
                  <h3 className="font-bold text-foreground">{item.title}</h3>
                </div>
                <p className="mt-3 text-xs leading-relaxed text-muted-foreground">
                  {item.description}
                </p>
              </div>
            );
          })}
        </div>
      </section>

      {/* Equipe do Projeto */}
      <section className="rounded-2xl border border-primary/40 bg-card p-6 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h2 className="flex items-center gap-2 text-xl font-bold text-foreground">
              <Users className="h-5 w-5 text-secondary" /> Nossa Equipe
            </h2>
            <p className="mt-1 text-xs text-muted-foreground">
              Time responsável pela concepção, arquitetura, desenvolvimento FullStack e documentação
              do Projeto Nexo.
            </p>
          </div>
        </div>

        <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {TEAM_MEMBERS.map((member) => (
            <div
              key={member.registration}
              className="flex flex-col justify-between rounded-xl border border-border bg-background p-4 shadow-sm"
            >
              <div>
                <div className="flex items-center justify-between gap-2">
                  <h3 className="font-bold text-foreground">{member.name}</h3>
                  <span className="rounded bg-primary/15 px-2 py-0.5 font-mono text-[10px] font-bold text-secondary">
                    #{member.registration}
                  </span>
                </div>
                <p className="mt-2 text-xs text-muted-foreground">{member.role}</p>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

function SobrePage() {
  const { profile } = useTransactions();
  const isLogged = Boolean(getAuthToken() || profile.email);

  if (isLogged) {
    return (
      <AppLayout>
        <SobreContent />
      </AppLayout>
    );
  }

  return (
    <NexoLayout hideFooter={false}>
      <SobreContent />
    </NexoLayout>
  );
}
