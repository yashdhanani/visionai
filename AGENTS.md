# VisionAI - Agent Documentation

## Project Overview

VisionAI is a production-grade real-time computer vision platform.

## Development Environment

- Python 3.11 for backend
- Node.js 20 for frontend
- Docker for containerization

## Key Directories

- `apps/api/` - FastAPI backend
- `apps/web/` - Next.js frontend
- `ml/` - Model files and inference code
- `docs/` - Documentation

## Useful Commands

```bash
# Backend
cd apps/api
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd apps/web
npm install
npm run dev
```

## Testing

```bash
# Backend
pytest tests/

# Frontend
npm run lint
npx tsc --noEmit
```

## Deployment

```bash
docker-compose up -d
```