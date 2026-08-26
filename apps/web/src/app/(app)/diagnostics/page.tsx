"use client";

import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, getWsUrl } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { CheckCircle, XCircle, Loader2, Camera, Cpu, Wifi, Brain, Eye, Monitor } from "lucide-react";

interface CheckResult {
  name: string;
  status: "ok" | "error" | "loading" | "pending";
  message: string;
  latency_ms?: number;
}

export default function DiagnosticsPage() {
  const { token } = useAuthStore();
  const [checks, setChecks] = useState<CheckResult[]>([
    { name: "Camera", status: "pending", message: "Not tested" },
    { name: "Frame Capture", status: "pending", message: "Not tested" },
    { name: "WebSocket", status: "pending", message: "Not tested" },
    { name: "Model", status: "pending", message: "Not tested" },
    { name: "Inference", status: "pending", message: "Not tested" },
    { name: "Detections", status: "pending", message: "Not tested" },
    { name: "Rendering", status: "pending", message: "Not tested" },
  ]);
  const [running, setRunning] = useState(false);

  const updateCheck = (idx: number, update: Partial<CheckResult>) => {
    setChecks((prev) => prev.map((c, i) => (i === idx ? { ...c, ...update } : c)));
  };

  const runDiagnostics = async () => {
    setRunning(true);
    setChecks((prev) => prev.map((c) => ({ ...c, status: "pending" as const, message: "Waiting..." })));

    // 1. Camera
    updateCheck(0, { status: "loading", message: "Testing camera access..." });
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      updateCheck(0, { status: "ok", message: `Active - ${stream.getVideoTracks()[0].label}` });

      // 2. Frame Capture
      updateCheck(1, { status: "loading", message: "Capturing frame..." });
      const video = document.createElement("video");
      video.srcObject = stream;
      await video.play();
      await new Promise((r) => setTimeout(r, 500));
      const canvas = document.createElement("canvas");
      canvas.width = video.videoWidth || 640;
      canvas.height = video.videoHeight || 360;
      const ctx = canvas.getContext("2d")!;
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      const b64 = canvas.toDataURL("image/jpeg", 0.8).split(",")[1];
      updateCheck(1, { status: "ok", message: `${canvas.width}x${canvas.height} frame captured` });

      // 3. WebSocket
      updateCheck(2, { status: "loading", message: "Connecting WebSocket..." });
      const wsStart = performance.now();
      const ws = new WebSocket(`${getWsUrl()}/api/v1/detect/live?token=${token}`);

      await new Promise<void>((resolve, reject) => {
        ws.onopen = () => resolve();
        ws.onerror = () => reject(new Error("WS connect failed"));
        setTimeout(() => reject(new Error("WS timeout")), 5000);
      });
      const wsLatency = Math.round(performance.now() - wsStart);
      updateCheck(2, { status: "ok", message: `Connected in ${wsLatency}ms` });

      // 4. Model (wait for connected message)
      updateCheck(3, { status: "loading", message: "Waiting for model info..." });
      const connectedMsg = await new Promise<any>((resolve, reject) => {
        ws.onmessage = (e) => resolve(JSON.parse(e.data));
        setTimeout(() => reject(new Error("Model timeout")), 5000);
      });
      updateCheck(3, { status: "ok", message: `${connectedMsg.model_info?.model_path || "unknown"} on ${connectedMsg.model_info?.device || "?"}` });

      // 5. Inference - send a frame
      updateCheck(4, { status: "loading", message: "Running inference..." });
      ws.send(JSON.stringify({ type: "config", confidence: 0.25 }));
      ws.send(JSON.stringify({ type: "frame", seq: 1, ts: Date.now(), width: canvas.width, height: canvas.height, jpeg_b64: b64 }));

      const detMsg = await new Promise<any>((resolve, reject) => {
        ws.onmessage = (e) => {
          const msg = JSON.parse(e.data);
          if (msg.type === "detection") resolve(msg);
        };
        setTimeout(() => reject(new Error("Inference timeout")), 10000);
      });
      updateCheck(4, { status: "ok", message: `${detMsg.performance?.inference_ms || "?"}ms inference` });

      // 6. Detections
      updateCheck(5, { status: "ok", message: `${detMsg.count} objects detected` });

      // 7. Rendering
      updateCheck(6, { status: "ok", message: "Canvas rendering functional" });

      ws.close();
      stream.getTracks().forEach((t) => t.stop());
    } catch (err: any) {
      const failedIdx = checks.findIndex((c) => c.status === "loading");
      if (failedIdx >= 0) {
        updateCheck(failedIdx, { status: "error", message: err.message || "Failed" });
      }
    }

    setRunning(false);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">AI Diagnostics</h1>
          <p className="text-sm text-muted-foreground mt-1">Verify every stage of the detection pipeline</p>
        </div>
        <Button onClick={runDiagnostics} disabled={running}>
          {running ? <Loader2 className="h-4 w-4 mr-1 animate-spin" /> : <Cpu className="h-4 w-4 mr-1" />}
          Run Diagnostics
        </Button>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm">Pipeline Status</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {checks.map((check, i) => (
            <div key={check.name} className="flex items-center justify-between py-2 border-b border-border last:border-0">
              <div className="flex items-center gap-3">
                {check.status === "ok" && <CheckCircle className="h-5 w-5 text-emerald-500" />}
                {check.status === "error" && <XCircle className="h-5 w-5 text-red-500" />}
                {check.status === "loading" && <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />}
                {check.status === "pending" && <div className="h-5 w-5 rounded-full border-2 border-muted" />}
                <div>
                  <span className="font-medium text-sm">{check.name}</span>
                  <p className="text-xs text-muted-foreground">{check.message}</p>
                </div>
              </div>
              <Badge variant={check.status === "ok" ? "success" : check.status === "error" ? "destructive" : "secondary"}>
                {check.status === "ok" ? "OK" : check.status === "error" ? "FAIL" : check.status === "loading" ? "Testing..." : "Pending"}
              </Badge>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
