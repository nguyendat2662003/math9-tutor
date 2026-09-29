"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { fetchMe, logout as apiLogout } from "../../lib/api";
import type { Me } from "../../types/auth";

// Trang dùng được khi chưa đăng nhập. Còn lại (giải bài, luyện đề, lịch sử) bắt buộc đăng nhập.
const PUBLIC = ["/login", "/admin"];

interface AuthState {
  user: Me | null;
  ready: boolean;
  refresh: () => Promise<void>;
  logout: () => Promise<void>;
}

const Ctx = createContext<AuthState>({ user: null, ready: false, refresh: async () => {}, logout: async () => {} });
export const useAuth = () => useContext(Ctx);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<Me | null>(null);
  const [ready, setReady] = useState(false);
  const router = useRouter();
  const path = usePathname();
  const isPublic = PUBLIC.some((p) => path === p || path.startsWith(p + "/"));

  const refresh = useCallback(async () => {
    try {
      setUser(await fetchMe());
    } catch {
      setUser(null);
    } finally {
      setReady(true);
    }
  }, []);

  const logout = useCallback(async () => {
    await apiLogout().catch(() => {});
    setUser(null);
    router.replace("/login");
  }, [router]);

  useEffect(() => { refresh(); }, [refresh]);

  // Phiên hết hạn giữa chừng (API trả 401) -> về trang đăng nhập, quay lại đúng trang đang dùng
  useEffect(() => {
    const onExpired = () => {
      setUser(null);
      router.replace(`/login?next=${encodeURIComponent(window.location.pathname + window.location.search)}`);
    };
    window.addEventListener("auth:expired", onExpired);
    return () => window.removeEventListener("auth:expired", onExpired);
  }, [router]);

  useEffect(() => {
    if (ready && !user && !isPublic) {
      router.replace(`/login?next=${encodeURIComponent(window.location.pathname + window.location.search)}`);
    }
  }, [ready, user, isPublic, router]);

  const gate = !isPublic && (!ready || !user);
  return (
    <Ctx.Provider value={{ user, ready, refresh, logout }}>
      {gate ? <main className="app"><div className="card muted">Đang kiểm tra đăng nhập…</div></main> : children}
    </Ctx.Provider>
  );
}
