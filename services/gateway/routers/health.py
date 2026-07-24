"""
RAG-ALL: Gateway Router - Health Check + Models
Health check + model listing endpoints.
"""

import httpx
from fastapi import APIRouter

from shared.config.settings import settings
from shared.utils.logger import gateway_logger as logger

router = APIRouter()


@router.get("/")
async def health_check():
    """Health check tat ca services."""
    services = {
        "gateway": {"url": "self", "status": "healthy"},
        "agent": {"url": settings.agent_service_url, "status": "unknown"},
        "rag": {"url": settings.rag_service_url, "status": "unknown"},
        "document": {"url": settings.document_service_url, "status": "unknown"},
        "research": {"url": settings.research_service_url, "status": "unknown"},
        "editor": {"url": settings.editor_service_url, "status": "unknown"},
        "voice": {"url": settings.voice_service_url, "status": "unknown"},
    }

    async with httpx.AsyncClient(timeout=5.0) as client:
        for name, info in services.items():
            if info["url"] == "self":
                continue
            try:
                r = await client.get(f"{info['url']}/health")
                info["status"] = "healthy" if r.status_code == 200 else "unhealthy"
            except Exception:
                info["status"] = "unreachable"

    all_ok = all(s["status"] == "healthy" or s["url"] == "self" for s in services.values())
    return {"status": "healthy" if all_ok else "degraded", "services": services}


@router.get("/models")
async def list_models():
    """Danh sach models co san tu Agent service."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{settings.agent_service_url}/models")
            if r.status_code == 200:
                return r.json()
    except Exception as e:
        logger.warning(f"Cannot fetch models from agent: {e}")

    return {"ollama": [], "gemini": [], "error": "Agent service unreachable"}
