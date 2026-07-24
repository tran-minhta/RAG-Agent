"""
RAG-ALL: CLI Agent
Command-line interface cho RAG-ALL system.

Features:
  - Interactive chat
  - Document upload
  - Deep research
  - Voice commands
  - Rich terminal UI (Rich library)
"""

import os
import sys
import httpx
import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.table import Table
from rich import print as rprint

# Gateway URL
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:8000")

console = Console()


# =============================================================================
# CLI Application
# =============================================================================

class RAGALLCLI:
    """Interactive CLI for RAG-ALL."""

    def __init__(self):
        self.conversation_id = None
        self.history = []
        self.running = True

    async def run(self):
        """Main CLI loop."""
        self.print_welcome()

        while self.running:
            try:
                user_input = Prompt.ask("\n[bold blue]You[/bold blue]")

                if not user_input.strip():
                    continue

                # Handle commands
                if user_input.startswith("/"):
                    await self.handle_command(user_input)
                else:
                    await self.chat(user_input)

            except KeyboardInterrupt:
                console.print("\n[yellow]Exiting...[/yellow]")
                self.running = False
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

    def print_welcome(self):
        """Print welcome message."""
        welcome = """
# 🚀 RAG-ALL CLI

Chào mừng đến với **RAG-ALL** - Trợ lý AI nghiên cứu học thuật.

## Lệnh disponibles:
- `/help` - Xem trợ giúp
- `/upload` - Upload tài liệu
- `/research` - Deep research
- `/status` - Kiểm tra trạng thái
- `/clear` - Xóa lịch sử
- `/quit` - Thoát

---
"""
        console.print(Panel(Markdown(welcome), border_style="blue"))

    async def chat(self, message: str):
        """Send message to agent."""
        console.print("\n[dim]🤔 Đang suy nghĩ...[/dim]")

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    f"{GATEWAY_URL}/chat/",
                    json={
                        "message": message,
                        "conversation_id": self.conversation_id or "cli-session",
                        "history": self.history[-10:],
                        "use_web_search": True,
                    },
                )

                if response.status_code == 200:
                    data = response.json()

                    # Update history
                    self.history.append({"role": "user", "content": message})
                    self.history.append({"role": "assistant", "content": data["message"]})

                    # Display response
                    console.print("\n[bold green]RAG-ALL[/bold green]")
                    console.print(Markdown(data["message"]))

                    # Show confidence if low
                    confidence = data.get("confidence_score", 1.0)
                    if confidence < 0.85:
                        console.print(
                            f"\n[yellow]⚠️  Độ tin cậy: {confidence:.0%}[/yellow]"
                        )
                else:
                    console.print(f"[red]Lỗi: {response.status_code}[/red]")

        except httpx.TimeoutException:
            console.print("[yellow]⏰ Hết thời gian xử lý.[/yellow]")
        except Exception as e:
            console.print(f"[red]Lỗi: {e}[/red]")

    async def handle_command(self, command: str):
        """Handle CLI commands."""
        cmd = command.lower().strip()

        if cmd == "/help":
            self.print_help()
        elif cmd == "/upload":
            await self.upload_file()
        elif cmd == "/research":
            await self.start_research()
        elif cmd == "/status":
            await self.check_status()
        elif cmd == "/clear":
            self.history = []
            console.print("[green]🗑️  Đã xóa lịch sử.[/green]")
        elif cmd == "/quit" or cmd == "/exit":
            self.running = False
            console.print("[yellow]👋 Tạm biệt![/yellow]")
        else:
            console.print(f"[red]Không rõ lệnh: {command}[/red]")

    def print_help(self):
        """Print help message."""
        help_text = """
## Lệnh CLI

| Lệnh | Mô tả |
|-------|-------|
| `/help` | Xem trợ giúp |
| `/upload` | Upload tài liệu |
| `/research` | Deep research |
| `/status` | Kiểm tra trạng thái |
| `/clear` | Xóa lịch sử |
| `/quit` | Thoát |
"""
        console.print(Panel(Markdown(help_text), border_style="green"))

    async def upload_file(self):
        """Upload a file."""
        file_path = Prompt.ask("Nhập đường dẫn file")

        if not os.path.exists(file_path):
            console.print(f"[red]File không tồn tại: {file_path}[/red]")
            return

        console.print(f"[dim]📤 Đang upload: {file_path}...[/dim]")

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                with open(file_path, "rb") as f:
                    files = {"file": (os.path.basename(file_path), f)}
                    response = await client.post(
                        f"{GATEWAY_URL}/documents/upload",
                        files=files,
                    )

                if response.status_code == 200:
                    data = response.json()
                    console.print(
                        f"[green]✅ Upload thành công! "
                        f"Document ID: {data.get('document_id', 'N/A')}[/green]"
                    )
                else:
                    console.print(f"[red]Upload thất bại: {response.text}[/red]")

        except Exception as e:
            console.print(f"[red]Lỗi upload: {e}[/red]")

    async def start_research(self):
        """Start deep research."""
        topic = Prompt.ask("Nhập chủ đề nghiên cứu")
        depth = Prompt.ask("Depth level (1-5)", default="2")

        console.print(f"[dim]🔬 Bắt đầu research: {topic} (depth={depth})...[/dim]")

        try:
            async with httpx.AsyncClient(timeout=600) as client:
                response = await client.post(
                    f"{GATEWAY_URL}/research/",
                    json={
                        "topic": topic,
                        "depth_level": int(depth),
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    console.print(
                        f"[green]✅ Research hoàn thành! "
                        f"Pages: {data.get('pages_crawled', 0)}[/green]"
                    )
                else:
                    console.print(f"[red]Research thất bại: {response.text}[/red]")

        except Exception as e:
            console.print(f"[red]Lỗi research: {e}[/red]")

    async def check_status(self):
        """Check system status."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{GATEWAY_URL}/health/")

                if response.status_code == 200:
                    data = response.json()
                    services = data.get("services", data)

                    table = Table(title="Trang thai He thong")
                    table.add_column("Service", style="cyan")
                    table.add_column("Status", style="green")

                    for name, info in services.items():
                        if isinstance(info, dict):
                            status = info.get("status", "unknown")
                        else:
                            status = str(info)
                        status_text = "OK" if status == "healthy" else f"FAIL ({status})"
                        table.add_row(name, status_text)

                    console.print(table)
                else:
                    console.print("[red]Không thể kiểm tra trạng thái.[/red]")

        except Exception:
            console.print("[red]Gateway không khả dụng.[/red]")


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    """Main entry point."""
    cli = RAGALLCLI()
    asyncio.run(cli.run())


if __name__ == "__main__":
    main()
