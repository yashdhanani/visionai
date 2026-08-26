"use client";

import { useState, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Select } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { UploadDropzone } from "@/components/ui/upload-dropzone";
import { useToast } from "@/components/ui/toast";
import { api } from "@/lib/api";
import { Upload, Download, Trash2, ExternalLink } from "lucide-react";

interface BBox { x: number; y: number; width: number; height: number; }
interface Detection {
  class_id: number;
  class_name: string;
  confidence: number;
  bbox: BBox;
  track_id: number | null;
}

export default function ImageDetectionPage() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [detections, setDetections] = useState<Detection[]>([]);
  const [objectCounts, setObjectCounts] = useState<Record<string, number>>({});
  const [confidence, setConfidence] = useState(0.35);
  const [iou, setIou] = useState(0.45);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imgRef = useRef<HTMLImageElement>(null);
  const { error: toastError, success: toastSuccess } = useToast();

  const handleFiles = (files: File[]) => {
    const f = files[0];
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setDetections([]);
    setResult(null);
    setObjectCounts({});
  };

  const runDetection = async () => {
    if (!file) return;
    setLoading(true);
    try {
      const form = new FormData();
      form.append("file", file);
      form.append("project_id", "default");
      form.append("confidence", String(confidence));
      form.append("iou", String(iou));

      const resp = await api.post("/api/v1/detections/image", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      const data = resp.data.data;
      setResult(data);
      setDetections(data.objects || []);
      const counts: Record<string, number> = {};
      (data.objects || []).forEach((d: Detection) => {
        counts[d.class_name] = (counts[d.class_name] || 0) + 1;
      });
      setObjectCounts(counts);
      toastSuccess(`Detected ${data.object_count} objects in ${(data.processing_time_ms || 0).toFixed(0)}ms`);
    } catch (err: any) {
      toastError(err.response?.data?.error?.message || "Detection failed");
    } finally {
      setLoading(false);
    }
  };

  const drawBoxes = () => {
    const img = imgRef.current;
    const canvas = canvasRef.current;
    if (!img || !canvas || !detections.length) return;

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

    const frameW = result?.image_width || img.naturalWidth;
    const frameH = result?.image_height || img.naturalHeight;
    const scaleX = displayW / frameW;
    const scaleY = displayH / frameH;

    const palette = ["#10b981", "#3b82f6", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899"];
    const classColors: Record<string, string> = {};
    let ci = 0;

    detections.forEach((det) => {
      if (!classColors[det.class_name]) {
        classColors[det.class_name] = palette[ci % palette.length];
        ci++;
      }
      const color = classColors[det.class_name];
      const x = det.bbox.x * scaleX;
      const y = det.bbox.y * scaleY;
      const w = det.bbox.width * scaleX;
      const h = det.bbox.height * scaleY;

      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.strokeRect(x - w / 2, y - h / 2, w, h);

      const label = `${det.class_name} ${(det.confidence * 100).toFixed(0)}%`;
      const fontSize = 12;
      ctx.font = `600 ${fontSize}px system-ui`;
      const tw = ctx.measureText(label).width;

      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.roundRect(x - w / 2, y - h / 2 - fontSize - 8, tw + 12, fontSize + 6, 3);
      ctx.fill();
      ctx.fillStyle = "#fff";
      ctx.fillText(label, x - w / 2 + 6, y - h / 2 - 6);
    });
  };

  const downloadResult = () => {
    if (!result?.id) return;
    window.open(`/api/v1/detections/${result.id}/assets/annotated`, "_blank");
  };

  const downloadJSON = () => {
    if (!result) return;
    const blob = new Blob([JSON.stringify(result, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.download = `detection-${result.id}.json`;
    link.href = url;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Image Detection</h1>
        <p className="text-sm text-zinc-500 mt-1">Upload an image to run object detection</p>
      </div>

      <div className="grid lg:grid-cols-4 gap-6">
        <div className="lg:col-span-3 space-y-4">
          {!preview ? (
            <UploadDropzone accept="image/jpeg,image/png,image/webp" onFiles={handleFiles} maxSizeMB={10} label="Drop an image here or click to upload (JPG, PNG, WebP)" />
          ) : (
            <Card className="overflow-hidden">
              <div className="relative bg-zinc-100 dark:bg-zinc-900">
                <img
                  ref={imgRef}
                  src={preview}
                  alt="Upload preview"
                  className="w-full max-h-[600px] object-contain"
                  onLoad={drawBoxes}
                />
                <canvas ref={canvasRef} className="absolute inset-0 w-full h-full pointer-events-none" />
                {detections.length > 0 && (
                  <div className="absolute top-3 right-3 flex gap-1">
                    <Button variant="ghost" size="icon" onClick={downloadResult} title="Download annotated image"><Download className="h-4 w-4" /></Button>
                    <Button variant="ghost" size="icon" onClick={() => { setFile(null); setPreview(null); setDetections([]); setResult(null); }} title="Clear"><Trash2 className="h-4 w-4" /></Button>
                  </div>
                )}
              </div>
            </Card>
          )}

          {detections.length > 0 && (
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm">Detection Results</CardTitle></CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b text-left text-zinc-500">
                        <th className="pb-2 font-medium">Object</th>
                        <th className="pb-2 font-medium">Confidence</th>
                        <th className="pb-2 font-medium">X</th>
                        <th className="pb-2 font-medium">Y</th>
                        <th className="pb-2 font-medium">Width</th>
                        <th className="pb-2 font-medium">Height</th>
                        <th className="pb-2 font-medium">Track ID</th>
                      </tr>
                    </thead>
                    <tbody>
                      {detections.map((det, i) => (
                        <tr key={i} className="border-b last:border-0">
                          <td className="py-2"><Badge variant="secondary">{det.class_name}</Badge></td>
                          <td className="py-2 font-mono">{(det.confidence * 100).toFixed(1)}%</td>
                          <td className="py-2 font-mono">{det.bbox.x.toFixed(0)}</td>
                          <td className="py-2 font-mono">{det.bbox.y.toFixed(0)}</td>
                          <td className="py-2 font-mono">{det.bbox.width.toFixed(0)}</td>
                          <td className="py-2 font-mono">{det.bbox.height.toFixed(0)}</td>
                          <td className="py-2 font-mono">{det.track_id ?? "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Controls */}
        <div className="space-y-4">
          <Card>
            <CardHeader className="pb-2"><CardTitle className="text-sm">Controls</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <Slider label="Confidence" value={confidence} onChange={setConfidence} min={0.1} max={1} step={0.05} />
              <Slider label="IoU" value={iou} onChange={setIou} min={0.1} max={1} step={0.05} />

              <Button onClick={runDetection} disabled={!file || loading} className="w-full" loading={loading}>
                <Upload className="h-4 w-4 mr-1" /> Run Detection
              </Button>

              {preview && (
                <Button variant="outline" className="w-full" onClick={() => { setFile(null); setPreview(null); setDetections([]); setResult(null); }}>
                  Upload New Image
                </Button>
              )}
            </CardContent>
          </Card>

          {result && (
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm">Metadata</CardTitle></CardHeader>
              <CardContent className="space-y-1 text-sm">
                <div className="flex justify-between"><span className="text-zinc-500">Objects</span><span className="font-mono">{result.object_count}</span></div>
                <div className="flex justify-between"><span className="text-zinc-500">Processing</span><span className="font-mono">{result.processing_time_ms?.toFixed(0)}ms</span></div>
                <div className="flex justify-between"><span className="text-zinc-500">FPS</span><span className="font-mono">{result.fps?.toFixed(1)}</span></div>
                <div className="flex justify-between"><span className="text-zinc-500">Resolution</span><span className="font-mono">{result.image_width}×{result.image_height}</span></div>
                <div className="flex justify-between"><span className="text-zinc-500">Avg Conf</span><span className="font-mono">{result.avg_confidence ? `${(result.avg_confidence * 100).toFixed(1)}%` : "—"}</span></div>
              </CardContent>
            </Card>
          )}

          {Object.keys(objectCounts).length > 0 && (
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm">Object Counts</CardTitle></CardHeader>
              <CardContent className="space-y-1">
                {Object.entries(objectCounts).sort((a, b) => b[1] - a[1]).map(([cls, count]) => (
                  <div key={cls} className="flex justify-between text-sm">
                    <span>{cls}</span>
                    <span className="font-mono font-medium">{count}</span>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {result && (
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm">Export & Database</CardTitle></CardHeader>
              <CardContent className="space-y-2">
                <div className="flex items-center gap-1.5 text-xs text-emerald-600 dark:text-emerald-400 mb-2 font-medium">
                  <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                  Saved to Database Record #{result.id.slice(0, 8)}
                </div>
                {result.id && (
                  <Button variant="default" className="w-full" size="sm" onClick={() => window.open(`/history/${result.id}`, "_blank")}>
                    <ExternalLink className="h-4 w-4 mr-1" /> View in History Record
                  </Button>
                )}
                <Button variant="outline" className="w-full" size="sm" onClick={downloadResult}>
                  <Download className="h-4 w-4 mr-1" /> Download Annotated Image
                </Button>
                <Button variant="outline" className="w-full" size="sm" onClick={downloadJSON}>
                  <Download className="h-4 w-4 mr-1" /> Download JSON Metadata
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}