"""
RAG-ALL: Document Service - Main Application
Xử lý tài liệu: detect type → extract content → clean → output markdown.

Supported extractors:
  - MinerU: PDF → Markdown (hỗ trợ công thức, bảng biểu)
  - MarkItDown: DOCX/PPTX/XLSX/HTML → Markdown
  - Magika: AI file type detection (99% accuracy)

Pipeline:
  File → Magika detect → Router → Extractor → Clean Markdown → Response
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from shared.config.settings import settings
from shared.utils.logger import document_logger as logger
from services.document.detectors.magika_detector import MagikaDetector
from services.document.extractors.mineru_extractor import MinerUExtractor
from services.document.extractors.markitdown_extractor import MarkItDownExtractor
from services.document.pipeline.document_pipeline import DocumentPipeline


# =============================================================================
# Lifespan
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting Document Service...")
    logger.info(f"   MinerU: {'enabled' if settings.mineru_enabled else 'disabled'}")
    logger.info(f"   MarkItDown: {'enabled' if settings.markitdown_enabled else 'disabled'}")
    logger.info(f"   Magika: {'enabled' if settings.magika_enabled else 'disabled'}")
    yield
    logger.info("🔄 Shutting down Document Service...")


# =============================================================================
# FastAPI App
# =============================================================================

app = FastAPI(
    title="RAG-ALL Document Service",
    description="Document processing: detect → extract → clean → markdown",
    version="0.1.0",
    lifespan=lifespan,
)

# Initialize pipeline components
pipeline = DocumentPipeline(
    detector=MagikaDetector(),
    extractors={
        "pdf": MinerUExtractor(),
        "docx": MarkItDownExtractor(),
        "pptx": MarkItDownExtractor(),
        "xlsx": MarkItDownExtractor(),
        "html": MarkItDownExtractor(),
        "txt": MarkItDownExtractor(),
        "markdown": MarkItDownExtractor(),
    },
)


# =============================================================================
# Request/Response Models
# =============================================================================

class ProcessRequest(BaseModel):
    file_path: str
    doc_id: str
    filename: str = ""


class ProcessResponse(BaseModel):
    doc_id: str
    doc_type: str
    markdown_content: str
    metadata: dict
    chunk_count: int = 0
    success: bool = True
    message: str = ""


# =============================================================================
# Endpoints
# =============================================================================

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "document"}


@app.post("/process", response_model=ProcessResponse)
async def process_document(request: ProcessRequest) -> ProcessResponse:
    """
    Process document: detect type → extract → clean → markdown.

    Pipeline:
      1. Magika detect file type
      2. Route to appropriate extractor
      3. Extract content to markdown
      4. Clean and post-process
      5. Return markdown + metadata
    """
    logger.info(f"Processing: {request.file_path} (doc_id={request.doc_id})")

    try:
        result = await pipeline.process(
            file_path=request.file_path,
            doc_id=request.doc_id,
            filename=request.filename,
        )
        return ProcessResponse(**result)

    except Exception as e:
        logger.error(f"Processing error: {e}")
        return ProcessResponse(
            doc_id=request.doc_id,
            doc_type="unknown",
            markdown_content="",
            metadata={},
            success=False,
            message=f"Processing failed: {str(e)}",
        )


@app.post("/detect")
async def detect_file_type(file_path: str):
    """Detect file type using Magika AI."""
    detector = MagikaDetector()
    result = await detector.detect(file_path)
    return result


@app.get("/extractors")
async def list_extractors():
    """Liệt kê các extractors có sẵn."""
    return {
        "extractors": {
            "pdf": {"name": "MinerU", "enabled": settings.mineru_enabled},
            "docx": {"name": "MarkItDown", "enabled": settings.markitdown_enabled},
            "pptx": {"name": "MarkItDown", "enabled": settings.markitdown_enabled},
            "xlsx": {"name": "MarkItDown", "enabled": settings.markitdown_enabled},
            "html": {"name": "MarkItDown", "enabled": settings.markitdown_enabled},
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
