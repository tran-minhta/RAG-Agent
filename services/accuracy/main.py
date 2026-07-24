"""
RAG-ALL: Accuracy Engine - Main Application
Verification + Citation + Hallucination detection.

Accuracy Levels:
  - Confidence > 0.85: Full answer
  - Confidence 0.60-0.85: Answer + disclaimer
  - Confidence 0.40-0.60: Search more
  - Confidence < 0.40: Refuse + suggest sources

Verification Sources:
  - CrossRef API (DOI verification)
  - PubMed (biomedical papers)
  - arXiv (preprints)
  - Semantic Scholar (AI/CS papers)
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any
import re

from shared.config.settings import settings
from shared.models.agent import (
    Citation,
    VerificationStatus,
    VerificationResult,
)
from shared.utils.logger import agent_logger as logger


# =============================================================================
# Lifespan
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting Accuracy Engine...")
    yield
    logger.info("🔄 Shutting down Accuracy Engine...")


# =============================================================================
# FastAPI App
# =============================================================================

app = FastAPI(
    title="RAG-ALL Accuracy Engine",
    description="Citation verification + Hallucination detection",
    version="0.1.0",
    lifespan=lifespan,
)


# =============================================================================
# Request/Response Models
# =============================================================================

class CitationVerifyRequest(BaseModel):
    citations: list[str]  # List of citation strings to verify
    text: str = ""  # Full text for context


class CitationVerifyResponse(BaseModel):
    verified: list[dict]  # Successfully verified citations
    unverified: list[str]  # Citations that couldn't be verified
    confidence_score: float
    suggestions: list[str] = []


class HallucinationCheckRequest(BaseModel):
    text: str
    sources: list[dict] = []  # Available sources to check against


class HallucinationCheckResponse(BaseModel):
    has_hallucination: bool
    suspicious_claims: list[dict]  # Claims that look like hallucinations
    confidence_score: float
    details: str = ""


# =============================================================================
# Citation Verifier
# =============================================================================

class CitationVerifier:
    """Verify citations against academic databases."""

    def __init__(self):
        pass

    async def verify_citation(self, citation: str) -> dict:
        """
        Verify a single citation.

        Returns:
            {status: verified|unverified|partial, details: str, source: str}
        """
        # Try CrossRef first (DOI verification)
        if "doi" in citation.lower() or "10." in citation:
            result = await self._verify_doi(citation)
            if result:
                return result

        # Try arXiv
        if "arxiv" in citation.lower():
            result = await self._verify_arxiv(citation)
            if result:
                return result

        # Try PubMed
        if "pubmed" in citation.lower() or "pmid" in citation.lower():
            result = await self._verify_pubmed(citation)
            if result:
                return result

        # Try title search
        result = await self._verify_by_title(citation)
        if result:
            return result

        return {
            "status": "unverified",
            "details": "Could not verify citation",
            "source": "none",
        }

    async def _verify_doi(self, citation: str) -> dict | None:
        """Verify DOI via CrossRef."""
        import httpx
        import re

        # Extract DOI
        doi_match = re.search(r'(10\.\d{4,}/[^\s]+)', citation)
        if not doi_match:
            return None

        doi = doi_match.group(1)

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"https://api.crossref.org/works/{doi}")
                if resp.status_code == 200:
                    data = resp.json().get("message", {})
                    return {
                        "status": "verified",
                        "title": data.get("title", [""])[0],
                        "authors": [
                            f"{a.get('given', '')} {a.get('family', '')}"
                            for a in data.get("author", [])
                        ],
                        "journal": data.get("container-title", [""])[0],
                        "year": str(data.get("published-print", {}).get("date-parts", [[""]])[0][0]),
                        "doi": doi,
                        "source": "crossref",
                    }
        except Exception as e:
            logger.warning(f"CrossRef verification failed: {e}")

        return None

    async def _verify_arxiv(self, citation: str) -> dict | None:
        """Verify via ArXiv API."""
        import httpx
        import re

        # Extract ArXiv ID
        arxiv_match = re.search(r'(\d{4}\.\d{4,5})', citation)
        if not arxiv_match:
            return None

        arxiv_id = arxiv_match.group(1)

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"http://export.arxiv.org/api/query",
                    params={"id_list": arxiv_id},
                )
                if resp.status_code == 200 and "<entry>" in resp.text:
                    # Parse XML
                    title_match = re.search(r'<title>(.*?)</title>', resp.text)
                    return {
                        "status": "verified",
                        "title": title_match.group(1) if title_match else "",
                        "arxiv_id": arxiv_id,
                        "source": "arxiv",
                    }
        except Exception as e:
            logger.warning(f"ArXiv verification failed: {e}")

        return None

    async def _verify_pubmed(self, citation: str) -> dict | None:
        """Verify via PubMed API."""
        import httpx
        import re

        pmid_match = re.search(r'PMID:?\s*(\d+)', citation)
        if not pmid_match:
            return None

        pmid = pmid_match.group(1)

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
                    params={
                        "db": "pubmed",
                        "id": pmid,
                        "retmode": "json",
                    },
                )
                if resp.status_code == 200:
                    result = resp.json().get("result", {}).get(pmid, {})
                    if result:
                        return {
                            "status": "verified",
                            "title": result.get("title", ""),
                            "authors": [
                                a.get("name", "")
                                for a in result.get("authors", [])
                            ],
                            "journal": result.get("fulljournalname", ""),
                            "year": result.get("pubdate", ""),
                            "pmid": pmid,
                            "source": "pubmed",
                        }
        except Exception as e:
            logger.warning(f"PubMed verification failed: {e}")

        return None

    async def _verify_by_title(self, citation: str) -> dict | None:
        """Verify by searching title on CrossRef."""
        import httpx

        # Simple title search (first 50 chars)
        title = citation[:50].strip()

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://api.crossref.org/works",
                    params={
                        "query.title": title,
                        "rows": 1,
                    },
                )
                if resp.status_code == 200:
                    items = resp.json().get("message", {}).get("items", [])
                    if items:
                        item = items[0]
                        return {
                            "status": "partial",
                            "title": item.get("title", [""])[0],
                            "doi": item.get("DOI", ""),
                            "source": "crossref_title_search",
                            "note": "Matched by title search",
                        }
        except Exception as e:
            logger.warning(f"Title search verification failed: {e}")

        return None


# =============================================================================
# Hallucination Detector
# =============================================================================

class HallucinationDetector:
    """Detect potential hallucinations in generated text."""

    # Patterns that often indicate hallucinations
    SUSPICIOUS_PATTERNS = [
        r'according to the (?:study|paper|research)',
        r'researchers (?:found|discovered|showed)',
        r'the (?:study|paper) (?:found|showed|demonstrated)',
        r'(?:statistics|data) show',
        r'\d+% of',
        r'published in (?:Nature|Science|Cell|The Lancet)',
    ]

    # Claims that need verification
    FACTUAL_CLAIMS = [
        r'(\d{4})\s*(?:study|paper|research)',
        r'(?:University|Institute) of',
        r'(?:Dr\.|Prof\.)\s+\w+',
        r'\d+\s*(?:percent|%)',
    ]

    def __init__(self):
        pass

    def check_text(
        self,
        text: str,
        sources: list[dict],
    ) -> dict:
        """
        Check text for potential hallucinations.

        Args:
            text: Generated text to check
            sources: Available sources to verify against

        Returns:
            {has_hallucination, suspicious_claims, confidence_score}
        """
        suspicious = []
        confidence = 1.0

        # Check for suspicious patterns
        for pattern in self.SUSPICIOUS_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                suspicious.append({
                    "pattern": pattern,
                    "matches": matches[:3],
                    "reason": "Pattern matches common hallucination markers",
                })
                confidence -= 0.1

        # Check for unverifiable factual claims
        for pattern in self.FACTUAL_CLAIMS:
            claims = re.findall(pattern, text)
            for claim in claims:
                # Check if any source supports this claim
                supported = any(
                    claim.lower() in s.get("content", "").lower()
                    for s in sources
                )
                if not supported:
                    suspicious.append({
                        "claim": claim,
                        "reason": "Factual claim not supported by sources",
                    })
                    confidence -= 0.05

        return {
            "has_hallucination": len(suspicious) > 0,
            "suspicious_claims": suspicious,
            "confidence_score": max(0.0, confidence),
            "details": f"Found {len(suspicious)} suspicious claims",
        }


# =============================================================================
# Confidence Calculator
# =============================================================================

class ConfidenceCalculator:
    """Calculate overall confidence score."""

    def calculate(
        self,
        kb_results: list[dict],
        web_results: list[dict],
        verification_results: list[dict],
        hallucination_check: dict,
    ) -> float:
        """
        Calculate overall confidence score.

        Factors:
          - KB result quality (20%)
          - Web result quality (20%)
          - Citation verification (30%)
          - Hallucination check (30%)
        """
        score = 0.0

        # KB results (20%)
        if kb_results:
            avg_kb = sum(r.get("score", 0) for r in kb_results) / len(kb_results)
            score += avg_kb * 0.2

        # Web results (20%)
        if web_results:
            avg_web = sum(r.get("score", 0) for r in web_results) / len(web_results)
            score += avg_web * 0.2

        # Citation verification (30%)
        if verification_results:
            verified = sum(
                1 for v in verification_results
                if v.get("status") == "verified"
            )
            score += (verified / len(verification_results)) * 0.3
        else:
            score += 0.15  # Neutral if no citations

        # Hallucination check (30%)
        if not hallucination_check.get("has_hallucination", False):
            score += 0.3
        else:
            # Penalize based on severity
            num_suspicious = len(hallucination_check.get("suspicious_claims", []))
            score += max(0, 0.3 - num_suspicious * 0.05)

        return min(1.0, max(0.0, score))


# =============================================================================
# Initialize & Endpoints
# =============================================================================

verifier = CitationVerifier()
detector = HallucinationDetector()
calculator = ConfidenceCalculator()


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "accuracy"}


@app.post("/verify-citations", response_model=CitationVerifyResponse)
async def verify_citations(request: CitationVerifyRequest) -> CitationVerifyResponse:
    """Verify citations against academic databases."""
    verified = []
    unverified = []

    for citation in request.citations:
        result = await verifier.verify_citation(citation)
        if result["status"] == "verified":
            verified.append(result)
        else:
            unverified.append(citation)

    confidence = len(verified) / len(request.citations) if request.citations else 1.0

    return CitationVerifyResponse(
        verified=verified,
        unverified=unverified,
        confidence_score=confidence,
        suggestions=[
            "Check CrossRef for DOI verification",
            "Search PubMed for biomedical papers",
            "Use Semantic Scholar for AI/CS papers",
        ],
    )


@app.post("/check-hallucination", response_model=HallucinationCheckResponse)
async def check_hallucination(request: HallucinationCheckRequest) -> HallucinationCheckResponse:
    """Check text for potential hallucinations."""
    result = detector.check_text(request.text, request.sources)

    return HallucinationCheckResponse(
        has_hallucination=result["has_hallucination"],
        suspicious_claims=result["suspicious_claims"],
        confidence_score=result["confidence_score"],
        details=result["details"],
    )


@app.post("/calculate-confidence")
async def calculate_confidence(
    kb_results: list[dict] = [],
    web_results: list[dict] = [],
    verification_results: list[dict] = [],
    hallucination_check: dict = {},
):
    """Calculate overall confidence score."""
    score = calculator.calculate(
        kb_results,
        web_results,
        verification_results,
        hallucination_check,
    )
    return {"confidence_score": score}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)
