import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { api, send, setCsrf } from "./api";
import type { Lookups, User } from "./types";

interface AuthState {
  user: User | null;
  loading: boolean;
  lookups: Lookups | null;
  login: (u: string, p: string) => Promise<void>;
  logout: () => Promise<void>;
  reloadLookups: () => Promise<void>;
}
const AuthContext = createContext<AuthState>(null!);
export const useAuth = () => useContext(AuthContext);
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null),
    [loading, setLoading] = useState(true),
    [lookups, setLookups] = useState<Lookups | null>(null);
  const reloadLookups = useCallback(async () => {
    setLookups(await api<Lookups>("/lookups"));
  }, []);
  const accept = useCallback(
    async (data: { user: User; csrf_token: string }) => {
      setCsrf(data.csrf_token);
      setLookups(await api<Lookups>("/lookups"));
      setUser(data.user);
    },
    [],
  );
  useEffect(() => {
    api<{ user: User; csrf_token: string }>("/auth/me")
      .then(accept)
      .catch(() => {
        setUser(null);
        setCsrf("");
      })
      .finally(() => setLoading(false));
    const expire = () => {
      setUser(null);
      setCsrf("");
    };
    window.addEventListener("session-expired", expire);
    return () => window.removeEventListener("session-expired", expire);
  }, [accept]);
  const login = async (u: string, p: string) =>
    accept(await send("/auth/login", { username: u, password: p }));
  const logout = async () => {
    await send("/auth/logout");
    setUser(null);
    setCsrf("");
    setLookups(null);
  };
  return (
    <AuthContext.Provider
      value={{ user, loading, lookups, login, logout, reloadLookups }}
    >
      {children}
    </AuthContext.Provider>
  );
}

const ToastContext = createContext<(message: string) => void>(() => {});
export const useToast = () => useContext(ToastContext);
export function ToastProvider({ children }: { children: ReactNode }) {
  const [message, setMessage] = useState("");
  useEffect(() => {
    if (message) {
      const timer = setTimeout(() => setMessage(""), 4500);
      return () => clearTimeout(timer);
    }
  }, [message]);
  return (
    <ToastContext.Provider value={setMessage}>
      {children}
      {message && (
        <div className="toast" role="status">
          {message}
          <button aria-label="Đóng thông báo" onClick={() => setMessage("")}>
            ×
          </button>
        </div>
      )}
    </ToastContext.Provider>
  );
}
