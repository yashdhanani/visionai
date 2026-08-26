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

export default function DetectPage() {
  const router = useRouter();

  const { data: categories = [], isLoading } = useQuery({
    queryKey: ["categories"],
    queryFn: () => api.get("/api/v1/categories").then((r) => r.data.data),
  });

  const handleSelect = (cat: DetectionCategory) => {
    router.push(`/detect/${cat.id}`);
  };

  return (
    <div className="space-y-8">
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold">Choose Detection</h1>
        <p className="text-muted-foreground max-w-lg mx-auto">
          Select what you want to detect. VisionAI will automatically configure the right model, pipeline, and controls.
        </p>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 9 }).map((_, i) => <Skeleton key={i} className="h-44" />)}
        </div>
      ) : (
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
      )}
    </div>
  );
}
