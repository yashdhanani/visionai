"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ArrowLeft, Download, Trash2 } from "lucide-react";
import { useEffect, useRef } from "react";

export default function DetectionDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imgRef = useRef<HTMLImageElement>(null);

  const { data: det, isLoading } = useQuery({
    queryKey: ["detection", id],
    queryFn: () => api.get(`/api/v1/detections/${id}`).then((r) => r.data.data),
    enabled: !!id,
  });

  const { data: assetUrl } = useQuery({
    queryKey: ["detection-asset", id],
    queryFn: async () => {
      const resp = await api.get(`/api/v1/detections/${id}/assets/annotated`, { responseType: "blob" });
      return URL.createObjectURL(new Blob([resp.data]));
    },
    enabled: !!id,
  });

  const drawBoxes = () => {
    const img = imgRef.current;
    const canvas = canvasRef.current;
    if (!img || !canvas || !det?.objects?.length) return;

    const displayW = img.clientWidth;
    const displayH = img.clientHeight;
    const dpr = window.devicePixelRatio || 1;
    canvas.width = displayW * dpr;
    canvas.height = displayH * dpr;
    canvas.style.width = `${displayW}px`;
    canvas.style.height = `${displayH}px`;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, displayW, displayH);

    const frameW = det.image_width || img.naturalWidth;
    const frameH = det.image_height || img.naturalHeight;
    const scaleX = displayW / frameW;
    const scaleY = displayH / frameH;

    const palette = ["#10b981", "#3b82f6", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899"];
    let ci = 0;
    const classColors: Record<string, string> = {};

    det.objects.forEach((obj: any) => {
      if (!classColors[obj.class_name]) {
        classColors[obj.class_name] = palette[ci % palette.length];
        ci++;
      }
      const color = classColors[obj.class_name];
      const x = (obj.x || obj.bbox?.x || 0) * scaleX;
      const y = (obj.y || obj.bbox?.y || 0) * scaleY;
      const w = (obj.width || obj.bbox?.width || 0) * scaleX;
      const h = (obj.height || obj.bbox?.height || 0) * scaleY;

      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.strokeRect(x, y, w, h);

      const label = `${obj.class_name} ${(obj.confidence * 100).toFixed(0)}%`;
      const fontSize = 12;
      ctx.font = `600 ${fontSize}px system-ui`;
      const tw = ctx.measureText(label).width;

      const padX = 6;
      const padY = 3;
      const labelH = fontSize + padY * 2;
      const labelY = y - labelH - 2;

      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.roundRect(x, labelY < 0 ? y : labelY, tw + padX * 2, labelH, 3);
      ctx.fill();
      ctx.fillStyle = "#fff";
      ctx.fillText(label, x + padX, (labelY < 0 ? y : labelY) + fontSize + padY - 1);
    });
  };

  const handleDelete = async () => {
    if (!confirm("Delete this detection?")) return;
    try {
      await api.delete(`/api/v1/detections/${id}`);
      router.push("/history");
    } catch {}
  };

  const handleDownloadJSON = () => {
    if (!det) return;
    const blob = new Blob([JSON.stringify(det, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.download = `detection-${id}.json`;
    a.href = url;
    a.click();
  };

  const handleDownloadCSV = () => {
    if (!det?.objects?.length) return;
    const header = "class_name,confidence,x,y,width,height,track_id\n";
    const rows = det.objects.map((o: any) => `${o.class_name},${o.confidence},${o.x},${o.y},${o.width},${o.height},${o.track_id ?? ""}`).join("\n");
    const blob = new Blob([header + rows], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.download = `detection-${id}.csv`;
    a.href = url;
    a.click();
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="grid lg:grid-cols-2 gap-6">
          <Skeleton className="aspect-video" />
          <Skeleton className="h-96" />
        </div>
      </div>
    );
  }

  if (!det) {
    return (
      <div className="text-center py-20 text-zinc-500">
        <p>Detection not found</p>
        <Button variant="link" onClick={() => router.push("/history")}>Back to History</Button>
      </div>
    );
  }

  const classCounts: Record<string, number> = {};
  det.objects?.forEach((o: any) => { classCounts[o.class_name] = (classCounts[o.class_name] || 0) + 1; });

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.back()}><ArrowLeft className="h-4 w-4" /></Button>
        <div>
          <h1 className="text-2xl font-bold">Detection Detail</h1>
          <p className="text-sm text-zinc-500 mt-1 font-mono">{id}</p>
        </div>
        <div className="ml-auto flex gap-2">
          <Button variant="outline" size="sm" onClick={handleDownloadJSON}><Download className="h-4 w-4 mr-1" /> JSON</Button>
          <Button variant="outline" size="sm" onClick={handleDownloadCSV}><Download className="h-4 w-4 mr-1" /> CSV</Button>
          <Button variant="destructive" size="sm" onClick={handleDelete}><Trash2 className="h-4 w-4 mr-1" /> Delete</Button>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card className="overflow-hidden">
            <div className="relative bg-zinc-100 dark:bg-zinc-900">
              {assetUrl ? (
                <img ref={imgRef} src={assetUrl} alt="Detection result" className="w-full object-contain max-h-[600px]" onLoad={drawBoxes} />
              ) : (
                <div className="aspect-video flex items-center justify-center text-zinc-400 text-sm">Loading image...</div>
              )}
              <canvas ref={canvasRef} className="absolute inset-0 w-full h-full pointer-events-none" />
            </div>
          </Card>
        </div>

        <div className="space-y-4">
          <Card>
            <CardHeader className="pb-2"><CardTitle className="text-sm">Metadata</CardTitle></CardHeader>
            <CardContent className="space-y-1 text-sm">
              <div className="flex justify-between"><span className="text-zinc-500">Source</span><Badge variant="outline">{det.source_type}</Badge></div>
              <div className="flex justify-between"><span className="text-zinc-500">Status</span><Badge variant={det.status === "completed" ? "success" : "destructive"}>{det.status}</Badge></div>
              <div className="flex justify-between"><span className="text-zinc-500">Resolution</span><span className="font-mono">{det.image_width}×{det.image_height}</span></div>
              <div className="flex justify-between"><span className="text-zinc-500">Processing</span><span className="font-mono">{det.processing_time_ms?.toFixed(0)}ms</span></div>
              <div className="flex justify-between"><span className="text-zinc-500">Inference</span><span className="font-mono">{det.inference_time_ms?.toFixed(0)}ms</span></div>
              <div className="flex justify-between"><span className="text-zinc-500">FPS</span><span className="font-mono">{det.fps?.toFixed(1)}</span></div>
              <div className="flex justify-between"><span className="text-zinc-500">Objects</span><span className="font-mono font-medium">{det.object_count}</span></div>
              <div className="flex justify-between"><span className="text-zinc-500">Avg Confidence</span><span className="font-mono">{det.avg_confidence ? `${(det.avg_confidence * 100).toFixed(1)}%` : "—"}</span></div>
              <div className="flex justify-between"><span className="text-zinc-500">Time</span><span className="font-mono text-xs">{new Date(det.created_at).toLocaleString()}</span></div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2"><CardTitle className="text-sm">Detected Classes</CardTitle></CardHeader>
            <CardContent className="space-y-1">
              {Object.entries(classCounts).sort((a, b) => b[1] - a[1]).map(([cls, count]) => (
                <div key={cls} className="flex justify-between text-sm">
                  <span>{cls}</span>
                  <span className="font-mono font-medium">{count}</span>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2"><CardTitle className="text-sm">Detection Table</CardTitle></CardHeader>
            <CardContent>
              <div className="max-h-64 overflow-y-auto">
                <table className="w-full text-xs">
                  <thead><tr className="border-b text-zinc-500"><th className="pb-1 text-left font-medium">Object</th><th className="pb-1 text-left font-medium">Conf</th><th className="pb-1 text-left font-medium">Track</th></tr></thead>
                  <tbody>
                    {det.objects?.map((o: any, i: number) => (
                      <tr key={i} className="border-b last:border-0"><td className="py-1">{o.class_name}</td><td className="py-1 font-mono">{(o.confidence * 100).toFixed(1)}%</td><td className="py-1 font-mono">{o.track_id ?? "—"}</td></tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}