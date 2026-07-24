"""
RAG-ALL: Web Search Tool
Multi-source web search cho Agent.
"""

from shared.config.settings import settings
from shared.utils.logger import agent_logger as logger


class WebSearchTool:
    """Multi-source web search tool."""

    def __init__(self):
        pass

    async def search(
        self,
        query: str,
        max_results: int = 5,
        sources: list[str] = None,
    ) -> list[dict]:
        """
        Search web using multiple sources.

        Sources:
          - DuckDuckGo (free, no API key)
          - ArXiv (academic papers)
          - PubMed (biomedical)
          - Semantic Scholar (AI/CS papers)
        """
        if sources is None:
            sources = ["duckduckgo"]

        all_results = []

        # DuckDuckGo search
        if "duckduckgo" in sources:
            try:
                from duckduckgo_search import DDGS
                ddgs = DDGS()
                results = ddgs.text(query, max_results=max_results)
                for r in results:
                    all_results.append({
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "snippet": r.get("body", ""),
                        "source": "duckduckgo",
                    })
                logger.info(f"DuckDuckGo: {len(results)} results")
            except Exception as e:
                logger.warning(f"DuckDuckGo failed: {e}")

        # ArXiv search
        if "arxiv" in sources:
            try:
                import arxiv
                search = arxiv.Search(
                    query=query,
                    max_results=max_results,
                    sort_by=arxiv.SortCriterion.Relevance,
                )
                for result in search.results():
                    all_results.append({
                        "title": result.title,
                        "url": result.entry_id,
                        "snippet": result.summary[:300],
                        "source": "arxiv",
                        "authors": [a.name for a in result.authors],
                        "published": str(result.published.date()),
                    })
                logger.info(f"ArXiv: completed search")
            except Exception as e:
                logger.warning(f"ArXiv failed: {e}")

        # Semantic Scholar search
        if "semantic_scholar" in sources:
            try:
                import requests
                resp = requests.get(
                    "https://api.semanticscholar.org/graph/v1/paper/search",
                    params={
                        "query": query,
                        "limit": max_results,
                        "fields": "title,abstract,url,year,authors",
                    },
                    timeout=10,
                )
                if resp.ok:
                    data = resp.json()
                    for paper in data.get("data", []):
                        all_results.append({
                            "title": paper.get("title", ""),
                            "url": paper.get("url", ""),
                            "snippet": paper.get("abstract", "")[:300] if paper.get("abstract") else "",
                            "source": "semantic_scholar",
                            "year": paper.get("year"),
                            "authors": [a.get("name", "") for a in paper.get("authors", [])],
                        })
                    logger.info(f"Semantic Scholar: {len(data.get('data', []))} results")
            except Exception as e:
                logger.warning(f"Semantic Scholar failed: {e}")

        return all_results
