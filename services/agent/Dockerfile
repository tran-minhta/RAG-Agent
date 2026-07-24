# =============================================================================
# RAG-ALL: Agent Service Dockerfile
# =============================================================================

FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy shared modules first (for caching)
COPY shared/ /app/shared/

# Copy agent service
COPY services/agent/ /app/services/agent/

# Install Python dependencies
COPY pyproject.toml /app/
RUN pip install --no-cache-dir \
    fastapi uvicorn httpx \
    langchain-core langchain langchain-community langchain-text-splitters langgraph \
    langchain-ollama langchain-google-genai \
    chromadb sentence-transformers \
    duckduckgo-search arxiv semanticscholar requests \
    pydantic pydantic-settings python-dotenv

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Run
CMD ["python", "-m", "uvicorn", "services.agent.main:app", "--host", "0.0.0.0", "--port", "8001"]
