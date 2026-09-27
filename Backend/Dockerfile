# Multi-stage Dockerfile for ContentForge AI / DocLink Backend

# ==========================================
# Stage 1: Build virtual environment & wheels
# ==========================================
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build tools and development libraries needed for compiling packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    build-essential \
    libtesseract-dev \
    libleptonica-dev \
    && rm -rf /var/lib/apt/lists/*

# Create a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements file
COPY requirements.txt .

# Install CPU-only torch first to avoid heavy CUDA wheels, then install all requirements
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt transformers peft

# ==========================================
# Stage 2: Final lightweight runtime image
# ==========================================
FROM python:3.11-slim AS runner

# CUDA GPU Note:
# To use CUDA acceleration instead of CPU:
# 1. Change base image to: nvidia/cuda:12.1.0-runtime-ubuntu22.04 with python3.11
# 2. Remove --index-url https://download.pytorch.org/whl/cpu in builder stage
# 3. Enable nvidia runtime in docker-compose.yml (deploy.resources.reservations.devices)

WORKDIR /app/Backend

# Install runtime dependencies (tesseract-ocr for OCR processing, ffmpeg for audio/video, curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    ffmpeg \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy virtualenv from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/app/Backend:/app"
ENV PYTHONUNBUFFERED=1

# HuggingFace & Torch cache locations (mapped to volume for persistence)
ENV HF_HOME=/app/Backend/storage/hf_cache
ENV TORCH_HOME=/app/Backend/storage/torch_cache

# Copy backend application source code
COPY . /app/Backend

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
