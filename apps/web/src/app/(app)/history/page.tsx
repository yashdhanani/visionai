"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Eye, ChevronLeft, ChevronRight } from "lucide-react";

export default function HistoryPage() {
  const [page, setPage] = useState(1);
  const [sourceType, setSourceType] = useState("");
  const [status, setStatus] = useState("");
  const pageSize = 20;

  const { data, isLoading } = useQuery({
    queryKey: ["detections", page, sourceType, status],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
      if (sourceType) params.set("source_type", sourceType);
      if (status) params.set("status", status);
      return api.get(`/api/v1/detections?${params}`).then((r) => r.data.data);
    },
  });

  const statusVariant = (s: string) => {
    if (s === "completed") return "success" as const;
    if (s === "failed") return "destructive" as const;
    if (s === "processing") return "warning" as const;
    return "secondary" as const;
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Detection History</h1>
        <p className="text-sm text-zinc-500 mt-1">Browse and filter all past detections</p>
      </div>

      <Card>
        <CardContent className="p-4">
          <div className="flex gap-3 items-center">
            <Select value={sourceType} onChange={(e) => { setSourceType(e.target.value); setPage(1); }}>
              <option value="">All Sources</option>
              <option value="image">Image</option>
              <option value="video">Video</option>
              <option value="webcam">Webcam</option>
            </Select>
            <Select value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }}>
              <option value="">All Status</option>
              <option value="completed">Completed</option>
              <option value="processing">Processing</option>
              <option value="failed">Failed</option>
            </Select>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-4 space-y-3">{Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-14" />)}</div>
          ) : !data?.items?.length ? (
            <div className="p-12 text-center text-zinc-500">
              <Eye className="h-12 w-12 mx-auto mb-3 opacity-30" />
              <p className="text-sm">No detections yet. Run your first detection to see history here.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-zinc-500 bg-zinc-50 dark:bg-zinc-800/50">
                    <th className="px-4 py-3 font-medium">Timestamp</th>
                    <th className="px-4 py-3 font-medium">Source</th>
                    <th className="px-4 py-3 font-medium">Objects</th>
                    <th className="px-4 py-3 font-medium">Confidence</th>
                    <th className="px-4 py-3 font-medium">Processing</th>
                    <th className="px-4 py-3 font-medium">FPS</th>
                    <th className="px-4 py-3 font-medium">Status</th>
                    <th className="px-4 py-3 font-medium"></th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((det: any) => (
                    <tr key={det.id} className="border-b last:border-0 hover:bg-zinc-50 dark:hover:bg-zinc-800/50">
                      <td className="px-4 py-3 font-mono text-xs">{new Date(det.created_at).toLocaleString()}</td>
                      <td className="px-4 py-3"><Badge variant="outline">{det.source_type}</Badge></td>
                      <td className="px-4 py-3 font-mono">{det.object_count}</td>
                      <td className="px-4 py-3 font-mono">{det.avg_confidence ? `${(det.avg_confidence * 100).toFixed(1)}%` : "—"}</td>
                      <td className="px-4 py-3 font-mono">{det.processing_time_ms?.toFixed(0) || "—"}ms</td>
                      <td className="px-4 py-3 font-mono">{det.fps?.toFixed(1) || "—"}</td>
                      <td className="px-4 py-3"><Badge variant={statusVariant(det.status)}>{det.status}</Badge></td>
                      <td className="px-4 py-3">
                        <Link href={`/history/${det.id}`}>
                          <Button variant="ghost" size="sm">View</Button>
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {data && data.pages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-zinc-500">
            Page {data.page} of {data.pages} ({data.total} total)
          </p>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>
              <ChevronLeft className="h-4 w-4" /> Previous
            </Button>
            <Button variant="outline" size="sm" disabled={page >= data.pages} onClick={() => setPage(page + 1)}>
              Next <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}