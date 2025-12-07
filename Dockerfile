# Production Dockerfile for SmartHR360 Backend

FROM python:3.12-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Build dependencies for wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --prefix /install -r requirements.txt


FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy built site-packages from builder stage
COPY --from=builder /install /usr/local

# Copy project code
COPY . .

# Create necessary directories
RUN mkdir -p staticfiles media

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Health check that succeeds if the app is responding (4xx treated as up, 5xx/down treated as unhealthy)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 CMD ["python", "-c", "import sys, urllib.request, urllib.error;\ntry:\n    resp = urllib.request.urlopen('http://localhost:8000/', timeout=5)\n    code = resp.getcode()\n    sys.exit(0 if code < 500 else 1)\nexcept urllib.error.HTTPError as exc:\n    sys.exit(0 if exc.code < 500 else 1)\nexcept Exception:\n    sys.exit(1)"]

# Start command (can be overridden by docker-compose)
CMD ["gunicorn", "smarthr360_backend.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--threads", "2", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-"]
