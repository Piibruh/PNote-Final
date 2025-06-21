# pnote-ai-app/config.py
import streamlit as st
import os

GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_DB_PATH = os.path.join(ROOT_DIR, "chroma_db")
USER_DATA_PATH = os.path.join(ROOT_DIR, "user_data")

TEXT_CHUNK_SIZE = 1500
TEXT_CHUNK_OVERLAP = 200
DEFAULT_MODEL = "gemini-1.5-flash"
VECTOR_DB_SEARCH_RESULTS = 5

DEFAULT_SYSTEM_PROMPT = """Bạn là một trợ lý AI chuyên gia, được lập trình để phân tích và trả lời các câu hỏi dựa trên một tập hợp tài liệu được cung cấp.
Nhiệm vụ của bạn là cung cấp câu trả lời chính xác, súc tích và chỉ dựa vào "NGỮ CẢNH" cho trước.
Nếu thông tin không có trong ngữ cảnh, hãy trả lời một cách trung thực rằng "Dựa trên tài liệu được cung cấp, tôi không tìm thấy thông tin để trả lời câu hỏi này."
Không được bịa đặt thông tin."""

SUMMARY_PROMPT_TEMPLATE = """Dựa vào toàn bộ "NGỮ CẢNH" dưới đây về một khóa học, hãy thực hiện các yêu cầu sau với vai trò là một chuyên gia phân tích:
1.  **Tóm tắt Tổng quan:** Viết một đoạn văn súc tích (khoảng 3-5 câu) nêu bật những nội dung chính và mục tiêu của tài liệu.
2.  **Các Ý tưởng Cốt lõi:** Liệt kê từ 5 đến 7 khái niệm, luận điểm, hoặc chủ đề quan trọng nhất dưới dạng gạch đầu dòng có giải thích ngắn gọn.
3.  **Câu hỏi Gợi mở:** Đặt ra một câu hỏi sâu sắc để người đọc có thể tự suy ngẫm và nghiên cứu thêm về chủ đề này.

Hãy trình bày câu trả lời một cách chuyên nghiệp, có cấu trúc rõ ràng.

NGỮ CẢNH:
---
{context}
---

BẢN PHÂN TÍCH CỦA BẠN:"""

QUIZ_PROMPT_TEMPLATE = """Với vai trò là một nhà giáo dục kinh nghiệm, hãy dựa vào "NGỮ CẢNH" được cung cấp để tạo ra chính xác {num_questions} câu hỏi trắc nghiệm (MCQ) chất lượng cao.
**YÊU CẦU BẮT BUỘC:**
1.  Câu hỏi phải kiểm tra sự hiểu biết, không chỉ là ghi nhớ thông tin.
2.  Mỗi câu hỏi có 4 lựa chọn (A, B, C, D), trong đó chỉ có MỘT đáp án đúng. Các lựa chọn gây nhiễu phải hợp lý.
3.  **TRẢ VỀ KẾT QUẢ DƯỚI DẠNG MỘT DANH SÁCH JSON HỢP LỆ VÀ CHỈ DUY NHẤT DANH SÁCH ĐÓ.**
4.  Mỗi đối tượng JSON trong danh sách phải có các key: "question" (string), "options" (list of 4 strings), và "answer" (string, là nội dung của đáp án đúng).

NGỮ CẢNH:
---
{context}
---

DANH SÁCH JSON:"""
