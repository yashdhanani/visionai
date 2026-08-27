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
import { Eye, EyeOff, Sparkles, Video, ArrowRight } from "lucide-react";

const schema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  email: z.string().email("Please enter a valid email address"),
  password: z.string().min(8, "Password must be at least 8 characters"),
});

export default function RegisterPage() {
  const router = useRouter();
  const { setAuth } = useAuthStore();
  const { error: toastError, success: toastSuccess } = useToast();
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const form = useForm({
    resolver: zodResolver(schema),
    defaultValues: { name: "", email: "", password: "" },
  });

  const onSubmit = async (values: z.infer<typeof schema>) => {
    setLoading(true);
    try {
      const resp = await api.post("/api/v1/auth/register", values);
      const { access_token } = resp.data.data;
      const me = await api.get("/api/v1/auth/me", {
        headers: { Authorization: `Bearer ${access_token}` },
      });
      setAuth(me.data.data, access_token);
      toastSuccess("Account created successfully!");
      router.push("/dashboard");
    } catch (err: any) {
      toastError(err.response?.data?.error?.message || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex bg-zinc-950 text-zinc-100 antialiased selection:bg-emerald-500 selection:text-black">
      {/* Left Feature Panel (Desktop) */}
      <div className="hidden lg:flex lg:w-1/2 flex-col justify-between p-12 bg-gradient-to-br from-zinc-900 via-zinc-950 to-black border-r border-zinc-800/80 relative overflow-hidden">
        {/* Glow Accents */}
        <div className="absolute -top-32 -left-32 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-32 -right-32 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

        {/* Top Logo */}
        <div className="flex items-center gap-3 relative z-10">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-400 to-emerald-600 flex items-center justify-center shadow-lg shadow-emerald-500/20">
            <span className="text-xl font-black text-black">V</span>
          </div>
          <div>
            <span className="font-bold text-lg tracking-tight text-white">VisionAI</span>
            <span className="block text-[11px] text-zinc-400 font-mono">NEURAL INFERENCE PLATFORM</span>
          </div>
        </div>

        {/* Hero Message */}
        <div className="max-w-md my-auto relative z-10 space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-400 font-medium">
            <Sparkles className="w-3.5 h-3.5" />
            Instant Developer Access
          </div>

          <h1 className="text-4xl font-extrabold tracking-tight text-white leading-tight">
            Deploy real-time computer vision in <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">minutes</span>.
          </h1>

          <p className="text-zinc-400 text-sm leading-relaxed">
            Create your developer account to access real-time inference APIs, custom model registries, batch processing, and live video analytics pipelines.
          </p>

          <div className="grid grid-cols-3 gap-3 pt-2">
            <div className="p-3 rounded-xl bg-zinc-900/80 border border-zinc-800 backdrop-blur-sm">
              <div className="text-xl font-bold text-emerald-400 font-mono">5 Models</div>
              <div className="text-[11px] text-zinc-400 mt-0.5">Pre-Trained Ready</div>
            </div>
            <div className="p-3 rounded-xl bg-zinc-900/80 border border-zinc-800 backdrop-blur-sm">
              <div className="text-xl font-bold text-cyan-400 font-mono">REST + WS</div>
              <div className="text-[11px] text-zinc-400 mt-0.5">Streaming API</div>
            </div>
            <div className="p-3 rounded-xl bg-zinc-900/80 border border-zinc-800 backdrop-blur-sm">
              <div className="text-xl font-bold text-amber-400 font-mono">Zero Setup</div>
              <div className="text-[11px] text-zinc-400 mt-0.5">Instant Inference</div>
            </div>
          </div>
        </div>

        {/* Bottom Status */}
        <div className="flex items-center justify-between text-xs text-zinc-400 border-t border-zinc-800/60 pt-6 relative z-10">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>Registration Open</span>
          </div>
          <span className="font-mono text-[11px]">v1.0.0</span>
        </div>
      </div>

      {/* Right Form Panel */}
      <div className="flex-1 flex flex-col justify-center items-center p-6 sm:p-12 bg-zinc-950 relative">
        <div className="w-full max-w-md space-y-6">
          {/* Mobile Logo Header */}
          <div className="lg:hidden flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-400 to-emerald-600 flex items-center justify-center shadow-lg shadow-emerald-500/20">
              <span className="text-xl font-black text-black">V</span>
            </div>
            <div>
              <span className="font-bold text-lg tracking-tight text-white">VisionAI</span>
              <span className="block text-[11px] text-zinc-400 font-mono">NEURAL VISION</span>
            </div>
          </div>

          <div>
            <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">Create an account</h2>
            <p className="text-sm text-zinc-400 mt-1.5">
              Get started with VisionAI developer workspace in seconds.
            </p>
          </div>

          {/* Form */}
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-zinc-300 uppercase tracking-wider">Full Name</label>
              <Input
                placeholder="Yash Dhanani"
                className="h-11 bg-zinc-900 border-zinc-800 text-white placeholder:text-zinc-500 focus-visible:ring-emerald-500 focus-visible:border-emerald-500"
                {...form.register("name")}
              />
              {form.formState.errors.name && (
                <p className="text-xs text-rose-400 mt-1 font-medium">{form.formState.errors.name.message}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-zinc-300 uppercase tracking-wider">Email Address</label>
              <Input
                type="email"
                placeholder="developer@visionai.io"
                className="h-11 bg-zinc-900 border-zinc-800 text-white placeholder:text-zinc-500 focus-visible:ring-emerald-500 focus-visible:border-emerald-500"
                {...form.register("email")}
              />
              {form.formState.errors.email && (
                <p className="text-xs text-rose-400 mt-1 font-medium">{form.formState.errors.email.message}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-zinc-300 uppercase tracking-wider">Password</label>
              <div className="relative">
                <Input
                  type={showPassword ? "text" : "password"}
                  placeholder="Min 8 characters"
                  className="h-11 bg-zinc-900 border-zinc-800 text-white placeholder:text-zinc-500 focus-visible:ring-emerald-500 focus-visible:border-emerald-500 pr-10"
                  {...form.register("password")}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-200 transition-colors"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {form.formState.errors.password && (
                <p className="text-xs text-rose-400 mt-1 font-medium">{form.formState.errors.password.message}</p>
              )}
            </div>

            <Button
              type="submit"
              className="w-full h-11 bg-emerald-500 hover:bg-emerald-400 text-black font-bold tracking-wide transition-all shadow-lg shadow-emerald-500/20"
              loading={loading}
            >
              Create Developer Account
            </Button>
          </form>

          {/* Links */}
          <div className="space-y-3 pt-2 text-center">
            <p className="text-sm text-zinc-400">
              Already have an account?{" "}
              <Link href="/login" className="text-emerald-400 font-semibold hover:underline">
                Sign in
              </Link>
            </p>

            <div>
              <Link
                href="/live"
                className="inline-flex items-center gap-1.5 text-xs text-zinc-400 hover:text-zinc-200 font-mono transition-colors"
              >
                <Video className="w-3.5 h-3.5 text-emerald-400" /> Skip registration & open Live Webcam <ArrowRight className="w-3 h-3" />
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}