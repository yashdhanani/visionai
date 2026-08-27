"use client";

import { useRef, useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Select } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/components/ui/toast";
import { getWsUrl, api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { Camera, CameraOff, Pause, Play, Download, Settings2, Activity, BookmarkPlus } from "lucide-react";

interface Detection {
  class_id: number;
  class_name: string;
  confidence: number;
  bbox: { x: number; y: number; width: number; height: number };
  track_id: number | null;
}

interface Perf {
  fps: number;
  latency_ms: number;
  preprocess_ms: number;
  inference_ms: number;
  postprocess_ms: number;
}

export default function LiveDetectionPage() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const animFrameRef = useRef<number>(0);
  const frameTimerRef = useRef<NodeJS.Timeout | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const [connected, setConnected] = useState(false);
  const [detecting, setDetecting] = useState(false);
  const [paused, setPaused] = useState(false);
  const [detections, setDetections] = useState<Detection[]>([]);
  const [perf, setPerf] = useState<Perf | null>(null);
  const [objectCounts, setObjectCounts] = useState<Record<string, number>>({});

  const [confidence, setConfidence] = useState(0.35);
  const [iou, setIou] = useState(0.45);
  const [maxFps, setMaxFps] = useState(15);
  const [showBoxes, setShowBoxes] = useState(true);
  const [showLabels, setShowLabels] = useState(true);
  const [showConf, setShowConf] = useState(true);
  const [tracker, setTracker] = useState<"off" | "bytetrack" | "botsort">("off");
  const [resolution, setResolution] = useState("640x360");
  const [modelId, setModelId] = useState<"default" | "face" | "plate" | "pose" | "fire_smoke">("default");

  const { token } = useAuthStore();
  const { error: toastError, success: toastSuccess } = useToast();

  const isDetectingRef = useRef<boolean>(false);
  const isPausedRef = useRef<boolean>(false);
  const inFlightRef = useRef<boolean>(false);
  const offscreenCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const lastFrameTimeRef = useRef<number>(0);

  const drawDetections = useCallback((dets: Detection[], frameW: number, frameH: number) => {
    const canvas = canvasRef.current;
    const video = videoRef.current;
    if (!canvas || !video) return;

    const containerW = video.clientWidth || 640;
    const containerH = video.clientHeight || 360;
    const dpr = window.devicePixelRatio || 1;

    if (canvas.width !== containerW * dpr || canvas.height !== containerH * dpr) {
      canvas.width = containerW * dpr;
      canvas.height = containerH * dpr;
      canvas.style.width = `${containerW}px`;
      canvas.style.height = `${containerH}px`;
    }

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.scale(dpr, dpr);

    if (!showBoxes || !dets || !dets.length) return;

    const videoRatio = (frameW || 640) / (frameH || 360);
    const containerRatio = containerW / containerH;
    let renderW: number, renderH: number, offsetX: number, offsetY: number;

    if (videoRatio > containerRatio) {
      renderW = containerW;
      renderH = containerW / videoRatio;
      offsetX = 0;
      offsetY = (containerH - renderH) / 2;
    } else {
      renderH = containerH;
      renderW = containerH * videoRatio;
      offsetX = (containerW - renderW) / 2;
      offsetY = 0;
    }

    const scaleX = renderW / (frameW || 640);
    const scaleY = renderH / (frameH || 360);

    const classColors: Record<string, string> = {};
    const palette = ["#10b981", "#3b82f6", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#06b6d4", "#84cc16"];
    let colorIdx = 0;

    dets.forEach((det) => {
      if (!classColors[det.class_name]) {
        classColors[det.class_name] = palette[colorIdx % palette.length];
        colorIdx++;
      }
      const color = classColors[det.class_name];
      const x = offsetX + det.bbox.x * scaleX;
      const y = offsetY + det.bbox.y * scaleY;
      const w = det.bbox.width * scaleX;
      const h = det.bbox.height * scaleY;

      ctx.strokeStyle = color;
      ctx.lineWidth = 2.5;
      ctx.strokeRect(x, y, w, h);

      const labelParts = [det.class_name];
      if (showConf) labelParts.push(`${(det.confidence * 100).toFixed(0)}%`);
      if (det.track_id !== null && det.track_id !== undefined) labelParts.push(`#${det.track_id}`);
      const label = labelParts.join(" ");

      if (showLabels && label) {
        const fontSize = 12;
        ctx.font = `700 ${fontSize}px system-ui, sans-serif`;
        const textWidth = ctx.measureText(label).width;
        const padX = 6;
        const padY = 3;
        const labelH = fontSize + padY * 2;
        const labelY = y - labelH - 2;

        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.roundRect(x, labelY < 0 ? y : labelY, textWidth + padX * 2, labelH, 4);
        ctx.fill();

        ctx.fillStyle = "#fff";
        ctx.fillText(label, x + padX, (labelY < 0 ? y : labelY) + fontSize + padY - 1);
      }
    });
  }, [showBoxes, showLabels, showConf]);

  const sendFrame = useCallback(() => {
    const video = videoRef.current;
    const ws = wsRef.current;
    if (!video || !ws || ws.readyState !== WebSocket.OPEN || isPausedRef.current) return;

    if (inFlightRef.current) return;

    const now = performance.now();
    const minInterval = 1000 / maxFps;
    if (now - lastFrameTimeRef.current < minInterval) return;
    lastFrameTimeRef.current = now;

    if (!offscreenCanvasRef.current) {
      offscreenCanvasRef.current = document.createElement("canvas");
    }

    const tempCanvas = offscreenCanvasRef.current;
    const w = video.videoWidth || 640;
    const h = video.videoHeight || 360;
    if (tempCanvas.width !== w || tempCanvas.height !== h) {
      tempCanvas.width = w;
      tempCanvas.height = h;
    }
    const ctx = tempCanvas.getContext("2d", { willReadFrequently: true });
    if (!ctx) return;

    ctx.drawImage(video, 0, 0, w, h);
    const dataUrl = tempCanvas.toDataURL("image/jpeg", 0.70);
    const b64 = dataUrl.split(",")[1];

    inFlightRef.current = true;

    // Safety timeout in case of dropped packet
    setTimeout(() => {
      inFlightRef.current = false;
    }, 150);

    ws.send(
      JSON.stringify({
        type: "frame",
        seq: Date.now(),
        ts: Date.now(),
        width: w,
        height: h,
        jpeg_b64: b64,
      })
    );
  }, [maxFps]);

  const startCamera = async () => {
    try {
      const [w, h] = resolution.split("x").map(Number);
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: w }, height: { ideal: h }, facingMode: "user" },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
    } catch (err) {
      toastError("Camera access denied. Please allow camera permissions.");
    }
  };

  const stopCamera = () => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
  };

  const connectWs = () => {
    const rawToken = token || (typeof window !== "undefined" ? localStorage.getItem("access_token") : "") || "";
    const wsUrl = `${getWsUrl()}/api/v1/detect/live?token=${encodeURIComponent(rawToken)}&model=${modelId}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setConnected(true);
      inFlightRef.current = false;
      ws.send(JSON.stringify({ type: "config", confidence, iou, tracker, max_fps: maxFps, resolution, quality: 70, model_id: modelId }));
      sendFrame();
    };

    ws.onmessage = (event) => {
      inFlightRef.current = false;
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === "detection") {
          const dets = msg.detections || [];
          setDetections(dets);
          setPerf(msg.performance);
          const counts: Record<string, number> = {};
          dets.forEach((d: Detection) => {
            counts[d.class_name] = (counts[d.class_name] || 0) + 1;
          });
          setObjectCounts(counts);
          drawDetections(dets, msg.frame_width || 640, msg.frame_height || 360);
        } else if (msg.type === "frame_skipped") {
          inFlightRef.current = false;
        }
      } catch (e) {}
    };

    ws.onerror = () => {
      inFlightRef.current = false;
      toastError("WebSocket connection error");
    };
    ws.onclose = () => {
      inFlightRef.current = false;
      setConnected(false);
    };
    wsRef.current = ws;
  };

  const disconnectWs = () => {
    wsRef.current?.close();
    wsRef.current = null;
    setConnected(false);
    inFlightRef.current = false;
  };

  // Continuous animation loop for capture
  const streamLoop = useCallback(() => {
    if (!isDetectingRef.current || isPausedRef.current) return;
    sendFrame();
    animFrameRef.current = requestAnimationFrame(streamLoop);
  }, [sendFrame]);

  const startDetection = async () => {
    await startCamera();
    connectWs();
    isDetectingRef.current = true;
    isPausedRef.current = false;
    setDetecting(true);
    setPaused(false);
    inFlightRef.current = false;
    animFrameRef.current = requestAnimationFrame(streamLoop);
  };

  const togglePause = () => {
    const nextPaused = !paused;
    isPausedRef.current = nextPaused;
    setPaused(nextPaused);
    if (!nextPaused && isDetectingRef.current) {
      inFlightRef.current = false;
      animFrameRef.current = requestAnimationFrame(streamLoop);
    }
  };

  const stopDetection = () => {
    isDetectingRef.current = false;
    isPausedRef.current = false;
    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    if (frameTimerRef.current) clearInterval(frameTimerRef.current);
    disconnectWs();
    stopCamera();
    setDetecting(false);
    setPaused(false);
    inFlightRef.current = false;
    setDetections([]);
    setPerf(null);
    setObjectCounts({});
    const canvas = canvasRef.current;
    if (canvas) {
      const ctx = canvas.getContext("2d");
      ctx?.clearRect(0, 0, canvas.width, canvas.height);
    }
  };

  const screenshot = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video) return;

    const tempCanvas = document.createElement("canvas");
    tempCanvas.width = video.videoWidth;
    tempCanvas.height = video.videoHeight;
    const ctx = tempCanvas.getContext("2d");
    if (!ctx) return;

    ctx.drawImage(video, 0, 0);
    if (canvas) {
      ctx.drawImage(canvas, 0, 0, tempCanvas.width, tempCanvas.height);
    }

    const link = document.createElement("a");
    link.download = `visionai-capture-${Date.now()}.jpg`;
    link.href = tempCanvas.toDataURL("image/jpeg", 0.95);
    link.click();
  };

  const [savingSnapshot, setSavingSnapshot] = useState(false);

  const saveToDatabase = async () => {
    const video = videoRef.current;
    if (!video) return;
    setSavingSnapshot(true);
    try {
      const tempCanvas = document.createElement("canvas");
      tempCanvas.width = video.videoWidth || 640;
      tempCanvas.height = video.videoHeight || 360;
      const ctx = tempCanvas.getContext("2d");
      if (!ctx) return;
      ctx.drawImage(video, 0, 0);

      tempCanvas.toBlob(async (blob) => {
        if (!blob) return;
        const formData = new FormData();
        formData.append("file", blob, `live-snapshot-${Date.now()}.jpg`);
        formData.append("confidence", String(confidence));
        formData.append("iou", String(iou));
        formData.append("model_id", modelId);

        const resp = await api.post("/api/v1/detections/image", formData);
        const data = resp.data.data;
        toastSuccess(`Saved to Database Record #${data.id.slice(0, 8)}`);
      }, "image/jpeg", 0.9);
    } catch (e: any) {
      toastError(e.response?.data?.error?.message || "Failed to save snapshot");
    } finally {
      setSavingSnapshot(false);
    }
  };

  useEffect(() => {
    if (connected) {
      wsRef.current?.send(JSON.stringify({ type: "config", confidence, iou, tracker, max_fps: maxFps, resolution, quality: 80, model_id: modelId }));
    }
  }, [confidence, iou, tracker, maxFps, resolution, modelId, connected]);

  useEffect(() => {
    return () => {
      stopDetection();
    };
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Live Detection</h1>
          <p className="text-sm text-zinc-500 mt-1">Real-time webcam detection — general objects or faces</p>
        </div>
        <div className="flex gap-2">
          {detecting && (
            <>
              <Button variant="outline" onClick={saveToDatabase} loading={savingSnapshot} size="sm">
                <BookmarkPlus className="h-4 w-4 mr-1" /> Save to DB
              </Button>
              <Button variant="outline" onClick={screenshot} size="sm">
                <Download className="h-4 w-4 mr-1" /> Download
              </Button>
            </>
          )}
          {detecting ? (
            <Button variant="destructive" onClick={stopDetection}><CameraOff className="h-4 w-4 mr-1" /> Stop</Button>
          ) : (
            <Button onClick={startDetection}><Camera className="h-4 w-4 mr-1" /> Start Detection</Button>
          )}
        </div>
      </div>

      <div className="grid lg:grid-cols-4 gap-6">
        {/* Video + Canvas */}
        <div className="lg:col-span-3">
          <Card className="overflow-hidden">
            <div className="relative bg-zinc-950 aspect-video">
              <video ref={videoRef} className="w-full h-full object-contain" muted playsInline />
              <canvas ref={canvasRef} className="absolute inset-0 w-full h-full" />
              {!detecting && (
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-center text-zinc-400">
                    <Camera className="h-12 w-12 mx-auto mb-3 opacity-50" />
                    <p className="text-sm">Click &quot;Start Detection&quot; to begin</p>
                  </div>
                </div>
              )}
              {detecting && (
                <div className="absolute top-3 left-3 flex gap-2">
                  {connected ? (
                    <>
                      <Badge variant="success">🟢 Live</Badge>
                      {perf && <Badge variant="secondary">{perf.fps.toFixed(1)} FPS</Badge>}
                      {perf && <Badge variant="secondary">{perf.latency_ms.toFixed(0)}ms</Badge>}
                    </>
                  ) : (
                    <Badge variant="destructive" className="animate-pulse">🟡 Connecting Stream...</Badge>
                  )}
                </div>
              )}
            </div>
          </Card>
        </div>

        {/* Detection Panel */}
        <div className="space-y-4">
          {/* Object Counts */}
          <Card>
            <CardHeader className="pb-2"><CardTitle className="text-sm">Detected Objects</CardTitle></CardHeader>
            <CardContent>
              {Object.keys(objectCounts).length === 0 ? (
                <p className="text-sm text-zinc-500">No objects detected</p>
              ) : (
                <div className="space-y-1">
                  {Object.entries(objectCounts)
                    .sort((a, b) => b[1] - a[1])
                    .map(([cls, count]) => (
                      <div key={cls} className="flex justify-between text-sm">
                        <span>{cls}</span>
                        <span className="font-mono font-medium">{count}</span>
                      </div>
                    ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Performance */}
          {perf && (
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm flex items-center gap-1"><Activity className="h-3.5 w-3.5" /> Performance</CardTitle></CardHeader>
              <CardContent className="space-y-1 text-sm">
                <div className="flex justify-between"><span className="text-zinc-500">FPS</span><span className="font-mono">{perf.fps.toFixed(1)}</span></div>
                <div className="flex justify-between"><span className="text-zinc-500">Latency</span><span className="font-mono">{perf.latency_ms.toFixed(1)}ms</span></div>
                <div className="flex justify-between"><span className="text-zinc-500">Preprocess</span><span className="font-mono">{perf.preprocess_ms.toFixed(1)}ms</span></div>
                <div className="flex justify-between"><span className="text-zinc-500">Inference</span><span className="font-mono">{perf.inference_ms.toFixed(1)}ms</span></div>
                <div className="flex justify-between"><span className="text-zinc-500">Postprocess</span><span className="font-mono">{perf.postprocess_ms.toFixed(1)}ms</span></div>
              </CardContent>
            </Card>
          )}

          {/* Controls */}
          <Card>
            <CardHeader className="pb-2"><CardTitle className="text-sm flex items-center gap-1"><Settings2 className="h-3.5 w-3.5" /> Controls</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-1">
                <label className="text-xs font-medium text-muted-foreground">Detection Model</label>
                <Select value={modelId} onChange={(e) => setModelId(e.target.value as any)}>
                  <option value="default">YOLOv8n (General - 80 classes)</option>
                  <option value="face">YOLOv8n-Face (Face Detection Only)</option>
                  <option value="pose">YOLOv8n-Pose (Pose & Body Skeleton)</option>
                  <option value="plate">YOLOv8m-Plate (License Plate Detection)</option>
                  <option value="fire_smoke">YOLOv8n-FireSmoke (Fire & Smoke)</option>
                </Select>
              </div>

              <Slider label="Confidence" value={confidence} onChange={setConfidence} min={0.1} max={1} step={0.05} />
              <Slider label="IoU" value={iou} onChange={setIou} min={0.1} max={1} step={0.05} />
              <Slider label="Max FPS" value={maxFps} onChange={setMaxFps} min={1} max={30} step={1} />

              <Select value={resolution} onChange={(e) => setResolution(e.target.value)}>
                <option value="1280x720">1280x720</option>
                <option value="640x360">640x360</option>
                <option value="320x180">320x180</option>
              </Select>

              <Select value={tracker} onChange={(e) => setTracker(e.target.value as any)}>
                <option value="off">No Tracking</option>
                <option value="bytetrack">ByteTrack</option>
                <option value="botsort">BoT-SORT</option>
              </Select>

              <div className="space-y-2 pt-2 border-t border-zinc-200 dark:border-zinc-800">
                <Switch checked={showBoxes} onCheckedChange={setShowBoxes} label="Bounding Boxes" />
                <Switch checked={showLabels} onCheckedChange={setShowLabels} label="Labels" />
                <Switch checked={showConf} onCheckedChange={setShowConf} label="Confidence" />
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}