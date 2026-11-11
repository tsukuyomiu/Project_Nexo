import { useEffect, useState } from "react";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { FieldLabel } from "@/components/FieldLabel";
import { useTransactions } from "@/hooks/useTransactions";
import { emptyProfile, profileSchema, type Profile } from "@/lib/profile";

const fields = [
  {
    key: "name",
    label: "Nome completo",
    type: "text",
    required: true,
    max: 100,
    autocomplete: "name",
  },
  { key: "email", label: "E-mail", type: "email", required: true, max: 255, autocomplete: "email" },
  { key: "phone", label: "Telefone", type: "tel", required: false, max: 25, autocomplete: "tel" },
  {
    key: "birthDate",
    label: "Data de nascimento",
    type: "date",
    required: false,
    max: 10,
    autocomplete: "bday",
  },
  {
    key: "address",
    label: "Endereço",
    type: "text",
    required: false,
    max: 200,
    autocomplete: "street-address",
  },
] as const;

export function ProfileDialog({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const { profile, updateProfile } = useTransactions();
  const [draft, setDraft] = useState<Profile>({ ...emptyProfile });
  const [errors, setErrors] = useState<Partial<Record<keyof Profile, string | undefined>>>({});
  const [saving, setSaving] = useState(false);
  useEffect(() => {
    if (open) {
      setDraft({ ...profile });
      setErrors({});
      setSaving(false);
    }
  }, [open, profile]);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (saving) return;
    const result = profileSchema.safeParse(draft);
    if (!result.success) {
      const next: Partial<Record<keyof Profile, string>> = {};
      for (const issue of result.error.issues) {
        const field = fields.find((item) => item.key === issue.path[0]);
        if (field && !next[field.key]) next[field.key] = issue.message;
      }
      setErrors(next);
      const first = fields.find((field) => next[field.key]);
      if (first) event.currentTarget.querySelector<HTMLElement>(`#profile-${first.key}`)?.focus();
      return;
    }
    setSaving(true);
    try {
      await updateProfile(result.data);
      toast.success("Informações pessoais salvas no banco de dados!");
      onOpenChange(false);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Não foi possível atualizar o perfil.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[85dvh] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Editar informações pessoais</DialogTitle>
          <DialogDescription>
            Alterações temporárias nesta sessão; não serão mantidas ao atualizar a página. O e-mail
            não altera uma conta verificada.
          </DialogDescription>
        </DialogHeader>
        <form method="post" onSubmit={submit} noValidate className="flex flex-col gap-4">
          {fields.map((field) => (
            <div key={field.key}>
              <FieldLabel htmlFor={`profile-${field.key}`} required={field.required}>
                {field.label}
              </FieldLabel>
              <input
                id={`profile-${field.key}`}
                name={field.key}
                type={field.type}
                autoComplete={field.autocomplete}
                maxLength={field.max}
                value={draft[field.key]}
                aria-required={field.required}
                aria-invalid={!!errors[field.key]}
                aria-describedby={errors[field.key] ? `profile-${field.key}-error` : undefined}
                onChange={(event) => {
                  const next = { ...draft, [field.key]: event.target.value };
                  setDraft(next);
                  if (profileSchema.shape[field.key].safeParse(event.target.value).success)
                    setErrors((current) => ({ ...current, [field.key]: undefined }));
                }}
                className="h-9 w-full rounded-lg border border-border bg-background px-3 text-sm text-foreground shadow-field outline-none focus:ring-2 focus:ring-secondary"
              />
              {errors[field.key] && (
                <p id={`profile-${field.key}-error`} className="mt-1 text-xs text-destructive">
                  {errors[field.key]}
                </p>
              )}
            </div>
          ))}
          <div className="grid grid-cols-2 gap-4">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button type="submit" variant="secondary" disabled={saving}>
              Salvar
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
