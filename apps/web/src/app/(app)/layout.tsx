"use client";

import { AuthGuard } from "@/components/auth-guard";
import { AppLayout } from "@/components/app-layout";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <AppLayout>{children}</AppLayout>
    </AuthGuard>
  );
}