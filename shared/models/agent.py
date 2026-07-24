"""
RAG-ALL: Core Data Models - Agent Tools
Models cho agent tools, web browsing, and verification.
"""

from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


# =============================================================================
# Enums
# =============================================================================

class CrawlStrategy(str, Enum):
    """ChiềuStrategy cho deep browsing"""
    BFS = "bfs"           # Breadth-first search
    DFS = "dfs"           # Depth-first search
    BEST_FIRST = "best_first"  # Relevance-guided
    ADAPTIVE = "adaptive" # Stop when confident


class VerificationStatus(str, Enum):
    """Trạng thái verification"""
    VERIFIED = "verified"
    PARTIALLY_VERIFIED = "partially_verified"
    NOT_FOUND = "not_found"
    CONFLICTING = "conflicting"


# =============================================================================
# Deep Browser Models
# =============================================================================

class CrawlSession(BaseModel):
    """Một session crawl web"""
    session_id: str
    start_urls: list[str]
    depth_level: int = 2
    strategy: CrawlStrategy = CrawlStrategy.BFS
    max_pages: int = 50
    max_depth: int = 2
    # Status
    status: str = "pending"  # pending, crawling, completed, failed
    pages_crawled: int = 0
    pages_queued: int = 0
    # Filters
    domain_whitelist: list[str] = Field(default_factory=list)
    domain_blacklist: list[str] = Field(default_factory=list)
    url_patterns: list[str] = Field(default_factory=list)
    # Results
    collected_urls: list[str] = Field(default_factory=list)
    collected_content: list[dict] = Field(default_factory=list)
    # Timestamps
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class CrawledPage(BaseModel):
    """Một trang web đã được crawl"""
    url: str
    title: str = ""
    content_markdown: str = ""
    content_html: str = ""
    depth: int = 0
    relevance_score: float = 0.0
    # Links
    outgoing_links: list[str] = Field(default_factory=list)
    incoming_links: list[str] = Field(default_factory=list)
    # Metadata
    crawl_time_ms: float = 0
    content_length: int = 0
    language: str = ""
    source_type: str = "web"  # web, academic, news


class DepthConfig(BaseModel):
    """Cấu hình cho depth level"""
    level: int
    name: str
    max_depth: int
    max_pages: int
    description: str
    time_estimate: str


# =============================================================================
# Verification Models
# =============================================================================

class Citation(BaseModel):
    """Một citation/reference"""
    title: str
    authors: list[str] = Field(default_factory=list)
    year: Optional[int] = None
    journal: str = ""
    doi: Optional[str] = None
    url: Optional[str] = None
    # Verification
    verification_status: VerificationStatus = VerificationStatus.NOT_FOUND
    verified_doi: Optional[str] = None
    verified_url: Optional[str] = None
    confidence: float = 0.0


class FactClaim(BaseModel):
    """Một fact claim cần verify"""
    claim: str
    source: str = ""
    context: str = ""
    # Verification
    verification_status: VerificationStatus = VerificationStatus.NOT_FOUND
    supporting_sources: list[str] = Field(default_factory=list)
    contradicting_sources: list[str] = Field(default_factory=list)
    confidence: float = 0.0


class VerificationResult(BaseModel):
    """Kết quả verification"""
    claim: str
    status: VerificationStatus
    confidence: float
    sources_checked: int = 0
    supporting_count: int = 0
    contradicting_count: int = 0
    details: str = ""


# =============================================================================
# Report / Document Models
# =============================================================================

class ReportSection(BaseModel):
    """Một section trong research report"""
    title: str
    content: str
    section_level: int = 1  # 1=H1, 2=H2, etc.
    citations: list[str] = Field(default_factory=list)
    subsections: list["ReportSection"] = Field(default_factory=list)


class ResearchReport(BaseModel):
    """Research report hoàn chỉnh"""
    title: str
    author: str = "RAG-ALL AI Agent"
    date: datetime = Field(default_factory=datetime.now)
    # Sections
    executive_summary: str = ""
    sections: list[ReportSection] = Field(default_factory=list)
    conclusions: str = ""
    recommendations: str = ""
    # Citations
    bibliography: list[Citation] = Field(default_factory=list)
    citation_style: str = "apa"
    # Quality
    overall_confidence: float = 0.0
    word_count: int = 0
    page_count: int = 0
    # Export
    export_paths: dict[str, str] = Field(default_factory=dict)
