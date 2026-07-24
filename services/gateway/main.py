"""
RAG-ALL: Gateway Service - Main Application
Central API Gateway routing requests to microservices.

Services:
  - /agent/*      → Agent Service (LangGraph AI Agent)
  - /rag/*        → RAG Service (Vector search)
  - /document/*   → Document Service (PDF/DOCX processing)
  - /research/*   → Research Service (Deep web browsing)
  - /editor/*     → Editor Service (Professional editing)
  - /voice/*      → Voice Service (TTS/STT)
  - /chat         → WebSocket chat (real-time streaming)
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from shared.config.settings import settings
from shared.utils.logger import gateway_logger as logger
from services.gateway.routers import chat, documents, research, voice, health


# =============================================================================
# Application Lifespan
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup và shutdown lifecycle cho Gateway."""
    # === Startup ===
    logger.info("🚀 Starting RAG-ALL Gateway Service...")
    logger.info(f"   Project: {settings.project_name} v{settings.version}")
    logger.info(f"   Gateway Port: {settings.gateway_port}")
    logger.info(f"   Agent URL: {settings.agent_service_url}")
    logger.info(f"   RAG URL: {settings.rag_service_url}")
    logger.info(f"   Document URL: {settings.document_service_url}")
    logger.info(f"   Research URL: {settings.research_service_url}")
    logger.info(f"   Editor URL: {settings.editor_service_url}")
    logger.info("✅ Gateway Service started successfully")

    yield  # App is running

    # === Shutdown ===
    logger.info("🔄 Shutting down Gateway Service...")


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="RAG-ALL Gateway",
    description="AI-Agent hỗ trợ nghiên cứu, học tập, làm luận án, luận văn",
    version=settings.version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# === CORS Middleware ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (restrict in production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Static Files ===
app.mount("/static", StaticFiles(directory="data"), name="static")


# =============================================================================
# Include Routers
# =============================================================================

# Health check + Models
app.include_router(health.router, prefix="/health", tags=["Health"])

# Chat (WebSocket + REST)
app.include_router(chat.router, prefix="/chat", tags=["Chat"])

# Document management
app.include_router(documents.router, prefix="/documents", tags=["Documents"])

# Research
app.include_router(research.router, prefix="/research", tags=["Research"])

# Voice
app.include_router(voice.router, prefix="/voice", tags=["Voice"])


# =============================================================================
# Root Endpoint
# =============================================================================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint - API info."""
    return {
        "name": settings.project_name,
        "version": settings.version,
        "description": "AI-Agent hỗ trợ nghiên cứu, học tập, làm luận án",
        "docs": "/docs",
        "services": {
            "gateway": f"http://localhost:{settings.gateway_port}",
            "chat": "/chat",
            "documents": "/documents",
            "research": "/research",
            "voice": "/voice",
        },
    }


# =============================================================================
# Run (Development)
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.gateway_port,
        reload=settings.debug,
        log_level="info",
    )
