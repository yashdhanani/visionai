"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Select } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { UploadDropzone } from "@/components/ui/upload-dropzone";
import { useToast } from "@/components/ui/toast";
import { api } from "@/lib/api";
import { Upload, Download, Film, CheckCircle2, AlertCircle, Loader2, ExternalLink } from "lucide-react";

export default function VideoDetectionPage() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [confidence, setConfidence] = useState(0.35);
  const [iou, setIou] = useState(0.45);
  const [sampleFps, setSampleFps] = useState(10);
  const [loading, setLoading] = useState(false);
  const [jobStatus, setJobStatus] = useState<any>(null);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const { error: toastError, success: toastSuccess } = useToast();

  const handleFiles = (files: File[]) => {
    const f = files[0];
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setJobStatus(null);
    setVideoUrl(null);
  };

  const pollStatus = async (detectionId: string) => {
    const interval = setInterval(async () => {
      try {
        const resp = await api.get(`/api/v1/detections/${detectionId}/status`);
        const status = resp.data.data;
        setJobStatus(status);
        if (status.status === "completed") {
          clearInterval(interval);
          toastSuccess(`Video processed! ${status.objects_detected} objects detected`);
          try {
            const assetResp = await api.get(`/api/v1/detections/${detectionId}/assets/annotated`, { responseType: "blob" });
            const blob = new Blob([assetResp.data], { type: "video/mp4" });
            setVideoUrl(URL.createObjectURL(blob));
          } catch {}
        } else if (status.status === "failed") {
          clearInterval(interval);
          toastError(status.error || "Video processing failed");
        }
      } catch {}
    }, 1500);
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
      form.append("sample_fps", String(sampleFps));

      const resp = await api.post("/api/v1/detections/video", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      const data = resp.data.data;
      setJobStatus(data);
      pollStatus(data.detection_id);
    } catch (err: any) {
      toastError(err.response?.data?.error?.message || "Video upload failed");
    } finally {
      setLoading(false);
    }
  };

  const statusIcon = () => {
    if (!jobStatus) return null;
    if (jobStatus.status === "processing") return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />;
    if (jobStatus.status === "completed") return <CheckCircle2 className="h-4 w-4 text-emerald-500" />;
    if (jobStatus.status === "failed") return <AlertCircle className="h-4 w-4 text-red-500" />;
    return <Film className="h-4 w-4 text-zinc-400" />;
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Video Detection</h1>
        <p className="text-sm text-zinc-500 mt-1">Upload a video for background object detection processing</p>
      </div>

      <div className="grid lg:grid-cols-4 gap-6">
        <div className="lg:col-span-3 space-y-4">
          {!preview ? (
            <UploadDropzone accept="video/mp4,video/webm,video/quicktime" onFiles={handleFiles} maxSizeMB={200} label="Drop a video here or click to upload (MP4, WebM, MOV)" />
          ) : (
            <Card className="overflow-hidden">
              <div className="relative bg-zinc-950 aspect-video">
                {videoUrl ? (
                  <video src={videoUrl} controls className="w-full h-full object-contain" />
                ) : (
                  <video src={preview} controls className="w-full h-full object-contain" />
                )}
              </div>
            </Card>
          )}

          {/* Progress */}
          {jobStatus && jobStatus.status !== "completed" && (
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center gap-3 mb-4">
                  {statusIcon()}
                  <span className="text-sm font-medium">
                    {jobStatus.status === "processing" ? "Processing Video..." : jobStatus.status === "failed" ? "Processing Failed" : "Queued"}
                  </span>
                </div>
                {jobStatus.status === "processing" && (
                  <>
                    <div className="w-full bg-zinc-200 dark:bg-zinc-700 rounded-full h-2.5 mb-3">
                      <div className="bg-zinc-900 dark:bg-zinc-100 h-2.5 rounded-full transition-all duration-300" style={{ width: `${jobStatus.progress || 0}%` }} />
                    </div>
                    <div className="grid grid-cols-4 gap-4 text-sm">
                      <div>
                        <p className="text-zinc-500">Progress</p>
                        <p className="font-mono font-medium">{(jobStatus.progress || 0).toFixed(0)}%</p>
                      </div>
                      <div>
                        <p className="text-zinc-500">Frames</p>
                        <p className="font-mono font-medium">{jobStatus.frames_done || 0} / {jobStatus.frames_total || "?"}</p>
                      </div>
                      <div>
                        <p className="text-zinc-500">FPS</p>
                        <p className="font-mono font-medium">{jobStatus.fps?.toFixed(1) || "—"}</p>
                      </div>
                      <div>
                        <p className="text-zinc-500">Objects</p>
                        <p className="font-mono font-medium">{jobStatus.objects_detected}</p>
                      </div>
                    </div>
                  </>
                )}
                {jobStatus.status === "failed" && (
                  <p className="text-sm text-red-500">{jobStatus.error}</p>
                )}
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
              <Slider label="Sample FPS" value={sampleFps} onChange={setSampleFps} min={1} max={30} step={1} />

              <Button onClick={runDetection} disabled={!file || loading} className="w-full" loading={loading}>
                <Upload className="h-4 w-4 mr-1" /> Process Video
              </Button>

              {preview && (
                <Button variant="outline" className="w-full" onClick={() => { setFile(null); setPreview(null); setJobStatus(null); setVideoUrl(null); }}>
                  Upload New Video
                </Button>
              )}
            </CardContent>
          </Card>

          {jobStatus && (
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm">Job Details & Actions</CardTitle></CardHeader>
              <CardContent className="space-y-3 text-sm">
                <div className="flex justify-between"><span className="text-zinc-500">Status</span><Badge variant={jobStatus.status === "completed" ? "success" : jobStatus.status === "failed" ? "destructive" : "secondary"}>{jobStatus.status}</Badge></div>
                <div className="flex justify-between"><span className="text-zinc-500">Objects</span><span className="font-mono">{jobStatus.objects_detected}</span></div>
                <div className="flex justify-between"><span className="text-zinc-500">FPS</span><span className="font-mono">{jobStatus.fps?.toFixed(1) || "—"}</span></div>
                {jobStatus.status === "completed" && (
                  <div className="space-y-2 pt-2 border-t">
                    <Button variant="default" size="sm" className="w-full" onClick={() => window.open(`/history/${jobStatus.detection_id || jobStatus.id}`, "_blank")}>
                      <ExternalLink className="h-4 w-4 mr-1" /> View in History
                    </Button>
                    {videoUrl && (
                      <Button variant="outline" size="sm" className="w-full" onClick={() => {
                        const a = document.createElement("a");
                        a.href = videoUrl;
                        a.download = `annotated-video-${Date.now()}.mp4`;
                        a.click();
                      }}>
                        <Download className="h-4 w-4 mr-1" /> Download Video
                      </Button>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}