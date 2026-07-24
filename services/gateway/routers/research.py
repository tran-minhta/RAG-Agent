"""
RAG-ALL: Gateway Router - Research
Deep research endpoints.
Routes to Research Service for web crawling and analysis.
"""

import uuid
from fastapi import APIRouter, HTTPException
from httpx import AsyncClient

from shared.config.settings import settings
from shared.models.chat import DeepResearchRequest, DeepResearchResult
from shared.utils.logger import gateway_logger as logger

router = APIRouter()


@router.post("/", response_model=DeepResearchResult)
async def start_research(request: DeepResearchRequest) -> DeepResearchResult:
    """
    Bắt đầu deep research.
    Pipeline: Query Planning → Search → Crawl → Analyze → Synthesize

    Depth Levels:
      1 - Shallow: Quick overview (1-10 pages, 1-2 min)
      2 - Moderate: Detailed research (10-50 pages, 5-10 min)
      3 - Deep: Comprehensive (50-200 pages, 15-30 min)
      4 - Exhaustive: Full coverage (200-500 pages, 30-60 min)
      5 - Adaptive: AI decides when to stop
    """
    research_id = str(uuid.uuid4())
    logger.info(
        f"Starting research: id={research_id}, topic={request.topic[:50]}..., "
        f"depth={request.depth_level}"
    )

    try:
        async with AsyncClient(timeout=600.0) as client:
            response = await client.post(
                f"{settings.research_service_url}/research",
                json={
                    "research_id": research_id,
                    "topic": request.topic,
                    "sub_topics": request.sub_topics,
                    "depth_level": request.depth_level,
                    "max_pages": request.max_pages,
                    "source_types": request.source_types,
                    "language": request.language,
                    "output_format": request.output_format,
                    "citation_style": request.citation_style,
                },
            )

            if response.status_code == 200:
                return DeepResearchResult(**response.json())
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Research failed: {response.text}"
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Research error: {e}")
        raise HTTPException(status_code=500, detail=f"Research failed: {e}")


@router.get("/{research_id}")
async def get_research_status(research_id: str):
    """Kiểm tra trạng thái research."""
    try:
        async with AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{settings.research_service_url}/research/{research_id}"
            )
            if response.status_code == 200:
                return response.json()
            raise HTTPException(status_code=404, detail="Research not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{research_id}/export")
async def export_research(
    research_id: str,
    format: str = "markdown",
    citation_style: str = "apa",
):
    """Export research report."""
    try:
        async with AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{settings.research_service_url}/research/{research_id}/export",
                json={"format": format, "citation_style": citation_style},
            )
            if response.status_code == 200:
                return response.json()
            raise HTTPException(status_code=400, detail="Export failed")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/depth-levels")
async def get_depth_levels():
    """Liệt kê các depth levels có sẵn."""
    return {
        "levels": [
            {
                "level": 1,
                "name": "Shallow",
                "max_pages": 10,
                "time_estimate": "1-2 minutes",
                "description": "Quick overview, suitable for simple questions",
            },
            {
                "level": 2,
                "name": "Moderate",
                "max_pages": 50,
                "time_estimate": "5-10 minutes",
                "description": "Detailed research for moderate complexity",
            },
            {
                "level": 3,
                "name": "Deep",
                "max_pages": 200,
                "time_estimate": "15-30 minutes",
                "description": "Comprehensive multi-source analysis",
            },
            {
                "level": 4,
                "name": "Exhaustive",
                "max_pages": 500,
                "time_estimate": "30-60 minutes",
                "description": "Full domain coverage",
            },
            {
                "level": 5,
                "name": "Adaptive",
                "max_pages": 300,
                "time_estimate": "Variable (5-30 minutes)",
                "description": "AI decides when enough info gathered",
            },
        ]
    }
