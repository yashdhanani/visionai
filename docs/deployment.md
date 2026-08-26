# Deployment

## Development

```bash
# Start API
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Start Web
cd apps/web
npm install
npm run dev
```

## Production with Docker

```bash
docker-compose up -d
```

## Environment Variables

See `.env.example` for required variables.

## GPU Support

For GPU inference, install NVIDIA Container Toolkit and set `MODEL_DEVICE=cuda`.

## Monitoring

- Health check: `/api/v1/health`
- Diagnostics: `/diagnostics`

## Scaling

- API service can be scaled horizontally
- WebSocket sessions stored in Redis
- Stateless design for inference workers