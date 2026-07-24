"""
RAG-ALL: Shared Models Package
Export all core data models.
"""

from shared.models.document import (
    DocumentType,
    ProcessingStatus,
    DepthLevel,
    ConfidenceLevel,
    DocumentMetadata,
    DocumentChunk,
    ProcessedDocument,
    IngestRequest,
    IngestResponse,
    SearchQuery,
    SearchResult,
    SearchResponse,
)

from shared.models.chat import (
    MessageRole,
    AgentAction,
    Message,
    Conversation,
    ToolCall,
    AgentState,
    ChatRequest,
    ChatResponse,
    DeepResearchRequest,
    DeepResearchResult,
)

from shared.models.agent import (
    CrawlStrategy,
    VerificationStatus,
    CrawlSession,
    CrawledPage,
    DepthConfig,
    Citation,
    FactClaim,
    VerificationResult,
    ReportSection,
    ResearchReport,
)

__all__ = [
    # Document
    "DocumentType", "ProcessingStatus", "DepthLevel", "ConfidenceLevel",
    "DocumentMetadata", "DocumentChunk", "ProcessedDocument",
    "IngestRequest", "IngestResponse",
    "SearchQuery", "SearchResult", "SearchResponse",
    # Chat
    "MessageRole", "AgentAction",
    "Message", "Conversation", "ToolCall", "AgentState",
    "ChatRequest", "ChatResponse",
    "DeepResearchRequest", "DeepResearchResult",
    # Agent
    "CrawlStrategy", "VerificationStatus",
    "CrawlSession", "CrawledPage", "DepthConfig",
    "Citation", "FactClaim", "VerificationResult",
    "ReportSection", "ResearchReport",
]
