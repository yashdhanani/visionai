"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { LineChart, Line, PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

const COLORS = ["#18181b", "#3f3f46", "#71717a", "#a1a1aa", "#d4d4d8", "#e4e4e7", "#52525b", "#a1a1aa"];

export default function AnalyticsPage() {
  const [days, setDays] = useState(30);

  const { data: summary, isLoading: loadingSummary } = useQuery({
    queryKey: ["analytics", "summary", days],
    queryFn: () => api.get(`/api/v1/analytics/summary?days=${days}`).then((r) => r.data.data),
  });

  const { data: timeseries = [] } = useQuery({
    queryKey: ["analytics", "timeseries", days],
    queryFn: () => api.get(`/api/v1/analytics/timeseries?days=${days}`).then((r) => r.data.data),
  });

  const { data: classDist = [] } = useQuery({
    queryKey: ["analytics", "classes", days],
    queryFn: () => api.get(`/api/v1/analytics/classes?days=${days}&limit=15`).then((r) => r.data.data),
  });

  const { data: confidence = [] } = useQuery({
    queryKey: ["analytics", "confidence", days],
    queryFn: () => api.get(`/api/v1/analytics/confidence?days=${days}`).then((r) => r.data.data),
  });

  const { data: performance = [] } = useQuery({
    queryKey: ["analytics", "performance", days],
    queryFn: () => api.get(`/api/v1/analytics/performance?days=${days}`).then((r) => r.data.data),
  });

  const { data: hourly = [] } = useQuery({
    queryKey: ["analytics", "hourly", days],
    queryFn: () => api.get(`/api/v1/analytics/hourly?days=7`).then((r) => r.data.data),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Analytics</h1>
          <p className="text-sm text-zinc-500 mt-1">Comprehensive detection analytics and insights</p>
        </div>
        <select value={days} onChange={(e) => setDays(Number(e.target.value))} className="h-9 rounded-lg border border-zinc-200 dark:border-zinc-700 px-3 text-sm bg-transparent">
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
        </select>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-6 gap-4">
        {[
          { label: "Total Objects", value: summary?.total_objects?.toLocaleString() ?? "0" },
          { label: "Unique Classes", value: summary?.unique_classes ?? 0 },
          { label: "Avg Confidence", value: summary?.avg_confidence ? `${(summary.avg_confidence * 100).toFixed(1)}%` : "—" },
          { label: "Avg FPS", value: summary?.avg_fps?.toFixed(1) ?? "—" },
          { label: "Avg Latency", value: summary?.avg_latency_ms ? `${summary.avg_latency_ms.toFixed(0)}ms` : "—" },
          { label: "Total Detections", value: summary?.total_detections?.toLocaleString() ?? "0" },
        ].map((stat, i) => (
          <Card key={i}>
            <CardContent className="p-4">
              <p className="text-xs text-zinc-500">{stat.label}</p>
              <p className="text-xl font-bold mt-1">{loadingSummary ? <Skeleton className="h-5 w-12 inline-block" /> : stat.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader><CardTitle className="text-sm">Detection Volume Over Time</CardTitle></CardHeader>
          <CardContent>
            {timeseries.length === 0 ? (
              <div className="h-64 flex items-center justify-center text-sm text-zinc-500">No data available</div>
            ) : (
              <ResponsiveContainer width="100%" height={280}>
                <LineChart data={timeseries}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e4e4e7" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={(v) => new Date(v).toLocaleDateString("en", { month: "short", day: "numeric" })} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Line type="monotone" dataKey="detections" stroke="#18181b" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="objects" stroke="#71717a" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="text-sm">Class Distribution</CardTitle></CardHeader>
          <CardContent>
            {classDist.length === 0 ? (
              <div className="h-64 flex items-center justify-center text-sm text-zinc-500">No data available</div>
            ) : (
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie data={classDist} dataKey="count" nameKey="class_name" cx="50%" cy="50%" outerRadius={100} label={({ name, percent }: any) => `${name} ${(percent * 100).toFixed(0)}%`}>
                    {classDist.map((_: any, i: number) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="text-sm">Top Detected Classes</CardTitle></CardHeader>
          <CardContent>
            {classDist.length === 0 ? (
              <div className="h-64 flex items-center justify-center text-sm text-zinc-500">No data available</div>
            ) : (
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={classDist} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#e4e4e7" />
                  <XAxis type="number" tick={{ fontSize: 11 }} />
                  <YAxis type="category" dataKey="class_name" tick={{ fontSize: 11 }} width={80} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#18181b" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="text-sm">Confidence Distribution</CardTitle></CardHeader>
          <CardContent>
            {confidence.length === 0 ? (
              <div className="h-64 flex items-center justify-center text-sm text-zinc-500">No data available</div>
            ) : (
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={confidence}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e4e4e7" />
                  <XAxis dataKey="bin" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#3f3f46" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="text-sm">FPS & Latency Trend</CardTitle></CardHeader>
          <CardContent>
            {performance.length === 0 ? (
              <div className="h-64 flex items-center justify-center text-sm text-zinc-500">No data available</div>
            ) : (
              <ResponsiveContainer width="100%" height={280}>
                <LineChart data={performance}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e4e4e7" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={(v) => new Date(v).toLocaleDateString("en", { month: "short", day: "numeric" })} />
                  <YAxis yAxisId="left" tick={{ fontSize: 11 }} />
                  <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Line yAxisId="left" type="monotone" dataKey="avg_fps" stroke="#18181b" strokeWidth={2} dot={false} name="FPS" />
                  <Line yAxisId="right" type="monotone" dataKey="avg_latency_ms" stroke="#71717a" strokeWidth={2} dot={false} name="Latency (ms)" />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="text-sm">Hourly Activity</CardTitle></CardHeader>
          <CardContent>
            {hourly.length === 0 ? (
              <div className="h-64 flex items-center justify-center text-sm text-zinc-500">No data available</div>
            ) : (
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={hourly}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e4e4e7" />
                  <XAxis dataKey="hour" tick={{ fontSize: 11 }} tickFormatter={(v) => `${v}:00`} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="detections" fill="#18181b" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}