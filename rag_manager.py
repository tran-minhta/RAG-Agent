#!/usr/bin/env python3
import os
import sys
import shutil
import glob
import argparse
import asyncio
from raganything import RAGAnything, RAGAnythingConfig
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.utils import EmbeddingFunc

# --- 1. CẤU HÌNH THÔNG SỐ ĐƯỜNG DẪN VÀ OLLAMA ---
OLLAMA_BASE_URL = "http://localhost:11434/v1"
OLLAMA_API_KEY = "ollama"
EMBEDDING_MODEL = "nomic-embed-text"
EMBEDDING_DIM = 768  # nomic-embed-text là 768. Nếu dùng bge-m3 đổi thành 1024.
LLM_MODEL = "qwen2-vl:7b"

# Thư mục làm việc
RAW_DIR = "./raw_documents"
BACKUP_DIR = "./backup_documents"
STORAGE_DIR = "./local_rag_storage"

# Tạo thư mục nếu chưa tồn tại
for directory in [RAW_DIR, BACKUP_DIR, STORAGE_DIR]:
    os.makedirs(directory, exist_ok=True)


# --- 2. ĐỊNH NGHĨA KẾT NỐI LOCAL LLM & EMBEDDING ---
async def local_llm_complete(prompt, system_prompt=None, history=[], **kwargs):
    return await openai_complete_if_cache(
        model=LLM_MODEL,
        prompt=prompt,
        system_prompt=system_prompt,
        history=history,
        api_key=OLLAMA_API_KEY,
        base_url=OLLAMA_BASE_URL,
        **kwargs
    )

async def local_embedding(texts: list[str]) -> list[list[float]]:
    return await openai_embed(
        texts,
        model=EMBEDDING_MODEL,
        api_key=OLLAMA_API_KEY,
        base_url=OLLAMA_BASE_URL
    )

embedding_func = EmbeddingFunc(
    embedding_dim=EMBEDDING_DIM,
    max_token_size=8192,
    func=local_embedding
)


# --- 3. KHỞI TẠO RAG-ANYTHING ---
def get_rag_instance():
    config = RAGAnythingConfig(
        working_dir=STORAGE_DIR,
        parser="mineru",
        parse_method="auto",
        enable_image_processing=True,
        enable_table_processing=True,
    )
    return RAGAnything(
        config=config,
        llm_model_func=local_llm_complete,
        vision_model_func=local_llm_complete, # Sử dụng chung qwen2-vl xử lý ảnh
        embedding_func=embedding_func
    )


# --- 4. CÁC TÁC VỤ XỬ LÝ CHÍNH ---

async def ingest_documents():
    """Tự động quét thư mục raw_documents, nạp dữ liệu và dọn dẹp an toàn"""
    rag = get_rag_instance()
    
    # Tìm kiếm các file tài liệu được hỗ trợ
    extensions = ["*.pdf", "*.docx", "*.pptx", "*.xlsx", "*.png", "*.jpg", "*.jpeg"]
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(RAW_DIR, ext)))
        
    if not files:
        print(f"⚠️ Không tìm thấy tài liệu nào trong thư mục '{RAW_DIR}'!")
        return

    print(f"🚀 Tìm thấy {len(files)} file tài liệu mới. Bắt đầu xử lý...")

    for file_path in files:
        filename = os.path.basename(file_path)
        print(f"\n📂 Đang nạp: {filename}")
        
        try:
            # 1. Thực hiện bóc tách và tạo Graph DB
            await rag.ainsert_document(file_path)
            print(f"✓ Hoàn thành phân tích và lập chỉ mục: {filename}")
            
            # 2. Sao lưu file thô sang thư mục Backup
            backup_path = os.path.join(BACKUP_DIR, filename)
            shutil.copy2(file_path, backup_path)
            print(f"💾 Đã sao lưu file gốc sang: {backup_path}")
            
            # 3. Xóa file thô trong thư mục raw_documents để giải phóng dung lượng
            os.remove(file_path)
            print(f"🗑️ Đã giải phóng file thô: {file_path}")
            
        except Exception as e:
            print(f"❌ Thất bại khi xử lý file '{filename}': {e}")
            print("⚠️ File gốc vẫn được giữ lại tại thư mục raw để bạn kiểm tra.")

    print("\n🎉 Toàn bộ tiến trình nạp dữ liệu hoàn tất!")


async def query_rag(query: str, mode: str = "hybrid"):
    """Thực hiện truy vấn cơ sở dữ liệu tri thức"""
    rag = get_rag_instance()
    print(f"🔍 Đang tìm kiếm với chế độ: '{mode}'...")
    try:
        response = await rag.aquery(query, mode=mode)
        print("\n=== KẾT QUẢ TRẢ VỀ ===")
        print(response)
        print("=======================")
    except Exception as e:
        print(f"❌ Lỗi truy vấn: {e}")


# --- 5. ĐIỀU HƯỚNG DÒNG LỆNH (CLI ENTRYPOINT) ---
def main():
    parser = argparse.ArgumentParser(description="RAG-Anything Offline Workspace Manager CLI")
    subparsers = parser.add_subparsers(dest="command", help="Các lệnh thực thi")

    # Lệnh nạp tài liệu
    subparsers.add_parser("ingest", help="Quét thư mục raw, phân tích nạp vào DB và dọn dẹp an toàn")

    # Lệnh truy vấn
    query_parser = subparsers.add_parser("query", help="Đặt câu hỏi truy vấn hệ thống tri thức")
    query_parser.add_argument("question", type=str, help="Câu hỏi bạn muốn đặt cho tài liệu")
    query_parser.add_argument(
        "--mode", 
        type=str, 
        default="hybrid", 
        choices=["local", "global", "hybrid", "naive"],
        help="Chế độ tìm kiếm (Mặc định: hybrid)"
    )

    args = parser.parse_args()

    if args.command == "ingest":
        asyncio.run(ingest_documents())
    elif args.command == "query":
        asyncio.run(query_rag(args.question, args.mode))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
