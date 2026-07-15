import os
import shutil
import glob
import asyncio
from datetime import datetime
import config

async def process_single_file(rag, file_path: str):
    filename = os.path.basename(file_path)
    print(f"\n⚡ Đang nhận dạng & quét: {filename}...")
    
    try:
        # 1. Đọc lướt và phân loại thông minh bằng cách kiểm tra định dạng
        _, ext = os.path.splitext(filename)
        ext = ext.lower()
        
        # Nhóm các file văn bản thuần/mã nguồn có thể đọc trực tiếp bằng text
        text_extensions = ['.py', '.sh', '.js', '.json', '.txt', '.log', '.csv', '.xml', '.yaml', '.yml', '.md', '.ini', '.conf']
        
        # Nếu là file mã nguồn/văn bản thuần, đọc nội dung trước để hỗ trợ LLM nhận dạng sâu
        content_preview = ""
        if ext in text_extensions:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content_preview = f.read(2000) # Lấy 2000 ký tự đầu tiên để phân tích chuyên sâu
            except Exception:
                pass

        # 2. Thực hiện lập chỉ mục vào cơ sở dữ liệu RAG
        await rag.ainsert_document(file_path)
        print(f"✓ {filename}: Đã quét và lập chỉ mục cấu trúc tri thức.")

        # 3. Yêu cầu LLM phân tích sâu để phân loại và gắn tag tự động
        print(f"📝 {filename}: Đang dùng LLM nhận dạng bản chất tệp tin để phân loại...")
        analysis_prompt = (
            f"Dựa trên tên tệp tin '{filename}' và nội dung trích xuất của nó, hãy thực hiện phân loại chính xác.\n"
            f"Nội dung xem trước (nếu có): \n--- Begin ---\n{content_preview}\n--- End ---\n\n"
            f"Hãy trả về kết quả định dạng Markdown gồm:\n"
            f"1. **Phân loại tệp tin (Category/Tags)**: Hãy tự gán các tag phù hợp nhất (Ví dụ: #Mã_Nguồn_Python, #Cấu_Hình_Hệ_Thống, #Nhật_Ký_Vận_Hành, #Tài_Liệu_Kỹ_Thuật, #Hình_Ảnh_Sơ_Đồ...)\n"
            f"2. **Tóm tắt chức năng/nội dung chính**: (Dưới 5 dòng ngắn gọn giải thích file này dùng để làm gì)."
        )
        analysis_result = await rag.aquery(analysis_prompt, mode="local")

        # 4. Xuất file báo cáo phân loại chi tiết (.md)
        summary_path = os.path.join(config.BACKUP_DIR, f"{filename}_summary.md")
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(f"# Kết Quả Phân Loại Tệp Tin: {filename}\n")
            f.write(f"**Thời gian quét:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(analysis_result)
        print(f"💾 {filename}: Đã lưu kết quả phân loại tại: {summary_path}")

        # 5. Di chuyển file thô vào vùng lưu trữ an toàn (Backup) và dọn dẹp thư mục đầu vào
        backup_path = os.path.join(config.BACKUP_DIR, filename)
        shutil.copy2(file_path, backup_path)
        os.remove(file_path)
        print(f"🗑️ {filename}: Đã hoàn tất dọn dẹp vùng đệm.")

    except Exception as e:
        print(f"❌ Lỗi khi quét file '{filename}': {e}")

async def ingest_all_documents(rag):
    """Quét MỌI tệp tin có trong thư mục raw_documents không giới hạn định dạng"""
    # Lấy toàn bộ mọi file trong thư mục, bỏ qua các thư mục con
    all_entries = glob.glob(os.path.join(config.RAW_DIR, "*"))
    files = [f for f in all_entries if os.path.isfile(f)]
        
    if not files:
        print(f"\n📭 Không tìm thấy tệp tin nào trong thư mục '{config.RAW_DIR}' để quét!")
        return

    print(f"\n🚀 Trợ lý phát hiện {len(files)} tệp tin. Bắt đầu quét và phân loại toàn diện...")
    
    # Kích hoạt xử lý song song bất đồng bộ cho toàn bộ các file được tìm thấy
    await asyncio.gather(*(process_single_file(rag, f) for f in files))
    
    # Giải phóng các thư mục tạm phát sinh trong quá trình phân tích dữ liệu
    for cache_dir in ["./pdf_parse_cache", "./mineru_cache"]:
        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir, ignore_errors=True)
            
    print(f"\n{'-'*40}\n🎉 Trợ lý đã quét sạch, phân loại và lập chỉ mục xong toàn bộ kho tệp tin!")
