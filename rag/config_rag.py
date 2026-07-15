import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, "raw_documents")
BACKUP_DIR = os.path.join(BASE_DIR, "backup_documents")
STORAGE_DIR = os.path.join(BASE_DIR, "local_rag_storage")

LLM_MODEL = "qwen2-vl:7b"
EMBEDDING_MODEL = "nomic-embed-text"

# Đảm bảo tự động tạo các thư mục lưu trữ khi RAG khởi động
for path in [RAW_DIR, BACKUP_DIR, STORAGE_DIR]:
    os.makedirs(path, exist_ok=True)
