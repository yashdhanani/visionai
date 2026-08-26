import { api } from "@/lib/api";

export interface CategorySetting {
  key: string;
  label: string;
  type: "slider" | "select" | "toggle" | "input";
  default: unknown;
  min_val?: number;
  max_val?: number;
  step?: number;
  options?: { value: string; label: string }[];
  description?: string;
}

export interface DetectionCategory {
  id: string;
  name: string;
  icon: string;
  description: string;
  long_description: string;
  supported_sources: string[];
  model_ids: string[];
  default_model_id: string;
  supports_tracking: boolean;
  supports_counting: boolean;
  supports_ocr: boolean;
  supports_zones: boolean;
  supports_alerts: boolean;
  supports_pose: boolean;
  settings: CategorySetting[];
  output_fields: { key: string; label: string }[];
  status: "production" | "beta" | "experimental" | "custom_model_required";
  tags: string[];
}

export async function fetchCategories(): Promise<DetectionCategory[]> {
  const res = await api.get("/api/v1/categories");
  return res.data.data;
}

export async function fetchCategory(id: string): Promise<DetectionCategory> {
  const res = await api.get(`/api/v1/categories/${id}`);
  return res.data.data;
}

export const CATEGORY_COLORS: Record<string, string> = {
  objects: "#3b82f6",
  people: "#10b981",
  counting: "#06b6d4",
  vehicles: "#f59e0b",
  number_plate: "#8b5cf6",
  face: "#ec4899",
  attendance: "#14b8a6",
  pose: "#f97316",
  safety: "#ef4444",
  zones: "#6366f1",
  fire_smoke: "#dc2626",
  inspection: "#84cc16",
  ocr: "#a855f7",
};

export const STATUS_BADGES: Record<string, { label: string; variant: string }> = {
  production: { label: "Production Ready", variant: "success" },
  beta: { label: "Beta", variant: "warning" },
  experimental: { label: "Experimental", variant: "secondary" },
  custom_model_required: { label: "Custom Model", variant: "outline" },
};
