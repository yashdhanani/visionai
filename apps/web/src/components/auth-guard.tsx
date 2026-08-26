"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth";
import { api } from "@/lib/api";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { user, setAuth, setHydrated, hydrated } = useAuthStore();
  const router = useRouter();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setHydrated(true);
      setLoading(false);
      router.replace("/login");
      return;
    }
    api
      .get("/api/v1/auth/me")
      .then((res) => {
        setAuth(res.data.data, token);
        setLoading(false);
      })
      .catch(() => {
        localStorage.removeItem("access_token");
        setHydrated(true);
        setLoading(false);
        router.replace("/login");
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (loading || !hydrated) {
    return (
      <div suppressHydrationWarning className="flex items-center justify-center h-screen">
        <div suppressHydrationWarning className="animate-spin rounded-full h-8 w-8 border-b-2 border-zinc-900 dark:border-zinc-100" />
      </div>
    );
  }

  if (!user) return null;

  return <>{children}</>;
}