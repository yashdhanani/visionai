# VisionAI Architecture

## Overview

VisionAI is a full-stack computer vision platform built with a modern, scalable architecture.

## Components

### Frontend (Next.js)
- React with TypeScript
- Tailwind CSS + shadcn/ui
- WebSocket client for real-time video
- Category-driven UI
- Diagnostics dashboard

### Backend (FastAPI)
- Python 3.11
- FastAPI for REST + WebSocket
- SQLAlchemy ORM + PostgreSQL
- Redis for caching and session state
- Pydantic for data validation

### ML Layer
- Ultralytics YOLO for detection
- ByteTrack / BoT-SORT for tracking
- Tesseract OCR for number plates
- Face detection and embedding

## Data Flow

1. User selects category and starts camera
2. Browser captures frames, sends via WebSocket
3. Backend runs inference, tracking, and events
4. Results streamed back via WebSocket
5. Frontend renders bounding boxes and metrics

## Deployment

- Docker containers
- GitHub Actions CI/CD
- Optional: NVIDIA GPU for inference

## Security

- JWT authentication
- Role-based access control
- API key support
- Rate limiting
- Audit logging

See [security.md](security.md) for details.