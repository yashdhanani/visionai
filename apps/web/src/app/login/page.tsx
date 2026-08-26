"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useToast } from "@/components/ui/toast";

const schema = z.object({ email: z.string().email(), password: z.string().min(6) });

export default function LoginPage() {
  const router = useRouter();
  const { setAuth } = useAuthStore();
  const { error: toastError } = useToast();
  const [loading, setLoading] = useState(false);
  const form = useForm({ resolver: zodResolver(schema), defaultValues: { email: "", password: "" } });

  const onSubmit = async (values: z.infer<typeof schema>) => {
    setLoading(true);
    try {
      const resp = await api.post("/api/v1/auth/login", values);
      const { access_token } = resp.data.data;
      const me = await api.get("/api/v1/auth/me", { headers: { Authorization: `Bearer ${access_token}` } });
      setAuth(me.data.data, access_token);
      router.push("/dashboard");
    } catch (err: any) {
      toastError(err.response?.data?.error?.message || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      <div className="hidden lg:flex lg:w-1/2 bg-zinc-900 dark:bg-zinc-950 items-center justify-center p-12">
        <div className="max-w-md text-white">
          <div className="w-12 h-12 rounded-xl bg-zinc-800 flex items-center justify-center mb-6">
            <span className="text-xl font-bold">V</span>
          </div>
          <h1 className="text-3xl font-bold mb-4">Welcome back to VisionAI</h1>
          <p className="text-zinc-400">Real-time object detection powered by state-of-the-art computer vision models.</p>
        </div>
      </div>
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-sm">
          <h2 className="text-2xl font-bold mb-1">Sign in</h2>
          <p className="text-sm text-zinc-500 mb-8">Enter your credentials to access your account</p>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-1 block">Email</label>
              <Input type="email" placeholder="you@example.com" {...form.register("email")} />
              {form.formState.errors.email && <p className="text-xs text-red-500 mt-1">{form.formState.errors.email.message}</p>}
            </div>
            <div>
              <label className="text-sm font-medium mb-1 block">Password</label>
              <Input type="password" placeholder="••••••" {...form.register("password")} />
              {form.formState.errors.password && <p className="text-xs text-red-500 mt-1">{form.formState.errors.password.message}</p>}
            </div>
            <Button type="submit" className="w-full" loading={loading}>Sign In</Button>
          </form>
          <p className="text-sm text-center mt-6 text-zinc-500">
            Don&apos;t have an account?{" "}
            <Link href="/register" className="text-zinc-900 dark:text-zinc-100 font-medium hover:underline">Sign up</Link>
          </p>
        </div>
      </div>
    </div>
  );
}