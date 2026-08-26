# VisionAI

### Production-grade real-time computer vision & video intelligence platform.

[Live Demo](https://your-live-demo.com) | [API Docs](https://your-api-docs.com) | [Architecture](docs/architecture.md) | [Demo Video](https://youtu.be/your-demo)

## What it does

VisionAI is a full-stack computer vision platform that enables real-time object detection, tracking, people counting, number plate recognition, face detection, and more. It is built for production with a focus on performance, scalability, and developer experience.

## Architecture

See [architecture diagram](docs/architecture.md).

## Supported AI Capabilities

- Object Detection (YOLO)
- Multi-Object Tracking (ByteTrack, BoT-SORT)
- People Counting
- Vehicle Analytics
- Number Plate Recognition + OCR
- Face Detection
- Attendance (Face Verification)
- Pose Estimation
- Safety Monitoring
- Industrial Inspection
- Custom Models

## Real-time Pipeline

Browser Camera → WebSocket → FastAPI → Model Inference → Tracking/OCR → Events → WebSocket → Canvas Overlay

## ML Evaluation

See [evaluation docs](docs/evaluation.md).

## Benchmarks

See [benchmarks docs](docs/benchmarks.md).

## Deployment

See [deployment docs](docs/deployment.md).

## Security

See [security docs](docs/security.md).

## Screenshots

![Dashboard](docs/screenshots/dashboard.png)

## Demo

1. Open the app
2. Select a category (e.g., People Counting)
3. Start camera
4. See detections in real-time
5. Open diagnostics to verify performance

## Roadmap

- [x] Real-time detection
- [x] Tracking
- [x] People counting
- [x] Number plate + OCR
- [x] Face detection
- [x] Attendance
- [x] Events & Rules
- [x] Diagnostics
- [x] Docker
- [ ] Model Registry (MLflow)
- [ ] Benchmarking
- [ ] Observability (OpenTelemetry)

## 👤 Author & Support

**Yash Dhanani** — AI/ML Engineer

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Yash%20Dhanani-0077B5?style=flat-square&logo=linkedin)](https://www.linkedin.com/in/yashdhanani/)
[![GitHub](https://img.shields.io/badge/GitHub-yashdhanani-181717?style=flat-square&logo=github)](https://github.com/yashdhanani)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-dhananiyash-FFDD00?style=flat-square&logo=buy-me-a-coffee&logoColor=black)](https://www.buymeacoffee.com/dhananiyash)

<br/>

<a href="https://www.buymeacoffee.com/dhananiyash" target="_blank">
  <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 48px !important;width: 174px !important;" />
</a>

---

## License

MIT