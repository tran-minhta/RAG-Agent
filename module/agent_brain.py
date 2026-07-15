import os
import sys
from datetime import datetime, timedelta

# Import thư viện nội bộ từ thư mục con rag/
from rag.core.rag_service import RAGService
from modules.os_tracer import OSTracer
from modules.planner import TaskPlanner

class AgentBrain:
    def __init__(self):
        # Bộ não chính khởi tạo RAG Service từ phân vùng độc lập
        self.rag_service = RAGService()
        self.os_tracer = OSTracer()
        self.planner = TaskPlanner()

    async def think_and_execute(self, user_input: str) -> str:
        now = datetime.now()
        lowered_input = user_input.lower()
        collected_context = f"Mốc thời gian máy: {now.strftime('%Y-%m-%d %H:%M:%S')}\n"

        # 1. Trích xuất dữ liệu từ các công cụ giám sát máy tính (OS Tracer / Planner)
        if "hôm qua" in lowered_input or "lúc" in lowered_input:
            logs = self.os_tracer.get_system_activity(since="1 day ago")
            collected_context += f"[Nhân hệ điều hành] Hoạt động máy:\n{logs[:800]}\n"

        if "tìm file" in lowered_input:
            target_name = user_input.split("file")[-1].strip()
            found = self.os_tracer.find_file_by_name(target_name)
            collected_context += f"[Hệ thống file] Vị trí thực tế trên ổ đĩa:\n" + "\n".join(found) + "\n"

        # 2. Gọi RAG Sub-system để lấy thông tin từ kho tri thức đã vector hóa
        print("🧠 Agent Core đang gửi yêu cầu tra cứu sang RAG Sub-project...")
        rag_knowledge = await self.rag_service.query_knowledge(user_input)
        collected_context += f"[Tri thức từ RAG cung cấp]:\n{rag_knowledge}\n"

        # 3. Tổng hợp tư duy cuối cùng
        final_prompt = (
            f"Bạn là Bộ Điều Hành Hệ Thống Máy (Agent Core).\n"
            f"Dữ liệu tổng hợp từ các phân vùng:\n{collected_context}\n"
            f"Hãy giải quyết yêu cầu của người dùng ngắn gọn, tập trung thẳng trọng tâm: {user_input}"
        )
        
        return await self.rag_service.rag.llm_model_func(final_prompt)
