# 🚀 Hướng dẫn Triển khai RAG-Agent

## Mục lục

- [Phương án 1: Docker Compose (Default)](#phương-án-1-docker-compose-default)
- [Phương án 2: Base Image + Docker Compose (Nhanh nhất)](#phương-án-2-base-image--docker-compose-nhanh-nhất)
- [Phương án 3: Docker BuildKit (Song song)](#phương-án-3-docker-buildkit-song-song)
- [Phương án 4: Pre-built Images (Docker Hub)](#phương-án-4-pre-built-images-docker-hub)
- [Phương án 5: Local Development (Không dùng Docker)](#phương-án-5-local-development-không-dùng-docker)
- [So sánh các phương án](#so-sánh-các-phương-án)
- [Troubleshooting](#troubleshooting)
- [Tối ưu hóa hiệu suất](#tối-ưu-hiệu-suất)

---

## Phương án 1: Docker Compose (Default)

### Tổng quan
- **Thời gian build lần đầu**: ~1000s (16 phút)
- **Thời gian build lại**: ~1000s
- **Độ phức tạp**: Dễ
- **Phù hợp**: Beginners, Development

### Ưu điểm
- Đơn giản nhất, chỉ cần 1 lệnh
- Tự động build tất cả services
- Không cần cấu hình thêm

### Nhược điểm
- Chậm vì build tuần tự từng service
- Mỗi service cài lại dependencies từ đầu

### Bước 1: Clone repository

```bash
# Clone từ GitHub
git clone https://github.com/tran-minhta/RAG-Agent.git

# Vào thư mục
cd RAG-Agent
```

### Bước 2: Copy file cấu hình

```bash
# Copy file .env.example sang .env
cp .env.example .env

# Kiểm tra file đã copy
ls -la .env
```

### Bước 3: Chỉnh sửa .env

```bash
# Mở file .env để chỉnh sửa
nano .env

# Hoặc dùng vim
vim .env
```

**Nội dung .env tối thiểu:**

```bash
# === LLM Providers ===
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.1:8b
OLLAMA_MODEL_LARGE=qwen2.5:14b

# Gemini API (tùy chọn - cần API key)
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.0-flash

# === Vector Store ===
CHROMA_HOST=chromadb
CHROMA_PORT=8000
CHROMA_COLLECTION=ragall_documents

# === Search APIs (tùy chọn) ===
TAVILY_API_KEY=
BRAVE_API_KEY=
SEMANTIC_SCHOLAR_API_KEY=

# === Voice ===
TTS_ENGINE=piper
STT_ENGINE=whisper
WHISPER_MODEL=base
PIPER_MODEL_DIR=/app/data/models/piper
```

### Bước 4: Build và chạy

```bash
# Build và chạy tất cả services
docker-compose up -d

# Hoặc build trước rồi chạy
docker-compose build
docker-compose up -d
```

### Bước 5: Kiểm tra trạng thái

```bash
# Kiểm tra tất cả services đang chạy
docker-compose ps

# Kết quả mong đợi:
# NAME                STATUS              PORTS
# rag-agent-gateway-1 running             0.0.0.0:8000->8000/tcp
# rag-agent-agent-1   running             0.0.0.0:8001->8001/tcp
# rag-agent-rag-1     running             0.0.0.0:8002->8002/tcp
# ...
```

### Bước 6: Xem logs

```bash
# Xem logs tất cả services
docker-compose logs -f

# Xem logs service cụ thể
docker-compose logs -f gateway
docker-compose logs -f agent

# Xem logs 100 dòng cuối
docker-compose logs --tail=100 gateway
```

### Bước 7: Truy cập

```bash
# WebUI (Chainlit)
open http://localhost:8005

# API Docs (Swagger)
open http://localhost:8000/docs

# API Docs (ReDoc)
open http://localhost:8000/redoc
```

### Các lệnh thường dùng

```bash
# Dừng tất cả services
docker-compose down

# Dừng và xóa volumes (xóa dữ liệu)
docker-compose down -v

# Rebuild khi có thay đổi code
docker-compose up -d --build

# Rebuild 1 service cụ thể
docker-compose up -d --build agent

# Restart service
docker-compose restart gateway

# Vào shell của container
docker-compose exec gateway bash
docker-compose exec agent bash

# Xem resource usage
docker stats
```

---

## Phương án 2: Base Image + Docker Compose (Nhanh nhất)

### Tổng quan
- **Thời gian build lần đầu**: ~10 phút
- **Thời gian build lại**: ~30 giây
- **Độ phức tạp**: Trung bình
- **Phù hợp**: Production, CI/CD

### Ưu điểm
- ✅ Giảm 80% thời gian build
- ✅ Build lại chỉ ~30 giây (chỉ copy code)
- ✅ Tiết kiệm disk space (~4GB thay vì ~8GB)
- ✅ Dễ maintain

### Nhược điểm
- Cần build base image lần đầu (~10 phút)
- Cần update base image khi thay đổi dependencies

### Bước 1: Tạo file base.Dockerfile

```bash
# Tạo file base.Dockerfile
cat > base.Dockerfile << 'EOF'
# =============================================================================
# RAG-Agent Base Image
# Chứa tất cả dependencies cho tất cả services
# =============================================================================

FROM python:3.13-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy shared modules trước (cho caching)
COPY shared/ /app/shared/

# Install ALL Python dependencies
COPY pyproject.toml /app/
RUN pip install --no-cache-dir \
    # === API / Server ===
    fastapi uvicorn httpx python-multipart \
    # === Agent Framework ===
    langchain-core langchain langchain-community langchain-text-splitters langgraph \
    # === LLM Providers ===
    langchain-ollama langchain-google-genai \
    # === RAG / Vector Store ===
    chromadb sentence-transformers numpy \
    # === Document Processing ===
    "markitdown[all]" magika \
    # === Web Crawling / Search ===
    crawl4ai duckduckgo-search arxiv semanticscholar requests \
    # === Voice ===
    edge-tts faster-whisper \
    # === CLI ===
    rich typer questionary \
    # === WebUI ===
    chainlit \
    # === Utilities ===
    pydantic pydantic-settings python-dotenv aiofiles jinja2

# Verify installation
RUN python -c "import fastapi; import langchain; import chromadb; print('✅ All dependencies OK')"

# Create data directories
RUN mkdir -p /app/data/cache /app/data/chroma /app/data/documents /app/data/models /app/data/research_cache

echo "✅ Base image built successfully"
EOF
```

### Bước 2: Build base image

```bash
# Build base image
docker build -t rag-agent-base:latest -f base.Dockerfile .

# Kiểm tra image đã tạo
docker images | grep rag-agent-base
```

### Bước 3: Tạo Dockerfile tối ưu cho mỗi service

```bash
# Tạo script tạo Dockerfile tối ưu
cat > create_optimized_dockerfiles.sh << 'EOF'
#!/bin/bash

# Service definitions
SERVICES=("gateway" "agent" "rag" "document" "voice" "research" "editor" "accuracy" "frontend")

# Ports
declare -A PORTS
PORTS[gateway]=8000
PORTS[agent]=8001
PORTS[rag]=8002
PORTS[document]=8003
PORTS[voice]=8004
PORTS[research]=8007
PORTS[editor]=8009
PORTS[accuracy]=8008
PORTS[frontend]=8005

# Main modules
declare -A MODULES
MODULES[gateway]="services.gateway.main:app"
MODULES[agent]="services.agent.main:app"
MODULES[rag]="services.rag.main:app"
MODULES[document]="services.document.main:app"
MODULES[voice]="services.voice.main:app"
MODULES[research]="services.research.main:app"
MODULES[editor]="services.editor.main:app"
MODULES[accuracy]="services.accuracy.main:app"

for SERVICE in "${SERVICES[@]}"; do
    PORT=${PORTS[$SERVICE]}
    MODULE=${MODULES[$SERVICE]}
    
    mkdir -p "services/$SERVICE"
    
    cat > "services/$SERVICE/Dockerfile.optimized" << DOCKERFILE
# =============================================================================
# RAG-Agent ${SERVICE^} Service (Optimized)
# Sử dụng base image để build nhanh
# =============================================================================

FROM rag-agent-base:latest

# Copy service code
COPY services/${SERVICE}/ /app/services/${SERVICE}/

# Expose port
EXPOSE ${PORT}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \\
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Run
CMD ["python", "-m", "uvicorn", "${MODULE}", "--host", "0.0.0.0", "--port", "${PORT}"]
DOCKERFILE
    
    echo "✅ Created services/$SERVICE/Dockerfile.optimized"
done
EOF

# Chạy script
chmod +x create_optimized_dockerfiles.sh
./create_optimized_dockerfiles.sh
```

### Bước 4: Tạo docker-compose.optimized.yml

```bash
cat > docker-compose.optimized.yml << 'EOF'
# =============================================================================
# RAG-Agent Docker Compose (Optimized với Base Image)
# =============================================================================

version: '3.8'

services:
  # ---------------------------------------------------------------------------
  # API GATEWAY
  # ---------------------------------------------------------------------------
  gateway:
    build:
      context: .
      dockerfile: services/gateway/Dockerfile.optimized
    ports:
      - "8000:8000"
    environment:
      - AGENT_SERVICE_URL=http://agent:8001
      - RAG_SERVICE_URL=http://rag:8002
      - DOCUMENT_SERVICE_URL=http://document:8003
      - RESEARCH_SERVICE_URL=http://research:8007
      - EDITOR_SERVICE_URL=http://editor:8009
      - VOICE_SERVICE_URL=http://voice:8004
    volumes:
      - ./shared:/app/shared
      - ./data:/app/data
    depends_on:
      - agent
      - rag
      - document
    networks:
      - rag-network
    restart: unless-stopped

  # ---------------------------------------------------------------------------
  # AGENT SERVICE
  # ---------------------------------------------------------------------------
  agent:
    build:
      context: .
      dockerfile: services/agent/Dockerfile.optimized
    ports:
      - "8001:8001"
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
      - GEMINI_API_KEY=${GEMINI_API_KEY:-}
      - RAG_SERVICE_URL=http://rag:8002
      - DOCUMENT_SERVICE_URL=http://document:8003
      - RESEARCH_SERVICE_URL=http://research:8007
      - EDITOR_SERVICE_URL=http://editor:8009
    volumes:
      - ./shared:/app/shared
      - ./data:/app/data
    depends_on:
      - ollama
      - rag
    networks:
      - rag-network
    restart: unless-stopped

  # ---------------------------------------------------------------------------
  # RAG SERVICE
  # ---------------------------------------------------------------------------
  rag:
    build:
      context: .
      dockerfile: services/rag/Dockerfile.optimized
    ports:
      - "8002:8002"
    environment:
      - CHROMA_HOST=chromadb
      - CHROMA_PORT=8000
      - EMBEDDING_MODEL=all-MiniLM-L6-v2
    volumes:
      - ./shared:/app/shared
      - ./data/chroma:/app/data/chroma
    depends_on:
      - chromadb
    networks:
      - rag-network
    restart: unless-stopped

  # ---------------------------------------------------------------------------
  # DOCUMENT SERVICE
  # ---------------------------------------------------------------------------
  document:
    build:
      context: .
      dockerfile: services/document/Dockerfile.optimized
    ports:
      - "8003:8003"
    environment:
      - MINERU_ENABLED=true
      - MARKITDOWN_ENABLED=true
      - MAGIKA_ENABLED=true
    volumes:
      - ./shared:/app/shared
      - ./data/documents:/app/data/documents
      - ./data/cache:/app/data/cache
    networks:
      - rag-network
    restart: unless-stopped

  # ---------------------------------------------------------------------------
  # VOICE SERVICE
  # ---------------------------------------------------------------------------
  voice:
    build:
      context: .
      dockerfile: services/voice/Dockerfile.optimized
    ports:
      - "8004:8004"
    environment:
      - TTS_ENGINE=piper
      - STT_ENGINE=whisper
      - WHISPER_MODEL=base
      - PIPER_MODEL_DIR=/app/data/models/piper
    volumes:
      - ./shared:/app/shared
      - ./data/models:/app/data/models
    networks:
      - rag-network
    restart: unless-stopped

  # ---------------------------------------------------------------------------
  # RESEARCH SERVICE
  # ---------------------------------------------------------------------------
  research:
    build:
      context: .
      dockerfile: services/research/Dockerfile.optimized
    ports:
      - "8007:8007"
    environment:
      - CRAWL4AI_URL=http://crawl4ai:3000
      - TAVILY_API_KEY=${TAVILY_API_KEY:-}
      - BRAVE_API_KEY=${BRAVE_API_KEY:-}
      - SEMANTIC_SCHOLAR_API_KEY=${SS_API_KEY:-}
    volumes:
      - ./shared:/app/shared
      - ./data/research_cache:/app/data/research_cache
    depends_on:
      - crawl4ai
    networks:
      - rag-network
    restart: unless-stopped

  # ---------------------------------------------------------------------------
  # EDITOR SERVICE
  # ---------------------------------------------------------------------------
  editor:
    build:
      context: .
      dockerfile: services/editor/Dockerfile.optimized
    ports:
      - "8009:8009"
    environment:
      - CITATION_VERIFY_ENABLED=true
      - FACT_CROSSREF_ENABLED=true
      - HALLUCINATION_DETECTION_ENABLED=true
    volumes:
      - ./shared:/app/shared
      - ./data:/app/data
    networks:
      - rag-network
    restart: unless-stopped

  # ---------------------------------------------------------------------------
  # ACCURACY ENGINE
  # ---------------------------------------------------------------------------
  accuracy:
    build:
      context: .
      dockerfile: services/accuracy/Dockerfile.optimized
    ports:
      - "8008:8008"
    environment:
      - CITATION_VERIFY_ENABLED=true
      - FACT_CROSSREF_ENABLED=true
      - HALLUCINATION_DETECTION_ENABLED=true
    volumes:
      - ./shared:/app/shared
      - ./data:/app/data
    networks:
      - rag-network
    restart: unless-stopped

  # ---------------------------------------------------------------------------
  # FRONTEND
  # ---------------------------------------------------------------------------
  frontend:
    build:
      context: .
      dockerfile: services/frontend/Dockerfile.optimized
    ports:
      - "8005:8005"
    environment:
      - CHAINLIT_APP_PORT=8005
      - API_GATEWAY_URL=http://gateway:8000
    volumes:
      - ./shared:/app/shared
      - ./services/frontend/.chainlit:/app/.chainlit
    depends_on:
      - gateway
    networks:
      - rag-network
    restart: unless-stopped

  # ---------------------------------------------------------------------------
  # OLLAMA
  # ---------------------------------------------------------------------------
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0
    networks:
      - rag-network
    restart: unless-stopped

  # ---------------------------------------------------------------------------
  # CHROMADB
  # ---------------------------------------------------------------------------
  chromadb:
    image: chromadb/chroma:latest
    ports:
      - "8006:8000"
    volumes:
      - chroma_data:/chroma/chroma
    environment:
      - ANONYMIZED_TELEMETRY=false
    networks:
      - rag-network
    restart: unless-stopped

  # ---------------------------------------------------------------------------
  # CRAWL4AI
  # ---------------------------------------------------------------------------
  crawl4ai:
    image: unclecode/crawl4ai:latest
    ports:
      - "3000:3000"
    environment:
      - CRAWL4AI_API_TOKEN=${CRAWL4AI_TOKEN:-}
    volumes:
      - crawl4ai_data:/app/data
    networks:
      - rag-network
    restart: unless-stopped

volumes:
  ollama_data:
  chroma_data:
  crawl4ai_data:

networks:
  rag-network:
    driver: bridge
EOF
```

### Bước 5: Chạy với optimized docker-compose

```bash
# Lần đầu: Build base image (~10 phút)
docker build -t rag-agent-base:latest -f base.Dockerfile .

# Chạy docker-compose optimized
docker-compose -f docker-compose.optimized.yml up -d

# Kiểm tra
docker-compose -f docker-compose.optimized.yml ps
```

### Kết quả
- **Lần đầu**: ~10 phút (build base image)
- **Lần sau**: ~30 giây (chỉ copy code)

---

## Phương án 3: Docker BuildKit (Song song)

### Tổng quan
- **Thời gian build lần đầu**: ~15 phút
- **Thời gian build lại**: ~5 phút
- **Độ phức tạp**: Dễ
- **Phù hợp**: Development

### Ưu điểm
- ✅ Build song song tất cả services
- ✅ Tận dụng cache layers
- ✅ Giảm ~30% thời gian

### Nhược điểm
- Vẫn build từ đầu nếu chưa có cache
- Cần Docker BuildKit

### Bước 1: Kích hoạt BuildKit

```bash
# Method 1: Environment variable (tạm thời)
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Method 2: Docker daemon config (vĩnh viễn)
sudo tee /etc/docker/daemon.json << 'EOF'
{
  "features": {
    "buildkit": true
  }
}
EOF

# Restart Docker
sudo systemctl restart docker

# Kiểm tra BuildKit đã kích hoạt
docker buildx ls
```

### Bước 2: Tạo .dockerignore

```bash
cat > .dockerignore << 'EOF'
.git
.github
.vscode
__pycache__
*.pyc
.pytest_cache
.mypy_cache
.ruff_cache
data/
tests/
*.md
.env
.venv/
node_modules/
*.log
EOF
```

### Bước 3: Build song song

```bash
# Build tất cả services song song
DOCKER_BUILDKIT=1 docker-compose build --parallel

# Hoặc với Docker Compose v2
COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 docker compose build --parallel

# Build cụ thể 3 services
docker-compose build --parallel gateway agent rag
```

### Bước 4: Chạy

```bash
docker-compose up -d
```

### Bước 5: Tận dụng cache

```bash
# Mount pip cache để tăng tốc build tiếp
docker-compose build \
  --build-arg PIP_CACHE_DIR=/root/.cache/pip \
  -v pip_cache:/root/.cache/pip

# Hoặc dùng BuildKit cache
docker-compose build \
  --build-arg BUILDKIT_INLINE_CACHE=1
```

### Kết quả
- **Lần đầu**: ~15 phút (song song)
- **Lần sau**: ~5 phút (có cache)

---

## Phương án 4: Pre-built Images (Docker Hub)

### Tổng quan
- **Thời gian deploy lần đầu**: ~2-5 phút (pull images)
- **Thời gian deploy lại**: ~1 phút
- **Độ phức tạp**: Dễ
- **Phù hợp**: Production, CI/CD

### Ưu điểm
- ✅ Pull nhanh (~2-5 phút)
- ✅ Không cần build lại
- ✅ Deploy ở bất kỳ đâu
- ✅ Version control images

### Nhược điểm
- Cần Docker Hub account
- Cần push/pull images
- Cần update khi có thay đổi

### Bước 1: Tạo Docker Hub Account

```bash
# Đăng ký tại https://hub.docker.com
# Login
docker login

# Nhập username và password
Username: yourusername
Password: ********
Login Succeeded
```

### Bước 2: Build tất cả images

```bash
# Build tất cả services
docker-compose build

# Hoặc build cụ thể
docker-compose build gateway agent rag document voice research editor accuracy frontend
```

### Bước 3: Tag images

```bash
# Định nghĩa username
DOCKER_USERNAME="yourusername"

# Tag tất cả services
docker tag rag-agent-gateway:latest $DOCKER_USERNAME/rag-agent-gateway:latest
docker tag rag-agent-agent:latest $DOCKER_USERNAME/rag-agent-agent:latest
docker tag rag-agent-rag:latest $DOCKER_USERNAME/rag-agent-rag:latest
docker tag rag-agent-document:latest $DOCKER_USERNAME/rag-agent-document:latest
docker tag rag-agent-voice:latest $DOCKER_USERNAME/rag-agent-voice:latest
docker tag rag-agent-research:latest $DOCKER_USERNAME/rag-agent-research:latest
docker tag rag-agent-editor:latest $DOCKER_USERNAME/rag-agent-editor:latest
docker tag rag-agent-accuracy:latest $DOCKER_USERNAME/rag-agent-accuracy:latest
docker tag rag-agent-frontend:latest $DOCKER_USERNAME/rag-agent-frontend:latest

# Kiểm tra images
docker images | grep $DOCKER_USERNAME
```

### Bước 4: Push lên Docker Hub

```bash
# Push tất cả images
docker push $DOCKER_USERNAME/rag-agent-gateway:latest
docker push $DOCKER_USERNAME/rag-agent-agent:latest
docker push $DOCKER_USERNAME/rag-agent-rag:latest
docker push $DOCKER_USERNAME/rag-agent-document:latest
docker push $DOCKER_USERNAME/rag-agent-voice:latest
docker push $DOCKER_USERNAME/rag-agent-research:latest
docker push $DOCKER_USERNAME/rag-agent-editor:latest
docker push $DOCKER_USERNAME/rag-agent-accuracy:latest
docker push $DOCKER_USERNAME/rag-agent-frontend:latest

# Hoặc push tất cả cùng lúc
docker push --all-tags $DOCKER_USERNAME/rag-agent-*
```

### Bước 5: Tạo docker-compose.prebuilt.yml

```bash
cat > docker-compose.prebuilt.yml << 'EOF'
# =============================================================================
# RAG-Agent Docker Compose (Pre-built Images)
# Sử dụng images từ Docker Hub
# =============================================================================

version: '3.8'

services:
  gateway:
    image: ${DOCKER_USERNAME}/rag-agent-gateway:latest
    ports:
      - "8000:8000"
    environment:
      - AGENT_SERVICE_URL=http://agent:8001
      - RAG_SERVICE_URL=http://rag:8002
      - DOCUMENT_SERVICE_URL=http://document:8003
      - RESEARCH_SERVICE_URL=http://research:8007
      - EDITOR_SERVICE_URL=http://editor:8009
      - VOICE_SERVICE_URL=http://voice:8004
    volumes:
      - ./shared:/app/shared
      - ./data:/app/data
    depends_on:
      - agent
      - rag
      - document
    networks:
      - rag-network
    restart: unless-stopped

  agent:
    image: ${DOCKER_USERNAME}/rag-agent-agent:latest
    ports:
      - "8001:8001"
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
      - GEMINI_API_KEY=${GEMINI_API_KEY:-}
      - RAG_SERVICE_URL=http://rag:8002
      - DOCUMENT_SERVICE_URL=http://document:8003
      - RESEARCH_SERVICE_URL=http://research:8007
      - EDITOR_SERVICE_URL=http://editor:8009
    volumes:
      - ./shared:/app/shared
      - ./data:/app/data
    depends_on:
      - ollama
      - rag
    networks:
      - rag-network
    restart: unless-stopped

  rag:
    image: ${DOCKER_USERNAME}/rag-agent-rag:latest
    ports:
      - "8002:8002"
    environment:
      - CHROMA_HOST=chromadb
      - CHROMA_PORT=8000
      - EMBEDDING_MODEL=all-MiniLM-L6-v2
    volumes:
      - ./shared:/app/shared
      - ./data/chroma:/app/data/chroma
    depends_on:
      - chromadb
    networks:
      - rag-network
    restart: unless-stopped

  document:
    image: ${DOCKER_USERNAME}/rag-agent-document:latest
    ports:
      - "8003:8003"
    environment:
      - MINERU_ENABLED=true
      - MARKITDOWN_ENABLED=true
      - MAGIKA_ENABLED=true
    volumes:
      - ./shared:/app/shared
      - ./data/documents:/app/data/documents
      - ./data/cache:/app/data/cache
    networks:
      - rag-network
    restart: unless-stopped

  voice:
    image: ${DOCKER_USERNAME}/rag-agent-voice:latest
    ports:
      - "8004:8004"
    environment:
      - TTS_ENGINE=piper
      - STT_ENGINE=whisper
      - WHISPER_MODEL=base
      - PIPER_MODEL_DIR=/app/data/models/piper
    volumes:
      - ./shared:/app/shared
      - ./data/models:/app/data/models
    networks:
      - rag-network
    restart: unless-stopped

  research:
    image: ${DOCKER_USERNAME}/rag-agent-research:latest
    ports:
      - "8007:8007"
    environment:
      - CRAWL4AI_URL=http://crawl4ai:3000
      - TAVILY_API_KEY=${TAVILY_API_KEY:-}
      - BRAVE_API_KEY=${BRAVE_API_KEY:-}
      - SEMANTIC_SCHOLAR_API_KEY=${SS_API_KEY:-}
    volumes:
      - ./shared:/app/shared
      - ./data/research_cache:/app/data/research_cache
    depends_on:
      - crawl4ai
    networks:
      - rag-network
    restart: unless-stopped

  editor:
    image: ${DOCKER_USERNAME}/rag-agent-editor:latest
    ports:
      - "8009:8009"
    environment:
      - CITATION_VERIFY_ENABLED=true
      - FACT_CROSSREF_ENABLED=true
      - HALLUCINATION_DETECTION_ENABLED=true
    volumes:
      - ./shared:/app/shared
      - ./data:/app/data
    networks:
      - rag-network
    restart: unless-stopped

  accuracy:
    image: ${DOCKER_USERNAME}/rag-agent-accuracy:latest
    ports:
      - "8008:8008"
    environment:
      - CITATION_VERIFY_ENABLED=true
      - FACT_CROSSREF_ENABLED=true
      - HALLUCINATION_DETECTION_ENABLED=true
    volumes:
      - ./shared:/app/shared
      - ./data:/app/data
    networks:
      - rag-network
    restart: unless-stopped

  frontend:
    image: ${DOCKER_USERNAME}/rag-agent-frontend:latest
    ports:
      - "8005:8005"
    environment:
      - CHAINLIT_APP_PORT=8005
      - API_GATEWAY_URL=http://gateway:8000
    volumes:
      - ./shared:/app/shared
      - ./services/frontend/.chainlit:/app/.chainlit
    depends_on:
      - gateway
    networks:
      - rag-network
    restart: unless-stopped

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0
    networks:
      - rag-network
    restart: unless-stopped

  chromadb:
    image: chromadb/chroma:latest
    ports:
      - "8006:8000"
    volumes:
      - chroma_data:/chroma/chroma
    environment:
      - ANONYMIZED_TELEMETRY=false
    networks:
      - rag-network
    restart: unless-stopped

  crawl4ai:
    image: unclecode/crawl4ai:latest
    ports:
      - "3000:3000"
    environment:
      - CRAWL4AI_API_TOKEN=${CRAWL4AI_TOKEN:-}
    volumes:
      - crawl4ai_data:/app/data
    networks:
      - rag-network
    restart: unless-stopped

volumes:
  ollama_data:
  chroma_data:
  crawl4ai_data:

networks:
  rag-network:
    driver: bridge
EOF
```

### Bước 6: Chạy với pre-built images

```bash
# Tạo file .env với DOCKER_USERNAME
echo "DOCKER_USERNAME=yourusername" >> .env

# Pull images
docker-compose -f docker-compose.prebuilt.yml pull

# Chạy
docker-compose -f docker-compose.prebuilt.yml up -d

# Kiểm tra
docker-compose -f docker-compose.prebuilt.yml ps
```

### Kết quả
- **Lần đầu**: ~2-5 phút (pull images)
- **Lần sau**: ~1 phút (có cache)

---

## Phương án 5: Local Development (Không dùng Docker)

### Tổng quan
- **Thời gian setup**: ~5 phút
- **Thời gian khởi động**: ~10 giây
- **Độ phức tạp**: Dễ
- **Phù hợp**: Development, Debugging

### Ưu điểm
- ✅ Không cần build
- ✅ Phát triển nhanh
- ✅ Debug dễ dàng
- ✅ Tiết kiệm disk space

### Nhược điểm
- Cần cài dependencies locally
- Không isolate environments
- Có thể conflict versions

### Bước 1: Yêu cầu hệ thống

```bash
# Kiểm tra Python version
python3 --version
# Yêu cầu: Python 3.13+

# Kiểm tra pip
pip --version

# Kiểm tra git
git --version

# Kiểm tra Ollama (tùy chọn)
ollama --version
```

### Bước 2: Clone repository

```bash
# Clone repository
git clone https://github.com/tran-minhta/RAG-Agent.git

# Vào thư mục
cd RAG-Agent
```

### Bước 3: Tạo virtual environment

```bash
# Tạo virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# Hoặc
.venv\Scripts\activate     # Windows

# Kiểm tra đã activate
which python
# Kết quả: /home/user/RAG-Agent/.venv/bin/python
```

### Bước 4: Cài dependencies

```bash
# Cài dependencies từ pyproject.toml
pip install -e .

# Hoặc cài từng nhóm dependencies
pip install fastapi uvicorn httpx python-multipart
pip install langchain-core langchain langchain-community langchain-text-splitters langgraph
pip install langchain-ollama langchain-google-genai
pip install chromadb sentence-transformers numpy
pip install "markitdown[all]" magika
pip install crawl4ai duckduckgo-search arxiv semanticscholar requests
pip install edge-tts faster-whisper
pip install rich typer questionary chainlit
pip install pydantic pydantic-settings python-dotenv aiofiles jinja2

# Kiểm tra dependencies
pip list | grep -E "fastapi|langchain|chromadb"
```

### Bước 5: Cấu hình

```bash
# Copy file .env
cp .env.example .env

# Chỉnh sửa .env
nano .env

# Cấu hình quan trọng
OLLAMA_BASE_URL=http://localhost:11434
GEMINI_API_KEY=your-api-key
```

### Bước 6: Chạy services

#### Terminal 1: Gateway

```bash
# Terminal 1
python -m services.gateway.main

# Kết quả:
# 🚀 Starting Gateway Service...
# Uvicorn running on http://0.0.0.0:8000
```

#### Terminal 2: Agent

```bash
# Terminal 2
python -m services.agent.main

# Kết quả:
# 🚀 Starting Agent Service...
# Uvicorn running on http://0.0.0.0:8001
```

#### Terminal 3: RAG

```bash
# Terminal 3
python -m services.rag.main

# Kết quả:
# 🚀 Starting RAG Service...
# Uvicorn running on http://0.0.0.0:8002
```

#### Terminal 4: Document

```bash
# Terminal 4
python -m services.document.main

# Kết quả:
# 🚀 Starting Document Service...
# Uvicorn running on http://0.0.0.0:8003
```

#### Terminal 5: Voice

```bash
# Terminal 5
python -m services.voice.main

# Kết quả:
# 🚀 Starting Voice Service...
# Uvicorn running on http://0.0.0.0:8004
```

#### Terminal 6: Research

```bash
# Terminal 6
python -m services.research.main

# Kết quả:
# 🚀 Starting Research Service...
# Uvicorn running on http://0.0.0.0:8007
```

#### Terminal 7: Editor

```bash
# Terminal 7
python -m services.editor.main

# Kết quả:
# 🚀 Starting Editor Service...
# Uvicorn running on http://0.0.0.0:8009
```

#### Terminal 8: Accuracy

```bash
# Terminal 8
python -m services.accuracy.main

# Kết quả:
# 🚀 Starting Accuracy Engine...
# Uvicorn running on http://0.0.0.0:8008
```

#### Terminal 9: Ollama (tùy chọn)

```bash
# Terminal 9
ollama serve

# Trong terminal khác
ollama pull llama3.1:8b
```

### Bước 7: Truy cập

```bash
# API Docs
open http://localhost:8000/docs

# WebUI (cần Chainlit)
chainlit run services/frontend/app.py
open http://localhost:8005
```

### Script chạy tất cả services

```bash
# Tạo script run_all.sh
cat > run_all.sh << 'EOF'
#!/bin/bash

echo "🚀 Starting RAG-Agent services..."

# Activate virtual environment
source .venv/bin/activate

# Start services in background
python -m services.gateway.main &
python -m services.agent.main &
python -m services.rag.main &
python -m services.document.main &
python -m services.voice.main &
python -m services.research.main &
python -m services.editor.main &
python -m services.accuracy.main &

echo "✅ All services started!"
echo "📡 API Docs: http://localhost:8000/docs"
echo "🌐 WebUI: http://localhost:8005"

# Wait for Ctrl+C
wait
EOF

chmod +x run_all.sh
./run_all.sh
```

### Kết quả
- **Thời gian khởi động**: ~10 giây
- **Không cần build**
- **Phát triển nhanh**

---

## So sánh các phương án

| Phương án | Thời gian build lần đầu | Thời gian build lại | Disk Space | Độ phức tạp | Phù hợp với |
|-----------|------------------------|---------------------|------------|------------|-------------|
| **1. Docker Compose** | ~1000s (16 phút) | ~1000s | ~8GB | Dễ | Beginners |
| **2. Base Image** | ~10 phút | ~30 giây | ~4GB | Trung bình | Production |
| **3. BuildKit** | ~15 phút | ~5 phút | ~8GB | Dễ | Development |
| **4. Pre-built** | ~2-5 phút pull | Không cần build | ~8GB | Dễ | Production |
| **5. Local** | Không cần build | Không cần build | ~2GB | Dễ | Development |

### Khuyến nghị

| Mục đích | Phương án đề xuất |
|----------|-------------------|
| **Development nhanh** | Phương án 5 (Local) |
| **Production** | Phương án 2 (Base Image) |
| **CI/CD** | Phương án 4 (Pre-built) |
| **Học tập** | Phương án 1 (Docker Compose) |
| **Debugging** | Phương án 5 (Local) |

---

## Troubleshooting

### Lỗi: "Permission denied"

```bash
# Fix permissions
sudo chown -R $USER:$USER ~/.docker
sudo chmod 666 /var/run/docker.sock

# Hoặc thêm user vào docker group
sudo usermod -aG docker $USER
# Đăng nhập lại để apply
```

### Lỗi: "No space left on device"

```bash
# Dọn dẹp Docker
docker system prune -a
docker volume prune

# Xóa images không dùng
docker images | grep none | awk '{print $3}' | xargs rmi

# Kiểm tra disk space
df -h
```

### Lỗi: "Service unavailable"

```bash
# Kiểm tra logs
docker-compose logs gateway
docker-compose logs agent

# Restart service
docker-compose restart gateway
docker-compose restart agent

# Kiểm tra health endpoint
curl http://localhost:8000/health
curl http://localhost:8001/health
```

### Lỗi: "Module not found"

```bash
# Rebuild service
docker-compose build --no-cache agent
docker-compose up -d agent

# Hoặc kiểm tra shared modules
ls -la shared/
```

### Lỗi: "Port already in use"

```bash
# Kiểm tra process đang dùng port
lsof -i :8000
lsof -i :8001

# Kill process
kill -9 <PID>

# Hoặc thay đổi port trong .env
GATEWAY_PORT=8010
```

### Lỗi: "Out of memory"

```bash
# Giảm memory usage trong docker-compose.yml
services:
  agent:
    deploy:
      resources:
        limits:
          memory: 2G
    environment:
      - PYTHONDONTWRITEBYTECODE=1

# Hoặc tăng memory cho Docker
# Docker Desktop > Settings > Resources > Memory: 4GB+
```

### Lỗi: "Connection refused"

```bash
# Kiểm tra service có đang chạy không
docker-compose ps

# Kiểm tra logs
docker-compose logs -f gateway

# Restart tất cả
docker-compose down
docker-compose up -d
```

---

## Tối ưu hóa hiệu suất

### 1. Sử dụng .dockerignore

```bash
# Tạo file .dockerignore
cat > .dockerignore << 'EOF'
.git
.github
.vscode
__pycache__
*.pyc
.pytest_cache
.mypy_cache
.ruff_cache
data/
tests/
*.md
.env
.venv/
node_modules/
*.log
EOF
```

### 2. Multi-stage build

```dockerfile
# Build stage
FROM python:3.13-slim AS builder
WORKDIR /app
COPY pyproject.toml .
RUN pip install --user -r requirements.txt

# Runtime stage
FROM python:3.13-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
CMD ["python", "-m", "uvicorn", "services.gateway.main:app"]
```

### 3. Sử dụng Docker cache

```bash
# Build với cache
docker-compose build --build-arg PIP_CACHE_DIR=/root/.cache/pip

# Mount cache volume
docker-compose build -v pip_cache:/root/.cache/pip
```

### 4. Parallel build với Docker Compose v2

```bash
# Sử dụng Docker Compose v2
docker compose build --parallel

# Hoặc với BuildKit
COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 docker compose build
```

### 5. Tối ưu dependencies

```bash
# Chỉ cài dependencies cần thiết
pip install --no-deps fastapi uvicorn httpx

# Sử dụng pip cache
pip install --cache-dir .pip-cache fastapi
```

---

## Liên hệ

- **GitHub**: https://github.com/tran-minhta/RAG-Agent
- **Issues**: https://github.com/tran-minhta/RAG-Agent/issues
- **Email**: your-email@example.com

---

*Cập nhật lần cuối: Tháng 7, 2026*
