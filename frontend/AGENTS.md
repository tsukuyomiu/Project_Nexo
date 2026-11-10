<!-- LOVABLE:BEGIN -->
> [!IMPORTANT]
> This project is connected to [Lovable](https://lovable.dev). Avoid rewriting
> published git history — force pushing, or rebasing/amending/squashing commits
> that are already pushed — as it rewrites history on Lovable's side and the
> user will likely lose their project history.
>
> Commits you push to the connected branch sync back to Lovable and show up in
> the editor, so keep the branch in a working state.
<!-- LOVABLE:END -->

## Architecture decisions

- Transactions data layer stays in `transactions.ts` and the root-mounted `TransactionsProvider` to avoid code-split context duplication. Live storage always receives an explicit local scope; the unscoped `nexo:transactions` legacy key is preserved but never automatically assigned to a user. Replace storage adapters when backend arrives.
- Internal pages (Dashboard, Lançamentos, Perfil) use `src/components/AppLayout.tsx` (dark header with nav); auth pages keep `NexoLayout`.
- Password change has a single integration point in `src/lib/change-password.ts`; it currently returns unavailable because no auth service exists.
- Required form labels use `FieldLabel`; signup rules live in `signup-validation` so existing validation can be tested independently.
- Transaction loading and short-lived new-row animation state remain in the existing root-mounted provider; no second provider or account identity is fabricated.
- Frontend profile and currency share the existing root-mounted context to avoid code-split duplication; profile adapters validate with Zod and keep personal data in memory only, while preference adapters isolate provisional browser storage for future replacement by an account API.
- `local-identity.ts` derives a provisional transaction namespace from validated login email and keeps the active scope in sessionStorage; this is not authentication or an access-control boundary, and passwords are never persisted.
