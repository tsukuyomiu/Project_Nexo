import { z } from "zod";

// Perfil temporário somente em memória. A persistência definitiva e a verificação
// do e-mail dependerão da API; nenhum dado pessoal é gravado no localStorage.
export const profileSchema = z.object({
  name: z.string().trim().min(1, "Informe seu nome.").max(100, "Use até 100 caracteres."),
  email: z
    .string()
    .trim()
    .min(1, "Informe seu e-mail.")
    .email("Informe um email válido.")
    .max(255, "Use até 255 caracteres."),
  phone: z
    .string()
    .trim()
    .max(25, "Use até 25 caracteres.")
    .refine(
      (value) => !value || (/^[+\d\s().-]+$/.test(value) && value.replace(/\D/g, "").length >= 8),
      "Informe um telefone válido.",
    ),
  birthDate: z
    .string()
    .refine(
      (value) =>
        !value ||
        (/^\d{4}-\d{2}-\d{2}$/.test(value) &&
          !Number.isNaN(Date.parse(value)) &&
          new Date(value).toISOString().slice(0, 10) === value &&
          value <= new Date().toISOString().slice(0, 10)),
      "Informe uma data de nascimento válida.",
    ),
  address: z.string().trim().max(200, "Use até 200 caracteres."),
});
export type Profile = z.infer<typeof profileSchema>;
export const emptyProfile: Profile = { name: "", email: "", phone: "", birthDate: "", address: "" };
export function prepareProfile(input: Profile): Profile {
  return profileSchema.parse(input);
}
