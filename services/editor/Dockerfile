# =============================================================================
# RAG-ALL: Editor Service Dockerfile
# =============================================================================

FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy shared modules first (for caching)
COPY shared/ /app/shared/

# Copy editor service
COPY services/editor/ /app/services/editor/

# Install Python dependencies
COPY pyproject.toml /app/
RUN pip install --no-cache-dir \
    fastapi uvicorn httpx \
    pydantic pydantic-settings python-dotenv jinja2

# Expose port
EXPOSE 8009

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8009/health || exit 1

# Run
CMD ["python", "-m", "uvicorn", "services.editor.main:app", "--host", "0.0.0.0", "--port", "8009"]
