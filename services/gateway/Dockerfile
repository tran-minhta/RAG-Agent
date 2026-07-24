# =============================================================================
# RAG-ALL: Gateway Service Dockerfile
# =============================================================================

FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy shared modules first (for caching)
COPY shared/ /app/shared/

# Copy gateway service
COPY services/gateway/ /app/services/gateway/

# Install Python dependencies
COPY pyproject.toml /app/
RUN pip install --no-cache-dir fastapi uvicorn httpx pydantic pydantic-settings python-multipart

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Run
CMD ["python", "-m", "uvicorn", "services.gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]
