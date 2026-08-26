# VisionAI API Documentation

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

### JWT Tokens

```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name": "User", "email": "user@example.com", "password": "Pass1234!"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "Pass1234!"}'
```

### API Keys

```bash
# Create API key
curl -X POST http://localhost:8000/api/v1/auth/api-keys \
  -H "Authorization: Bearer YOUR_JWT" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Integration"}'

# Use API key for detection
curl -X POST http://localhost:8000/api/v1/detections/image \
  -H "Authorization: Bearer vk_live_..." \
  -F "file=@image.jpg" \
  -F "project_id=default"
```

## Endpoints

### Auth

| Method | Path | Description |
|--------|------|-------------|
| POST | /auth/register | Register new user |
| POST | /auth/login | Login |
| POST | /auth/refresh | Refresh access token |
| GET | /auth/me | Current user profile |
| POST | /auth/change-password | Change password |
| POST | /auth/api-keys | Create API key |
| GET | /auth/api-keys | List API keys |
| DELETE | /auth/api-keys/:id | Revoke API key |

### Projects

| Method | Path | Description |
|--------|------|-------------|
| POST | /projects | Create project |
| GET | /projects | List projects |
| GET | /projects/:id | Get project |
| PATCH | /projects/:id | Update project |
| DELETE | /projects/:id | Delete project |

### Detections

| Method | Path | Description |
|--------|------|-------------|
| POST | /detections/image | Image detection (multipart) |
| POST | /detections/video | Start video processing |
| GET | /detections | List detections (paginated) |
| GET | /detections/:id | Detection detail |
| GET | /detections/:id/status | Video processing status |
| GET | /detections/:id/assets/:kind | Get original/annotated |
| DELETE | /detections/:id | Delete detection |

### Models

| Method | Path | Description |
|--------|------|-------------|
| GET | /models | List models |
| GET | /models/active | Active model |
| POST | /models/:id/activate | Activate (admin) |
| POST | /models/:id/deactivate | Deactivate (admin) |

### Analytics

| Method | Path | Description |
|--------|------|-------------|
| GET | /analytics/summary | Summary stats |
| GET | /analytics/timeseries | Detection timeseries |
| GET | /analytics/classes | Class distribution |
| GET | /analytics/confidence | Confidence histogram |
| GET | /analytics/performance | FPS/latency trend |
| GET | /analytics/hourly | Hourly activity |

### WebSocket

```
ws://localhost:8000/api/v1/detect/live?token=JWT_TOKEN
```

### Health

| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Full health check |
| GET | /health/live | Liveness probe |
| GET | /health/ready | Readiness probe |