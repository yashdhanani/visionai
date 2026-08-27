"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { Cpu, Zap, CheckCircle, XCircle, Eye, Box, Car, PersonStanding, Flame } from "lucide-react";

const MODEL_ICONS: Record<string, typeof Cpu> = {
  default: Box,
  face: Eye,
  plate: Car,
  pose: PersonStanding,
  fire_smoke: Flame,
};

const FALLBACK_MODELS = [
  { id: "default", name: "YOLOv8n (General)", description: "Real-time object detection across 80 COCO categories (people, vehicles, animals, items).", classes: "80 classes", loaded: true, metadata: { device: "MPS/CUDA/CPU", class_count: 80 } },
  { id: "face", name: "YOLOv8n-Face", description: "Ultra-fast face detection optimized for close and distant facial bounding boxes.", classes: "1 class (face)", loaded: true, metadata: { device: "MPS/CUDA/CPU", class_count: 1 } },
  { id: "plate", name: "YOLOv8m-Plate (ANPR)", description: "Automatic vehicle license plate localization and character OCR integration.", classes: "1 class (plate)", loaded: true, metadata: { device: "MPS/CUDA/CPU", class_count: 1 } },
  { id: "pose", name: "YOLOv8n-Pose", description: "Full-body 17-keypoint skeleton joint tracking and pose estimation.", classes: "1 class (person + 17 keypoints)", loaded: true, metadata: { device: "MPS/CUDA/CPU", class_count: 17 } },
  { id: "fire_smoke", name: "YOLOv8n-FireSmoke", description: "Hazard surveillance model trained on D-Fire dataset for early fire and smoke detection.", classes: "2 classes (fire, smoke)", loaded: true, metadata: { device: "MPS/CUDA/CPU", class_count: 2 } },
];

export default function ModelsPage() {
  const queryClient = useQueryClient();
  const { success, error: toastError } = useToast();

  const { data: models = FALLBACK_MODELS, isLoading } = useQuery({
    queryKey: ["models", "available"],
    queryFn: () => api.get("/api/v1/models/available").then((r) => r.data.data),
    initialData: FALLBACK_MODELS,
  });

  const { data: active = FALLBACK_MODELS[0] } = useQuery({
    queryKey: ["models", "active"],
    queryFn: () => api.get("/api/v1/models/active").then((r) => r.data.data),
    initialData: FALLBACK_MODELS[0],
  });

  const activateMutation = useMutation({
    mutationFn: (id: string) => api.post(`/api/v1/models/${id}/activate`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["models"] });
      success("Model activated");
    },
    onError: (err: any) => toastError(err.response?.data?.error?.message || "Failed"),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Models</h1>
          <p className="text-sm text-muted-foreground mt-1">Switch between detection models</p>
        </div>
      </div>

      {/* Active Model */}
      {active && (
        <Card className="border-emerald-200 dark:border-emerald-800">
          <CardHeader className="pb-2">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-emerald-500" />
              <CardTitle className="text-sm">Active Model</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-lg font-semibold">{active.name || active.model_path}</p>
            <p className="text-sm text-muted-foreground">Framework: {active.framework || "ultralytics-yolo"}</p>
            {active.classes_count && <p className="text-sm text-muted-foreground">{active.classes_count} classes</p>}
          </CardContent>
        </Card>
      )}

      {/* Models List */}
      {isLoading ? (
        <div className="grid md:grid-cols-2 gap-4">
          {Array.from({ length: 2 }).map((_, i) => <Skeleton key={i} className="h-48" />)}
        </div>
      ) : (
        <div className="grid md:grid-cols-2 gap-4">
          {models.map((model: any) => {
            const isActive = active?.id === model.id;
            const Icon = MODEL_ICONS[model.id] || Cpu;
            return (
              <Card key={model.id} className={isActive ? "border-emerald-200 dark:border-emerald-800" : ""}>
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      <Icon className="h-5 w-5 text-muted-foreground" />
                      <CardTitle className="text-base">{model.name}</CardTitle>
                    </div>
                    <Badge variant={isActive ? "success" : "secondary"}>
                      {isActive ? "Active" : "Available"}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <p className="text-sm text-muted-foreground">{model.description}</p>
                  {model.loaded && model.metadata && (
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div><span className="text-muted-foreground">Device:</span> <span className="font-mono">{model.metadata.device}</span></div>
                      <div><span className="text-muted-foreground">Classes:</span> <span className="font-mono">{model.metadata.class_count}</span></div>
                    </div>
                  )}
                  <div className="flex gap-2 pt-1">
                    {isActive ? (
                      <Button variant="outline" size="sm" disabled>
                        <CheckCircle className="h-4 w-4 mr-1" /> Active
                      </Button>
                    ) : (
                      <Button size="sm" onClick={() => activateMutation.mutate(model.id)} disabled={activateMutation.isPending}>
                        <Zap className="h-4 w-4 mr-1" /> Switch to {model.name}
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
