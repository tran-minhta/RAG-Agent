# =============================================================================
# RAG-ALL: Frontend (Chainlit) Dockerfile
# =============================================================================

FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy shared modules first (for caching)
COPY shared/ /app/shared/

# Copy frontend service
COPY services/frontend/ /app/services/frontend/

# Create .chainlit directory
RUN mkdir -p /app/.chainlit

# Install Python dependencies
COPY pyproject.toml /app/
RUN pip install --no-cache-dir \
    chainlit \
    httpx \
    pydantic pydantic-settings python-dotenv

# Expose port
EXPOSE 8005

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8005/ || exit 1

# Run Chainlit
CMD ["python", "-m", "chainlit", "run", "services/frontend/app.py", "--host", "0.0.0.0", "--port", "8005"]
