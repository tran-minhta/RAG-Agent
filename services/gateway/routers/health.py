"""
RAG-ALL: Gateway Router - Health Check
Health check endpoints cho monitoring.
"""

from fastapi import APIRouter
from httpx import AsyncClient

from shared.config.settings import settings
from shared.utils.logger import gateway_logger as logger

router = APIRouter()


@router.get("/")
async def health_check():
    """
    Health check tổng hợp - kiểm tra tất cả services.
    Trả về status của từng service.
    """
    services = {
        "gateway": {"url": "self", "status": "healthy"},
        "agent": {"url": settings.agent_service_url, "status": "unknown"},
        "rag": {"url": settings.rag_service_url, "status": "unknown"},
        "document": {"url": settings.document_service_url, "status": "unknown"},
        "research": {"url": settings.research_service_url, "status": "unknown"},
        "editor": {"url": settings.editor_service_url, "status": "unknown"},
        "voice": {"url": settings.voice_service_url, "status": "unknown"},
    }

    async with AsyncClient(timeout=5.0) as client:
        for service_name, info in services.items():
            if info["url"] == "self":
                continue
            try:
                response = await client.get(f"{info['url']}/health")
                if response.status_code == 200:
                    info["status"] = "healthy"
                else:
                    info["status"] = "unhealthy"
            except Exception as e:
                info["status"] = "unreachable"
                info["error"] = str(e)

    all_healthy = all(s["status"] == "healthy" or s["url"] == "self"
                      for s in services.values())

    return {
        "status": "healthy" if all_healthy else "degraded",
        "services": services,
    }
