"use client";

import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Box, Users, Calculator, Car, Hash, ScanFace, ClipboardCheck,
  PersonStanding, ShieldAlert, BoxSelect, Flame, SearchCheck, Type, ArrowRight,
  TrafficCone,
} from "lucide-react";
import type { DetectionCategory } from "@/lib/category";

const ICON_MAP: Record<string, typeof Box> = {
  Box, Users, Calculator, Car, Hash, ScanFace, ClipboardCheck,
  PersonStanding, ShieldAlert, BoxSelect, Flame, SearchCheck, Type, TrafficCone,
};

const STATUS_STYLE: Record<string, string> = {
  production: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20",
  beta: "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20",
  experimental: "bg-zinc-500/10 text-zinc-500 border-zinc-500/20",
  custom_model_required: "bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20",
};

const STATUS_LABEL: Record<string, string> = {
  production: "Production Ready",
  beta: "Beta",
  experimental: "Experimental",
  custom_model_required: "Custom Model Required",
};

const FALLBACK_CATEGORIES: DetectionCategory[] = [
  {
    id: "objects",
    name: "Object Detection",
    icon: "Box",
    description: "Detect & classify 80+ everyday objects in real time",
    long_description: "General COCO multi-class detection",
    supported_sources: ["webcam", "image", "video"],
    model_ids: ["default"],
    default_model_id: "default",
    supports_tracking: true,
    supports_counting: true,
    supports_ocr: false,
    supports_zones: true,
    supports_alerts: true,
    supports_pose: false,
    settings: [],
    output_fields: [],
    status: "production",
    tags: ["general", "coco"],
  },
  {
    id: "people",
    name: "People & Crowd",
    icon: "Users",
    description: "Detect pedestrians, track crowds, and monitor occupancy",
    long_description: "Person detection & crowd density",
    supported_sources: ["webcam", "image", "video"],
    model_ids: ["default"],
    default_model_id: "default",
    supports_tracking: true,
    supports_counting: true,
    supports_ocr: false,
    supports_zones: true,
    supports_alerts: true,
    supports_pose: false,
    settings: [],
    output_fields: [],
    status: "production",
    tags: ["people", "security"],
  },
  {
    id: "face",
    name: "Face Detection",
    icon: "ScanFace",
    description: "High-precision face detection and landmark bounding boxes",
    long_description: "Dedicated face detection neural model",
    supported_sources: ["webcam", "image", "video"],
    model_ids: ["face"],
    default_model_id: "face",
    supports_tracking: true,
    supports_counting: true,
    supports_ocr: false,
    supports_zones: false,
    supports_alerts: false,
    supports_pose: false,
    settings: [],
    output_fields: [],
    status: "production",
    tags: ["face", "biometrics"],
  },
  {
    id: "pose",
    name: "Human Pose Estimation",
    icon: "PersonStanding",
    description: "17-keypoint skeletal joint tracking and gesture perception",
    long_description: "COCO-17 keypoint pose estimation",
    supported_sources: ["webcam", "image", "video"],
    model_ids: ["pose"],
    default_model_id: "pose",
    supports_tracking: true,
    supports_counting: false,
    supports_ocr: false,
    supports_zones: false,
    supports_alerts: false,
    supports_pose: true,
    settings: [],
    output_fields: [],
    status: "production",
    tags: ["pose", "skeleton"],
  },
  {
    id: "vehicles",
    name: "Vehicle & Traffic",
    icon: "Car",
    description: "Detect cars, trucks, buses, and monitor traffic flow",
    long_description: "Vehicle class detection & tracking",
    supported_sources: ["webcam", "image", "video"],
    model_ids: ["default"],
    default_model_id: "default",
    supports_tracking: true,
    supports_counting: true,
    supports_ocr: false,
    supports_zones: true,
    supports_alerts: true,
    supports_pose: false,
    settings: [],
    output_fields: [],
    status: "production",
    tags: ["vehicles", "traffic"],
  },
  {
    id: "number_plate",
    name: "License Plate & ANPR",
    icon: "Hash",
    description: "Vehicle license plate detection and high-accuracy OCR",
    long_description: "Automatic Number Plate Recognition (ANPR)",
    supported_sources: ["webcam", "image", "video"],
    model_ids: ["plate"],
    default_model_id: "plate",
    supports_tracking: true,
    supports_counting: true,
    supports_ocr: true,
    supports_zones: false,
    supports_alerts: true,
    supports_pose: false,
    settings: [],
    output_fields: [],
    status: "production",
    tags: ["anpr", "plates"],
  },
  {
    id: "fire_smoke",
    name: "Fire & Smoke Hazard",
    icon: "Flame",
    description: "Real-time flame and smoke detection for hazard warning",
    long_description: "D-Fire neural model for early fire detection",
    supported_sources: ["webcam", "image", "video"],
    model_ids: ["fire_smoke"],
    default_model_id: "fire_smoke",
    supports_tracking: false,
    supports_counting: false,
    supports_ocr: false,
    supports_zones: true,
    supports_alerts: true,
    supports_pose: false,
    settings: [],
    output_fields: [],
    status: "production",
    tags: ["hazard", "fire"],
  },
  {
    id: "counting",
    name: "Line Crossing & Counting",
    icon: "Calculator",
    description: "Bidirectional entry/exit tripwire counting across gates",
    long_description: "Automated line crossing analytics",
    supported_sources: ["webcam", "video"],
    model_ids: ["default"],
    default_model_id: "default",
    supports_tracking: true,
    supports_counting: true,
    supports_ocr: false,
    supports_zones: true,
    supports_alerts: true,
    supports_pose: false,
    settings: [],
    output_fields: [],
    status: "production",
    tags: ["counting", "tripwire"],
  },
  {
    id: "traffic_analysis",
    name: "Adaptive Signal Control",
    icon: "TrafficCone",
    description: "Real-time vehicle queue estimation and adaptive traffic control",
    long_description: "Traffic volume & green signal optimization",
    supported_sources: ["webcam", "video"],
    model_ids: ["default"],
    default_model_id: "default",
    supports_tracking: true,
    supports_counting: true,
    supports_ocr: false,
    supports_zones: true,
    supports_alerts: true,
    supports_pose: false,
    settings: [],
    output_fields: [],
    status: "production",
    tags: ["traffic", "smart-city"],
  },
];

export default function DetectPage() {
  const router = useRouter();

  const { data: categories = FALLBACK_CATEGORIES } = useQuery({
    queryKey: ["categories"],
    queryFn: () => api.get("/api/v1/categories").then((r) => r.data.data),
    initialData: FALLBACK_CATEGORIES,
  });

  const handleSelect = (cat: DetectionCategory) => {
    router.push(`/detect/${cat.id}`);
  };

  return (
    <div className="space-y-8">
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-extrabold tracking-tight">Choose Detection Task</h1>
        <p className="text-muted-foreground max-w-lg mx-auto text-sm">
          Select a perception category below. VisionAI will automatically configure the neural model, inference parameters, and live telemetry overlays.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {categories.map((cat: DetectionCategory) => {
            const Icon = ICON_MAP[cat.icon] || Box;
            return (
              <Card
                key={cat.id}
                className="group cursor-pointer hover:border-primary/50 hover:shadow-md transition-all duration-200"
                onClick={() => handleSelect(cat)}
              >
                <CardContent className="p-5 space-y-3">
                  <div className="flex items-start justify-between">
                    <div className="p-2 rounded-lg bg-primary/10">
                      <Icon className="h-5 w-5 text-primary" />
                    </div>
                    <Badge variant="outline" className={`text-[10px] ${STATUS_STYLE[cat.status]}`}>
                      {STATUS_LABEL[cat.status]}
                    </Badge>
                  </div>
                  <div>
                    <h3 className="font-semibold text-base">{cat.name}</h3>
                    <p className="text-sm text-muted-foreground mt-1 line-clamp-2">{cat.description}</p>
                  </div>
                  <div className="flex items-center justify-between pt-1">
                    <div className="flex gap-1.5 flex-wrap">
                      {cat.supports_tracking && <Badge variant="secondary" className="text-[10px] px-1.5">Tracking</Badge>}
                      {cat.supports_counting && <Badge variant="secondary" className="text-[10px] px-1.5">Counting</Badge>}
                      {cat.supports_ocr && <Badge variant="secondary" className="text-[10px] px-1.5">OCR</Badge>}
                      {cat.supports_zones && <Badge variant="secondary" className="text-[10px] px-1.5">Zones</Badge>}
                    </div>
                    <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>
    );
}
