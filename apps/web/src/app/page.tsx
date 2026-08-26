"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Camera, ArrowRight, Zap, Shield, Globe, BarChart3, Eye, Boxes } from "lucide-react";
import { motion } from "framer-motion";
import { useEffect, useState } from "react";

const features = [
  { icon: Eye, title: "Real-Time Detection", desc: "Stream camera feed with sub-50ms inference latency via WebSocket." },
  { icon: Boxes, title: "Object Counting", desc: "Automatic object counting and persistent track IDs across frames." },
  { icon: BarChart3, title: "Analytics Dashboard", desc: "Class distribution, confidence trends, FPS monitoring, and more." },
  { icon: Zap, title: "YOLO Inference", desc: "Production-optimized YOLO models with GPU acceleration." },
  { icon: Shield, title: "Enterprise Security", desc: "JWT auth, API keys, rate limiting, role-based access control." },
  { icon: Globe, title: "REST + WebSocket API", desc: "Full API access with OpenAPI docs for custom integrations." },
];

const stats = [
  { value: "50+", label: "FPS Inference" },
  { value: "80+", label: "COCO Classes" },
  { value: "<50ms", label: "Latency" },
  { value: "99.9%", label: "Uptime" },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white dark:bg-zinc-950" suppressHydrationWarning>
      {/* Nav */}
      <nav className="flex items-center justify-between px-6 lg:px-12 h-16 border-b border-zinc-100 dark:border-zinc-800">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-zinc-900 dark:bg-zinc-100 flex items-center justify-center">
            <span className="text-white dark:text-zinc-900 text-sm font-bold">V</span>
          </div>
          <span className="text-xl font-bold">VisionAI</span>
        </div>
        <div className="flex items-center gap-3">
          <a
            href="https://buymeacoffee.com/dhananiyash"
            target="_blank"
            rel="noopener noreferrer"
            className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-[#FFDD00] text-black hover:bg-[#ffea4d] transition-colors shadow-sm"
          >
            <span>☕</span>
            <span>Buy me a coffee</span>
          </a>
          <Link href="/login">
            <Button variant="ghost" size="sm">Log In</Button>
          </Link>
          <Link href="/register">
            <Button size="sm">Get Started <ArrowRight className="h-4 w-4" /></Button>
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="max-w-6xl mx-auto px-6 lg:px-12 py-24 lg:py-32">
          <div className="max-w-3xl">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-100 dark:bg-zinc-800 text-sm text-zinc-600 dark:text-zinc-400 mb-6">
                <Camera className="h-3.5 w-3.5" />
                Real-Time Vision Intelligence
              </div>
              <h1 className="text-4xl lg:text-6xl font-bold tracking-tight leading-tight mb-6">
                Detect, classify, count, and analyze objects{" "}
                <span className="text-zinc-500">in real time</span>
              </h1>
              <p className="text-lg lg:text-xl text-zinc-600 dark:text-zinc-400 mb-8 max-w-2xl">
                Production-grade computer vision platform powered by YOLO. Upload images, stream video, or connect your camera — get instant detection results with bounding boxes, confidence scores, and analytics.
              </p>
              <div className="flex items-center gap-4">
                <Link href="/detect">
                  <Button size="lg" className="text-base">
                    Start Detecting <ArrowRight className="h-5 w-5" />
                  </Button>
                </Link>
                <Link href="/api-docs">
                  <Button variant="outline" size="lg" className="text-base">
                    View Documentation
                  </Button>
                </Link>
              </div>
            </motion.div>
          </div>

          {/* Hero Visual - High-Tech Animated Vision Detection Canvas */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="mt-16 relative"
          >
            <div className="relative rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-zinc-950 p-2 shadow-2xl overflow-hidden ring-1 ring-white/10">
              <div className="rounded-xl aspect-video relative overflow-hidden bg-zinc-900">
                {/* Real-world high-resolution detection scene background */}
                <img
                  src="https://images.unsplash.com/photo-1519501025264-65ba15a82390?auto=format&fit=crop&w=1600&q=80"
                  alt="City Traffic and Pedestrian Detection Scene"
                  className="w-full h-full object-cover brightness-[0.7] contrast-[1.1] saturate-[1.2]"
                />

                {/* Cyberpunk / High-tech Scanlines & Grid Overlay */}
                <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_30%,rgba(0,0,0,0.6)_100%)] pointer-events-none" />
                <div className="absolute inset-0 bg-emerald-500/[0.03] pointer-events-none" />

                {/* Camera HUD Header */}
                <div className="absolute top-4 left-4 right-4 flex items-center justify-between pointer-events-none text-[11px] font-mono font-semibold text-emerald-400">
                  <div className="flex items-center gap-2 bg-black/60 backdrop-blur-md px-3 py-1 rounded-lg border border-emerald-500/30">
                    <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
                    <span className="text-white">LIVE STREAM</span>
                    <span className="text-zinc-400">|</span>
                    <span>CAM-04 [HD 1080P]</span>
                  </div>
                  <div className="flex items-center gap-3 bg-black/60 backdrop-blur-md px-3 py-1 rounded-lg border border-emerald-500/30">
                    <span className="text-emerald-400">FPS: 58.2</span>
                    <span className="text-zinc-400">|</span>
                    <span className="text-cyan-400">YOLOv8x GPU</span>
                    <span className="text-zinc-400">|</span>
                    <span className="text-amber-400">LATENCY: 18ms</span>
                  </div>
                </div>

                {/* Animated Laser Scanning Line */}
                <motion.div
                  animate={{ y: ["0%", "100%", "0%"] }}
                  transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
                  className="absolute left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-emerald-400 to-transparent shadow-[0_0_15px_#10b981] opacity-70 pointer-events-none"
                />

                {/* Bounding Boxes with Glow & Corner Markers */}
                {[
                  { label: "Person", conf: "98.4%", id: "#041", x: "22%", y: "38%", w: "14%", h: "48%", color: "emerald", delay: 0 },
                  { label: "Car", conf: "96.1%", id: "#118", x: "42%", y: "45%", w: "32%", h: "38%", color: "cyan", delay: 0.2 },
                  { label: "Backpack", conf: "91.8%", id: "#089", x: "16%", y: "52%", w: "8%", h: "22%", color: "amber", delay: 0.4 },
                  { label: "Traffic Light", conf: "94.5%", id: "#022", x: "78%", y: "18%", w: "6%", h: "26%", color: "emerald", delay: 0.6 },
                ].map((box, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.4, delay: 0.6 + box.delay }}
                    className={`absolute rounded border-2 shadow-lg ${
                      box.color === "cyan" 
                        ? "border-cyan-400 shadow-cyan-500/20 bg-cyan-400/10" 
                        : box.color === "amber" 
                        ? "border-amber-400 shadow-amber-500/20 bg-amber-400/10" 
                        : "border-emerald-400 shadow-emerald-500/20 bg-emerald-400/10"
                    }`}
                    style={{ left: box.x, top: box.y, width: box.w, height: box.h }}
                  >
                    {/* Corner Reticles */}
                    <span className="absolute -top-1 -left-1 w-2 h-2 border-t-2 border-l-2 border-white" />
                    <span className="absolute -top-1 -right-1 w-2 h-2 border-t-2 border-r-2 border-white" />
                    <span className="absolute -bottom-1 -left-1 w-2 h-2 border-b-2 border-l-2 border-white" />
                    <span className="absolute -bottom-1 -right-1 w-2 h-2 border-b-2 border-r-2 border-white" />

                    {/* Detection Badge */}
                    <div className={`absolute -top-5 left-0 text-[10px] font-mono font-bold px-1.5 py-0.5 rounded shadow-sm text-black flex items-center gap-1 ${
                      box.color === "cyan" ? "bg-cyan-400" : box.color === "amber" ? "bg-amber-400" : "bg-emerald-400"
                    }`}>
                      <span>{box.label}</span>
                      <span className="opacity-80 font-normal">{box.conf}</span>
                      <span className="text-[8px] opacity-60">[{box.id}]</span>
                    </div>
                  </motion.div>
                ))}

                {/* Bottom HUD Metadata */}
                <div className="absolute bottom-3 left-4 right-4 flex items-center justify-between pointer-events-none text-[10px] font-mono text-zinc-400 bg-black/60 backdrop-blur-md px-3 py-1.5 rounded-lg border border-white/10">
                  <div className="flex items-center gap-4">
                    <span className="text-emerald-400 font-bold">DETECTED OBJECTS: 4</span>
                    <span>TRACKING: ACTIVE</span>
                    <span>COORDINATES: [37.7749° N, 122.4194° W]</span>
                  </div>
                  <div className="text-zinc-500">
                    ENGINE: TENSORRT-YOLO8
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Stats */}
      <section className="border-y border-zinc-100 dark:border-zinc-800">
        <div className="max-w-6xl mx-auto px-6 lg:px-12 py-12 grid grid-cols-2 lg:grid-cols-4 gap-8">
          {stats.map((s, i) => (
            <div key={i} className="text-center">
              <p className="text-3xl font-bold">{s.value}</p>
              <p className="text-sm text-zinc-500 mt-1">{s.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="max-w-6xl mx-auto px-6 lg:px-12 py-24">
        <h2 className="text-3xl font-bold text-center mb-12">Everything you need for production computer vision</h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((f, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: i * 0.1 }}
              viewport={{ once: true }}
              className="p-6 rounded-xl border border-zinc-200 dark:border-zinc-800 hover:border-zinc-300 dark:hover:border-zinc-700 transition-colors"
            >
              <f.icon className="h-8 w-8 mb-4 text-zinc-700 dark:text-zinc-300" />
              <h3 className="text-lg font-semibold mb-2">{f.title}</h3>
              <p className="text-sm text-zinc-600 dark:text-zinc-400">{f.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-zinc-100 dark:border-zinc-800">
        <div className="max-w-6xl mx-auto px-6 lg:px-12 py-24 text-center">
          <h2 className="text-3xl font-bold mb-4">Ready to start detecting?</h2>
          <p className="text-zinc-600 dark:text-zinc-400 mb-8 max-w-lg mx-auto">
            Set up VisionAI in minutes. No credit card required.
          </p>
          <Link href="/register">
            <Button size="lg" className="text-base">
              Create Free Account <ArrowRight className="h-5 w-5" />
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-zinc-100 dark:border-zinc-800 py-8">
        <div className="max-w-6xl mx-auto px-6 lg:px-12 flex items-center justify-between text-sm text-zinc-500">
          <p>&copy; 2026 VisionAI. All rights reserved.</p>
          <div className="flex gap-4">
            <Link href="/login" className="hover:text-zinc-900 dark:hover:text-zinc-100">Login</Link>
            <Link href="/api-docs" className="hover:text-zinc-900 dark:hover:text-zinc-100">API Docs</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}