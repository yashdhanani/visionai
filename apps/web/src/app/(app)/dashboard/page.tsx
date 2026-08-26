"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { BarChart3, Boxes, Clock, Cpu, Eye, Zap } from "lucide-react";
import { LineChart, Line, PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { useEffect, useState } from "react";
import { useTheme } from "next-themes";

const COLORS = ["#18181b", "#3f3f46", "#71717a", "#a1a1aa", "#d4d4d8", "#e4e4e7"];
const DARK_COLORS = ["#fafafa", "#d4d4d8", "#a1a1aa", "#71717a", "#3f3f46", "#27272a"];

interface KPI { label: string; value: string | number; icon: any; color: string; }

function KPICard({ kpi, loading }: { kpi: KPI; loading: boolean }) {
  return (
    <Card>
      <CardContent className="p-5">
        <div className="flex items-center gap-4">
          <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${kpi.color}`}>
            <kpi.icon className="h-5 w-5 text-white" />
          </div>
          <div>
            <p className="text-sm text-muted-foreground">{kpi.label}</p>
            {loading ? <Skeleton className="h-6 w-16 mt-1" /> : <p className="text-2xl font-bold text-foreground">{kpi.value}</p>}
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
  const lineColor1 = isDark ? "#fafafa" : "#18181b";
  const lineColor2 = isDark ? "#a1a1aa" : "#71717a";
  const barFill = isDark ? "#fafafa" : "#18181b";

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
    { label: "Total Detections", value: summary?.total_detections?.toLocaleString() ?? "0", icon: Eye, color: "bg-zinc-900 dark:bg-zinc-100" },
    { label: "Objects Detected", value: summary?.total_objects?.toLocaleString() ?? "0", icon: Boxes, color: "bg-zinc-700" },
    { label: "Avg FPS", value: summary?.avg_fps?.toFixed(1) ?? "—", icon: Zap, color: "bg-emerald-600" },
    { label: "Avg Confidence", value: summary?.avg_confidence ? `${(summary.avg_confidence * 100).toFixed(1)}%` : "—", icon: BarChart3, color: "bg-amber-600" },
    { label: "Avg Latency", value: summary?.avg_latency_ms ? `${summary.avg_latency_ms.toFixed(0)}ms` : "—", icon: Clock, color: "bg-sky-600" },
    { label: "Active Sessions", value: summary?.active_sessions ?? 0, icon: Cpu, color: "bg-violet-600" },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-sm text-zinc-500 mt-1">Real-time detection analytics overview</p>
        </div>
        <select
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          className="h-9 rounded-lg border border-border px-3 text-sm bg-transparent text-foreground"
        >
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
        </select>
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