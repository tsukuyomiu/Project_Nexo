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
import {
  apiCreateTransaction,
  apiDeleteTransaction,
  apiGetMyProfile,
  apiListTransactions,
  apiLogFrontendEvent,
  apiLogout,
  apiUpdateMyPreferences,
  apiUpdateMyProfile,
  apiUpdateTransaction,
  getAuthToken,
  getStoredAuthUser,
  setAuthSession,
  type StoredAuthUser,
} from "@/lib/api";

interface TransactionsContextValue {
  transactions: Transaction[];
  loaded: boolean;
  lastAddedId: string | null;
  profile: Profile;
  avatarUrl: string | null;
  setAvatarUrl: (dataUrl: string | null) => void;
  role: "user" | "admin" | "auditor";
  twoFactorEnabled: boolean;
  currency: Currency;
  setCurrency: (currency: Currency) => boolean;
  setTwoFactorEnabled: (enabled: boolean) => Promise<boolean>;
  updateProfile: (profile: Profile) => Promise<void>;
  resetProfile: () => void;
  authenticateSession: (token: string, user: StoredAuthUser) => Promise<void>;
  startLocalSession: (email: string) => Promise<void>;
  endLocalSession: () => void;
  add: (data: Omit<Transaction, "id">) => void;
  update: (id: string, data: Omit<Transaction, "id">) => void;
  remove: (id: string) => void;
}

const TransactionsContext = createContext<TransactionsContextValue | null>(null);

function getAvatarStorageKey(email?: string): string {
  return `nexo:avatar:${(email || "default").trim().toLowerCase()}`;
}

export function TransactionsProvider({ children }: { children: ReactNode }) {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [lastAddedId, setLastAddedId] = useState<string | null>(null);
  const [profile, setProfile] = useState<Profile>({ ...emptyProfile });
  const [avatarUrl, setAvatarUrlState] = useState<string | null>(null);
  const [role, setRole] = useState<"user" | "admin" | "auditor">("user");
  const [twoFactorEnabled, setTwoFactorState] = useState<boolean>(false);
  const [currency, setCurrencyState] = useState<Currency>("BRL");
  const [scope, setScope] = useState<string | null>(null);

  useEffect(() => {
    try {
      const savedAvatar = localStorage.getItem(getAvatarStorageKey(profile.email));
      setAvatarUrlState(savedAvatar || null);
    } catch {
      setAvatarUrlState(null);
    }
  }, [profile.email]);

  useEffect(() => {
    if (!lastAddedId) return;
    const timer = window.setTimeout(() => setLastAddedId(null), 350);
    return () => window.clearTimeout(timer);
  }, [lastAddedId]);

  async function syncFromBackend() {
    const token = getAuthToken();
    const storedUser = getStoredAuthUser();
    if (!token) {
      const savedScope = loadLocalScope();
      setScope(savedScope);
      setTransactions(loadTransactions(savedScope));
      setCurrencyState(loadCurrency());
      setLoaded(true);
      return;
    }

    if (storedUser) {
      setRole(storedUser.role || "user");
      setProfile((prev) => ({
        ...prev,
        name: storedUser.name || prev.name,
        email: storedUser.email || prev.email,
      }));
      if (storedUser.currency) setCurrencyState(storedUser.currency);
      if (typeof storedUser.twoFactorEnabled === "boolean") {
        setTwoFactorState(storedUser.twoFactorEnabled);
      }
    }

    try {
      const [remoteProfile, remoteTx] = await Promise.all([
        apiGetMyProfile(),
        apiListTransactions(),
      ]);
      setProfile({
        name: remoteProfile.name || "",
        email: remoteProfile.email || "",
        phone: remoteProfile.phone || "",
        birthDate: remoteProfile.birthDate || "",
        address: remoteProfile.address || "",
      });
      setRole(remoteProfile.role || "user");
      setCurrencyState(remoteProfile.currency || "BRL");
      setTwoFactorState(Boolean(remoteProfile.twoFactorEnabled));
      setTransactions(remoteTx);
      setAuthSession(token, {
        id: remoteProfile.id,
        name: remoteProfile.name,
        email: remoteProfile.email,
        role: remoteProfile.role,
        currency: remoteProfile.currency,
        twoFactorEnabled: remoteProfile.twoFactorEnabled,
      });
    } catch {
      // Se o token expirou ou o servidor reiniciou
    } finally {
      setLoaded(true);
    }
  }

  useEffect(() => {
    void syncFromBackend();
  }, []);

  useEffect(() => {
    if (loaded && scope && !getAuthToken()) {
      saveTransactions(transactions, scope);
    }
  }, [transactions, loaded, scope]);

  const value = useMemo<TransactionsContextValue>(
    () => ({
      transactions: sortTransactions(transactions),
      loaded,
      lastAddedId,
      profile,
      avatarUrl,
      setAvatarUrl: (dataUrl) => {
        setAvatarUrlState(dataUrl);
        try {
          const key = getAvatarStorageKey(profile.email);
          if (dataUrl) {
            localStorage.setItem(key, dataUrl);
          } else {
            localStorage.removeItem(key);
          }
        } catch {
          // ignore storage quota errors
        }
        if (getAuthToken()) {
          void apiLogFrontendEvent(
            "PROFILE_PHOTO_UPDATED",
            dataUrl
              ? `Usuário '${profile.name || profile.email}' alterou a foto de perfil.`
              : `Usuário '${profile.name || profile.email}' removeu a foto de perfil.`,
          );
        }
      },
      role,
      twoFactorEnabled,
      currency,
      setCurrency: (next) => {
        const saved = saveCurrency(next);
        if (saved) setCurrencyState(next);
        if (getAuthToken()) {
          void apiUpdateMyPreferences({ currency: next, twoFactorEnabled });
        }
        return saved;
      },
      setTwoFactorEnabled: async (enabled) => {
        if (!getAuthToken()) return false;
        try {
          const updated = await apiUpdateMyPreferences({
            currency,
            twoFactorEnabled: enabled,
          });
          setTwoFactorState(Boolean(updated.twoFactorEnabled));
          return true;
        } catch {
          return false;
        }
      },
      updateProfile: async (next) => {
        const prepared = prepareProfile(next);
        if (getAuthToken()) {
          const updated = await apiUpdateMyProfile(prepared);
          setProfile({
            name: updated.name,
            email: updated.email,
            phone: updated.phone,
            birthDate: updated.birthDate,
            address: updated.address,
          });
          setRole(updated.role);
        } else {
          setProfile(prepared);
        }
      },
      resetProfile: () => setProfile({ ...emptyProfile }),
      authenticateSession: async (token, user) => {
        setAuthSession(token, user);
        const nextScope = await startLocalScope(user.email);
        setScope(nextScope);
        setRole(user.role || "user");
        setProfile({
          name: user.name,
          email: user.email,
          phone: "",
          birthDate: "",
          address: "",
        });
        setCurrencyState(user.currency || "BRL");
        setTwoFactorState(Boolean(user.twoFactorEnabled));
        await syncFromBackend();
      },
      startLocalSession: async (email) => {
        const nextScope = await startLocalScope(email);
        setScope(nextScope);
        setTransactions(loadTransactions(nextScope));
        setProfile({ ...emptyProfile, email });
        setLastAddedId(null);
        setLoaded(true);
      },
      endLocalSession: () => {
        void apiLogout();
        if (scope && !getAuthToken()) saveTransactions(transactions, scope);
        endLocalScope();
        setScope(null);
        setTransactions([]);
        setProfile({ ...emptyProfile });
        setRole("user");
        setTwoFactorState(false);
        setLastAddedId(null);
      },
      add: (data) => {
        if (getAuthToken()) {
          void apiCreateTransaction(data).then((created) => {
            setLastAddedId(created.id);
            setTransactions((cur) => [created, ...cur]);
          });
        } else {
          const transaction = createTransaction(data);
          setLastAddedId(transaction.id);
          setTransactions((cur) => [transaction, ...cur]);
        }
      },
      update: (id, data) => {
        if (getAuthToken()) {
          void apiUpdateTransaction(id, data).then((updated) => {
            setTransactions((cur) => cur.map((t) => (t.id === id ? updated : t)));
          });
        } else {
          setTransactions((cur) => cur.map((t) => (t.id === id ? { ...data, id } : t)));
        }
      },
      remove: (id) => {
        if (getAuthToken()) {
          void apiDeleteTransaction(id).then(() => {
            setTransactions((cur) => cur.filter((t) => t.id !== id));
          });
        } else {
          setTransactions((cur) => cur.filter((t) => t.id !== id));
        }
      },
    }),
    [transactions, loaded, lastAddedId, profile, avatarUrl, role, twoFactorEnabled, currency, scope],
  );

  return <TransactionsContext.Provider value={value}>{children}</TransactionsContext.Provider>;
}

export function useTransactions(): TransactionsContextValue {
  const ctx = useContext(TransactionsContext);
  if (!ctx) throw new Error("useTransactions deve ser usado dentro de TransactionsProvider");
  return ctx;
}
