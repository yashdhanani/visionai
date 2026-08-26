FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set environment to production
ENV APP_ENV=production

# Copy requirements first for better layer caching
COPY apps/api/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY apps/api/ .

# Create non-root user for security
RUN useradd -m -u 1000 visionai && chown -R visionai:visionai /app
USER visionai

EXPOSE 8001

# Run database migrations and start application
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8001 --workers 4"]