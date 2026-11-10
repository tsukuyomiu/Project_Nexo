import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { emptyProfile, prepareProfile, type Profile } from "@/lib/profile";
import { loadCurrency, saveCurrency, type Currency } from "@/lib/preferences";
import { endLocalScope, loadLocalScope, startLocalScope } from "@/lib/local-identity";
import {
  createTransaction,
  loadTransactions,
  saveTransactions,
  sortTransactions,
  type Transaction,
} from "@/lib/transactions";

interface TransactionsContextValue {
  transactions: Transaction[]; // sempre na ordenação única do app
  loaded: boolean;
  lastAddedId: string | null;
  profile: Profile;
  currency: Currency;
  setCurrency: (currency: Currency) => boolean;
  updateProfile: (profile: Profile) => void;
  resetProfile: () => void;
  startLocalSession: (email: string) => Promise<void>;
  endLocalSession: () => void;
  add: (data: Omit<Transaction, "id">) => void;
  update: (id: string, data: Omit<Transaction, "id">) => void;
  remove: (id: string) => void;
}

const TransactionsContext = createContext<TransactionsContextValue | null>(null);

// Provider da fonte única de verdade: Dashboard, Lançamentos, Perfil e o
// modal consomem este mesmo estado. A persistência (temporária) fica
// centralizada aqui — nenhum componente de tela toca o localStorage.
export function TransactionsProvider({ children }: { children: ReactNode }) {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [lastAddedId, setLastAddedId] = useState<string | null>(null);
  const [profile, setProfile] = useState<Profile>({ ...emptyProfile });
  const [currency, setCurrencyState] = useState<Currency>("BRL");
  const [scope, setScope] = useState<string | null>(null);

  useEffect(() => {
    if (!lastAddedId) return;
    const timer = window.setTimeout(() => setLastAddedId(null), 350);
    return () => window.clearTimeout(timer);
  }, [lastAddedId]);

  useEffect(() => {
    const savedScope = loadLocalScope();
    setScope(savedScope);
    setTransactions(loadTransactions(savedScope));
    setCurrencyState(loadCurrency());
    setLoaded(true);
  }, []);

  useEffect(() => {
    if (loaded && scope) saveTransactions(transactions, scope);
  }, [transactions, loaded, scope]);

  const value = useMemo<TransactionsContextValue>(
    () => ({
      transactions: sortTransactions(transactions),
      loaded,
      lastAddedId,
      profile,
      currency,
      setCurrency: (next) => {
        const saved = saveCurrency(next);
        if (saved) setCurrencyState(next);
        return saved;
      },
      updateProfile: (next) => setProfile(prepareProfile(next)),
      resetProfile: () => setProfile({ ...emptyProfile }),
      startLocalSession: async (email) => {
        const nextScope = await startLocalScope(email);
        setScope(nextScope);
        setTransactions(loadTransactions(nextScope));
        setProfile({ ...emptyProfile });
        setLastAddedId(null);
        setLoaded(true);
      },
      endLocalSession: () => {
        // Persistir antes da saída não apaga nem transfere dados para outro escopo.
        if (scope) saveTransactions(transactions, scope);
        endLocalScope();
        setScope(null);
        setTransactions([]);
        setProfile({ ...emptyProfile });
        setLastAddedId(null);
      },
      // novos lançamentos entram no início (desempate da ordenação)
      add: (data) => {
        const transaction = createTransaction(data);
        setLastAddedId(transaction.id);
        setTransactions((cur) => [transaction, ...cur]);
      },
      update: (id, data) =>
        setTransactions((cur) => cur.map((t) => (t.id === id ? { ...data, id } : t))),
      remove: (id) => setTransactions((cur) => cur.filter((t) => t.id !== id)),
    }),
    [transactions, loaded, lastAddedId, profile, currency, scope],
  );

  return <TransactionsContext.Provider value={value}>{children}</TransactionsContext.Provider>;
}

export function useTransactions(): TransactionsContextValue {
  const ctx = useContext(TransactionsContext);
  if (!ctx) throw new Error("useTransactions deve ser usado dentro de TransactionsProvider");
  return ctx;
}
