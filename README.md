Dưới đây là nội dung chi tiết cho file hướng dẫn sử dụng (**README.md**) được thiết kế chuyên nghiệp, rõ ràng và tập trung trực tiếp vào cách vận hành hệ thống trợ lý tài liệu offline của bạn.
Bạn hãy mở file bằng lệnh nano README.md, xóa nội dung cũ và dán toàn bộ phần hướng dẫn dưới đây vào:
```markdown
# 🤖 AI Document Assistant (RAG-Anything Offline CLI)

Hệ thống trợ lý quản lý tài liệu cá nhân chạy hoàn toàn **Offline** trên Terminal. Tích hợp bóc tách tài liệu cấu trúc phức tạp (MinerU), mô hình ngôn ngữ lớn và mô hình nhúng cục bộ (Ollama) cùng khả năng tương tác linh hoạt bằng giọng nói (Voice Wake Word) hoặc giao diện dòng lệnh dạng Gemini CLI.

---

## 📁 Cấu Trúc Thư Mục Dự Án

```text
rag-workspace/
├── raw_documents/              # Nơi chứa tài liệu thô đầu vào (.pdf, .png, .docx...)
├── backup_documents/           # Nơi lưu trữ file gốc sau khi nạp + file tóm tắt (.md)
├── local_rag_storage/          # Cơ sở dữ liệu đồ thị tri thức (Graph & Vector DB)
├── config.py                   # Cấu hình tập trung (Model, Thư mục, Wake Word)
├── modules/
│   ├── rag_core.py             # Lõi kết nối LLM/Embedding & RAG-Anything
│   ├── document_handler.py     # Pipeline nạp, phân loại và tóm tắt tài liệu tự động
│   └── voice_engine.py         # Bộ máy xử lý âm thanh Offline (STT & TTS)
└── main.py                     # File điều phối khởi động giao diện chính (CLI)

```
## 🛠️ Hướng Dẫn Cài Đặt (Setup)
### 1. Chuẩn bị môi trường hệ thống
Đảm bảo máy của bạn đã cài đặt các thư viện xử lý âm thanh hệ thống (ALSA / PortAudio):
```bash
sudo apt update && sudo apt install -y portaudio19-dev python3-pyaudio flac

```
### 2. Thiết lập môi trường ảo và cài đặt thư viện Python
Sử dụng công cụ uv để tạo môi trường ảo và cài đặt thư viện siêu tốc:
```bash
# Tạo và kích hoạt môi trường ảo
uv venv
source .venv/bin/activate

# Cài đặt thư viện RAG cốt lõi cùng các gói Audio/Speech
uv pip install "raganything[all]" pyaudio SpeechRecognition pyttsx3

```
### 3. Tải và chạy các mô hình cục bộ qua Ollama
Đảm bảo bạn đã kéo sẵn các mô hình này về máy trước khi chạy ứng dụng:
```bash
# Tải mô hình nhúng (Embedding Model)
ollama pull nomic-embed-text

# Tải mô hình suy luận đa phương tiện (Vision-LLM)
ollama pull qwen2-vl:7b

```
## 🚀 Hướng Dẫn Vận Hành
Chỉ cần kích hoạt môi trường ảo .venv và khởi chạy file main.py, hệ thống sẽ tự động đưa bạn vào thẳng giao diện chat thông minh như Gemini CLI:
```bash
python main.py

```
### 1. Các lệnh nhanh (Slash Commands) trực tiếp trong phòng chat:
 * /ingest : Tự động quét các tài liệu mới trong thư mục raw_documents/, nạp song song, sinh file tóm tắt nhanh .md lưu vào backup_documents/ và dọn dẹp file thô gốc.
 * /voice  : Chuyển sang chế độ trợ lý giọng nói chạy ngầm. Chỉ cần gọi từ khóa mặc định là assistant, trợ lý sẽ lập tức phản hồi và lắng nghe câu hỏi của bạn qua Micro.
 * /stats  : Xem thống kê tổng số lượng tài liệu đang được quản lý trong hệ thống.
 * /clear  : Làm sạch màn hình Terminal để bắt đầu phiên làm việc mới.
 * /exit   : Thoát chương trình một cách an toàn.
## ⚙️ Tùy Chỉnh Cấu Hình (config.py)
Nếu muốn thay đổi tên Mô hình, Từ khóa đánh thức (Wake word) hoặc Đường dẫn lưu trữ, bạn chỉ cần mở file config.py ra và chỉnh sửa các tham số sau:
```python
# Ví dụ: Đổi từ khóa đánh thức từ "assistant" sang "jarvis"
WAKE_WORD = "jarvis"

# Thay đổi tốc độ đọc của trợ lý (Mặc định: 175)
SPEECH_RATE = 160

```
```

---

Dán xong bạn nhấn `Ctrl + O` để lưu và `Ctrl + X` để thoát. Vậy là toàn bộ dự án của bạn từ mã nguồn chia tách cho tới tài liệu hướng dẫn vận hành đã hoàn tất cực kỳ chỉn chu và gọn gàng!

```
