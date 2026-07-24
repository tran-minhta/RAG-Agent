"""
RAG-ALL: Integration Tests
Tests cho toàn bộ hệ thống RAG-ALL.
"""

import pytest
import httpx
import asyncio
import os

# Gateway URL
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:8000")


# =============================================================================
# Health Check Tests
# =============================================================================

@pytest.mark.asyncio
async def test_gateway_health():
    """Test gateway health endpoint."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{GATEWAY_URL}/health/")
        assert response.status_code == 200
        data = response.json()
        assert "gateway" in data


@pytest.mark.asyncio
async def test_agent_health():
    """Test agent service health."""
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8001/health")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_rag_health():
    """Test RAG service health."""
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8002/health")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_document_health():
    """Test document service health."""
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8003/health")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_voice_health():
    """Test voice service health."""
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8004/health")
        assert response.status_code == 200


# =============================================================================
# Chat Tests
# =============================================================================

@pytest.mark.asyncio
async def test_chat_basic():
    """Test basic chat functionality."""
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            f"{GATEWAY_URL}/chat/",
            json={
                "message": "Xin chào",
                "conversation_id": "test-session",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert len(data["message"]) > 0


@pytest.mark.asyncio
async def test_chat_with_history():
    """Test chat with conversation history."""
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            f"{GATEWAY_URL}/chat/",
            json={
                "message": "Cho tôi biết về AI",
                "conversation_id": "test-history",
                "history": [
                    {"role": "user", "content": "Xin chào"},
                    {"role": "assistant", "content": "Xin chào! Tôi có thể giúp gì cho bạn?"},
                ],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


# =============================================================================
# Document Tests
# =============================================================================

@pytest.mark.asyncio
async def test_document_upload():
    """Test document upload."""
    # Create a test file
    test_content = "This is a test document for RAG-ALL."
    test_file = "/tmp/test_document.txt"

    with open(test_file, "w") as f:
        f.write(test_content)

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            with open(test_file, "rb") as f:
                files = {"file": ("test.txt", f, "text/plain")}
                response = await client.post(
                    f"{GATEWAY_URL}/documents/upload",
                    files=files,
                )

            assert response.status_code == 200
            data = response.json()
            assert "document_id" in data
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)


@pytest.mark.asyncio
async def test_document_list():
    """Test document listing."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{GATEWAY_URL}/documents/")
        assert response.status_code == 200


# =============================================================================
# Research Tests
# =============================================================================

@pytest.mark.asyncio
async def test_research_depth_levels():
    """Test research depth levels endpoint."""
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8007/depth-levels")
        assert response.status_code == 200
        data = response.json()
        assert "1" in data
        assert "5" in data


# =============================================================================
# Voice Tests
# =============================================================================

@pytest.mark.asyncio
async def test_voice_voices():
    """Test voice listing."""
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8004/voices")
        assert response.status_code == 200
        data = response.json()
        assert "tts_voices" in data


# =============================================================================
# Editor Tests
# =============================================================================

@pytest.mark.asyncio
async def test_editor_citation_styles():
    """Test citation styles endpoint."""
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8009/citation-styles")
        assert response.status_code == 200
        data = response.json()
        assert "styles" in data


@pytest.mark.asyncio
async def test_editor_edit():
    """Test text editing."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8009/edit",
            json={
                "text": "Đây là một đoạn văn bản test.",
                "check_grammar": True,
                "check_readability": True,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "readability_score" in data


# =============================================================================
# Accuracy Engine Tests
# =============================================================================

@pytest.mark.asyncio
async def test_accuracy_health():
    """Test accuracy engine health."""
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8008/health")
        assert response.status_code == 200


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
