"""
RAG-ALL: Centralized Settings
Đọc cấu hình từ environment variables và .env file.
"""

from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    Central settings for all RAG-ALL services.
    Reads from environment variables and .env file.
    """

    # --- Project ---
    project_name: str = "RAG-ALL"
    version: str = "0.1.0"
    debug: bool = False

    # --- Paths ---
    base_dir: Path = Path(__file__).resolve().parent.parent.parent
    data_dir: Path = Field(default=None)

    # --- LLM Providers ---
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3.1:8b"
    ollama_model_large: str = "qwen2.5:14b"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # --- Embeddings ---
    embedding_model: str = "all-MiniLM-L6-v2"

    # --- ChromaDB ---
    chroma_host: str = "chromadb"
    chroma_port: int = 8000
    chroma_collection: str = "ragall_documents"

    # --- Document Processing ---
    mineru_enabled: bool = True
    markitdown_enabled: bool = True
    magika_enabled: bool = True

    # --- Search ---
    tavily_api_key: str = ""
    brave_api_key: str = ""
    semantic_scholar_api_key: str = ""
    duckduckgo_enabled: bool = True

    # --- Web Crawling ---
    crawl4ai_url: str = "http://crawl4ai:3000"

    # --- Accuracy / Verification ---
    citation_verify_enabled: bool = True
    fact_crossref_enabled: bool = True
    hallucination_detection_enabled: bool = True
    confidence_threshold_high: float = 0.85
    confidence_threshold_medium: float = 0.60
    confidence_threshold_low: float = 0.40

    # --- Voice ---
    tts_engine: str = "piper"
    stt_engine: str = "whisper"
    whisper_model: str = "base"
    piper_model_dir: str = "/app/data/models/piper"
    piper_voice_vi: str = "vi-VN-hoaimy-medium"
    piper_voice_en: str = "en-US-lessac-medium"

    # --- API ---
    gateway_port: int = 8000
    agent_service_url: str = "http://agent:8001"
    rag_service_url: str = "http://rag:8002"
    document_service_url: str = "http://document:8003"
    voice_service_url: str = "http://voice:8004"
    research_service_url: str = "http://research:8007"
    editor_service_url: str = "http://editor:8009"
    accuracy_service_url: str = "http://accuracy:8008"

    # --- Research / Deep Browsing ---
    default_depth_level: int = 2  # Moderate
    max_crawl_pages: int = 200
    crawl_confidence_threshold: float = 0.85

    # --- Chainlit ---
    chainlit_auth_secret: str = "change-me-in-production"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.data_dir is None:
            self.data_dir = self.base_dir / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)


# Singleton instance - import this everywhere
settings = Settings()
