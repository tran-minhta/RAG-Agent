# RAG-Agent

<p align="center">
  <strong>AI-Agent hỗ trợ nghiên cứu học thuật, làm luận văn, và phân tích tài liệu</strong>
</p>

<p align="center">
  <a href="#-tính-năng">Tính năng</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-cấu-hình">Cấu hình</a> •
  <a href="#-api-reference">API</a> •
  <a href="#-license">License</a>
</p>

---

## 📋 Giới thiệu

RAG-Agent là hệ thống AI-Agent hoàn chỉnh, kết hợp **Retrieval-Augmented Generation (RAG)** với **Deep Research** để hỗ trợ sinh viên, nghiên cứu viên trong việc:

- 🔍 Tìm kiếm và phân tích tài liệu học thuật
- 📚 Xử lý PDF, Word, Markdown, HTML
- 🌐 Deep web browsing với nhiều cấp độ
- ✅ Xác minh citation và phát hiện hallucination
- 🎤 Chuyển đổi giọng nói (TTS/STT)
- 💻 Giao diện WebUI và CLI

## ✨ Tính năng chính

### 🤖 AI Agent với Multi-LLM
- **Ollama** (local, miễn phí): Llama 3.1, Qwen 2.5, Mistral
- **Gemini API** (cloud, free tier): Gemini 2.0 Flash
- Smart routing dựa trên độ phức tạp của câu hỏi
- LangGraph workflow cho multi-step reasoning

### 📚 Document Processing
- **MinerU**: Trích xuất PDF nâng cao (tables, images, equations)
- **MarkItDown**: Chuyển đổi Word, PPT, Excel, HTML sang Markdown
- **Magika**: Nhận dạng loại file tự động
- Hỗ trợ: PDF, DOCX, PPTX, XLSX, TXT, Markdown, HTML

### 🔍 RAG Pipeline
- **ChromaDB**: Vector store persistent, local
- **Sentence-Transformers**: Embedding models (all-MiniLM-L6-v2, bge-m3)
- Chunking strategies: Fixed-size, Sentence-based, Markdown-aware
- Cosine similarity search với metadata filtering

### 🌐 Deep Research (5 Levels)
| Level | Pages | Time | Description |
|-------|-------|------|-------------|
| 1 - Shallow | 10 | 1-2 min | Quick overview |
| 2 - Moderate | 50 | 5-10 min | Balanced research |
| 3 - Deep | 200 | 15-30 min | Comprehensive analysis |
| 4 - Exhaustive | 500 | 30-60 min | Systematic review |
| 5 - Adaptive | AI-decided | Variable | AI decides when to stop |

### ✅ Accuracy Engine
- **Citation Verification**: CrossRef, PubMed, ArXiv, Semantic Scholar
- **Hallucination Detection**: Pattern-based + source verification
- **Confidence Scoring**: Multi-factor calculation
  - \> 85%: Full answer
  - 60-85%: Answer + disclaimer
  - 40-60%: Search more
  - < 40%: Refuse + suggest sources

### 🎤 Voice (Offline)
- **Piper TTS**: Vietnamese (huymetric) + English (lessac)
- **Faster-Whisper**: Speech-to-Text (tiny, base, small, medium, large-v2)
- **Edge-TTS**: Fallback when Piper not available

### 💻 Interfaces
- **Chainlit WebUI**: Chat, file upload, deep research triggers
- **CLI**: Interactive terminal với Rich UI

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         RAG-Agent System                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │   Frontend   │    │     CLI      │    │  3rd Party   │       │
│  │  (Chainlit)  │    │   (Rich)     │    │    Apps      │       │
│  │   :8005      │    │              │    │              │       │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘       │
│         │                   │                   │                │
│         └───────────────────┼───────────────────┘                │
│                             │                                    │
│                    ┌────────▼────────┐                           │
│                    │     Gateway     │                           │
│                    │   (FastAPI)     │                           │
│                    │     :8000       │                           │
│                    └────────┬────────┘                           │
│                             │                                    │
│         ┌───────────────────┼───────────────────┐                │
│         │                   │                   │                │
│  ┌──────▼───────┐  ┌───────▼──────┐  ┌────────▼───────┐       │
│  │    Agent     │  │     RAG      │  │   Document     │       │
│  │   Service    │  │   Service    │  │    Service     │       │
│  │    :8001     │  │    :8002     │  │     :8003      │       │
│  │  LangGraph   │  │  ChromaDB    │  │  MinerU/MarkIt │       │
│  │  Multi-LLM   │  │  Embeddings  │  │  Magika        │       │
│  └──────────────┘  └──────────────┘  └────────────────┘       │
│                                                                  │
│         ┌───────────────────┼───────────────────┐                │
│         │                   │                   │                │
│  ┌──────▼───────┐  ┌───────▼──────┐  ┌────────▼───────┐       │
│  │   Research   │  │   Accuracy   │  │     Voice      │       │
│  │   Service    │  │   Engine     │  │    Service     │       │
│  │    :8007     │  │    :8008     │  │     :8004      │       │
│  │  Crawl4AI    │  │  Verify+Cite │  │  Piper/Whisper │       │
│  │  Multi-src   │  │  Hallucinate │  │  TTS/STT       │       │
│  └──────────────┘  └──────────────┘  └────────────────┘       │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐       │
│  │    Editor    │  │   ChromaDB   │  │    Ollama      │       │
│  │   Service    │  │   :8006      │  │    :11434      │       │
│  │    :8009     │  │  Vector DB   │  │  Local LLM     │       │
│  │  Formatting  │  │              │  │                 │       │
│  └──────────────┘  └──────────────┘  └────────────────┘       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- **Docker** & **Docker Compose** (recommended)
- OR **Python 3.13+** for local development
- **Ollama** (optional, for local LLM)

### Option 1: Docker (Recommended)

```bash
# 1. Clone repository
git clone https://github.com/your-username/RAG-Agent.git
cd RAG-Agent

# 2. Copy environment file
cp .env.example .env

# 3. Edit .env (add API keys if needed)
nano .env

# 4. Start all services
docker-compose up -d

# 5. Check status
docker-compose ps

# 6. Access WebUI
open http://localhost:8005
```

### Option 2: Local Development

```bash
# 1. Clone repository
git clone https://github.com/your-username/RAG-Agent.git
cd RAG-Agent

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install -e .

# 4. Start services (in separate terminals)
python -m services.gateway.main
python -m services.agent.main
python -m services.rag.main
python -m services.document.main
python -m services.voice.main
python -m services.research.main
python -m services.editor.main
python -m services.accuracy.main

# 5. Start Ollama (in another terminal)
ollama serve
ollama pull llama3.1:8b

# 6. Access API docs
open http://localhost:8000/docs
```

---

## 📁 Project Structure

```
RAG-Agent/
├── shared/                    # Shared modules
│   ├── config/
│   │   └── settings.py        # Centralized configuration
│   ├── models/
│   │   ├── document.py        # Document data models
│   │   ├── chat.py            # Chat/Agent models
│   │   └── agent.py           # Research/Verification models
│   └── utils/
│       └── logger.py          # Structured logging
│
├── services/
│   ├── gateway/               # API Gateway (FastAPI)
│   │   ├── main.py
│   │   ├── routers/
│   │   │   ├── chat.py
│   │   │   ├── documents.py
│   │   │   ├── research.py
│   │   │   ├── voice.py
│   │   │   └── health.py
│   │   └── Dockerfile
│   │
│   ├── agent/                 # AI Agent (LangGraph)
│   │   ├── main.py
│   │   ├── tools/
│   │   │   ├── knowledge_search.py
│   │   │   └── web_search.py
│   │   ├── prompts/
│   │   │   └── system_prompts.py
│   │   └── Dockerfile
│   │
│   ├── rag/                   # RAG Pipeline
│   │   ├── main.py
│   │   ├── embeddings/
│   │   │   └── embedding_manager.py
│   │   ├── index/
│   │   │   └── chroma_manager.py
│   │   ├── ingest/
│   │   │   └── chunker.py
│   │   ├── retriever/
│   │   │   └── vector_retriever.py
│   │   └── Dockerfile
│   │
│   ├── document/              # Document Processing
│   │   ├── main.py
│   │   ├── detectors/
│   │   │   └── magika_detector.py
│   │   ├── extractors/
│   │   │   ├── mineru_extractor.py
│   │   │   └── markitdown_extractor.py
│   │   ├── pipeline/
│   │   │   └── document_pipeline.py
│   │   └── Dockerfile
│   │
│   ├── research/              # Deep Research
│   │   ├── main.py
│   │   └── Dockerfile
│   │
│   ├── accuracy/              # Accuracy Engine
│   │   ├── main.py
│   │   └── Dockerfile
│   │
│   ├── editor/                # Professional Editor
│   │   ├── main.py
│   │   └── Dockerfile
│   │
│   ├── voice/                 # Voice Service
│   │   ├── main.py
│   │   └── Dockerfile
│   │
│   └── frontend/              # Chainlit WebUI
│       ├── app.py
│       ├── .chainlit/
│       └── Dockerfile
│
├── cli/                       # CLI Agent
│   └── main.py
│
├── tests/
│   └── test_integration.py
│
├── data/                      # Data directories
│   ├── cache/
│   ├── chroma/
│   ├── documents/
│   ├── models/
│   └── research_cache/
│
├── docker-compose.yml
├── pyproject.toml
├── .env.example
└── README.md
```

---

## 🔧 Cấu hình

### Environment Variables

```bash
# .env

# === LLM Providers ===
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.1:8b
OLLAMA_MODEL_LARGE=qwen2.5:14b

# Gemini (optional)
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.0-flash

# === Vector Store ===
CHROMA_HOST=chromadb
CHROMA_PORT=8000
CHROMA_COLLECTION=ragall_documents

# === Search APIs (optional) ===
TAVILY_API_KEY=your-tavily-key
BRAVE_API_KEY=your-brave-key
SEMANTIC_SCHOLAR_API_KEY=your-ss-key

# === Voice ===
TTS_ENGINE=piper
STT_ENGINE=whisper
WHISPER_MODEL=base
```

### Deep Research Levels

| Level | Max Pages | Timeout | Use Case |
|-------|-----------|---------|----------|
| 1 | 10 | 2 min | Quick questions |
| 2 | 50 | 10 min | Homework, essays |
| 3 | 200 | 30 min | Research papers |
| 4 | 500 | 60 min | Systematic reviews |
| 5 | 1000 | 2 hours | Comprehensive analysis |

### Confidence Thresholds

```python
CONFIDENCE_HIGH = 0.85    # Full answer
CONFIDENCE_MEDIUM = 0.60  # Answer + disclaimer
CONFIDENCE_LOW = 0.40     # Search more
CONFIDENCE_REFUSE = 0.40  # Refuse + suggest sources
```

---

## 📡 API Reference

### Base URL
```
http://localhost:8000
```

### Endpoints

#### Chat
```http
POST /chat/
Content-Type: application/json

{
  "message": "Phân tích tác động của AI trong giáo dục",
  "conversation_id": "session-123",
  "use_web_search": true
}
```

#### Document Upload
```http
POST /documents/upload
Content-Type: multipart/form-data

file: document.pdf
```

#### Deep Research
```http
POST /research/start
Content-Type: application/json

{
  "topic": "Machine Learning in Healthcare",
  "depth_level": 3,
  "sources": ["arxiv", "pubmed", "semantic_scholar", "web"]
}
```

#### Text-to-Speech
```http
POST /voice/tts
Content-Type: application/json

{
  "text": "Xin chào, đây là RAG-Agent",
  "language": "vi"
}
```

#### Speech-to-Text
```http
POST /voice/stt
Content-Type: multipart/form-data

file: audio.wav
```

### WebSocket Chat
```javascript
const ws = new WebSocket("ws://localhost:8000/chat/ws/session-id");
ws.send(JSON.stringify({ message: "Hello" }));
```

---

## 🛠️ Development

### Run Tests
```bash
# Unit tests
pytest tests/

# With coverage
pytest tests/ --cov=services --cov-report=html

# Integration tests
pytest tests/test_integration.py -v
```

### Code Quality
```bash
# Linting
ruff check .

# Type checking
mypy services/

# Format
ruff format .
```

### Add New Service
1. Create `services/new_service/`
2. Add `main.py` with FastAPI app
3. Create `Dockerfile`
4. Add to `docker-compose.yml`
5. Add router to gateway

---

## 🐳 Docker Services

| Service | Port | Description |
|---------|------|-------------|
| gateway | 8000 | API Gateway |
| agent | 8001 | AI Agent (LangGraph) |
| rag | 8002 | RAG Pipeline |
| document | 8003 | Document Processing |
| voice | 8004 | TTS/STT |
| frontend | 8005 | Chainlit WebUI |
| chromadb | 8006 | Vector Store |
| research | 8007 | Deep Research |
| accuracy | 8008 | Citation Verification |
| editor | 8009 | Professional Editing |
| ollama | 11434 | Local LLM Server |
| crawl4ai | 3000 | Web Crawler |

---

## 🤝 Contributing

1. Fork repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- [LangChain](https://github.com/langchain-ai/langchain) - LLM Framework
- [LangGraph](https://github.com/langchain-ai/langgraph) - Agent Workflow
- [ChromaDB](https://github.com/chroma-core/chroma) - Vector Store
- [Chainlit](https://github.com/Chainlit/chainlit) - WebUI Framework
- [Crawl4AI](https://github.com/unclecode/crawl4ai) - Web Crawler
- [Piper](https://github.com/rhasspy/piper) - Offline TTS
- [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper) - Offline STT

---

<p align="center">
  Made with ❤️ for researchers and students
</p>
