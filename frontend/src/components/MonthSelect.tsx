import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { monthLabel } from "@/lib/transactions";

/* Seletor de mês/ano no padrão das telas internas (Dashboard, Lançamentos, Perfil). */
export function MonthSelect({
  value,
  onChange,
  options,
  allowAll = false,
}: {
  value: string;
  onChange: (v: string) => void;
  options: string[];
  allowAll?: boolean;
}) {
  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger className="w-[190px] bg-background" aria-label="Selecionar mês">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {allowAll && <SelectItem value="all">Todos os meses</SelectItem>}
        {options.map((key) => (
          <SelectItem key={key} value={key}>
            {monthLabel(key)}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
