# RAG-ALL - AI Agent hỗ trợ Nghiên cứu & Học tập

## Tổng quan Dự án
AI-Agent hỗ trợ nghiên cứu, học tập, làm luận án, luận văn.
- CLI + WebUI (Chainlit) + Voice (Piper TTS / Whisper STT)
- Microservice architecture
- Multi-LLM: Ollama (local) + Gemini API + Free models
- Deep Web Browsing với depth control
- Professional Editing với accuracy enforcement

## Kiến trúc Tổng thể

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐     │
│  │  CLI Agent   │  │  Chainlit    │  │  Voice Interface     │     │
│  │  (Terminal)  │  │  WebUI       │  │  (Piper/Whisper)     │     │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘     │
└─────────┼─────────────────┼─────────────────────┼──────────────────┘
          ▼                 ▼                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     API GATEWAY (FastAPI)                            │
└─────────────────────────┬───────────────────────────────────────────┘
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
┌─────────────────┐ ┌──────────────┐ ┌─────────────────────────┐
│  AGENT SERVICE  │ │ RAG SERVICE  │ │  DOCUMENT SERVICE       │
│  (LangGraph)    │ │ (ChromaDB)   │ │  (MinerU/MarkItDown)    │
└─────────────────┘ └──────────────┘ └─────────────────────────┘
          │               │               │
          ▼               ▼               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  RESEARCH SERVICE         │ │ EDITOR SERVICE      │ │ VOICE SERVICE │
│  (Deep Browser + Search)  │ │ (Accuracy + Format) │ │ (TTS/STT)     │
└─────────────────────────────────────────────────────────────────────┘
          │               │               │
          ▼               ▼               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     STORAGE LAYER                                   │
│  ChromaDB (Vectors) │ PostgreSQL (Metadata) │ File Storage         │
└─────────────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.13+ |
| Package Manager | uv |
| Agent Framework | LangChain + LangGraph |
| RAG | ChromaDB + sentence-transformers |
| Document Processing | MinerU, MarkItDown, Magika |
| Web Crawling | Crawl4AI (self-hosted), Jina Reader |
| Search | DuckDuckGo, arXiv, Semantic Scholar |
| LLM | Ollama (local), Gemini API |
| TTS | Piper TTS |
| STT | OpenAI Whisper / Faster-Whisper |
| WebUI | Chainlit |
| API | FastAPI |
| Container | Docker + Docker Compose |

## Implementation Phases

### Phase 1: Project Structure + Docker Compose
### Phase 2: Shared Models & Config
### Phase 3: Gateway Service
### Phase 4: Document Service
### Phase 5: RAG Service
### Phase 6: Agent Service
### Phase 7: Research Service (Deep Browser)
### Phase 8: Accuracy Engine
### Phase 9: Editor Service
### Phase 10: Voice Service
### Phase 11: Chainlit Frontend
### Phase 12: CLI Agent
### Phase 13: Integration & Testing

## Depth Levels

| Level | Name | Depth | Pages | Time |
|-------|------|-------|-------|------|
| 1 | Shallow | 1 | 10 | 1-2 min |
| 2 | Moderate | 2 | 50 | 5-10 min |
| 3 | Deep | 3 | 200 | 15-30 min |
| 4 | Exhaustive | 5 | 500 | 30-60 min |
| 5 | Adaptive | Auto | 300 | Variable |

## Accuracy Enforcement

| Confidence | Action |
|-----------|--------|
| > 0.85 | Full answer + citations |
| 0.60-0.85 | Answer + disclaimer |
| 0.40-0.60 | Search more sources |
| < 0.40 | Refuse + suggest sources |
