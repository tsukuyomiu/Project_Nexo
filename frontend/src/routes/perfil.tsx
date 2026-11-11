import { createFileRoute, Link } from "@tanstack/react-router";
import {
  ArrowDown,
  ArrowUp,
  CalendarDays,
  Camera,
  Clock,
  Eye,
  EyeOff,
  Lock,
  Mail,
  MapPin,
  Minus,
  Pencil,
  Phone,
  Plus,
  Settings,
  ShieldCheck,
  User,
  Wallet,
} from "lucide-react";
import { useRef, useState } from "react";
import { toast } from "sonner";
import { AppLayout } from "@/components/AppLayout";
import { PasswordStrengthMeter } from "@/components/NexoLayout";
import { MonthSelect } from "@/components/MonthSelect";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Switch } from "@/components/ui/switch";
import { useTransactions } from "@/hooks/useTransactions";
import { changePassword } from "@/lib/change-password";
import { ProfileDialog } from "@/components/ProfileDialog";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { CURRENCIES, currencySchema } from "@/lib/preferences";
import {
  calcTotals,
  currentMonthKey,
  filterByMonth,
  formatBRL,
  formatDate,
  monthOptions,
} from "@/lib/transactions";

export const Route = createFileRoute("/perfil")({
  head: () => ({
    meta: [
      { title: "Perfil | Nexo" },
      {
        name: "description",
        content: "Visualize e edite suas informações pessoais e preferências.",
      },
    ],
  }),
  component: ProfilePage,
});

type PasswordErrors = Partial<Record<"current" | "next" | "confirm", string>>;

function ProfilePage() {
  const {
    transactions,
    profile,
    avatarUrl,
    setAvatarUrl,
    twoFactorEnabled,
    setTwoFactorEnabled,
    currency,
    setCurrency,
  } = useTransactions();
  const [month, setMonth] = useState(currentMonthKey());
  const [passwordOpen, setPasswordOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [toggling2FA, setToggling2FA] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const totals = calcTotals(filterByMonth(transactions, month));
  const recent = transactions.slice(0, 3);
  const displayName = profile.name?.trim() || profile.email?.split("@")[0] || "Membro Nexo";

  function handleAvatarChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.type.startsWith("image/")) {
      toast.error("Selecione um arquivo de imagem válido (PNG, JPG ou WEBP).");
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      const rawDataUrl = typeof reader.result === "string" ? reader.result : null;
      if (!rawDataUrl) return;

      const img = new Image();
      img.onload = () => {
        try {
          const canvas = document.createElement("canvas");
          const size = 256;
          canvas.width = size;
          canvas.height = size;
          const ctx = canvas.getContext("2d");
          if (ctx) {
            const minSide = Math.min(img.width, img.height);
            const sx = (img.width - minSide) / 2;
            const sy = (img.height - minSide) / 2;
            ctx.drawImage(img, sx, sy, minSide, minSide, 0, 0, size, size);
            setAvatarUrl(canvas.toDataURL("image/jpeg", 0.85));
          } else {
            setAvatarUrl(rawDataUrl);
          }
        } catch {
          setAvatarUrl(rawDataUrl);
        }
        toast.success("Foto de perfil atualizada com sucesso!");
      };
      img.onerror = () => {
        setAvatarUrl(rawDataUrl);
        toast.success("Foto de perfil atualizada com sucesso!");
      };
      img.src = rawDataUrl;
    };
    reader.readAsDataURL(file);
    e.target.value = "";
  }

  async function handleToggle2FA(checked: boolean) {
    if (toggling2FA) return;
    setToggling2FA(true);
    try {
      const ok = await setTwoFactorEnabled(checked);
      if (ok) {
        toast.success(
          checked
            ? "Autenticação em duas etapas (2FA) ATIVADA! No próximo login enviaremos um código de 6 dígitos para o seu e-mail."
            : "Autenticação em duas etapas (2FA) desativada.",
        );
      } else {
        toast.error("Faça login com uma conta cadastrada para ativar a autenticação em 2 etapas.");
      }
    } finally {
      setToggling2FA(false);
    }
  }

  return (
    <AppLayout>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="flex flex-col gap-4">
          <section className="flex items-center gap-6 rounded-2xl bg-primary p-8 text-primary-foreground shadow-card">
            <div className="relative">
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleAvatarChange}
                className="hidden"
                aria-label="Selecionar foto de perfil"
              />
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                title="Clique para alterar sua foto de perfil"
                aria-label="Alterar foto de perfil"
                className="group relative block rounded-full focus:outline-none focus-visible:ring-2 focus-visible:ring-secondary"
              >
                <span className="grid h-24 w-24 overflow-hidden place-items-center rounded-full bg-muted text-muted-foreground transition group-hover:brightness-95">
                  {avatarUrl ? (
                    <img
                      src={avatarUrl}
                      alt={`Foto de perfil de ${displayName}`}
                      className="h-full w-full object-cover"
                    />
                  ) : (
                    <User className="h-12 w-12" />
                  )}
                </span>
                <span className="absolute -bottom-1 -right-1 grid h-7 w-7 place-items-center rounded-full border-2 border-primary bg-secondary text-secondary-foreground shadow-btn transition group-hover:scale-110">
                  <Camera className="h-3.5 w-3.5" />
                </span>
              </button>
            </div>
            <div>
              <h1 className="break-words text-2xl font-bold">Olá, {displayName}!</h1>
              <p className="mt-1 max-w-xs text-xs">
                {profile.email
                  ? `Conectado como ${profile.email}`
                  : "Aqui você pode visualizar e editar suas informações pessoais e preferências."}
              </p>
            </div>
          </section>

          <section className="rounded-xl border border-primary/40 bg-card p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <h2 className="flex items-center gap-2 font-bold text-foreground">
                <User className="h-4 w-4" /> Informações pessoais
              </h2>
              <Button
                variant="link"
                size="sm"
                type="button"
                onClick={() => setProfileOpen(true)}
                className="flex items-center gap-1 text-xs font-bold text-link hover:underline"
              >
                <Pencil className="h-3 w-3" /> Editar
              </Button>
            </div>
            <dl className="mt-4 flex flex-col gap-3 text-sm">
              {[
                { icon: <User className="h-4 w-4" />, label: "Nome completo", value: profile.name },
                { icon: <Mail className="h-4 w-4" />, label: "E-mail", value: profile.email },
                { icon: <Phone className="h-4 w-4" />, label: "Telefone", value: profile.phone },
                {
                  icon: <CalendarDays className="h-4 w-4" />,
                  label: "Data de nascimento",
                  value: profile.birthDate ? formatDate(profile.birthDate) : "",
                },
                { icon: <MapPin className="h-4 w-4" />, label: "Endereço", value: profile.address },
              ].map((row) => (
                <div key={row.label} className="flex items-center gap-3">
                  <span className="text-muted-foreground">{row.icon}</span>
                  <dt className="w-28 shrink-0 text-muted-foreground sm:w-36">{row.label}</dt>
                  <dd className="min-w-0 break-words font-bold text-foreground">
                    {row.value || "Não informado"}
                  </dd>
                </div>
              ))}
            </dl>
          </section>

          <section className="rounded-xl border border-primary/40 bg-card p-5 shadow-sm">
            <div className="flex items-center justify-between gap-4">
              <div>
                <h2 className="flex items-center gap-2 font-bold text-foreground">
                  <Lock className="h-4 w-4" /> Segurança
                </h2>
                <p className="mt-1 text-xs text-muted-foreground">
                  Mantenha seus dados protegidos com uma senha forte e a autenticação em duas
                  etapas.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setPasswordOpen(true)}
                className="h-9 shrink-0 rounded-lg bg-secondary px-4 text-xs font-bold text-secondary-foreground shadow-btn hover:brightness-110"
              >
                Alterar senha
              </button>
            </div>
            <div className="mt-4 flex items-center justify-between border-t border-border pt-4">
              <div>
                <span className="flex items-center gap-2 text-sm font-semibold text-foreground">
                  <ShieldCheck className="h-4 w-4 text-secondary" /> Autenticação em duas etapas
                  (2FA)
                </span>
                <p className="mt-0.5 text-[11px] text-muted-foreground">
                  {twoFactorEnabled
                    ? "Ativa: exigirá código de 6 dígitos enviado por e-mail ao fazer login."
                    : "Desativada: ative para exigir código de segurança por e-mail no login."}
                </p>
              </div>
              <Switch
                checked={twoFactorEnabled}
                disabled={toggling2FA}
                onCheckedChange={handleToggle2FA}
                aria-label="Autenticação em duas etapas"
              />
            </div>
          </section>
        </div>

        <div className="flex flex-col gap-4">
          <section className="rounded-xl border border-primary/40 bg-card p-5 shadow-sm">
            <div className="flex items-start justify-between gap-2">
              <div>
                <h2 className="font-bold text-foreground">Resumo financeiro</h2>
                <p className="text-xs text-muted-foreground">
                  Acompanhe de forma rápida o desempenho da sua situação financeira.
                </p>
              </div>
              <MonthSelect value={month} onChange={setMonth} options={monthOptions(transactions)} />
            </div>
            <div className="mt-4 grid grid-cols-3 gap-2 text-center">
              <div>
                <span className="mx-auto grid h-8 w-8 place-items-center rounded-full bg-income-soft text-income">
                  <ArrowUp className="h-4 w-4" />
                </span>
                <p className="mt-1 text-xs text-muted-foreground">Entradas</p>
                <p className="break-words text-sm font-bold text-foreground">
                  {formatBRL(totals.income, currency)}
                </p>
              </div>
              <div>
                <span className="mx-auto grid h-8 w-8 place-items-center rounded-full bg-expense-soft text-expense">
                  <ArrowDown className="h-4 w-4" />
                </span>
                <p className="mt-1 text-xs text-muted-foreground">Saídas</p>
                <p className="break-words text-sm font-bold text-foreground">
                  {formatBRL(totals.expense, currency)}
                </p>
              </div>
              <div>
                <span className="mx-auto grid h-8 w-8 place-items-center rounded-full bg-primary-soft text-primary">
                  <Wallet className="h-4 w-4" />
                </span>
                <p className="mt-1 text-xs text-muted-foreground">Resultado</p>
                <p className="break-words text-sm font-bold text-foreground">
                  {formatBRL(totals.balance, currency)}
                </p>
              </div>
            </div>
          </section>

          <section className="rounded-xl border border-primary/40 bg-card p-5 shadow-sm">
            <h2 className="flex items-center gap-2 font-bold text-foreground">
              <Settings className="h-4 w-4" /> Preferências
            </h2>
            <ul className="mt-4 flex flex-col gap-3 text-sm">
              <li className="flex flex-wrap items-center justify-between gap-3">
                <span className="flex items-center gap-2 text-foreground">
                  <span className="grid h-7 w-7 place-items-center rounded-full bg-primary-soft text-xs font-bold text-primary">
                    R$
                  </span>{" "}
                  Moeda
                </span>
                <Select
                  value={currency}
                  onValueChange={(value) => {
                    const result = currencySchema.safeParse(value);
                    if (!result.success) return;
                    if (setCurrency(result.data))
                      toast.success("Moeda de preferência salva com sucesso!");
                    else toast.error("Não foi possível salvar a moeda.");
                  }}
                >
                  <SelectTrigger aria-label="Moeda" className="w-full sm:w-56">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {CURRENCIES.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </li>
            </ul>
            <p className="mt-3 text-xs text-muted-foreground">
              Altera o símbolo exibido e salva a preferência vinculada à sua conta no banco SQL.
            </p>
          </section>

          <section className="rounded-xl border border-primary/40 bg-card p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <h2 className="flex items-center gap-2 font-bold text-foreground">
                <Clock className="h-4 w-4" /> Atividade recente
              </h2>
              <Link to="/lancamentos" className="text-xs font-bold text-link hover:underline">
                Ver todas
              </Link>
            </div>
            <ul className="mt-4 flex flex-col gap-3 text-sm">
              {recent.length === 0 && (
                <li className="text-xs text-muted-foreground">Nenhuma atividade recente.</li>
              )}
              {recent.map((t) => (
                <li key={t.id} className="flex items-center gap-3">
                  <span
                    className={`grid h-8 w-8 shrink-0 place-items-center rounded-full ${t.type === "income" ? "bg-income-soft text-income" : "bg-expense-soft text-expense"}`}
                  >
                    {t.type === "income" ? (
                      <Plus className="h-4 w-4" />
                    ) : (
                      <Minus className="h-4 w-4" />
                    )}
                  </span>
                  <div className="flex-1">
                    <p className="font-bold text-foreground">
                      {t.type === "income" ? "Nova receita registrada" : "Despesa registrada"}
                    </p>
                    <p className="max-w-[200px] truncate text-xs text-muted-foreground">
                      {t.description}
                    </p>
                  </div>
                  <span className="text-xs text-muted-foreground">{formatDate(t.date)}</span>
                </li>
              ))}
            </ul>
          </section>
        </div>
      </div>

      <PasswordDialog open={passwordOpen} onOpenChange={setPasswordOpen} />
      <ProfileDialog open={profileOpen} onOpenChange={setProfileOpen} />
    </AppLayout>
  );
}

function PasswordDialog({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const [form, setForm] = useState({ current: "", next: "", confirm: "" });
  const [show, setShow] = useState({ current: false, next: false, confirm: false });
  const [errors, setErrors] = useState<PasswordErrors>({});
  const [notice, setNotice] = useState("");
  const [saving, setSaving] = useState(false);

  function reset() {
    setForm({ current: "", next: "", confirm: "" });
    setShow({ current: false, next: false, confirm: false });
    setErrors({});
    setNotice("");
    setSaving(false);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (saving) return;
    const next: PasswordErrors = {};
    if (!form.current) next.current = "Informe sua senha atual.";
    if (form.next.length < 6) next.next = "A nova senha deve ter ao menos 6 caracteres.";
    if (form.next && form.next === form.current)
      next.next = "A nova senha deve ser diferente da atual.";
    if (form.confirm !== form.next) next.confirm = "As senhas não coincidem.";
    setErrors(next);
    setNotice("");
    if (Object.keys(next).length > 0) return;

    setSaving(true);
    try {
      const result = await changePassword(form.current, form.next);
      if (!result.ok) {
        setNotice(result.message ?? "Não foi possível alterar a senha.");
        setForm({ current: "", next: "", confirm: "" });
      } else {
        toast.success(result.message || "Senha alterada com sucesso!");
        reset();
        onOpenChange(false);
      }
    } finally {
      setSaving(false);
    }
  }

  const fields = [
    { key: "current" as const, label: "Senha atual" },
    { key: "next" as const, label: "Nova senha" },
    { key: "confirm" as const, label: "Confirmar nova senha" },
  ];

  return (
    <Dialog
      open={open}
      onOpenChange={(v) => {
        if (!v) reset();
        onOpenChange(v);
      }}
    >
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Alterar senha</DialogTitle>
          <DialogDescription>
            Preencha os campos abaixo para alterar sua senha de acesso no banco de dados.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4">
          {fields.map((field) => (
            <div key={field.key}>
              <label
                htmlFor={`pw-${field.key}`}
                className="mb-1 block text-xs font-bold text-foreground"
              >
                {field.label}
              </label>
              <div className="flex items-center gap-1 rounded-lg border border-border bg-background px-3 shadow-field focus-within:ring-2 focus-within:ring-secondary">
                <Lock className="h-4 w-4 text-muted-foreground" />
                <input
                  id={`pw-${field.key}`}
                  type={show[field.key] ? "text" : "password"}
                  value={form[field.key]}
                  onChange={(e) => setForm({ ...form, [field.key]: e.target.value })}
                  aria-invalid={!!errors[field.key]}
                  className="h-9 flex-1 bg-transparent text-sm outline-none"
                />
                <button
                  type="button"
                  onClick={() => setShow({ ...show, [field.key]: !show[field.key] })}
                  aria-label={
                    show[field.key]
                      ? `Ocultar ${field.label.toLowerCase()}`
                      : `Mostrar ${field.label.toLowerCase()}`
                  }
                  className="text-muted-foreground hover:text-primary"
                >
                  {show[field.key] ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              {errors[field.key] && (
                <p className="mt-1 text-xs text-destructive">{errors[field.key]}</p>
              )}
              {field.key === "next" && <PasswordStrengthMeter password={form.next} />}
            </div>
          ))}

          {notice && (
            <p
              role="alert"
              className="rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-xs text-destructive"
            >
              {notice}
            </p>
          )}

          <div className="mt-2 grid grid-cols-2 gap-4">
            <button
              type="button"
              onClick={() => onOpenChange(false)}
              className="h-10 rounded-lg border border-border bg-background text-sm font-bold text-foreground shadow-btn hover:bg-muted"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={saving}
              className="h-10 rounded-lg bg-secondary text-sm font-bold text-secondary-foreground shadow-btn hover:brightness-110 disabled:opacity-50"
            >
              {saving ? "Salvando..." : "Salvar nova senha"}
            </button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
