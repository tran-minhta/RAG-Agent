# =============================================================================
# RAG-ALL: Voice Service Dockerfile
# =============================================================================

FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy shared modules first (for caching)
COPY shared/ /app/shared/

# Copy voice service
COPY services/voice/ /app/services/voice/

# Install Python dependencies
COPY pyproject.toml /app/
RUN pip install --no-cache-dir \
    fastapi uvicorn httpx python-multipart \
    edge-tts faster-whisper \
    pydantic pydantic-settings python-dotenv

# Expose port
EXPOSE 8004

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8004/health || exit 1

# Run
CMD ["python", "-m", "uvicorn", "services.voice.main:app", "--host", "0.0.0.0", "--port", "8004"]
