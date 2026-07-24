"""
RAG-ALL: Research Service - Main Application
Deep Browser + Multi-source search cho research chuyên sâu.

Crawl4AI Integration:
  - Deep crawling với depth levels 1-5
  - Parallel crawling
  - Content extraction & cleaning
  - Source verification
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any

from shared.config.settings import settings
from shared.models.document import DepthLevel
from shared.models.agent import CrawlStrategy, CrawledPage
from shared.utils.logger import research_logger as logger


# =============================================================================
# Lifespan
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting Research Service...")
    logger.info(f"   Crawl4AI: {settings.crawl4ai_url}")
    logger.info(f"   Max depth: {settings.default_depth_level}")
    yield
    logger.info("🔄 Shutting down Research Service...")


# =============================================================================
# FastAPI App
# =============================================================================

app = FastAPI(
    title="RAG-ALL Research Service",
    description="Deep Browser + Multi-source academic search",
    version="0.1.0",
    lifespan=lifespan,
)


# =============================================================================
# Request/Response Models
# =============================================================================

class ResearchRequest(BaseModel):
    topic: str
    depth_level: int = 2
    max_pages: int = 50
    sources: list[str] = ["arxiv", "pubmed", "semantic_scholar", "web"]
    strategy: str = "breadth_first"


class CrawledPageResponse(BaseModel):
    url: str
    title: str
    content: str
    depth: int
    source: str
    relevance_score: float = 0.0
    metadata: dict = {}


class ResearchSessionResponse(BaseModel):
    session_id: str
    topic: str
    depth_level: int
    pages_crawled: int
    status: str
    pages: list[CrawledPageResponse] = []


# =============================================================================
# Depth Configurations
# =============================================================================

DEPTH_CONFIGS = {
    1: {"max_pages": 10, "timeout": 120, "description": "Shallow - 10 pages, 1-2 min"},
    2: {"max_pages": 50, "timeout": 600, "description": "Moderate - 50 pages, 5-10 min"},
    3: {"max_pages": 200, "timeout": 1800, "description": "Deep - 200 pages, 15-30 min"},
    4: {"max_pages": 500, "timeout": 3600, "description": "Exhaustive - 500 pages, 30-60 min"},
    5: {"max_pages": 1000, "timeout": 7200, "description": "Adaptive - AI-decided"},
}


# =============================================================================
# Crawl4AI Client
# =============================================================================

class Crawl4AIClient:
    """Client for Crawl4AI microservice."""

    def __init__(self):
        self.base_url = settings.crawl4ai_url

    async def crawl(
        self,
        urls: list[str],
        depth: int = 2,
        strategy: str = "breadth_first",
    ) -> list[dict]:
        """
        Crawl URLs using Crawl4AI.

        Args:
            urls: Starting URLs
            depth: Crawl depth
            strategy: Crawl strategy

        Returns:
            List of crawled pages
        """
        import httpx

        try:
            async with httpx.AsyncClient(timeout=300) as client:
                response = await client.post(
                    f"{self.base_url}/crawl",
                    json={
                        "urls": urls,
                        "depth": depth,
                        "strategy": strategy,
                    },
                )
                if response.status_code == 200:
                    return response.json().get("pages", [])
                else:
                    logger.warning(f"Crawl4AI returned {response.status_code}")
                    return []
        except Exception as e:
            logger.error(f"Crawl4AI error: {e}")
            return []


# =============================================================================
# Academic Search
# =============================================================================

class AcademicSearch:
    """Multi-source academic search."""

    async def search_arxiv(self, query: str, max_results: int = 10) -> list[dict]:
        """Search ArXiv for papers."""
        try:
            import arxiv
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance,
            )
            results = []
            for paper in search.results():
                results.append({
                    "title": paper.title,
                    "url": paper.entry_id,
                    "abstract": paper.summary,
                    "authors": [a.name for a in paper.authors],
                    "published": str(paper.published.date()),
                    "source": "arxiv",
                })
            return results
        except Exception as e:
            logger.warning(f"ArXiv search failed: {e}")
            return []

    async def search_pubmed(self, query: str, max_results: int = 10) -> list[dict]:
        """Search PubMed for biomedical papers."""
        try:
            import requests
            # Search for IDs
            search_resp = requests.get(
                "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
                params={
                    "db": "pubmed",
                    "term": query,
                    "retmax": max_results,
                    "retmode": "json",
                },
                timeout=10,
            )
            if not search_resp.ok:
                return []

            ids = search_resp.json().get("esearchresult", {}).get("idlist", [])
            if not ids:
                return []

            # Fetch details
            detail_resp = requests.get(
                "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
                params={
                    "db": "pubmed",
                    "id": ",".join(ids),
                    "retmode": "json",
                },
                timeout=10,
            )
            if not detail_resp.ok:
                return []

            results = []
            for uid in ids:
                article = detail_resp.json().get("result", {}).get(uid, {})
                if article:
                    results.append({
                        "title": article.get("title", ""),
                        "url": f"https://pubmed.ncbi.nlm.nih.gov/{uid}/",
                        "abstract": article.get("title", ""),  # Summary not in esummary
                        "authors": [a.get("name", "") for a in article.get("authors", [])],
                        "published": article.get("pubdate", ""),
                        "source": "pubmed",
                    })
            return results
        except Exception as e:
            logger.warning(f"PubMed search failed: {e}")
            return []

    async def search_semantic_scholar(self, query: str, max_results: int = 10) -> list[dict]:
        """Search Semantic Scholar."""
        try:
            import requests
            resp = requests.get(
                "https://api.semanticscholar.org/graph/v1/paper/search",
                params={
                    "query": query,
                    "limit": max_results,
                    "fields": "title,abstract,url,year,authors,citationCount",
                },
                timeout=10,
            )
            if not resp.ok:
                return []

            results = []
            for paper in resp.json().get("data", []):
                results.append({
                    "title": paper.get("title", ""),
                    "url": paper.get("url", ""),
                    "abstract": paper.get("abstract", ""),
                    "authors": [a.get("name", "") for a in paper.get("authors", [])],
                    "published": str(paper.get("year", "")),
                    "citation_count": paper.get("citationCount", 0),
                    "source": "semantic_scholar",
                })
            return results
        except Exception as e:
            logger.warning(f"Semantic Scholar search failed: {e}")
            return []


# =============================================================================
# Research Orchestrator
# =============================================================================

class ResearchOrchestrator:
    """Orchestrate deep research across multiple sources."""

    def __init__(self):
        self.crawl4ai = Crawl4AIClient()
        self.academic = AcademicSearch()

    async def research(
        self,
        topic: str,
        depth_level: int,
        sources: list[str],
        max_pages: int,
    ) -> ResearchSessionResponse:
        """
        Conduct deep research on a topic.

        Args:
            topic: Research topic
            depth_level: Depth level (1-5)
            sources: Sources to search
            max_pages: Maximum pages to crawl

        Returns:
            ResearchSessionResponse with all findings
        """
        import uuid
        session_id = str(uuid.uuid4())
        config = DEPTH_CONFIGS.get(depth_level, DEPTH_CONFIGS[2])

        logger.info(f"Starting research: {topic}")
        logger.info(f"  Depth: {depth_level} ({config['description']})")
        logger.info(f"  Sources: {sources}")

        all_pages = []

        # Academic sources
        if "arxiv" in sources:
            arxiv_results = await self.academic.search_arxiv(topic, max_results=min(max_pages, 20))
            for r in arxiv_results:
                all_pages.append(CrawledPage(
                    url=r["url"],
                    title=r["title"],
                    content=r.get("abstract", ""),
                    depth=0,
                    source="arxiv",
                ))

        if "pubmed" in sources:
            pubmed_results = await self.academic.search_pubmed(topic, max_results=min(max_pages, 20))
            for r in pubmed_results:
                all_pages.append(CrawledPage(
                    url=r["url"],
                    title=r["title"],
                    content=r.get("abstract", ""),
                    depth=0,
                    source="pubmed",
                ))

        if "semantic_scholar" in sources:
            ss_results = await self.academic.search_semantic_scholar(topic, max_results=min(max_pages, 20))
            for r in ss_results:
                all_pages.append(CrawledPage(
                    url=r["url"],
                    title=r["title"],
                    content=r.get("abstract", ""),
                    depth=0,
                    source="semantic_scholar",
                ))

        # Web crawling with Crawl4AI
        if "web" in sources and len(all_pages) < max_pages:
            # Get URLs from academic results for deeper crawling
            seed_urls = [p.url for p in all_pages[:5]]
            if seed_urls:
                crawled = await self.crawl4ai.crawl(
                    urls=seed_urls,
                    depth=min(depth_level, 3),
                )
                for c in crawled:
                    all_pages.append(CrawledPage(
                        url=c.get("url", ""),
                        title=c.get("title", ""),
                        content=c.get("content", ""),
                        depth=c.get("depth", 0),
                        source="web",
                    ))

        logger.info(f"Research complete: {len(all_pages)} pages collected")

        return ResearchSessionResponse(
            session_id=session_id,
            topic=topic,
            depth_level=depth_level,
            pages_crawled=len(all_pages),
            status="completed",
            pages=[
                CrawledPageResponse(
                    url=p.url,
                    title=p.title,
                    content=p.content[:500],  # Truncate for response
                    depth=p.depth,
                    source=p.source,
                )
                for p in all_pages[:max_pages]
            ],
        )


# =============================================================================
# Initialize & Endpoints
# =============================================================================

orchestrator = ResearchOrchestrator()


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "research"}


@app.post("/research", response_model=ResearchSessionResponse)
async def start_research(request: ResearchRequest) -> ResearchSessionResponse:
    """Start deep research on a topic."""
    logger.info(f"Research request: {request.topic}")

    if request.depth_level not in DEPTH_CONFIGS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid depth level: {request.depth_level}. Must be 1-5."
        )

    try:
        return await orchestrator.research(
            topic=request.topic,
            depth_level=request.depth_level,
            sources=request.sources,
            max_pages=request.max_pages,
        )
    except Exception as e:
        logger.error(f"Research error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/depth-levels")
async def get_depth_levels():
    """Get available depth levels."""
    return DEPTH_CONFIGS


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)
