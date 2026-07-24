"""
RAG-ALL: Agent Service
AI Agent — raw httpx calls to Ollama/Gemini, no LangChain dependency.

Capabilities:
  - Chat với context (RAG)
  - Web search (DuckDuckGo, ArXiv, PubMed, Semantic Scholar)
  - Multi-LLM routing (Ollama local + Gemini cloud)
  - Confidence scoring
"""

import httpx
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel

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
    logger.info("Agent Service starting...")
    logger.info(f"  Ollama: {settings.ollama_base_url}")
    logger.info(f"  Model: {settings.ollama_model}")
    logger.info(f"  Gemini: {'configured' if settings.gemini_api_key else 'not configured'}")

    # Kiem tra ket noi Ollama khi startup
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get(f"{settings.ollama_base_url}/api/tags")
            if r.status_code == 200:
                models = r.json().get("models", [])
                logger.info(f"  Ollama OK — {len(models)} models available")
                for m in models:
                    logger.info(f"    - {m['name']}")
            else:
                logger.warning(f"  Ollama responded with status {r.status_code}")
        except Exception as e:
            logger.error(f"  Ollama unreachable: {e}")

    yield
    logger.info("Agent Service shut down.")


# =============================================================================
# App
# =============================================================================

app = FastAPI(title="RAG-ALL Agent", version="0.1.0", lifespan=lifespan)

knowledge_tool = KnowledgeSearchTool()
web_search_tool = WebSearchTool()


# =============================================================================
# Models
# =============================================================================

class InvokeRequest(BaseModel):
    message: str
    conversation_id: str
    history: list[dict] = []
    depth_level: int = 2
    use_web_search: bool = True
    provider: str | None = None       # "ollama" | "gemini" | None (auto)
    model: str | None = None          # override model name


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
    provider: str = ""
    model: str = ""


# =============================================================================
# LLM Providers — raw httpx
# =============================================================================

async def call_ollama(
    messages: list[dict],
    model: str | None = None,
) -> str:
    """Goi Ollama chat API truc tiep."""
    model = model or settings.ollama_model
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.7, "num_predict": 2048},
    }
    async with httpx.AsyncClient(timeout=300) as client:
        r = await client.post(f"{settings.ollama_base_url}/api/chat", json=payload)
        r.raise_for_status()
        data = r.json()
        content = data.get("message", {}).get("content", "")
        if not content:
            logger.warning(f"Ollama returned empty response for model={model}")
        return content


async def call_gemini(
    messages: list[dict],
    model: str | None = None,
) -> str:
    """Goi Gemini API truc tiep qua Google REST."""
    model = model or settings.gemini_model
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={settings.gemini_api_key}"

    # Chuyen doi messages sang Gemini format
    contents = []
    system_instruction = None
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        if role == "system":
            system_instruction = {"parts": [{"text": content}]}
        elif role == "user":
            contents.append({"role": "user", "parts": [{"text": content}]})
        elif role == "assistant":
            contents.append({"role": "model", "parts": [{"text": content}]})

    payload: dict = {"contents": contents}
    if system_instruction:
        payload["systemInstruction"] = system_instruction

    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(url, json=payload)
        r.raise_for_status()
        data = r.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]


async def call_llm(
    messages: list[dict],
    provider: str | None = None,
    model: str | None = None,
) -> tuple[str, str, str]:
    """
    Goi LLM — tra ve (response_text, provider_used, model_used).
    Auto-chon provider neu khong specifiy.
    """
    # Auto-route: query phuc tap → Gemini, don gian → Ollama
    if provider is None:
        complex_kw = [
            "phan tich", "so sanh", "danh gia", "nghien cuu",
            "analyze", "compare", "evaluate", "research",
            "luan van", "thesis", "da chieu", "multi-perspective",
        ]
        # (don't filter on user message, just use ollama by default)
        provider = "ollama"

    if provider == "gemini" and settings.gemini_api_key:
        text = await call_gemini(messages, model)
        return text, "gemini", model or settings.gemini_model

    # Default: Ollama
    text = await call_ollama(messages, model)
    return text, "ollama", model or settings.ollama_model


# =============================================================================
# Agent Logic
# =============================================================================

async def run_agent(request: InvokeRequest) -> InvokeResponse:
    tools_used: list[str] = []
    sources: list[dict] = []
    context_parts: list[str] = []

    # Step 1: Search knowledge base
    kb_results: list[dict] = []
    try:
        kb_results = await knowledge_tool.search(query=request.message, top_k=5)
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

    # Step 2: Web search
    web_results: list[dict] = []
    if request.use_web_search:
        try:
            web_results = await web_search_tool.search(query=request.message, max_results=5)
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

    # Step 3: Build messages
    system_prompt = get_system_prompt()
    context = "\n\n".join(context_parts) if context_parts else "No relevant context found."

    messages = [
        {"role": "system", "content": f"{system_prompt}\n\nContext:\n{context}"},
    ]

    # History (chi user/assistant)
    for msg in request.history[-10:]:
        role = msg.get("role", "user")
        if role in ("user", "assistant"):
            messages.append({"role": role, "content": msg.get("content", "")})

    # Current query
    messages.append({"role": "user", "content": request.message})

    # Step 4: Call LLM
    assistant_message = ""
    provider_used = ""
    model_used = ""
    try:
        assistant_message, provider_used, model_used = await call_llm(
            messages,
            provider=request.provider,
            model=request.model,
        )
    except Exception as e:
        logger.error(f"LLM failed: {type(e).__name__}: {e}")
        assistant_message = (
            "Xin loi, toi gap loi khi xu ly yeu cau. "
            "Vui long thu lai hoac su dung cau hoi don gian hon."
        )

    # Step 5: Confidence
    confidence = _calc_confidence(kb_results, web_results, len(assistant_message))

    return InvokeResponse(
        message=assistant_message,
        conversation_id=request.conversation_id,
        confidence_score=confidence,
        confidence_level=_confidence_level(confidence),
        disclaimer=(
            f"Do tin cay: {confidence:.0%}. Can xac minh them."
            if confidence < 0.60 else None
        ),
        sources=sources,
        tools_used=tools_used,
        provider=provider_used,
        model=model_used,
    )


def _calc_confidence(kb: list, web: list, resp_len: int) -> float:
    score = 0.5
    if kb:
        avg = sum(r.get("score", 0) for r in kb) / len(kb)
        score += avg * 0.2
    if web:
        score += min(0.2, len(web) * 0.04)
    if resp_len < 100:
        score -= 0.1
    return max(0.0, min(1.0, score))


def _confidence_level(score: float) -> str:
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


@app.get("/models")
async def list_models():
    """Danh sach model co san tu Ollama + Gemini."""
    result = {"ollama": [], "gemini": []}

    # Ollama models
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{settings.ollama_base_url}/api/tags")
            if r.status_code == 200:
                for m in r.json().get("models", []):
                    result["ollama"].append({
                        "name": m["name"],
                        "size": m.get("details", {}).get("parameter_size", ""),
                        "family": m.get("details", {}).get("family", ""),
                    })
    except Exception as e:
        logger.warning(f"Cannot list Ollama models: {e}")

    # Gemini models (static list)
    result["gemini"] = [
        {"name": "gemini-2.0-flash", "description": "Fast, free tier"},
        {"name": "gemini-1.5-flash", "description": "Fast, cheaper"},
        {"name": "gemini-1.5-pro", "description": "Best quality"},
    ]

    return result


@app.post("/invoke", response_model=InvokeResponse)
async def invoke(request: InvokeRequest) -> InvokeResponse:
    logger.info(f"Invoke: conv={request.conversation_id}, msg={request.message[:50]}...")
    try:
        return await run_agent(request)
    except Exception as e:
        logger.error(f"Agent error: {e}")
        return InvokeResponse(
            message="Co loi xay ra. Vui long thu lai.",
            conversation_id=request.conversation_id,
            confidence_score=0.0,
            confidence_level="very_low",
            refusal=True,
            refusal_reason=str(e),
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
