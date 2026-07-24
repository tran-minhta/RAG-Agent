# =============================================================================
# RAG-ALL: Agent Service Dockerfile
# =============================================================================

FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY shared/ /app/shared/
COPY services/agent/ /app/services/agent/

RUN pip install --no-cache-dir \
    fastapi uvicorn httpx \
    chromadb sentence-transformers \
    duckduckgo-search arxiv semanticscholar requests \
    pydantic pydantic-settings python-dotenv

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

CMD ["python", "-m", "uvicorn", "services.agent.main:app", "--host", "0.0.0.0", "--port", "8001"]
