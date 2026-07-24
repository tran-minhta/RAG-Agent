# =============================================================================
# RAG-ALL: Research Service Dockerfile
# =============================================================================

FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy shared modules first (for caching)
COPY shared/ /app/shared/

# Copy research service
COPY services/research/ /app/services/research/

# Install Python dependencies
COPY pyproject.toml /app/
RUN pip install --no-cache-dir \
    fastapi uvicorn httpx requests \
    crawl4ai duckduckgo-search arxiv semanticscholar \
    pydantic pydantic-settings python-dotenv

# Expose port
EXPOSE 8007

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8007/health || exit 1

# Run
CMD ["python", "-m", "uvicorn", "services.research.main:app", "--host", "0.0.0.0", "--port", "8007"]
