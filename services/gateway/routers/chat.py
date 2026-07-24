"""
RAG-ALL: Gateway Router - Chat
REST + WebSocket chat endpoints.
Routes requests to Agent Service.
"""

import json
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from httpx import AsyncClient

from shared.config.settings import settings
from shared.models.chat import ChatRequest, ChatResponse
from shared.utils.logger import gateway_logger as logger

router = APIRouter()

# In-memory conversation store
conversations: dict[str, list[dict]] = {}


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """REST chat endpoint."""
    conversation_id = request.conversation_id or str(uuid.uuid4())
    logger.info(f"Chat: conv={conversation_id}, msg={request.message[:50]}...")

    if conversation_id not in conversations:
        conversations[conversation_id] = []

    conversations[conversation_id].append({
        "role": "user",
        "content": request.message,
    })

    try:
        async with AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"{settings.agent_service_url}/invoke",
                json={
                    "message": request.message,
                    "conversation_id": conversation_id,
                    "history": conversations[conversation_id],
                    "depth_level": request.depth_level,
                    "use_web_search": request.use_web_search,
                    "provider": getattr(request, "provider", None),
                    "model": getattr(request, "model", None),
                },
            )

            if response.status_code == 200:
                data = response.json()
                chat_response = ChatResponse(**data)

                conversations[conversation_id].append({
                    "role": "assistant",
                    "content": chat_response.message,
                })

                # Limit history
                if len(conversations[conversation_id]) > 50:
                    conversations[conversation_id] = conversations[conversation_id][-30:]

                return chat_response
            else:
                logger.error(f"Agent error: {response.status_code}")
                return ChatResponse(
                    message="Co loi xay ra. Vui long thu lai.",
                    conversation_id=conversation_id,
                    confidence_score=0.0,
                    confidence_level="very_low",
                    refusal=True,
                    refusal_reason="Agent unavailable",
                )

    except Exception as e:
        logger.error(f"Chat error: {e}")
        return ChatResponse(
            message="Khong ket noi duoc toi Agent Service.",
            conversation_id=conversation_id,
            confidence_score=0.0,
            confidence_level="very_low",
            refusal=True,
            refusal_reason=str(e),
        )


@router.websocket("/ws/{conversation_id}")
async def chat_websocket(websocket: WebSocket, conversation_id: str):
    """WebSocket chat endpoint."""
    await websocket.accept()
    logger.info(f"WS connected: {conversation_id}")

    if conversation_id not in conversations:
        conversations[conversation_id] = []

    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)

            user_message = message_data.get("message", "")
            provider = message_data.get("provider")
            model = message_data.get("model")

            conversations[conversation_id].append({
                "role": "user",
                "content": user_message,
            })

            await websocket.send_json({"type": "status", "message": "Dang xu ly..."})

            try:
                async with AsyncClient(timeout=360.0) as client:
                    response = await client.post(
                        f"{settings.agent_service_url}/invoke",
                        json={
                            "message": user_message,
                            "conversation_id": conversation_id,
                            "history": conversations[conversation_id][-20:],
                            "provider": provider,
                            "model": model,
                        },
                    )

                    if response.status_code == 200:
                        data = response.json()
                        content = data.get("message", "")

                        # Stream token by token
                        tokens = content.split()
                        for i, token in enumerate(tokens):
                            await websocket.send_json({
                                "type": "token",
                                "content": token + " ",
                                "done": False,
                            })
                            if i % 5 == 0:
                                import asyncio
                                await asyncio.sleep(0.02)

                        await websocket.send_json({
                            "type": "message",
                            "content": content,
                            "confidence_score": data.get("confidence_score", 1.0),
                            "sources": data.get("sources", []),
                            "model": data.get("model", ""),
                            "done": True,
                        })

                        conversations[conversation_id].append({
                            "role": "assistant",
                            "content": content,
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
                    "message": f"Loi ket noi: {str(e)}",
                })

    except WebSocketDisconnect:
        logger.info(f"WS disconnected: {conversation_id}")


@router.get("/{conversation_id}/history")
async def get_history(conversation_id: str):
    """Lay lich su conversation."""
    if conversation_id not in conversations:
        return {"conversation_id": conversation_id, "messages": []}
    return {
        "conversation_id": conversation_id,
        "messages": conversations[conversation_id],
    }
