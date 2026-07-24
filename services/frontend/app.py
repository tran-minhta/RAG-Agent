"""
RAG-ALL: Chainlit Frontend
Web UI cho RAG-ALL system sử dụng Chainlit.

Features:
  - Chat interface với WebSocket
  - Document upload & management
  - Deep research triggers
  - Voice input/output
  - Confidence indicators
  - Source citations
"""

import chainlit as cl
import httpx
import os
from typing import Optional

# Gateway URL
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:8000")


# =============================================================================
# Chat Interface
# =============================================================================

@cl.set_starters
async def set_starters():
    """Set welcome starters for the chat."""
    return [
        cl.Starter(
            label="📚 Upload Document",
            message="Tôi muốn upload tài liệu để phân tích",
            icon="📚",
        ),
        cl.Starter(
            label="🔬 Deep Research",
            message="Tôi muốn nghiên cứu sâu về một chủ đề",
            icon="🔬",
        ),
        cl.Starter(
            label="💬 Chat with RAG",
            message="Hãy giúp tôi tìm kiếm thông tin",
            icon="💬",
        ),
        cl.Starter(
            label="📝 Academic Writing",
            message="Tôi cần hỗ trợ viết bài luận",
            icon="📝",
        ),
    ]


@cl.on_chat_start
async def on_chat_start():
    """Initialize chat session."""
    cl.user_session.set("conversation_id", cl.context.session.id)
    cl.user_session.set("history", [])

    await cl.Message(
        content="👋 Chào mừng đến với **RAG-ALL**!\n\n"
                "Tôi là trợ lý AI chuyên về nghiên cứu học thuật.\n\n"
                "**Khả năng:**\n"
                "- 🔍 Tìm kiếm trong tài liệu đã upload\n"
                "- 🌐 Tìm kiếm web và paper học thuật\n"
                "- 📊 Phân tích tài liệu PDF, Word, Markdown\n"
                "- 📝 Hỗ trợ viết luận văn, báo cáo\n"
                "- 🎤 Chuyển đổi giọng nói\n\n"
                "**Gợi ý:** Bắt đầu bằng cách upload tài liệu hoặc đặt câu hỏi!",
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming messages."""
    conversation_id = cl.user_session.get("conversation_id")
    history = cl.user_session.get("history", [])

    # Check for special commands
    if message.content.startswith("/"):
        await handle_command(message.content)
        return

    # Show thinking indicator
    async with cl.Message(content="🤔 Đang suy nghĩ...").send() as thinking_msg:
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    f"{GATEWAY_URL}/chat/",
                    json={
                        "message": message.content,
                        "conversation_id": conversation_id,
                        "history": history[-10:],  # Last 10 messages
                        "use_web_search": True,
                    },
                )

                if response.status_code == 200:
                    data = response.json()

                    # Update history
                    history.append({"role": "user", "content": message.content})
                    history.append({"role": "assistant", "content": data["message"]})
                    cl.user_session.set("history", history)

                    # Build response with metadata
                    response_text = data["message"]

                    # Add confidence indicator
                    confidence = data.get("confidence_score", 0)
                    if confidence < 0.85:
                        response_text += f"\n\n---\n⚠️ **Độ tin cậy:** {confidence:.0%}"
                        if data.get("disclaimer"):
                            response_text += f"\n{data['disclaimer']}"

                    # Add sources
                    sources = data.get("sources", [])
                    if sources:
                        response_text += "\n\n📚 **Nguồn tham khảo:**"
                        for i, src in enumerate(sources[:5], 1):
                            if src.get("type") == "web":
                                response_text += f"\n{i}. [{src.get('title', 'Link')}]({src.get('url', '#')})"
                            elif src.get("type") == "knowledge_base":
                                response_text += f"\n{i}. 📄 Knowledge Base (score: {src.get('score', 0):.2f})"

                    # Update thinking message
                    thinking_msg.content = response_text

                else:
                    thinking_msg.content = "❌ Xin lỗi, có lỗi xảy ra. Vui lòng thử lại."

        except httpx.TimeoutException:
            thinking_msg.content = "⏰ Hết thời gian xử lý. Vui lòng thử câu hỏi đơn giản hơn."
        except Exception as e:
            thinking_msg.content = f"❌ Lỗi: {str(e)}"


async def handle_command(command: str):
    """Handle special commands."""
    cmd = command.lower().strip()

    if cmd == "/help":
        await cl.Message(
            content="📋 **Danh sách lệnh:**\n\n"
                    "- `/help` - Hiển thị trợ giúp\n"
                    "- `/upload` - Upload tài liệu\n"
                    "- `/research` - Bắt đầu deep research\n"
                    "- `/clear` - Xóa lịch sử chat\n"
                    "- `/status` - Kiểm tra trạng thái hệ thống"
        ).send()

    elif cmd == "/clear":
        cl.user_session.set("history", [])
        await cl.Message(content="🗑️ Đã xóa lịch sử chat.").send()

    elif cmd == "/status":
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{GATEWAY_URL}/health/")
                if response.status_code == 200:
                    data = response.json()
                    await cl.Message(
                        content=f"✅ **Trạng thái hệ thống:**\n\n"
                               f"- Gateway: {'🟢 Healthy' if data.get('gateway') == 'healthy' else '🔴 Unhealthy'}\n"
                               f"- Agent: {'🟢 Healthy' if data.get('agent') == 'healthy' else '🔴 Unhealthy'}\n"
                               f"- RAG: {'🟢 Healthy' if data.get('rag') == 'healthy' else '🔴 Unhealthy'}"
                    ).send()
                else:
                    await cl.Message(content="❌ Không thể kiểm tra trạng thái.").send()
        except Exception:
            await cl.Message(content="❌ Gateway không khả dụng.").send()

    else:
        await cl.Message(content=f"❓ Không rõ lệnh: `{command}`. Gõ `/help` để xem danh sách lệnh.").send()


# =============================================================================
# File Upload
# =============================================================================

@cl.on_file_upload
async def on_file_upload(files: list[cl.File]):
    """Handle file uploads."""
    for file in files:
        await cl.Message(
            content=f"📤 Đang upload: **{file.name}** ({file.size} bytes)..."
        ).send()

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                # Upload file
                with open(file.path, "rb") as f:
                    files_data = {"file": (file.name, f, "application/octet-stream")}
                    response = await client.post(
                        f"{GATEWAY_URL}/documents/upload",
                        files=files_data,
                    )

                if response.status_code == 200:
                    data = response.json()
                    await cl.Message(
                        content=f"✅ Upload thành công!\n\n"
                               f"- **Document ID:** {data.get('document_id', 'N/A')}\n"
                               f"- **Pages:** {data.get('pages', 'N/A')}\n"
                               f"- **Chunks:** {data.get('chunks', 'N/A')}"
                    ).send()
                else:
                    await cl.Message(
                        content=f"❌ Upload thất bại: {response.text}"
                    ).send()

        except Exception as e:
            await cl.Message(
                content=f"❌ Lỗi upload: {str(e)}"
            ).send()


# =============================================================================
# Deep Research
# =============================================================================

async def start_deep_research(topic: str, depth: int = 2):
    """Start deep research process."""
    await cl.Message(
        content=f"🔬 **Bắt đầu Deep Research:**\n\n"
               f"- **Chủ đề:** {topic}\n"
               f"- **Depth Level:** {depth}/5\n"
               f"- **Trạng thái:** Đang thu thập dữ liệu..."
    ).send()

    try:
        async with httpx.AsyncClient(timeout=600) as client:
            response = await client.post(
                f"{GATEWAY_URL}/research/start",
                json={
                    "topic": topic,
                    "depth_level": depth,
                    "sources": ["arxiv", "pubmed", "semantic_scholar", "web"],
                },
            )

            if response.status_code == 200:
                data = response.json()
                await cl.Message(
                    content=f"✅ **Deep Research hoàn thành!**\n\n"
                           f"- **Pages crawled:** {data.get('pages_crawled', 0)}\n"
                           f"- **Session ID:** {data.get('session_id', 'N/A')}\n\n"
                           f"Kết quả đã được lưu. Bạn có thể hỏi về chủ đề này."
                ).send()
            else:
                await cl.Message(
                    content=f"❌ Deep research thất bại: {response.text}"
                ).send()

    except Exception as e:
        await cl.Message(
            content=f"❌ Lỗi deep research: {str(e)}"
        ).send()


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    chainlit.run_app()
