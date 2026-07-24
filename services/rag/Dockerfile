# =============================================================================
# RAG-ALL: RAG Service Dockerfile
# =============================================================================

FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy shared modules first (for caching)
COPY shared/ /app/shared/

# Copy RAG service
COPY services/rag/ /app/services/rag/

# Install Python dependencies
COPY pyproject.toml /app/
RUN pip install --no-cache-dir \
    fastapi uvicorn httpx \
    chromadb sentence-transformers \
    pydantic pydantic-settings python-dotenv numpy

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Run
CMD ["python", "-m", "uvicorn", "services.rag.main:app", "--host", "0.0.0.0", "--port", "8002"]
