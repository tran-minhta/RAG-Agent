"""
RAG-Agent: Chainlit Frontend (v2)
Web UI cho RAG-Agent system sử dụng Chainlit 2.x.
"""

import chainlit as cl
import httpx
import os

# Gateway URL
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://gateway:8000")


# =============================================================================
# Starters
# =============================================================================

@cl.set_starters
async def set_starters():
    return [
        cl.Starter(label="Chat", message="Xin chào, tôi cần giúp đỡ"),
        cl.Starter(label="Upload tài liệu", message="/upload"),
        cl.Starter(label="Deep Research", message="/research"),
        cl.Starter(label="Kiểm tra hệ thống", message="/status"),
    ]


# =============================================================================
# Chat Start
# =============================================================================

@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("conversation_id", cl.context.session.id)
    cl.user_session.set("history", [])
    cl.user_session.set("model", "llama3.1:8b")
    cl.user_session.set("provider", "ollama")
    cl.user_session.set("use_web_search", True)

    await cl.Message(
        content=(
            "Chao mung den **RAG-Agent!**\n\n"
            "Go `/help` de xem danh sach lenh.\n"
            "Go `/settings` de cai dat model.\n\n"
            "**Cau hinh hien tai:**\n"
            "- Provider: Ollama\n"
            "- Model: llama3.1:8b\n"
            "- Web Search: Bat"
        )
    ).send()


# =============================================================================
# Commands
# =============================================================================

@cl.on_message
async def on_message(message: cl.Message):
    content = message.content.strip()

    if content.startswith("/"):
        await handle_command(content)
        return

    await chat_with_agent(content)


async def handle_command(command: str):
    cmd = command.lower().strip()

    if cmd == "/help":
        await cl.Message(
            content=(
                "**Danh sach lenh:**\n\n"
                "- `/help` - Tro giup\n"
                "- `/settings` - Cai dat\n"
                "- `/model ollama` - Dung Ollama\n"
                "- `/model gemini` - Dung Gemini\n"
                "- `/search on` - Bat web search\n"
                "- `/search off` - Tat web search\n"
                "- `/clear` - Xoa lich su\n"
                "- `/status` - Trang thai he thong\n"
                "- `/upload` - Upload tai lieu\n"
                "- `/research` - Deep Research"
            )
        ).send()

    elif cmd == "/settings":
        provider = cl.user_session.get("provider", "ollama")
        model = cl.user_session.get("model", "llama3.1:8b")
        ws = cl.user_session.get("use_web_search", True)
        await cl.Message(
            content=(
                "**Cai dat hien tai:**\n\n"
                f"- Provider: `{provider}`\n"
                f"- Model: `{model}`\n"
                f"- Web Search: `{'Bat' if ws else 'Tat'}`\n\n"
                "**Thay doi:**\n"
                "- `/model ollama` hoac `/model gemini`\n"
                "- `/search on` hoac `/search off`"
            )
        ).send()

    elif cmd.startswith("/model"):
        parts = cmd.split()
        if len(parts) < 2:
            await cl.Message(content="Dung: `/model ollama` hoac `/model gemini`").send()
            return

        provider = parts[1]
        if provider == "ollama":
            cl.user_session.set("provider", "ollama")
            cl.user_session.set("model", "llama3.1:8b")
            await cl.Message(content="Da chuyen sang **Ollama** (llama3.1:8b)").send()
        elif provider == "gemini":
            cl.user_session.set("provider", "gemini")
            cl.user_session.set("model", "gemini-2.0-flash")
            await cl.Message(content="Da chuyen sang **Gemini** (gemini-2.0-flash)").send()
        else:
            await cl.Message(content=f"Provider khong ho tro: `{provider}`").send()

    elif cmd.startswith("/search"):
        parts = cmd.split()
        if len(parts) < 2:
            await cl.Message(content="Dung: `/search on` hoac `/search off`").send()
            return

        state = parts[1]
        if state == "on":
            cl.user_session.set("use_web_search", True)
            await cl.Message(content="Da **bat** web search").send()
        elif state == "off":
            cl.user_session.set("use_web_search", False)
            await cl.Message(content="Da **tat** web search").send()

    elif cmd == "/clear":
        cl.user_session.set("history", [])
        await cl.Message(content="Da xoa lich su chat.").send()

    elif cmd == "/status":
        await check_system_status()

    elif cmd == "/upload":
        await cl.Message(
            content=(
                "**Upload tai lieu:**\n\n"
                "Su dung nut upload file o goc duoi ben trai.\n"
                "Ho tro: PDF, DOCX, TXT, Markdown, HTML"
            )
        ).send()

    elif cmd.startswith("/research"):
        parts = command.split(maxsplit=1)
        if len(parts) > 1 and parts[1].strip():
            await do_research(parts[1].strip())
        else:
            await cl.Message(
                content=(
                    "**Deep Research:**\n\n"
                    "Nhap chu de nghien cuu, vi du:\n"
                    "`/research Machine Learning in Healthcare`\n\n"
                    "Hoac chat truc tiep de agent tu research."
                )
            ).send()

    else:
        await cl.Message(
            content=f"Khong ro lenh: `{command}`\nGo `/help` de xem danh sach."
        ).send()


# =============================================================================
# Chat
# =============================================================================

async def chat_with_agent(content: str):
    conversation_id = cl.user_session.get("conversation_id")
    history = cl.user_session.get("history", [])
    use_web_search = cl.user_session.get("use_web_search", True)

    thinking = cl.Message(content="Dang suy nghi...")
    await thinking.send()

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{GATEWAY_URL}/chat/",
                json={
                    "message": content,
                    "conversation_id": conversation_id,
                    "history": history[-10:],
                    "use_web_search": use_web_search,
                },
            )

            if response.status_code == 200:
                data = response.json()

                history.append({"role": "user", "content": content})
                history.append({"role": "assistant", "content": data.get("message", "")})
                cl.user_session.set("history", history)

                reply = data.get("message", "Khong co phan hoi.")

                confidence = data.get("confidence_score", 1.0)
                if confidence < 0.85:
                    reply += f"\n\n---\n**Do tin cay:** {confidence:.0%}"

                sources = data.get("sources", [])
                if sources:
                    reply += "\n\n**Nguon tham khao:**"
                    for i, src in enumerate(sources[:5], 1):
                        if src.get("type") == "web":
                            reply += f"\n{i}. [{src.get('title', 'Link')}]({src.get('url', '#')})"
                        elif src.get("type") == "knowledge_base":
                            reply += f"\n{i}. Knowledge Base (score: {src.get('score', 0):.2f})"

                await thinking.update(content=reply)

            else:
                await thinking.update(content="Co loi xay ra. Vui long thu lai.")

    except httpx.TimeoutException:
        await thinking.update(content="Het thoi gian xu ly. Vui long thu cau hoi don gian hon.")
    except Exception as e:
        await thinking.update(content=f"Loi: {str(e)}")


# =============================================================================
# System Status
# =============================================================================

async def check_system_status():
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{GATEWAY_URL}/health/")
            if response.status_code == 200:
                data = response.json()
                lines = []
                for svc, status in data.items():
                    icon = "OK" if status == "healthy" else "FAIL"
                    lines.append(f"- {svc}: {icon}")
                await cl.Message(content="**Trang thai he thong:**\n\n" + "\n".join(lines)).send()
            else:
                await cl.Message(content="Khong the kiem tra trang thai.").send()
    except Exception:
        await cl.Message(content="Gateway khong kha dung.").send()


# =============================================================================
# Research
# =============================================================================

async def do_research(topic: str):
    await cl.Message(
        content=f"Dang nghien cuu: **{topic}**\nVui long cho..."
    ).send()

    try:
        async with httpx.AsyncClient(timeout=600) as client:
            response = await client.post(
                f"{GATEWAY_URL}/research/start",
                json={
                    "topic": topic,
                    "depth_level": 2,
                    "sources": ["arxiv", "pubmed", "semantic_scholar", "web"],
                },
            )

            if response.status_code == 200:
                data = response.json()
                await cl.Message(
                    content=(
                        f"**Nghien cuu hoan thanh!**\n\n"
                        f"- Pages crawled: {data.get('pages_crawled', 0)}\n"
                        f"- Session: {data.get('session_id', 'N/A')}\n\n"
                        f"Ket qua da duoc luu. Ban co the hoi ve chu de nay."
                    )
                ).send()
            else:
                await cl.Message(content=f"Nghien cuu that bai: {response.text}").send()

    except Exception as e:
        await cl.Message(content=f"Loi nghien cuu: {str(e)}").send()


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    cl.run_app()
