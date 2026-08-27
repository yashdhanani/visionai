"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Copy, Check, ExternalLink } from "lucide-react";
import { useToast } from "@/components/ui/toast";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "https://visionai-236r.onrender.com";

const endpoints = [
  { method: "POST", path: "/api/v1/auth/register", desc: "Register a new user" },
  { method: "POST", path: "/api/v1/auth/login", desc: "Login and get access token" },
  { method: "POST", path: "/api/v1/auth/refresh", desc: "Refresh access token" },
  { method: "GET", path: "/api/v1/auth/me", desc: "Get current user profile" },
  { method: "POST", path: "/api/v1/auth/change-password", desc: "Change password" },
  { method: "POST", path: "/api/v1/auth/api-keys", desc: "Create an API key (vk_live_...)" },
  { method: "GET", path: "/api/v1/auth/api-keys", desc: "List API keys" },
  { method: "DELETE", path: "/api/v1/auth/api-keys/:id", desc: "Revoke an API key" },
  { method: "POST", path: "/api/v1/projects", desc: "Create a project" },
  { method: "GET", path: "/api/v1/projects", desc: "List projects" },
  { method: "GET", path: "/api/v1/projects/:id", desc: "Get project details" },
  { method: "PATCH", path: "/api/v1/projects/:id", desc: "Update project" },
  { method: "DELETE", path: "/api/v1/projects/:id", desc: "Delete project" },
  { method: "POST", path: "/api/v1/detections/image", desc: "Run image detection (YOLO, Face, Pose, Plate)" },
  { method: "POST", path: "/api/v1/detections/video", desc: "Start video processing" },
  { method: "GET", path: "/api/v1/detections", desc: "List detections with filters" },
  { method: "GET", path: "/api/v1/detections/:id", desc: "Get detection detail" },
  { method: "GET", path: "/api/v1/detections/:id/status", desc: "Get video processing status" },
  { method: "GET", path: "/api/v1/detections/:id/assets/:kind", desc: "Get original/annotated asset" },
  { method: "DELETE", path: "/api/v1/detections/:id", desc: "Delete detection" },
  { method: "GET", path: "/api/v1/categories", desc: "List 14 specialized detection categories" },
  { method: "GET", path: "/api/v1/models", desc: "List loaded ML models" },
  { method: "GET", path: "/api/v1/models/active", desc: "Get active model" },
  { method: "POST", path: "/api/v1/models/:id/activate", desc: "Activate model (admin)" },
  { method: "GET", path: "/api/v1/analytics/summary", desc: "Analytics summary" },
  { method: "GET", path: "/api/v1/analytics/timeseries", desc: "Detection timeseries" },
  { method: "GET", path: "/api/v1/analytics/classes", desc: "Class distribution" },
  { method: "GET", path: "/api/v1/analytics/performance", desc: "FPS & latency trend" },
  { method: "WS", path: "/api/v1/detect/live", desc: "WebSocket live webcam / RTSP streaming" },
  { method: "GET", path: "/api/v1/health", desc: "Health check & diagnostics" },
];

const methodColors: Record<string, string> = {
  GET: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-300",
  POST: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300",
  PATCH: "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-300",
  DELETE: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300",
  WS: "bg-violet-100 text-violet-800 dark:bg-violet-900 dark:text-violet-300",
};

const codeExamples = {
  python_rest: `import requests

API_KEY = "vk_live_your_api_key_here"  # Get from Settings -> API Keys
BASE_URL = "${API_BASE}/api/v1"

# 1. Detect Objects in Image
with open("test.jpg", "rb") as f:
    resp = requests.post(
        f"{BASE_URL}/detections/image",
        headers={"Authorization": f"Bearer {API_KEY}"},
        files={"file": f},
        data={"project_id": "your-project-id", "confidence": 0.35}
    )
    data = resp.json()["data"]
    print(f"Detected {data['object_count']} objects in {data['inference_time_ms']}ms:")
    for obj in data["objects"]:
        print(f" - {obj['class_name']} ({obj['confidence']:.1%}) at {obj['bbox']}")`,

  python_ws: `import cv2, base64, json, asyncio, websockets

API_KEY = "vk_live_your_api_key_here"
WS_URL = "ws://localhost:8001/api/v1/detect/live?api_key=" + API_KEY + "&model=face"

async def live_stream():
    cap = cv2.VideoCapture(0)
    async with websockets.connect(WS_URL) as ws:
        init_msg = json.loads(await ws.recv())
        print("Connected to VisionAI:", init_msg)
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break
            
            # Encode frame to JPEG base64
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            b64_frame = base64.b64encode(buffer).decode('utf-8')
            
            await ws.send(json.dumps({
                "type": "frame", "seq": 1, "ts": 1000,
                "width": frame.shape[1], "height": frame.shape[0],
                "jpeg_b64": b64_frame
            }))
            
            res = json.loads(await ws.recv())
            if res.get("type") == "detection":
                print(f"Live Detections: {len(res['detections'])}, FPS: {res['performance']['fps']:.1f}")

asyncio.run(live_stream())`,

  javascript: `// Connect VisionAI to any Web or Node.js application
const API_KEY = "vk_live_your_api_key_here";
const BASE_URL = "${API_BASE}/api/v1";

// 1. REST Detection
async function detectImage(fileBlob, projectId) {
  const formData = new FormData();
  formData.append("file", fileBlob);
  formData.append("project_id", projectId);
  formData.append("confidence", "0.35");

  const response = await fetch(\`\${BASE_URL}/detections/image\`, {
    method: "POST",
    headers: { "Authorization": \`Bearer \${API_KEY}\` },
    body: formData,
  });
  const json = await response.json();
  return json.data;
}

// 2. WebSocket Live Stream
function connectLiveStream(onDetections) {
  const ws = new WebSocket(\`ws://localhost:8001/api/v1/detect/live?api_key=\${API_KEY}&model=face\`);
  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.type === "detection") {
      onDetections(msg.detections, msg.performance);
    }
  };
  return ws;
}`,

  curl: `# Image Detection
curl -X POST \\
  ${API_BASE}/api/v1/detections/image \\
  -H "Authorization: Bearer vk_live_your_api_key_here" \\
  -F "file=@sample.jpg" \\
  -F "project_id=your-project-id" \\
  -F "confidence=0.35"

# List Categories
curl -H "Authorization: Bearer vk_live_your_api_key_here" \\
  ${API_BASE}/api/v1/categories`,
};

export default function APIDocsPage() {
  const [activeTab, setActiveTab] = useState("python_rest");
  const [copied, setCopied] = useState<string | null>(null);
  const { success } = useToast();

  const copyCode = (key: string, code: string) => {
    navigator.clipboard.writeText(code);
    setCopied(key);
    success("Copied to clipboard");
    setTimeout(() => setCopied(null), 2000);
  };

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">API Documentation</h1>
          <p className="text-sm text-zinc-500 mt-1">REST API and WebSocket reference</p>
        </div>
        <Button variant="outline" size="sm" onClick={() => window.open(`${API_BASE}/docs`, "_blank")}>
          <ExternalLink className="h-4 w-4 mr-1" /> Swagger UI
        </Button>
      </div>

      {/* Authentication */}
      <Card>
        <CardHeader><CardTitle className="text-sm">Authentication</CardTitle></CardHeader>
        <CardContent className="text-sm text-zinc-600 dark:text-zinc-400 space-y-2">
          <p>All API endpoints require authentication via Bearer token in the Authorization header:</p>
          <code className="block bg-zinc-100 dark:bg-zinc-800 p-3 rounded-lg text-xs">
            Authorization: Bearer your_access_token_or_api_key
          </code>
          <p>API keys start with <code className="bg-zinc-100 dark:bg-zinc-800 px-1 rounded">vk_live_</code> and can be created in Settings.</p>
        </CardContent>
      </Card>

      {/* Endpoints */}
      <Card>
        <CardHeader><CardTitle className="text-sm">Endpoints</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-1">
            {endpoints.map((ep, i) => (
              <div key={i} className="flex items-center gap-3 py-2 border-b border-zinc-100 dark:border-zinc-800 last:border-0">
                <span className={`text-xs font-mono font-bold px-2 py-0.5 rounded ${methodColors[ep.method]}`}>{ep.method}</span>
                <code className="text-sm font-mono flex-1">{ep.path}</code>
                <span className="text-xs text-zinc-500 hidden md:block">{ep.desc}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Code Examples */}
      <Card>
        <CardHeader><CardTitle className="text-sm">Code Examples</CardTitle></CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList>
              <TabsTrigger value="python_rest">Python (REST)</TabsTrigger>
              <TabsTrigger value="python_ws">Python (Live Stream)</TabsTrigger>
              <TabsTrigger value="javascript">JavaScript / Node.js</TabsTrigger>
              <TabsTrigger value="curl">cURL</TabsTrigger>
            </TabsList>
            <TabsContent value="python_rest">
              <div className="relative">
                <pre className="bg-zinc-100 dark:bg-zinc-800 p-4 rounded-lg text-xs overflow-x-auto">{codeExamples.python_rest}</pre>
                <Button variant="ghost" size="icon" className="absolute top-2 right-2 h-7 w-7" onClick={() => copyCode("python_rest", codeExamples.python_rest)}>
                  {copied === "python_rest" ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                </Button>
              </div>
            </TabsContent>
            <TabsContent value="python_ws">
              <div className="relative">
                <pre className="bg-zinc-100 dark:bg-zinc-800 p-4 rounded-lg text-xs overflow-x-auto">{codeExamples.python_ws}</pre>
                <Button variant="ghost" size="icon" className="absolute top-2 right-2 h-7 w-7" onClick={() => copyCode("python_ws", codeExamples.python_ws)}>
                  {copied === "python_ws" ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                </Button>
              </div>
            </TabsContent>
            <TabsContent value="javascript">
              <div className="relative">
                <pre className="bg-zinc-100 dark:bg-zinc-800 p-4 rounded-lg text-xs overflow-x-auto">{codeExamples.javascript}</pre>
                <Button variant="ghost" size="icon" className="absolute top-2 right-2 h-7 w-7" onClick={() => copyCode("javascript", codeExamples.javascript)}>
                  {copied === "javascript" ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                </Button>
              </div>
            </TabsContent>
            <TabsContent value="curl">
              <div className="relative">
                <pre className="bg-zinc-100 dark:bg-zinc-800 p-4 rounded-lg text-xs overflow-x-auto">{codeExamples.curl}</pre>
                <Button variant="ghost" size="icon" className="absolute top-2 right-2 h-7 w-7" onClick={() => copyCode("curl", codeExamples.curl)}>
                  {copied === "curl" ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                </Button>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* WebSocket */}
      <Card>
        <CardHeader><CardTitle className="text-sm">WebSocket — Live Detection</CardTitle></CardHeader>
        <CardContent className="text-sm space-y-3">
          <code className="block bg-zinc-100 dark:bg-zinc-800 p-3 rounded-lg text-xs">
            ws://{API_BASE.replace("http://", "").replace("https://", "")}/api/v1/detect/live?token=your_jwt_token
          </code>
          <p className="text-zinc-600 dark:text-zinc-400">Send frames as JSON messages with base64-encoded JPEG. Receive detection results with bounding boxes, performance metrics, and object counts.</p>
          <div className="bg-zinc-100 dark:bg-zinc-800 p-4 rounded-lg text-xs space-y-2">
            <p className="font-medium">Client → Server:</p>
            <pre>{`{"type":"frame","seq":1,"ts":123456789,"width":640,"height":360,"jpeg_b64":"..."}`}</pre>
            <p className="font-medium">Server → Client:</p>
            <pre>{`{"type":"detection","seq":1,"detections":[{"class_name":"person","confidence":0.94,"bbox":{"x":120,"y":80,"width":220,"height":410}}],"performance":{"fps":48,"latency_ms":21},"count":1}`}</pre>
          </div>
        </CardContent>
      </Card>

      {/* Response Format */}
      <Card>
        <CardHeader><CardTitle className="text-sm">Response Format</CardTitle></CardHeader>
        <CardContent className="text-sm space-y-3">
          <div>
            <p className="font-medium mb-1">Success:</p>
            <pre className="bg-zinc-100 dark:bg-zinc-800 p-3 rounded-lg text-xs">{"{"}"success": true, "data": {"{}"}, "meta": {"{"}"request_id": "abc123"{"}"}{"}"}</pre>
          </div>
          <div>
            <p className="font-medium mb-1">Error:</p>
            <pre className="bg-zinc-100 dark:bg-zinc-800 p-3 rounded-lg text-xs">{"{"}"success": false, "error": {"{"}"code": "INVALID_FILE", "message": "Unsupported format"{"}"}{"}"}</pre>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}