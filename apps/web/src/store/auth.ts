"use client";

import { create } from "zustand";

interface User {
  id: string;
  name: string;
  email: string;
  avatar: string | null;
  role: string;
  email_verified: boolean;
  created_at: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  setAuth: (user: User, token: string) => void;
  logout: () => void;
  hydrated: boolean;
  setHydrated: (v: boolean) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  hydrated: false,
  setAuth: (user, token) => {
    if (typeof window !== "undefined") {
      localStorage.setItem("access_token", token);
    }
    set({ user, token, hydrated: true });
  },
  logout: () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("access_token");
    }
    set({ user: null, token: null, hydrated: true });
  },
  setHydrated: (v) => set({ hydrated: v }),
}));