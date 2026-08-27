"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { BarChart3, Boxes, Clock, Cpu, Eye, Zap, Camera, Image as ImageIcon, Film, Crosshair, ArrowRight } from "lucide-react";
import { LineChart, Line, PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { useEffect, useState } from "react";
import { useTheme } from "next-themes";

const COLORS = ["#10b981", "#3b82f6", "#f59e0b", "#8b5cf6", "#06b6d4", "#ec4899"];
const DARK_COLORS = ["#34d399", "#60a5fa", "#fbbf24", "#a78bfa", "#22d3ee", "#f472b6"];

interface KPI { label: string; value: string | number; icon: any; iconColor: string; bg: string; }

function KPICard({ kpi, loading }: { kpi: KPI; loading: boolean }) {
  return (
    <Card className="hover:border-zinc-700 transition-all">
      <CardContent className="p-5">
        <div className="flex items-center gap-4">
          <div className={`w-11 h-11 rounded-xl flex items-center justify-center ${kpi.bg}`}>
            <kpi.icon className={`h-5 w-5 ${kpi.iconColor}`} />
          </div>
          <div>
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">{kpi.label}</p>
            {loading ? <Skeleton className="h-6 w-16 mt-1" /> : <p className="text-2xl font-extrabold text-foreground">{kpi.value}</p>}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const [days, setDays] = useState(30);
  const { resolvedTheme } = useTheme();
  const isDark = resolvedTheme === "dark";
  const chartColors = isDark ? DARK_COLORS : COLORS;
  const gridColor = isDark ? "#27272a" : "#e4e4e7";
  const lineColor1 = "#10b981";
  const lineColor2 = "#3b82f6";
  const barFill = "#10b981";

  const { data: summary, isLoading: loadingSummary } = useQuery({
    queryKey: ["analytics", "summary", days],
    queryFn: () => api.get(`/api/v1/analytics/summary?days=${days}`).then((r) => r.data.data),
  });

  const { data: timeseries = [], isLoading: loadingTS } = useQuery({
    queryKey: ["analytics", "timeseries", days],
    queryFn: () => api.get(`/api/v1/analytics/timeseries?days=${days}`).then((r) => r.data.data),
  });

  const { data: classDist = [] } = useQuery({
    queryKey: ["analytics", "classes", days],
    queryFn: () => api.get(`/api/v1/analytics/classes?days=${days}&limit=10`).then((r) => r.data.data),
  });

  const { data: performance = [] } = useQuery({
    queryKey: ["analytics", "performance", days],
    queryFn: () => api.get(`/api/v1/analytics/performance?days=${days}`).then((r) => r.data.data),
  });

  const { data: hourly = [] } = useQuery({
    queryKey: ["analytics", "hourly", days],
    queryFn: () => api.get(`/api/v1/analytics/hourly?days=7`).then((r) => r.data.data),
  });

  const kpis: KPI[] = [
    { label: "Total Detections", value: summary?.total_detections?.toLocaleString() ?? "0", icon: Eye, iconColor: "text-emerald-400", bg: "bg-emerald-500/10 border border-emerald-500/20" },
    { label: "Objects Detected", value: summary?.total_objects?.toLocaleString() ?? "0", icon: Boxes, iconColor: "text-blue-400", bg: "bg-blue-500/10 border border-blue-500/20" },
    { label: "Avg FPS", value: summary?.avg_fps ? summary.avg_fps.toFixed(1) : "—", icon: Zap, iconColor: "text-purple-400", bg: "bg-purple-500/10 border border-purple-500/20" },
    { label: "Avg Confidence", value: summary?.avg_confidence ? `${(summary.avg_confidence * 100).toFixed(1)}%` : "—", icon: BarChart3, iconColor: "text-amber-400", bg: "bg-amber-500/10 border border-amber-500/20" },
    { label: "Avg Latency", value: summary?.avg_latency_ms ? `${summary.avg_latency_ms.toFixed(0)}ms` : "—", icon: Clock, iconColor: "text-cyan-400", bg: "bg-cyan-500/10 border border-cyan-500/20" },
    { label: "Active Sessions", value: summary?.active_sessions ?? 0, icon: Cpu, iconColor: "text-rose-400", bg: "bg-rose-500/10 border border-rose-500/20" },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">VisionAI Dashboard</h1>
          <p className="text-sm text-zinc-500 mt-1">Real-time computer vision inference and telemetry metrics</p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="h-9 rounded-lg border border-border px-3 text-sm bg-card text-foreground"
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </select>
        </div>
      </div>

      {/* Quick Launch Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <Link href="/live" className="p-4 rounded-xl border border-border bg-card hover:bg-accent hover:border-emerald-500/50 transition-all flex items-center justify-between group">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
              <Camera className="w-4 h-4" />
            </div>
            <div>
              <div className="text-sm font-bold group-hover:text-emerald-400 transition-colors">Live Webcam</div>
              <div className="text-xs text-muted-foreground">30 FPS Stream</div>
            </div>
          </div>
          <ArrowRight className="w-4 h-4 text-muted-foreground group-hover:text-emerald-400 group-hover:translate-x-0.5 transition-all" />
        </Link>

        <Link href="/detect" className="p-4 rounded-xl border border-border bg-card hover:bg-accent hover:border-blue-500/50 transition-all flex items-center justify-between group">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
              <Crosshair className="w-4 h-4" />
            </div>
            <div>
              <div className="text-sm font-bold group-hover:text-blue-400 transition-colors">Choose Category</div>
              <div className="text-xs text-muted-foreground">14 Perception Tasks</div>
            </div>
          </div>
          <ArrowRight className="w-4 h-4 text-muted-foreground group-hover:text-blue-400 group-hover:translate-x-0.5 transition-all" />
        </Link>

        <Link href="/image" className="p-4 rounded-xl border border-border bg-card hover:bg-accent hover:border-amber-500/50 transition-all flex items-center justify-between group">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
              <ImageIcon className="w-4 h-4" />
            </div>
            <div>
              <div className="text-sm font-bold group-hover:text-amber-400 transition-colors">Image Detect</div>
              <div className="text-xs text-muted-foreground">Upload & Annotate</div>
            </div>
          </div>
          <ArrowRight className="w-4 h-4 text-muted-foreground group-hover:text-amber-400 group-hover:translate-x-0.5 transition-all" />
        </Link>

        <Link href="/video" className="p-4 rounded-xl border border-border bg-card hover:bg-accent hover:border-purple-500/50 transition-all flex items-center justify-between group">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400">
              <Film className="w-4 h-4" />
            </div>
            <div>
              <div className="text-sm font-bold group-hover:text-purple-400 transition-colors">Video Detect</div>
              <div className="text-xs text-muted-foreground">Batch & Tracking</div>
            </div>
          </div>
          <ArrowRight className="w-4 h-4 text-muted-foreground group-hover:text-purple-400 group-hover:translate-x-0.5 transition-all" />
        </Link>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {kpis.map((kpi, i) => <KPICard key={i} kpi={kpi} loading={loadingSummary} />)}
      </div>

      {/* Charts Row 1 */}
      <div className="grid lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader><CardTitle>Detection Activity</CardTitle></CardHeader>
          <CardContent>
            {loadingTS ? <Skeleton className="h-64" /> : (
              <ResponsiveContainer width="100%" height={280}>
                <LineChart data={timeseries}>
                  <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={(v) => new Date(v).toLocaleDateString("en", { month: "short", day: "numeric" })} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Line type="monotone" dataKey="detections" stroke={lineColor1} strokeWidth={2} dot={false} name="Detections" />
                  <Line type="monotone" dataKey="objects" stroke={lineColor2} strokeWidth={2} dot={false} name="Objects" />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Object Distribution</CardTitle></CardHeader>
          <CardContent>
            {classDist.length === 0 ? (
              <div className="h-64 flex items-center justify-center text-sm text-zinc-500">
                No detection data yet. Run your first detection to see analytics.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie data={classDist} dataKey="count" nameKey="class_name" cx="50%" cy="50%" outerRadius={100} label={({ name, percent }: any) => `${name} ${(percent * 100).toFixed(0)}%`}>
                    {classDist.map((_: any, i: number) => <Cell key={i} fill={chartColors[i % chartColors.length]} />)}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Charts Row 2 */}
      <div className="grid lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader><CardTitle>Top Detected Classes</CardTitle></CardHeader>
          <CardContent>
            {classDist.length === 0 ? (
              <div className="h-64 flex items-center justify-center text-sm text-zinc-500">No data available</div>
            ) : (
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={classDist} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                  <XAxis type="number" tick={{ fontSize: 11 }} />
                  <YAxis type="category" dataKey="class_name" tick={{ fontSize: 11 }} width={80} />
                  <Tooltip />
                  <Bar dataKey="count" fill={barFill} radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>FPS & Latency Trend</CardTitle></CardHeader>
          <CardContent>
            {performance.length === 0 ? (
              <div className="h-64 flex items-center justify-center text-sm text-zinc-500">No performance data yet</div>
            ) : (
              <ResponsiveContainer width="100%" height={280}>
                <LineChart data={performance}>
                  <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={(v) => new Date(v).toLocaleDateString("en", { month: "short", day: "numeric" })} />
                  <YAxis yAxisId="left" tick={{ fontSize: 11 }} />
                  <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Line yAxisId="left" type="monotone" dataKey="avg_fps" stroke={lineColor1} strokeWidth={2} dot={false} name="FPS" />
                  <Line yAxisId="right" type="monotone" dataKey="avg_latency_ms" stroke={lineColor2} strokeWidth={2} dot={false} name="Latency (ms)" />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Hourly Activity */}
      <Card>
        <CardHeader><CardTitle>Hourly Detection Activity</CardTitle></CardHeader>
        <CardContent>
          {hourly.length === 0 ? (
            <div className="h-48 flex items-center justify-center text-sm text-zinc-500">No activity data yet</div>
          ) : (
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={hourly}>
                  <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                  <XAxis dataKey="hour" tick={{ fontSize: 11 }} tickFormatter={(v) => `${v}:00`} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="detections" fill={barFill} radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
          )}
        </CardContent>
      </Card>
    </div>
  );
}