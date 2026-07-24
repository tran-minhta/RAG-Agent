"""
RAG-Agent: Centralized Settings
Doc cau hinh tu environment variables va .env file.
"""

from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Central settings — reads from env vars and .env file."""

    # --- Project ---
    project_name: str = "RAG-Agent"
    version: str = "0.1.0"
    debug: bool = False

    # --- Paths ---
    base_dir: Path = Path(__file__).resolve().parent.parent.parent
    data_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent / "data")

    # --- Ollama ---
    ollama_base_url: str = Field(default="http://ollama:11434", alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="qwen3.5:4b", alias="OLLAMA_MODEL")
    ollama_model_large: str = Field(default="qwen3.5:4b", alias="OLLAMA_MODEL_LARGE")

    # --- Gemini ---
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    gemini_model: str = "gemini-2.0-flash"

    # --- Embeddings ---
    embedding_model: str = "all-MiniLM-L6-v2"

    # --- ChromaDB ---
    chroma_host: str = "chromadb"
    chroma_port: int = 8000
    chroma_collection: str = "ragall_documents"

    # --- Search (optional) ---
    tavily_api_key: str = Field(default="", alias="TAVILY_API_KEY")
    brave_api_key: str = Field(default="", alias="BRAVE_API_KEY")
    semantic_scholar_api_key: str = Field(default="", alias="SEMANTIC_SCHOLAR_API_KEY")
    duckduckgo_enabled: bool = True

    # --- Web Crawling ---
    crawl4ai_url: str = "http://crawl4ai:3000"

    # --- Voice ---
    tts_engine: str = "piper"
    stt_engine: str = "whisper"
    whisper_model: str = Field(default="base", alias="WHISPER_MODEL")
    piper_model_dir: str = "/app/data/models/piper"
    piper_voice_vi: str = "vi-VN-hoaimy-medium"
    piper_voice_en: str = "en-US-lessac-medium"

    # --- Chainlit ---
    chainlit_auth_secret: str = Field(default="change-me-in-production", alias="CHAINLIT_AUTH_SECRET")

    # --- Service URLs ---
    agent_service_url: str = "http://agent:8001"
    rag_service_url: str = "http://rag:8002"
    document_service_url: str = "http://document:8003"
    voice_service_url: str = "http://voice:8004"
    research_service_url: str = "http://research:8007"
    editor_service_url: str = "http://editor:8009"
    accuracy_service_url: str = "http://accuracy:8008"
    frontend_service_url: str = "http://frontend:8005"
    gateway_port: int = 8000

    # --- Accuracy ---
    confidence_threshold_high: float = 0.85
    confidence_threshold_medium: float = 0.60
    confidence_threshold_low: float = 0.40

    # --- Research ---
    default_depth_level: int = 2
    max_crawl_pages: int = 200

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data_dir.mkdir(parents=True, exist_ok=True)


# Singleton — import Settings from here
settings = Settings()
