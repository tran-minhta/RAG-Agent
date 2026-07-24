# =============================================================================
# RAG-ALL: Accuracy Engine Dockerfile
# =============================================================================

FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy shared modules first (for caching)
COPY shared/ /app/shared/

# Copy accuracy service
COPY services/accuracy/ /app/services/accuracy/

# Install Python dependencies
COPY pyproject.toml /app/
RUN pip install --no-cache-dir \
    fastapi uvicorn httpx \
    pydantic pydantic-settings python-dotenv

# Expose port
EXPOSE 8008

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8008/health || exit 1

# Run
CMD ["python", "-m", "uvicorn", "services.accuracy.main:app", "--host", "0.0.0.0", "--port", "8008"]
