"""
RAG-ALL: Gateway Router - Documents
Document upload, ingestion, and management endpoints.
Routes to Document Service for processing and RAG Service for indexing.
"""

import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from httpx import AsyncClient

from shared.config.settings import settings
from shared.models.document import IngestRequest, IngestResponse
from shared.utils.logger import gateway_logger as logger

router = APIRouter()


@router.post("/upload", response_model=IngestResponse)
async def upload_document(
    file: UploadFile = File(...),
    collection_name: str = "ragall_documents",
    chunk_size: int = 512,
) -> IngestResponse:
    """
    Upload và ingest document.
    Pipeline: Upload → Magika detect → Extract → Chunk → Embed → Store

    Steps:
      1. Save uploaded file
      2. Detect file type (Magika)
      3. Extract content (MinerU/MarkItDown)
      4. Chunk content
      5. Generate embeddings
      6. Store in ChromaDB
    """
    doc_id = str(uuid.uuid4())
    file_path = f"data/documents/{doc_id}_{file.filename}"

    logger.info(f"Uploading document: {file.filename} (id={doc_id})")

    # Save uploaded file
    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        logger.info(f"File saved: {file_path} ({len(content)} bytes)")
    except Exception as e:
        logger.error(f"File save error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    # Route to Document Service for extraction + RAG Service for indexing
    try:
        async with AsyncClient(timeout=300.0) as client:
            # Step 1: Process document (detect + extract)
            doc_response = await client.post(
                f"{settings.document_service_url}/process",
                json={
                    "file_path": file_path,
                    "doc_id": doc_id,
                    "filename": file.filename,
                },
            )

            if doc_response.status_code != 200:
                raise HTTPException(
                    status_code=500,
                    detail=f"Document processing failed: {doc_response.text}"
                )

            doc_data = doc_response.json()

            # Step 2: Ingest into RAG (chunk + embed + store)
            rag_response = await client.post(
                f"{settings.rag_service_url}/ingest",
                json={
                    "doc_id": doc_id,
                    "file_path": file_path,
                    "markdown_content": doc_data.get("markdown_content", ""),
                    "collection_name": collection_name,
                    "chunk_size": chunk_size,
                    "metadata": doc_data.get("metadata", {}),
                },
            )

            if rag_response.status_code != 200:
                raise HTTPException(
                    status_code=500,
                    detail=f"RAG ingestion failed: {rag_response.text}"
                )

            rag_data = rag_response.json()

            return IngestResponse(
                success=True,
                doc_id=doc_id,
                filename=file.filename,
                doc_type=doc_data.get("doc_type", "unknown"),
                chunk_count=rag_data.get("chunk_count", 0),
                status="completed",
                message=f"Document '{file.filename}' processed successfully",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ingest error: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")


@router.post("/ingest-path")
async def ingest_from_path(request: IngestRequest):
    """
    Ingest document từ local file path (không cần upload).
    Dùng khi document đã có trên server.
    """
    doc_id = str(uuid.uuid4())
    logger.info(f"Ingesting from path: {request.file_path}")

    try:
        async with AsyncClient(timeout=300.0) as client:
            # Process + ingest
            doc_response = await client.post(
                f"{settings.document_service_url}/process",
                json={
                    "file_path": request.file_path,
                    "doc_id": doc_id,
                },
            )

            if doc_response.status_code != 200:
                raise HTTPException(status_code=500, detail="Document processing failed")

            doc_data = doc_response.json()

            rag_response = await client.post(
                f"{settings.rag_service_url}/ingest",
                json={
                    "doc_id": doc_id,
                    "file_path": request.file_path,
                    "markdown_content": doc_data.get("markdown_content", ""),
                    "collection_name": request.collection_name,
                    "chunk_size": request.chunk_size,
                },
            )

            if rag_response.status_code != 200:
                raise HTTPException(status_code=500, detail="RAG ingestion failed")

            return {
                "success": True,
                "doc_id": doc_id,
                "chunk_count": rag_response.json().get("chunk_count", 0),
                "message": "Document ingested successfully",
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ingest from path error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_documents(collection_name: str = "ragall_documents"):
    """Liệt kê tất cả documents trong collection."""
    try:
        async with AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{settings.rag_service_url}/collections/{collection_name}/documents"
            )
            if response.status_code == 200:
                return response.json()
            return {"documents": [], "total": 0}
    except Exception as e:
        logger.error(f"List documents error: {e}")
        return {"documents": [], "total": 0, "error": str(e)}


@router.delete("/{doc_id}")
async def delete_document(doc_id: str, collection_name: str = "ragall_documents"):
    """Xóa document khỏi collection."""
    try:
        async with AsyncClient(timeout=30.0) as client:
            response = await client.delete(
                f"{settings.rag_service_url}/collections/{collection_name}/documents/{doc_id}"
            )
            return {"success": response.status_code == 200, "doc_id": doc_id}
    except Exception as e:
        logger.error(f"Delete document error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
