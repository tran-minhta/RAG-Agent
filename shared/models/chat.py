"""
RAG-ALL: Core Data Models - Chat & Agent
Models cho chat interactions, agent tools, and responses.
"""

from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


# =============================================================================
# Enums
# =============================================================================

class MessageRole(str, Enum):
    """Role của message trong conversation"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class AgentAction(str, Enum):
    """Các action mà agent có thể thực hiện"""
    CHAT = "chat"
    SEARCH_KB = "search_knowledge"
    SEARCH_WEB = "search_web"
    DEEP_RESEARCH = "deep_research"
    EXTRACT_DOCUMENT = "extract_document"
    SUMMARIZE = "summarize"
    GENERATE_OUTLINE = "generate_outline"
    GENERATE_CITATION = "generate_citation"
    VERIFY_CLAIM = "verify_claim"
    PROFESSIONAL_EDIT = "professional_edit"
    VOICE_INPUT = "voice_input"


# =============================================================================
# Chat Models
# =============================================================================

class Message(BaseModel):
    """Một message trong conversation"""
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: dict = Field(default_factory=dict)
    # Tool call info (if role is ASSISTANT and used tools)
    tool_calls: list[dict] = Field(default_factory=list)
    # Confidence info
    confidence_score: Optional[float] = Field(default=None, description="0-1 confidence")
    disclaimer: Optional[str] = Field(default=None, description="Disclaimer if confidence < 0.85")


class Conversation(BaseModel):
    """Một conversation/session"""
    conversation_id: str
    user_id: str = "default"
    messages: list[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: dict = Field(default_factory=dict)
    # Research context
    current_research_id: Optional[str] = None
    depth_level: int = Field(default=2, description="Current depth level 1-5")


# =============================================================================
# Agent Models
# =============================================================================

class ToolCall(BaseModel):
    """Thông tin về tool call"""
    tool_name: str
    tool_args: dict[str, Any] = Field(default_factory=dict)
    tool_result: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None


class AgentState(BaseModel):
    """State của agent trong LangGraph"""
    messages: list[Message] = Field(default_factory=list)
    current_action: Optional[AgentAction] = None
    tool_calls: list[ToolCall] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)
    confidence_score: float = Field(default=1.0)
    # Research state
    research_depth: int = Field(default=2)
    sources_collected: int = Field(default=0)
    crawl_session_id: Optional[str] = None


# =============================================================================
# Request/Response Models
# =============================================================================

class ChatRequest(BaseModel):
    """Request tu user de chat"""
    message: str = Field(description="User message")
    conversation_id: Optional[str] = Field(default=None, description="Existing conversation ID")
    user_id: str = Field(default="default")
    # Research options
    depth_level: int = Field(default=2, ge=1, le=5, description="Research depth 1-5")
    use_web_search: bool = Field(default=True, description="Allow web search")
    use_deep_research: bool = Field(default=False, description="Enable deep research mode")
    # Provider/model override
    provider: Optional[str] = Field(default=None, description="LLM provider: ollama | gemini")
    model: Optional[str] = Field(default=None, description="Model name override")
    # Voice
    voice_input: bool = Field(default=False, description="Input is voice (auto STT)")
    voice_output: bool = Field(default=False, description="Output as voice (auto TTS)")


class ChatResponse(BaseModel):
    """Response tu agent"""
    message: str = Field(description="Agent response")
    conversation_id: str
    # Confidence & accuracy
    confidence_score: float = Field(default=1.0, description="Confidence 0-1")
    confidence_level: str = Field(default="high", description="high/medium/low/very_low")
    disclaimer: Optional[str] = Field(default=None)
    refusal: bool = Field(default=False, description="Whether agent refused to answer")
    refusal_reason: Optional[str] = None
    suggested_sources: list[str] = Field(default_factory=list)
    # Sources & citations
    sources: list[dict] = Field(default_factory=list, description="Sources used")
    citations: list[str] = Field(default_factory=list, description="Formatted citations")
    # Metadata
    tools_used: list[str] = Field(default_factory=list)
    processing_time_ms: float = 0
    provider: str = Field(default="", description="LLM provider used")
    model: str = Field(default="", description="Model used")
    # Voice
    audio_url: Optional[str] = Field(default=None, description="TTS audio file URL")


# =============================================================================
# Deep Research Models
# =============================================================================

class DeepResearchRequest(BaseModel):
    """Request cho deep research"""
    topic: str = Field(description="Research topic")
    sub_topics: list[str] = Field(default_factory=list, description="Sub-topics to research")
    depth_level: int = Field(default=2, ge=1, le=5)
    max_pages: int = Field(default=100)
    source_types: list[str] = Field(
        default=["web", "academic"],
        description="Source types: web, academic, local_kb"
    )
    language: str = Field(default="vi", description="Preferred language")
    output_format: str = Field(default="markdown", description="markdown, pdf, docx, latex")
    citation_style: str = Field(default="apa", description="apa, ieee, vancouver")


class DeepResearchResult(BaseModel):
    """Kết quả deep research"""
    research_id: str
    topic: str
    status: str  # processing, completed, failed
    # Results
    report_markdown: Optional[str] = None
    executive_summary: Optional[str] = None
    # Sources
    total_sources: int = 0
    verified_sources: int = 0
    sources: list[dict] = Field(default_factory=list)
    # Citations
    citations: list[dict] = Field(default_factory=list)
    bibliography: Optional[str] = None
    # Quality metrics
    overall_confidence: float = 0.0
    perspective_scores: dict[str, float] = Field(default_factory=dict)
    # Export
    export_paths: dict[str, str] = Field(default_factory=dict)
    # Metadata
    processing_time_seconds: float = 0
    depth_level: int = 2
    pages_crawled: int = 0
