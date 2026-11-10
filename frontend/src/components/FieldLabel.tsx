import type { ReactNode } from "react";

export function FieldLabel({
  htmlFor,
  required = false,
  children,
}: {
  htmlFor: string;
  required?: boolean;
  children: ReactNode;
}) {
  return (
    <label htmlFor={htmlFor} className="mb-1 block text-xs font-bold text-foreground">
      {children}
      {required && (
        <span aria-hidden="true" className="ml-1 text-destructive">
          *
        </span>
      )}
    </label>
  );
}
