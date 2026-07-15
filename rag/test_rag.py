#!/usr/bin/env python3
import asyncio
import sys
import os

# Bổ sung path để chạy độc lập không bị lỗi import
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.rag_service import RAGService

async def debug_pipeline():
    print("🛠️  Đang khởi động RAG Sub-system ở chế độ Debug độc lập...")
    service = RAGService()
    
    # 1. Thử nghiệm quét và lập chỉ mục tài liệu
    print("\n[1/2] Đang quét thư mục tài liệu thô...")
    # Gọi hàm quét (nội dung tương tự luồng cũ nhưng dùng config_rag)
    # await service.ingest_all_documents()
    
    # 2. Thử nghiệm truy vấn trực tiếp kho tri thức
    print("\n[2/2] Thử nghiệm truy vấn dữ liệu đã vector hóa...")
    test_query = "Tài liệu kỹ thuật của dự án nằm ở đâu?"
    response = await service.query_knowledge(test_query)
    print(f"\n🤖 Kết quả phản hồi từ RAG:\n{response}\n")

if __name__ == "__main__":
    asyncio.run(debug_pipeline())
