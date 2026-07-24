"""
RAG-ALL: Gateway Router - Chat
REST + WebSocket chat endpoints.
Routes requests to Agent Service for processing.
"""

import json
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from httpx import AsyncClient

from shared.config.settings import settings
from shared.models.chat import ChatRequest, ChatResponse
from shared.utils.logger import gateway_logger as logger

router = APIRouter()

# In-memory conversation store (simplified; use Redis/DB in production)
conversations: dict[str, list[dict]] = {}


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    REST chat endpoint.
    Gửi tin nhắn và nhận response từ Agent Service.
    """
    conversation_id = request.conversation_id or str(uuid.uuid4())
    logger.info(f"Chat request: conversation={conversation_id}, depth={request.depth_level}")

    # Initialize conversation if new
    if conversation_id not in conversations:
        conversations[conversation_id] = []

    # Add user message
    conversations[conversation_id].append({
        "role": "user",
        "content": request.message,
    })

    # Route to Agent Service
    try:
        async with AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{settings.agent_service_url}/invoke",
                json={
                    "message": request.message,
                    "conversation_id": conversation_id,
                    "history": conversations[conversation_id],
                    "depth_level": request.depth_level,
                    "use_web_search": request.use_web_search,
                    "use_deep_research": request.use_deep_research,
                },
            )

            if response.status_code == 200:
                data = response.json()
                chat_response = ChatResponse(**data)

                # Add assistant message to conversation
                conversations[conversation_id].append({
                    "role": "assistant",
                    "content": chat_response.message,
                    "confidence": chat_response.confidence_score,
                })

                return chat_response
            else:
                logger.error(f"Agent service error: {response.status_code}")
                return ChatResponse(
                    message="Xin lỗi, có lỗi xảy ra khi xử lý yêu cầu. Vui lòng thử lại.",
                    conversation_id=conversation_id,
                    confidence_score=0.0,
                    confidence_level="very_low",
                    refusal=True,
                    refusal_reason="Agent service unavailable",
                )

    except Exception as e:
        logger.error(f"Chat error: {e}")
        return ChatResponse(
            message="Xin lỗi, không thể kết nối đến Agent Service. Vui lòng thử lại sau.",
            conversation_id=conversation_id,
            confidence_score=0.0,
            confidence_level="very_low",
            refusal=True,
            refusal_reason=str(e),
        )


@router.websocket("/ws/{conversation_id}")
async def chat_websocket(websocket: WebSocket, conversation_id: str):
    """
    WebSocket chat endpoint - real-time streaming.
    Suitable for Chainlit and CLI real-time chat.
    """
    await websocket.accept()
    logger.info(f"WebSocket connected: conversation={conversation_id}")

    # Initialize conversation
    if conversation_id not in conversations:
        conversations[conversation_id] = []

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)

            user_message = message_data.get("message", "")
            depth_level = message_data.get("depth_level", 2)

            logger.info(f"WS message: {user_message[:50]}...")

            # Add user message
            conversations[conversation_id].append({
                "role": "user",
                "content": user_message,
            })

            # Send "thinking" status
            await websocket.send_json({
                "type": "status",
                "message": "Đang xử lý...",
            })

            # Route to Agent Service with streaming
            try:
                async with AsyncClient(timeout=120.0) as client:
                    response = await client.post(
                        f"{settings.agent_service_url}/invoke",
                        json={
                            "message": user_message,
                            "conversation_id": conversation_id,
                            "history": conversations[conversation_id][-20:],  # Last 20 messages
                            "depth_level": depth_level,
                            "stream": True,
                        },
                    )

                    if response.status_code == 200:
                        data = response.json()
                        assistant_message = data.get("message", "")

                        # Stream response token by token
                        tokens = assistant_message.split()
                        streamed_content = ""
                        for i, token in enumerate(tokens):
                            streamed_content += token + " "
                            await websocket.send_json({
                                "type": "token",
                                "content": token + " ",
                                "done": False,
                            })
                            # Small delay for streaming effect
                            if i % 5 == 0:
                                import asyncio
                                await asyncio.sleep(0.02)

                        # Send final message with metadata
                        await websocket.send_json({
                            "type": "message",
                            "content": assistant_message,
                            "confidence_score": data.get("confidence_score", 1.0),
                            "confidence_level": data.get("confidence_level", "high"),
                            "disclaimer": data.get("disclaimer"),
                            "sources": data.get("sources", []),
                            "citations": data.get("citations", []),
                            "tools_used": data.get("tools_used", []),
                            "done": True,
                        })

                        # Add to conversation
                        conversations[conversation_id].append({
                            "role": "assistant",
                            "content": assistant_message,
                        })
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Agent service error",
                        })

            except Exception as e:
                logger.error(f"WS agent error: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": f"Lỗi kết nối: {str(e)}",
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: conversation={conversation_id}")


@router.get("/{conversation_id}/history")
async def get_history(conversation_id: str):
    """Lấy lịch sử conversation."""
    if conversation_id not in conversations:
        return {"conversation_id": conversation_id, "messages": []}
    return {
        "conversation_id": conversation_id,
        "messages": conversations[conversation_id],
    }
