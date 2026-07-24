"""
RAG-ALL: Core Data Models - Document
Models cho document processing, storage, and retrieval.
"""

from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


# =============================================================================
# Enums
# =============================================================================

class DocumentType(str, Enum):
    """Loại tài liệu được hỗ trợ"""
    PDF = "pdf"
    DOCX = "docx"
    PPTX = "pptx"
    XLSX = "xlsx"
    TXT = "txt"
    MARKDOWN = "markdown"
    HTML = "html"
    IMAGE = "image"
    UNKNOWN = "unknown"


class ProcessingStatus(str, Enum):
    """Trạng thái xử lý document"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DepthLevel(str, Enum):
    """Mức độ deep browsing"""
    SHALLOW = "shallow"       # Level 1: 1-10 pages
    MODERATE = "moderate"     # Level 2: 10-50 pages
    DEEP = "deep"             # Level 3: 50-200 pages
    EXHAUSTIVE = "exhaustive" # Level 4: 200-500 pages
    ADAPTIVE = "adaptive"     # Level 5: AI decides


class ConfidenceLevel(str, Enum):
    """Mức độ tin cậy của thông tin"""
    HIGH = "high"           # > 0.85 - Full answer
    MEDIUM = "medium"       # 0.60-0.85 - Answer + disclaimer
    LOW = "low"             # 0.40-0.60 - Search more
    VERY_LOW = "very_low"  # < 0.40 - Refuse


# =============================================================================
# Document Models
# =============================================================================

class DocumentMetadata(BaseModel):
    """Metadata của một document"""
    doc_id: str = Field(description="Unique document ID")
    filename: str = Field(description="Original filename")
    doc_type: DocumentType = Field(description="Document type (detected by Magika)")
    file_size: int = Field(description="File size in bytes")
    mime_type: str = Field(default="", description="MIME type")
    created_at: datetime = Field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None
    status: ProcessingStatus = Field(default=ProcessingStatus.PENDING)

    # Content metadata
    title: str = Field(default="", description="Document title")
    author: str = Field(default="", description="Document author")
    language: str = Field(default="", description="Detected language")
    page_count: int = Field(default=0, description="Number of pages")

    # Processing metadata
    extractor_used: str = Field(default="", description="Which extractor was used")
    chunk_count: int = Field(default=0, description="Number of chunks created")
    embedding_model: str = Field(default="", description="Embedding model used")


class DocumentChunk(BaseModel):
    """Một chunk của document (đã được split)"""
    chunk_id: str = Field(description="Unique chunk ID")
    doc_id: str = Field(description="Parent document ID")
    content: str = Field(description="Chunk text content")
    chunk_index: int = Field(description="Index of chunk in document")
    start_page: int = Field(default=0, description="Starting page number")
    end_page: int = Field(default=0, description="Ending page number")
    heading: str = Field(default="", description="Section heading if available")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


class ProcessedDocument(BaseModel):
    """Kết quả sau khi xử lý document"""
    metadata: DocumentMetadata
    markdown_content: str = Field(description="Full markdown content")
    chunks: list[DocumentChunk] = Field(default_factory=list, description="Document chunks")
    images: list[dict] = Field(default_factory=list, description="Extracted images info")
    tables: list[dict] = Field(default_factory=list, description="Extracted tables info")
    formulas: list[dict] = Field(default_factory=list, description="Extracted formulas")


# =============================================================================
# Ingest Request/Response
# =============================================================================

class IngestRequest(BaseModel):
    """Request để ingest document"""
    file_path: str = Field(description="Path to the file to ingest")
    collection_name: str = Field(default="ragall_documents", description="ChromaDB collection")
    chunk_size: int = Field(default=512, description="Chunk size in tokens")
    chunk_overlap: int = Field(default=50, description="Overlap between chunks")


class IngestResponse(BaseModel):
    """Response sau khi ingest document"""
    success: bool
    doc_id: str
    filename: str
    doc_type: DocumentType
    chunk_count: int
    status: ProcessingStatus
    message: str = ""


# =============================================================================
# Search / Retrieval Models
# =============================================================================

class SearchQuery(BaseModel):
    """Query để tìm kiếm trong knowledge base"""
    query: str = Field(description="Search query")
    collection_name: str = Field(default="ragall_documents")
    top_k: int = Field(default=5, description="Number of results")
    min_relevance: float = Field(default=0.5, description="Minimum relevance score")


class SearchResult(BaseModel):
    """Một kết quả tìm kiếm"""
    chunk_id: str
    doc_id: str
    content: str
    relevance_score: float
    metadata: dict = Field(default_factory=dict)
    document_title: str = ""
    source_url: str = ""


class SearchResponse(BaseModel):
    """Response từ tìm kiếm"""
    query: str
    results: list[SearchResult]
    total_results: int
    search_time_ms: float
