import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { AppLayout } from "@/components/AppLayout";
import { useTransactions } from "@/hooks/useTransactions";
import { API_BASE_URL, getAuthToken } from "@/lib/api";
import {
  ShieldCheck,
  RefreshCw,
  Download,
  Clock,
  User,
  Terminal,
  AlertTriangle,
  CheckCircle2,
  Info,
  Database,
  Lock,
} from "lucide-react";

export const Route = createFileRoute("/logs")({
  head: () => ({
    meta: [
      { title: "Logs | Nexo" },
      {
        name: "description",
        content: "Registro cronológico de eventos e movimentações do sistema.",
      },
    ],
  }),
  component: LogsPage,
});

interface TimelineItem {
  log_id: string;
  quando_fez: string;
  quem_fez: string;
  quem_nome: string;
  quem_email: string;
  o_que_fez: string;
  acao: string;
  modulo: string;
  severidade: string;
  ip: string;
  origem: string;
  rota: string;
  antes: Record<string, unknown> | null;
  depois: Record<string, unknown> | null;
}

interface StatsData {
  total_audit_events: number;
  total_sql_trigger_events: number;
  total_http_requests: number;
  average_http_latency_ms: number;
  events_by_category: Record<string, number>;
  events_by_severity: Record<string, number>;
  most_active_users: { email: string; name: string; actions_count: number }[];
}

function LogsPage() {
  const { role } = useTransactions();
  const isAdmin = role === "admin" || role === "auditor";

  const [timeline, setTimeline] = useState<TimelineItem[]>([]);
  const [stats, setStats] = useState<StatsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [filterModule, setFilterModule] = useState<string>("ALL");
  const [filterUser, setFilterUser] = useState<string>("ALL");
  const [includeSqlTriggers, setIncludeSqlTriggers] = useState(false);

  async function loadData() {
    const token = getAuthToken();
    if (!token || !isAdmin) {
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const headers = { Authorization: `Bearer ${token}` };
      const [resTimeline, resStats] = await Promise.all([
        fetch(
          `${API_BASE_URL}/logs/timeline?limit=200&incluir_triggers_sql=${includeSqlTriggers}`,
          { headers },
        ),
        fetch(`${API_BASE_URL}/logs/stats`, { headers }),
      ]);

      if (resTimeline.ok) {
        const json = await resTimeline.json();
        setTimeline(json.timeline || []);
      }
      if (resStats.ok) {
        const json = await resStats.json();
        setStats(json);
      }
    } catch {
      // erro de conexão
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadData();
    const interval = setInterval(() => void loadData(), 8000);
    return () => clearInterval(interval);
  }, [isAdmin, includeSqlTriggers]);

  if (!isAdmin) {
    return (
      <AppLayout>
        <div className="mx-auto flex max-w-lg flex-col items-center gap-4 rounded-2xl border border-destructive/40 bg-card p-10 text-center shadow-card">
          <div className="grid h-14 w-14 place-items-center rounded-full bg-destructive/15 text-destructive">
            <Lock className="h-7 w-7" />
          </div>
          <h1 className="text-2xl font-bold text-foreground">Acesso Restrito</h1>
          <p className="text-sm text-muted-foreground">
            Esta página não está disponível para sua conta.
          </p>
          <Link
            to="/dashboard"
            className="mt-2 rounded-lg bg-secondary px-6 py-2 text-xs font-bold text-secondary-foreground shadow-btn hover:brightness-110"
          >
            Voltar ao Dashboard
          </Link>
        </div>
      </AppLayout>
    );
  }

  const uniqueUsers = Array.from(new Set(timeline.map((item) => item.quem_email)));

  const filteredTimeline = timeline.filter(
    (item) =>
      (filterModule === "ALL" || item.modulo === filterModule) &&
      (filterUser === "ALL" || item.quem_email === filterUser),
  );

  const exportUrl = `${API_BASE_URL}/logs/export?format=csv&incluir_triggers_sql=${includeSqlTriggers}&token=${encodeURIComponent(getAuthToken() || "")}`;

  return (
    <AppLayout>
      <div className="flex flex-col gap-6">
        {/* Cabeçalho */}
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-6 w-6 text-secondary" />
              <h1 className="text-2xl font-bold text-foreground">Logs do Sistema</h1>
            </div>
            <p className="text-sm text-muted-foreground">
              Registro cronológico de eventos e movimentações realizadas na plataforma.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2.5">
            <button
              type="button"
              onClick={() => void loadData()}
              disabled={loading}
              className="flex items-center gap-1.5 rounded-lg border border-border bg-background px-3 py-2 text-xs font-bold text-foreground shadow-sm hover:bg-muted"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
              Atualizar
            </button>

            <a
              href={exportUrl}
              download="nexo_audit_logs.csv"
              className="flex items-center gap-1.5 rounded-lg bg-secondary px-3.5 py-2 text-xs font-bold text-secondary-foreground shadow-btn hover:brightness-110"
            >
              <Download className="h-3.5 w-3.5" />
              Baixar Planilha (Excel)
            </a>
          </div>
        </div>

        {/* Cards de Métricas (Sem Requisições HTTP) */}
        {stats && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="rounded-xl border border-primary/40 bg-card p-4 shadow-sm">
              <span className="flex items-center gap-2 text-xs font-bold text-muted-foreground">
                <Database className="h-4 w-4 text-primary" /> Eventos Registrados
              </span>
              <p className="mt-2 text-2xl font-bold text-foreground">{stats.total_audit_events}</p>
              <p className="text-[11px] text-muted-foreground">
                + {stats.total_sql_trigger_events} eventos capturados pelos Triggers SQL
              </p>
            </div>

            <div className="rounded-xl border border-primary/40 bg-card p-4 shadow-sm">
              <span className="flex items-center gap-2 text-xs font-bold text-muted-foreground">
                <ShieldCheck className="h-4 w-4 text-green-500" /> Proteção do Banco (Triggers SQL)
              </span>
              <p className="mt-2 text-2xl font-bold text-green-500">Ativa (Imutável)</p>
              <p className="text-[11px] text-muted-foreground">
                Triggers bloqueiam tentativas de apagar ou editar logs no banco SQL
              </p>
            </div>
          </div>
        )}

        {/* Filtros de Módulo e Usuário */}
        <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-border bg-card p-3.5 text-xs">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-bold text-muted-foreground">Módulo:</span>
            {["ALL", "AUTH", "TRANSACTION", "PROFILE", "PREFERENCES", "SECURITY", "REPORT"].map(
              (mod) => (
                <button
                  key={mod}
                  type="button"
                  onClick={() => setFilterModule(mod)}
                  className={`rounded-md px-2.5 py-1 font-semibold transition-colors ${
                    filterModule === mod
                      ? "bg-secondary text-secondary-foreground"
                      : "bg-muted text-muted-foreground hover:bg-muted/80"
                  }`}
                >
                  {mod === "ALL" ? "Todos" : mod}
                </button>
              ),
            )}
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <label className="flex items-center gap-1.5 font-bold text-muted-foreground">
              Usuário:
              <select
                value={filterUser}
                onChange={(e) => setFilterUser(e.target.value)}
                className="rounded border border-border bg-background px-2 py-1 text-xs text-foreground outline-none"
              >
                <option value="ALL">Todos ({uniqueUsers.length})</option>
                {uniqueUsers.map((u) => (
                  <option key={u} value={u}>
                    {u}
                  </option>
                ))}
              </select>
            </label>

            <label className="flex cursor-pointer items-center gap-1.5 text-muted-foreground">
              <input
                type="checkbox"
                checked={includeSqlTriggers}
                onChange={(e) => setIncludeSqlTriggers(e.target.checked)}
                className="accent-secondary"
              />
              Incluir Triggers SQL
            </label>
          </div>
        </div>

        {/* Lista Cronológica de Logs */}
        <div className="overflow-hidden rounded-xl border border-border bg-card shadow-sm">
          <div className="flex items-center justify-between border-b border-border bg-muted/40 px-4 py-3 text-xs font-bold text-foreground">
            <span>Trilha Cronológica de Atividades ({filteredTimeline.length} eventos)</span>
            <span className="text-[11px] font-normal text-muted-foreground">
              Horário de Brasília (dd/MM/aaaa HH:mm:ss)
            </span>
          </div>

          {filteredTimeline.length === 0 ? (
            <div className="p-8 text-center text-sm text-muted-foreground">
              {loading ? "Carregando registros..." : "Nenhum evento encontrado para este filtro."}
            </div>
          ) : (
            <div className="divide-y divide-border">
              {filteredTimeline.map((item) => {
                const isWarning = item.severidade === "WARNING";
                const isError = item.severidade === "ERROR" || item.severidade === "CRITICAL";

                return (
                  <div key={item.log_id} className="p-4 transition-colors hover:bg-muted/30">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        {isError ? (
                          <AlertTriangle className="h-4 w-4 shrink-0 text-destructive" />
                        ) : isWarning ? (
                          <AlertTriangle className="h-4 w-4 shrink-0 text-amber-500" />
                        ) : (
                          <CheckCircle2 className="h-4 w-4 shrink-0 text-secondary" />
                        )}

                        <span className="text-sm font-bold text-foreground">{item.o_que_fez}</span>
                      </div>

                      <span className="flex items-center gap-1 rounded bg-primary/15 px-2.5 py-1 font-mono text-xs font-bold text-secondary">
                        <Clock className="h-3.5 w-3.5" />
                        {item.quando_fez}
                      </span>
                    </div>

                    <div className="mt-2 flex flex-wrap items-center gap-4 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <User className="h-3.5 w-3.5 text-secondary" />
                        Usuário: <strong className="text-foreground">{item.quem_fez}</strong>
                      </span>

                      <span className="flex items-center gap-1 font-mono">
                        <Terminal className="h-3.5 w-3.5" />
                        IP: {item.ip}
                      </span>

                      <span className="rounded bg-muted px-2 py-0.5 text-[10px] font-semibold text-foreground">
                        {item.modulo} :: {item.acao}
                      </span>
                    </div>

                    {(item.antes || item.depois) && (
                      <div className="mt-3 grid grid-cols-1 gap-2 rounded-lg bg-muted/50 p-2.5 text-xs sm:grid-cols-2">
                        {item.antes && (
                          <div>
                            <span className="flex items-center gap-1 text-[11px] font-bold text-amber-500">
                              <Info className="h-3 w-3" /> Como estava ANTES:
                            </span>
                            <pre className="mt-1 overflow-x-auto rounded bg-background p-2 font-mono text-[10px] text-muted-foreground">
                              {JSON.stringify(item.antes, null, 2)}
                            </pre>
                          </div>
                        )}
                        {item.depois && (
                          <div>
                            <span className="flex items-center gap-1 text-[11px] font-bold text-secondary">
                              <Info className="h-3 w-3" /> Como ficou DEPOIS:
                            </span>
                            <pre className="mt-1 overflow-x-auto rounded bg-background p-2 font-mono text-[10px] text-muted-foreground">
                              {JSON.stringify(item.depois, null, 2)}
                            </pre>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  );
}
