export interface BBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface DetectionObject {
  class_id: number;
  class_name: string;
  confidence: number;
  bbox: BBox;
  track_id: number | null;
}

export interface DetectionResult {
  id: string;
  project_id: string;
  source_type: "image" | "video" | "webcam" | "stream";
  model_id: string | null;
  source_url: string | null;
  original_path: string | null;
  annotated_path: string | null;
  processing_time_ms: number | null;
  inference_time_ms: number | null;
  fps: number | null;
  object_count: number;
  avg_confidence: number | null;
  image_width: number | null;
  image_height: number | null;
  status: "pending" | "processing" | "completed" | "failed";
  objects: DetectionObject[];
  created_at: string;
}

export interface WSClientMessage {
  type: "frame" | "config" | "start" | "stop" | "heartbeat";
  seq?: number;
  ts?: number;
  width?: number;
  height?: number;
  jpeg_b64?: string;
  confidence?: number;
  iou?: number;
  model?: string;
  class_filter?: number[];
  tracker?: "bytetrack" | "botsort" | "off";
  max_fps?: number;
  resolution?: "1280x720" | "640x360" | "320x180";
  quality?: number;
}

export interface WSDetectionMessage {
  type: "detection";
  seq: number;
  ts: number;
  detections: DetectionObject[];
  performance: {
    fps: number;
    latency_ms: number;
    preprocess_ms: number;
    inference_ms: number;
    postprocess_ms: number;
  };
  frame_width: number;
  frame_height: number;
  count: number;
}

export interface WSErrorMessage {
  type: "error";
  code: string;
  message: string;
}

export interface WSConnectedMessage {
  type: "connected";
  session_id: string;
  model_info: Record<string, unknown>;
}

export type WSServerMessage = WSDetectionMessage | WSErrorMessage | WSConnectedMessage;

export interface VideoJobStatus {
  detection_id: string;
  status: "pending" | "processing" | "completed" | "failed";
  progress: number;
  frames_total: number | null;
  frames_done: number | null;
  fps: number | null;
  objects_detected: number;
  eta_seconds: number | null;
  error: string | null;
}

export interface User {
  id: string;
  name: string;
  email: string;
  avatar: string | null;
  role: "USER" | "ADMIN";
  email_verified: boolean;
  created_at: string;
}

export interface Project {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface ModelInfo {
  id: string;
  name: string;
  version: string;
  framework: string;
  path: string;
  status: "available" | "active" | "disabled";
  accuracy_map: number | null;
  classes_count: number | null;
  inference_speed_fps: number | null;
  created_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  meta: { request_id: string };
  error?: { code: string; message: string };
}

export interface AnalyticsSummary {
  total_detections: number;
  total_objects: number;
  unique_classes: number;
  avg_confidence: number;
  avg_fps: number;
  avg_latency_ms: number;
  active_sessions: number;
}

export interface TimeseriesPoint {
  date: string;
  detections: number;
  objects: number;
}

export interface ClassDistribution {
  class_name: string;
  count: number;
}

export interface ConfidenceBin {
  bin: string;
  count: number;
}

export interface PerformancePoint {
  date: string;
  avg_fps: number;
  avg_latency_ms: number;
}