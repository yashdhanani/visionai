FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for OpenCV and image processing
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set environment to production
ENV APP_ENV=production \
    PYTHONUNBUFFERED=1

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Pre-download YOLO weights during build for instant 0ms startup
RUN python3 -c "from ultralytics import YOLO; YOLO('yolov8n.pt'); YOLO('yolov8n-pose.pt')" || true

# Copy application code & models
COPY . .

# Create writable data directories and non-root user
RUN mkdir -p /app/data /app/data/uploads /app/models && \
    useradd -m -u 1000 visionai && \
    chown -R visionai:visionai /app /home/visionai
USER visionai

EXPOSE 8001

# Start FastAPI application
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8001}"]