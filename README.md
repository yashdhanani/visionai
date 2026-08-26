<div align="center">

# ⚡ VisionAI

### Production-Grade Real-Time Computer Vision & Video Intelligence Platform

[![Next.js](https://img.shields.io/badge/Next.js-16.3-black?style=flat-square&logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-00599C?style=flat-square&logo=python)](https://github.com/ultralytics/ultralytics)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.6-EE4C2C?style=flat-square&logo=pytorch)](https://pytorch.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6?style=flat-square&logo=typescript)](https://www.typescriptlang.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-dhananiyash-FFDD00?style=flat-square&logo=buy-me-a-coffee&logoColor=black)](https://www.buymeacoffee.com/dhananiyash)

<p align="center">
  <a href="#-key-features">Key Features</a> •
  <a href="#-supported-vision-categories">14 Vision Tasks</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-api-keys--sdk-integration">API & SDKs</a> •
  <a href="#-support--donations">Support</a>
</p>

---

</div>

## 🌟 Key Features

- ⚡ **Ultra-Fast Real-Time Inference**: Sub-25ms inference latency powered by Apple Silicon GPU (`mps`) & CUDA.
- 🎯 **14 Specialized Computer Vision Pipelines**: Face, pose estimation, number plates + OCR, crowd counting, traffic analysis, safety PPE, and fire detection.
- 🔄 **Live Bi-Directional WebSockets**: Stream camera frames directly with instant HUD bounding box rendering, FPS counters, and latency monitoring.
- 🔑 **Universal API Key System**: Integrate VisionAI into any Python script, Node.js app, mobile application, or IoT camera via `vk_live_...` API keys.
- 🗄️ **Relational Persistence**: Automated database saving for detections, objects, confidence scores, and raw/annotated images with full history inspection.
- 📊 **Real-Time Analytics Dashboard**: Interactive charts tracking detection volume, class distributions, and performance trends.

---

## 🎯 Supported Vision Categories

| # | Task | Features & Capabilities | Model Loaded |
| :-: | :--- | :--- | :---: |
| 1 | **Object Detection** | 80 COCO classes, high-speed multi-tracking | `YOLOv8n` |
| 2 | **People Detection** | Crowd tracking, real-time bounding, occupancy count | `YOLOv8n` |
| 3 | **People Counting** | Bidirectional virtual line in/out counter with peak occupancy | `YOLOv8n` |
| 4 | **Vehicle Detection** | Cars, trucks, buses, motorcycles multi-class tracking | `YOLOv8n` |
| 5 | **Number Plate Detection** | License plate bounding + automated OCR text transcription | `YOLOv8m-Plate` |
| 6 | **Face Detection** | High-precision facial bounding + quality assessment | `YOLOv8n-Face` |
| 7 | **Attendance** | Face verification, presence confirmation, attendance timestamps | `YOLOv8n-Face` |
| 8 | **Pose Detection** | 17 body keypoints with real-time skeleton overlay | `YOLOv8n-Pose` |
| 9 | **Safety Detection** | PPE compliance monitoring and safety hazard logging | `YOLOv8n` |
| 10 | **Zone Monitoring** | Restricted area polygon intrusion detection | `YOLOv8n` |
| 11 | **Fire & Smoke** | Multi-frame temporal confirmation to prevent false alarms | `YOLOv8n-Fire` |
| 12 | **Industrial Inspection** | Quality inspection, anomaly detection, pass/fail reporting | `Inspection` |
| 13 | **OCR / Text Detection** | Text region extraction from signs, packages, and documents | `EasyOCR` |
| 14 | **Traffic Analysis** | 4-approach vehicle counter & adaptive signal countdown | `TrafficSignal` |

---

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/<your-username>/visionai.git
cd visionai
```

### 2. Start Backend (FastAPI)
```bash
cd apps/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/seed.py  # Seed initial admin user & models
uvicorn app.main:app --port 8001 --reload
```

### 3. Start Frontend (Next.js)
```bash
cd apps/web
npm install
npm run dev -- -p 3000
```

- **Frontend:** [http://localhost:3000](http://localhost:3000)
- **Backend API & Swagger:** [http://localhost:8001/docs](http://localhost:8001/docs)

**Default Credentials:** `admin@gmail.com` / `admin123`

---

## 🔑 API Keys & SDK Integration

### Python REST Detection
```python
import requests

API_KEY = "vk_live_your_api_key_here"  # Get from Settings -> API Keys

with open("sample.jpg", "rb") as f:
    resp = requests.post(
        "http://localhost:8001/api/v1/detections/image",
        headers={"Authorization": f"Bearer {API_KEY}"},
        files={"file": f},
        data={"confidence": 0.35, "model_id": "face"}
    )
    print(resp.json()["data"])
```

### Python Real-Time WebSocket Streaming
```python
import cv2, base64, json, asyncio, websockets

API_KEY = "vk_live_your_api_key_here"
WS_URL = f"ws://localhost:8001/api/v1/detect/live?api_key={API_KEY}&model=face"

async def stream():
    cap = cv2.VideoCapture(0)
    async with websockets.connect(WS_URL) as ws:
        await ws.recv()
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break
            _, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            b64 = base64.b64encode(buf).decode('utf-8')
            await ws.send(json.dumps({"type": "frame", "seq": 1, "ts": 1000, "width": frame.shape[1], "height": frame.shape[0], "jpeg_b64": b64}))
            res = json.loads(await ws.recv())
            if res.get("type") == "detection":
                print(f"Live FPS: {res['performance']['fps']:.1f}, Detections: {len(res['detections'])}")

asyncio.run(stream())
```

---

## ☕ Support & Donations

If you find VisionAI helpful, consider supporting the project:

<a href="https://www.buymeacoffee.com/dhananiyash" target="_blank">
  <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" height="40" style="height: 40px; width: auto;" />
</a>

---

## 👤 Author

**Yash Dhanani**  
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Yash%20Dhanani-0077B5?style=flat-square&logo=linkedin)](https://www.linkedin.com/in/yashdhanani/)  
[![GitHub](https://img.shields.io/badge/GitHub-yashdhanani-181717?style=flat-square&logo=github)](https://github.com/yashdhanani)

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).