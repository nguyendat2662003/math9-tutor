"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { fetchMe, logout as apiLogout } from "../../lib/api";
import type { Me } from "../../types/auth";

// Trang dùng được khi chưa đăng nhập. Còn lại (giải bài, luyện đề, lịch sử, quản trị) bắt buộc đăng nhập.
const PUBLIC = ["/login"];
// Tài khoản mới cấp / vừa được đặt lại mật khẩu: chỉ được ở trang đổi mật khẩu
const CHANGE_PASSWORD = "/account";

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
    } else if (user?.must_change_password && path !== CHANGE_PASSWORD) {
      router.replace(CHANGE_PASSWORD);
    }
  }, [ready, user, isPublic, path, router]);

  const mustChange = !!user?.must_change_password && path !== CHANGE_PASSWORD;
  const gate = (!isPublic && (!ready || !user)) || mustChange;
  return (
    <Ctx.Provider value={{ user, ready, refresh, logout }}>
      {gate ? <main className="app"><div className="card muted">Đang kiểm tra đăng nhập…</div></main> : children}
    </Ctx.Provider>
  );
}
