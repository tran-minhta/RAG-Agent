"""
RAG-Agent: Chainlit Frontend (v2)
Web UI cho RAG-Agent — Chainlit 2.x compatible.
"""

import chainlit as cl
import httpx
import os

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://gateway:8000")


# =============================================================================
# Starters
# =============================================================================

@cl.set_starters
async def set_starters():
    return [
        cl.Starter(label="Chat", message="Xin chao, toi can giup do"),
        cl.Starter(label="Upload tai lieu", message="upload tai lieu"),
        cl.Starter(label="Deep Research", message="research Machine Learning"),
        cl.Starter(label="Kiem tra he thong", message="kiem tra he thong"),
    ]


# =============================================================================
# Chat Start
# =============================================================================

@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("conversation_id", cl.context.session.id)
    cl.user_session.set("history", [])
    cl.user_session.set("model", None)  # None = use server default
    cl.user_session.set("provider", "ollama")
    cl.user_session.set("use_web_search", True)

    # Kiem tra ket noi + lay danh sach models
    status_text = await _build_welcome()
    await cl.Message(content=status_text).send()


async def _build_welcome() -> str:
    """Xay dung tin chao mung voi trang thai he thong."""
    lines = ["**Chao mung den RAG-Agent!**\n"]

    # Kiem tra health
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{GATEWAY_URL}/health/")
            if r.status_code == 200:
                data = r.json()
                services = data.get("services", {})
                ok_count = sum(1 for s in services.values() if s.get("status") == "healthy")
                total = len(services)
                lines.append(f"**He thong:** {ok_count}/{total} services OK\n")

                # Chi hien thi services that bai
                failed = [name for name, s in services.items() if s.get("status") != "healthy"]
                if failed:
                    lines.append(f"  Loi: {', '.join(failed)}\n")
    except Exception:
        lines.append("**He thong:** Gateway khong kha dung\n")

    # Lay danh sach models
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{GATEWAY_URL}/models")
            if r.status_code == 200:
                data = r.json()
                ollama_models = data.get("ollama", [])
                if ollama_models:
                    lines.append("**Ollama models:**")
                    for m in ollama_models:
                        lines.append(f"  - {m['name']} ({m.get('size', '')})")
                    lines.append("")

                    # Hien thi model dang dung
                    current = cl.user_session.get("model")
                    if current:
                        lines.append(f"**Model hien tai:** `{current}`")
                    else:
                        lines.append(f"**Model hien tai:** `{ollama_models[0]['name']}` (server default)")
                else:
                    lines.append("**Ollama:** Khong co model nao\n")
    except Exception:
        pass

    lines.append("\nGo **/help** de xem danh sach lenh.")
    return "\n".join(lines)


# =============================================================================
# Commands
# =============================================================================

@cl.on_message
async def on_message(message: cl.Message):
    content = message.content.strip()
    cmd = content.lower()

    # --- help ---
    if cmd in ("/help", "help"):
        await cl.Message(content=_help_text()).send()
        return

    # --- settings / setting ---
    if cmd in ("/settings", "/setting", "settings", "setting"):
        await cl.Message(content=await _settings_text()).send()
        return

    # --- model ---
    if cmd.startswith("/model ") or cmd.startswith("model "):
        arg = content.split(None, 1)[1].strip() if len(content.split(None, 1)) > 1 else ""
        await _switch_model(arg)
        return

    # --- search ---
    if cmd.startswith("/search ") or cmd.startswith("search "):
        arg = content.split(None, 1)[1].strip().lower() if len(content.split(None, 1)) > 1 else ""
        if arg == "on":
            cl.user_session.set("use_web_search", True)
            await cl.Message(content="Da **bat** web search.").send()
        elif arg == "off":
            cl.user_session.set("use_web_search", False)
            await cl.Message(content="Da **tat** web search.").send()
        else:
            await cl.Message(content="Dung: **/search on** hoac **/search off**").send()
        return

    # --- clear ---
    if cmd in ("/clear", "clear"):
        cl.user_session.set("history", [])
        await cl.Message(content="Da xoa lich su chat.").send()
        return

    # --- status ---
    if cmd in ("/status", "status", "kiem tra he thong"):
        welcome = await _build_welcome()
        await cl.Message(content=welcome).send()
        return

    # --- upload ---
    if cmd in ("/upload", "upload", "upload tai lieu"):
        await cl.Message(
            content=(
                "**Upload tai lieu:**\n\n"
                "Su dung nut upload file o goc duoi ben trai.\n"
                "Ho tro: PDF, DOCX, TXT, Markdown, HTML"
            )
        ).send()
        return

    # --- research ---
    if cmd.startswith("/research") or cmd.startswith("research"):
        parts = content.split(maxsplit=1)
        topic = parts[1].strip() if len(parts) > 1 else ""
        if topic:
            await _do_research(topic)
        else:
            await cl.Message(
                content=(
                    "**Deep Research:**\n\n"
                    "Nhap chu de nghien cuu, vi du:\n"
                    "**/research Machine Learning in Healthcare**"
                )
            ).send()
        return

    # --- mac dinh: chat ---
    await chat_with_agent(content)


def _help_text():
    return (
        "**Danh sach lenh:**\n\n"
        "- **/help** — Tro giup\n"
        "- **/settings** — Cai dat hien tai\n"
        "- **/model <ten>** — Chuyen model (xem danh sach o /settings)\n"
        "- **/search on/off** — Bat/tat web search\n"
        "- **/clear** — Xoa lich su\n"
        "- **/status** — Kiem tra he thong + models\n"
        "- **/upload** — Upload tai lieu\n"
        "- **/research <chu de>** — Deep Research"
    )


async def _settings_text():
    provider = cl.user_session.get("provider", "ollama")
    model = cl.user_session.get("model") or "(server default)"
    ws = cl.user_session.get("use_web_search", True)

    # Lay danh sach models
    models_info = ""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{GATEWAY_URL}/models")
            if r.status_code == 200:
                data = r.json()
                ollama_models = data.get("ollama", [])
                if ollama_models:
                    models_info = "**Ollama models:**\n"
                    for m in ollama_models:
                        models_info += f"  - `{m['name']}` ({m.get('size', '')})\n"
                gemini_models = data.get("gemini", [])
                if gemini_models:
                    models_info += "\n**Gemini models:**\n"
                    for m in gemini_models:
                        models_info += f"  - `{m['name']}` — {m.get('description', '')}\n"
    except Exception:
        models_info = "(Khong the lay danh sach models)"

    return (
        f"**Cai dat hien tai:**\n\n"
        f"- Provider: `{provider}`\n"
        f"- Model: `{model}`\n"
        f"- Web Search: `{'Bat' if ws else 'Tat'}`\n\n"
        f"{models_info}\n\n"
        f"**Thay doi:**\n"
        f"- **/model <ten>** — Chuyen model\n"
        f"- **/search on/off** — Bat/tat web search"
    )


async def _switch_model(name: str):
    if not name:
        await cl.Message(content="Dung: **/model <ten-model>**").send()
        return

    # Kiem tra model co ton tai trong Ollama khong
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{GATEWAY_URL}/models")
            if r.status_code == 200:
                data = r.json()
                ollama_models = [m["name"] for m in data.get("ollama", [])]

                # Tim model phu hop (fuzzy match)
                matched = None
                for m in ollama_models:
                    if name.lower() in m.lower():
                        matched = m
                        break

                if matched:
                    cl.user_session.set("model", matched)
                    cl.user_session.set("provider", "ollama")
                    await cl.Message(content=f"Da chuyen sang **{matched}**").send()
                elif name.lower() in ("gemini", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"):
                    cl.user_session.set("model", name)
                    cl.user_session.set("provider", "gemini")
                    await cl.Message(content=f"Da chuyen sang **{name}** (Gemini)").send()
                else:
                    await cl.Message(
                        content=(
                            f"Khong tim thay model `{name}`.\n\n"
                            f"Models co san: {', '.join(ollama_models)}"
                        )
                    ).send()
    except Exception:
        # Khong kiem tra duoc, cho phep doi
        cl.user_session.set("model", name)
        await cl.Message(content=f"Da chuyen sang **{name}**").send()


# =============================================================================
# Chat
# =============================================================================

async def chat_with_agent(content: str):
    conversation_id = cl.user_session.get("conversation_id")
    history = cl.user_session.get("history", [])
    use_web_search = cl.user_session.get("use_web_search", True)
    provider = cl.user_session.get("provider", "ollama")
    model = cl.user_session.get("model")

    thinking = cl.Message(content="Dang suy nghi...")
    await thinking.send()

    try:
        async with httpx.AsyncClient(timeout=180) as client:
            response = await client.post(
                f"{GATEWAY_URL}/chat/",
                json={
                    "message": content,
                    "conversation_id": conversation_id,
                    "history": history[-10:],
                    "use_web_search": use_web_search,
                    "provider": provider,
                    "model": model,
                },
            )

            if response.status_code == 200:
                data = response.json()

                history.append({"role": "user", "content": content})
                history.append({"role": "assistant", "content": data.get("message", "")})
                cl.user_session.set("history", history[-20:])

                reply = data.get("message", "Khong co phan hoi.")

                # Hien thi model da dung
                used_model = data.get("model", "")
                if used_model:
                    reply += f"\n\n---\n*Model: {used_model}*"

                confidence = data.get("confidence_score", 1.0)
                if confidence < 0.85:
                    reply += f"\n**Do tin cay:** {confidence:.0%}"

                sources = data.get("sources", [])
                if sources:
                    reply += "\n\n**Nguon tham khao:**"
                    for i, src in enumerate(sources[:5], 1):
                        if src.get("type") == "web":
                            reply += f"\n{i}. [{src.get('title', 'Link')}]({src.get('url', '#')})"
                        elif src.get("type") == "knowledge_base":
                            reply += f"\n{i}. KB (score: {src.get('score', 0):.2f})"

                await thinking.remove()
                await cl.Message(content=reply).send()
            else:
                await thinking.remove()
                await cl.Message(content="Co loi xay ra. Vui long thu lai.").send()

    except httpx.TimeoutException:
        await thinking.remove()
        await cl.Message(content="Het thoi gian xu ly. Vui long thu cau hoi don gian hon.").send()
    except Exception as e:
        await thinking.remove()
        await cl.Message(content=f"Loi: {str(e)}").send()


# =============================================================================
# Research
# =============================================================================

async def _do_research(topic: str):
    await cl.Message(content=f"Dang nghien cuu: **{topic}**\nVui long cho...").send()

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
                        f"Ket qua da duoc luu."
                    )
                ).send()
            else:
                await cl.Message(content=f"Nghien cuu that bai: {response.text}").send()

    except Exception as e:
        await cl.Message(content=f"Loi nghien cuu: {str(e)}").send()


if __name__ == "__main__":
    cl.run_app()
