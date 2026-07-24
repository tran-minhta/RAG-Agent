"""
RAG-ALL: RAG Service - Main Application
Vector store management: chunking, embedding, retrieval.

Components:
  - ChromaDB: Vector storage
  - Sentence-Transformers: Embeddings
  - Hybrid search: Vector + BM25
  - Reranking: Cross-encoder
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from shared.config.settings import settings
from shared.utils.logger import rag_logger as logger
from services.rag.index.chroma_manager import ChromaManager
from services.rag.embeddings.embedding_manager import EmbeddingManager
from services.rag.ingest.chunker import TextChunker
from services.rag.retriever.vector_retriever import VectorRetriever


# =============================================================================
# Lifespan
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting RAG Service...")
    logger.info(f"   ChromaDB: {settings.chroma_host}:{settings.chroma_port}")
    logger.info(f"   Embedding model: {settings.embedding_model}")
    yield
    logger.info("🔄 Shutting down RAG Service...")


# =============================================================================
# FastAPI App
# =============================================================================

app = FastAPI(
    title="RAG-ALL RAG Service",
    description="Vector store + embeddings + retrieval",
    version="0.1.0",
    lifespan=lifespan,
)

# Initialize components
chroma_manager = ChromaManager()
embedding_manager = EmbeddingManager()
chunker = TextChunker()
retriever = VectorRetriever()


# =============================================================================
# Request/Response Models
# =============================================================================

class IngestRequest(BaseModel):
    doc_id: str
    file_path: str
    markdown_content: str
    collection_name: str = "ragall_documents"
    chunk_size: int = 512
    metadata: dict = {}


class IngestResponse(BaseModel):
    success: bool
    doc_id: str
    chunk_count: int
    message: str = ""


class SearchRequest(BaseModel):
    query: str
    collection_name: str = "ragall_documents"
    top_k: int = 5
    min_relevance: float = 0.5


# =============================================================================
# Endpoints
# =============================================================================

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "rag"}


@app.post("/ingest", response_model=IngestResponse)
async def ingest_document(request: IngestRequest) -> IngestResponse:
    """
    Ingest document vào vector store.
    Pipeline: Content → Chunk → Embed → Store in ChromaDB
    """
    logger.info(f"Ingesting doc: {request.doc_id} ({len(request.markdown_content)} chars)")

    try:
        # Step 1: Chunk content
        chunks = chunker.chunk_text(
            text=request.markdown_content,
            chunk_size=request.chunk_size,
            chunk_overlap=50,
        )
        logger.info(f"  Created {len(chunks)} chunks")

        # Step 2: Generate embeddings
        texts = [chunk["text"] for chunk in chunks]
        embeddings = embedding_manager.encode(texts)
        logger.info(f"  Generated {len(embeddings)} embeddings")

        # Step 3: Store in ChromaDB
        await chroma_manager.add_documents(
            collection_name=request.collection_name,
            doc_id=request.doc_id,
            chunks=chunks,
            embeddings=embeddings,
            metadata=request.metadata,
        )

        return IngestResponse(
            success=True,
            doc_id=request.doc_id,
            chunk_count=len(chunks),
            message=f"Successfully ingested {len(chunks)} chunks",
        )

    except Exception as e:
        logger.error(f"Ingest error: {e}")
        return IngestResponse(
            success=False,
            doc_id=request.doc_id,
            chunk_count=0,
            message=f"Ingestion failed: {str(e)}",
        )


@app.post("/search")
async def search(request: SearchRequest):
    """
    Search trong vector store.
    Returns top-k relevant chunks.
    """
    logger.info(f"Search: '{request.query[:50]}...' (top_k={request.top_k})")

    try:
        # Generate query embedding
        query_embedding = embedding_manager.encode([request.query])[0]

        # Search ChromaDB
        results = await chroma_manager.search(
            collection_name=request.collection_name,
            query_embedding=query_embedding.tolist(),
            top_k=request.top_k,
        )

        # Filter by minimum relevance
        filtered = [r for r in results if r.get("score", 0) >= request.min_relevance]

        return {
            "query": request.query,
            "results": filtered,
            "total_results": len(filtered),
        }

    except Exception as e:
        logger.error(f"Search error: {e}")
        return {"query": request.query, "results": [], "total_results": 0, "error": str(e)}


@app.get("/collections/{collection_name}/documents")
async def list_documents(collection_name: str):
    """Liệt kê documents trong collection."""
    try:
        docs = await chroma_manager.list_documents(collection_name)
        return {"collection": collection_name, "documents": docs, "total": len(docs)}
    except Exception as e:
        return {"collection": collection_name, "documents": [], "total": 0, "error": str(e)}


@app.delete("/collections/{collection_name}/documents/{doc_id}")
async def delete_document(collection_name: str, doc_id: str):
    """Xóa document khỏi collection."""
    try:
        await chroma_manager.delete_document(collection_name, doc_id)
        return {"success": True, "doc_id": doc_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
