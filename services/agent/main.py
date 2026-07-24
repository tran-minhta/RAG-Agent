"""
RAG-ALL: Agent Service - Main Application
AI Agent với LangGraph, multi-LLM routing, và tool calling.

Agent Capabilities:
  - Chat với context (RAG)
  - Web search (DuckDuckGo, Tavily)
  - Deep research (multi-source crawling)
  - Document analysis
  - Citation generation
  - Fact verification
  - Professional editing

LLM Providers:
  - Ollama (local): llama3.1, qwen2.5, mistral
  - Gemini API (cloud): gemini-2.0-flash
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any

from shared.config.settings import settings
from shared.utils.logger import agent_logger as logger
from services.agent.tools.knowledge_search import KnowledgeSearchTool
from services.agent.tools.web_search import WebSearchTool
from services.agent.prompts.system_prompts import get_system_prompt


# =============================================================================
# Lifespan
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting Agent Service...")
    logger.info(f"   Ollama: {settings.ollama_base_url}")
    logger.info(f"   Gemini: {'configured' if settings.gemini_api_key else 'not configured'}")
    logger.info(f"   Default model: {settings.ollama_model}")
    yield
    logger.info("🔄 Shutting down Agent Service...")


# =============================================================================
# FastAPI App
# =============================================================================

app = FastAPI(
    title="RAG-ALL Agent Service",
    description="AI Agent with LangGraph + Multi-LLM routing",
    version="0.1.0",
    lifespan=lifespan,
)

# Initialize tools
knowledge_tool = KnowledgeSearchTool()
web_search_tool = WebSearchTool()


# =============================================================================
# Request/Response Models
# =============================================================================

class InvokeRequest(BaseModel):
    message: str
    conversation_id: str
    history: list[dict] = []
    depth_level: int = 2
    use_web_search: bool = True
    use_deep_research: bool = False
    stream: bool = False


class InvokeResponse(BaseModel):
    message: str
    conversation_id: str
    confidence_score: float = 1.0
    confidence_level: str = "high"
    disclaimer: str | None = None
    refusal: bool = False
    refusal_reason: str | None = None
    sources: list[dict] = []
    citations: list[str] = []
    tools_used: list[str] = []


# =============================================================================
# LLM Router
# =============================================================================

async def select_llm(query: str, complexity: str = "auto") -> Any:
    """
    Smart LLM routing based on query complexity.

    Strategy:
      - Simple queries → Ollama llama3.1:8b (fast, free)
      - Medium queries → Ollama qwen2.5:14b (better quality)
      - Complex queries → Gemini 2.0 Flash (best quality, free tier)
    """
    # Simple heuristic for complexity
    complex_keywords = [
        "phân tích", "so sánh", "đánh giá", "nghiên cứu",
        "analyze", "compare", "evaluate", "research",
        "luận văn", "thesis", "đa chiều", "multi-perspective",
    ]

    is_complex = any(kw in query.lower() for kw in complex_keywords)

    if is_complex and settings.gemini_api_key:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model=settings.gemini_model,
                google_api_key=settings.gemini_api_key,
                temperature=0.7,
            )
        except Exception as e:
            logger.warning(f"Gemini failed, falling back to Ollama: {e}")

    # Default to Ollama
    try:
        from langchain_ollama import ChatOllama
        model = settings.ollama_model_large if is_complex else settings.ollama_model
        return ChatOllama(
            base_url=settings.ollama_base_url,
            model=model,
            temperature=0.7,
        )
    except Exception as e:
        logger.error(f"Ollama connection failed: {e}")
        raise


# =============================================================================
# Agent Logic
# =============================================================================

async def run_agent(request: InvokeRequest) -> InvokeResponse:
    """
    Main agent loop.

    Flow:
      1. Analyze query
      2. Select tools (RAG, web search, deep research)
      3. Execute tools
      4. Generate response with LLM
      5. Calculate confidence
      6. Return response
    """
    tools_used = []
    sources = []
    context_parts = []

    # Step 1: Search knowledge base (always)
    try:
        kb_results = await knowledge_tool.search(
            query=request.message,
            top_k=5,
        )
        if kb_results:
            tools_used.append("knowledge_search")
            for r in kb_results:
                context_parts.append(f"[KB] {r.get('content', '')}")
                sources.append({
                    "type": "knowledge_base",
                    "content": r.get("content", "")[:200],
                    "score": r.get("score", 0),
                })
    except Exception as e:
        logger.warning(f"KB search failed: {e}")

    # Step 2: Web search (if enabled)
    if request.use_web_search:
        try:
            web_results = await web_search_tool.search(
                query=request.message,
                max_results=5,
            )
            if web_results:
                tools_used.append("web_search")
                for r in web_results:
                    context_parts.append(f"[Web] {r.get('snippet', '')}")
                    sources.append({
                        "type": "web",
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "snippet": r.get("snippet", "")[:200],
                    })
        except Exception as e:
            logger.warning(f"Web search failed: {e}")

    # Step 3: Generate response
    system_prompt = get_system_prompt()
    context = "\n\n".join(context_parts) if context_parts else "No relevant context found."

    # Build messages
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": f"Context:\n{context}"},
    ]

    # Add conversation history
    for msg in request.history[-10:]:  # Last 10 messages
        messages.append({
            "role": msg.get("role", "user"),
            "content": msg.get("content", ""),
        })

    # Add current query
    messages.append({"role": "user", "content": request.message})

    # Call LLM
    try:
        llm = await select_llm(request.message)
        from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

        lc_messages = []
        for msg in messages:
            if msg["role"] == "system":
                lc_messages.append(SystemMessage(content=msg["content"]))
            elif msg["role"] == "user":
                lc_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                lc_messages.append(AIMessage(content=msg["content"]))

        response = await llm.ainvoke(lc_messages)
        assistant_message = response.content

    except Exception as e:
        logger.error(f"LLM invocation failed: {e}")
        assistant_message = (
            "Xin lỗi, tôi gặp lỗi khi xử lý yêu cầu. "
            "Vui lòng thử lại hoặc sử dụng câu hỏi đơn giản hơn."
        )

    # Step 4: Calculate confidence
    confidence = _calculate_confidence(
        kb_results=kb_results if 'kb_results' in dir() else [],
        web_results=web_results if 'web_results' in dir() else [],
        response_length=len(assistant_message),
    )

    confidence_level = _get_confidence_level(confidence)
    disclaimer = None
    refusal = False

    if confidence < settings.confidence_threshold_medium:
        disclaimer = (
            f"⚠️ Độ tin cậy: {confidence:.0%}. "
            "Thông tin này cần được xác minh thêm từ các nguồn học thuật."
        )

    if confidence < settings.confidence_threshold_low:
        refusal = True
        return InvokeResponse(
            message=(
                "❌ Tôi không đủ thông tin để trả lời câu hỏi này một cách chính xác.\n\n"
                "Gợi ý:\n"
                "1. Thử tìm kiếm với từ khóa cụ thể hơn\n"
                "2. Kiểm tra nguồn: Google Scholar, PubMed, arXiv\n"
                "3. Liên hệ chuyên gia trong lĩnh vực này"
            ),
            conversation_id=request.conversation_id,
            confidence_score=confidence,
            confidence_level="very_low",
            refusal=True,
            refusal_reason="Insufficient reliable sources",
            tools_used=tools_used,
        )

    return InvokeResponse(
        message=assistant_message,
        conversation_id=request.conversation_id,
        confidence_score=confidence,
        confidence_level=confidence_level,
        disclaimer=disclaimer,
        sources=sources,
        citations=[],  # TODO: extract citations
        tools_used=tools_used,
    )


def _calculate_confidence(kb_results: list, web_results: list, response_length: int) -> float:
    """Calculate confidence score based on available evidence."""
    score = 0.5  # Base score

    # Boost for KB results
    if kb_results:
        avg_score = sum(r.get("score", 0) for r in kb_results) / len(kb_results)
        score += avg_score * 0.2

    # Boost for web results
    if web_results:
        score += min(0.2, len(web_results) * 0.04)

    # Penalize very short responses
    if response_length < 100:
        score -= 0.1

    return max(0.0, min(1.0, score))


def _get_confidence_level(score: float) -> str:
    """Convert score to confidence level."""
    if score >= 0.85:
        return "high"
    elif score >= 0.60:
        return "medium"
    elif score >= 0.40:
        return "low"
    return "very_low"


# =============================================================================
# Endpoints
# =============================================================================

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "agent"}


@app.post("/invoke", response_model=InvokeResponse)
async def invoke_agent(request: InvokeRequest) -> InvokeResponse:
    """Invoke agent với message."""
    logger.info(f"Agent invoke: conv={request.conversation_id}, msg={request.message[:50]}...")
    try:
        return await run_agent(request)
    except Exception as e:
        logger.error(f"Agent error: {e}")
        return InvokeResponse(
            message="Xin lỗi, có lỗi xảy ra. Vui lòng thử lại.",
            conversation_id=request.conversation_id,
            confidence_score=0.0,
            confidence_level="very_low",
            refusal=True,
            refusal_reason=str(e),
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
