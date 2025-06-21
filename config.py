# config.py
import os
import streamlit as st
from dotenv import load_dotenv

# Tải biến môi trường từ file .env (chỉ có tác dụng khi chạy local)
load_dotenv()

def get_gemini_api_key():
    """
    Hàm lấy API key một cách linh hoạt:
    1. Ưu tiên lấy từ Streamlit Secrets (khi deploy lên Streamlit Cloud).
    2. Nếu không có, lấy từ biến môi trường (file .env ở local).
    """
    if hasattr(st, 'secrets') and "GEMINI_API_KEY" in st.secrets:
        return st.secrets["GEMINI_API_KEY"]
    return os.getenv("GEMINI_API_KEY")

# --- Cấu hình API và Model ---
GEMINI_API_KEY = get_gemini_api_key()
AVAILABLE_MODELS = {
    "Nhanh & Tối ưu (Flash)": "gemini-1.5-flash-latest",
    "Mạnh & Thông minh (Pro)": "gemini-1.5-pro-latest"
}

# --- Cấu hình xử lý văn bản ---
TEXT_CHUNK_SIZE = 1000
TEXT_CHUNK_OVERLAP = 150
VECTOR_DB_SEARCH_RESULTS = 7

# --- Cấu hình ứng dụng ---
CHROMA_DB_PATH = "./pnote_chroma_db"
USER_DATA_PATH = "./user_uploaded_data"
MAX_FILE_SIZE_MB = 50
DEFAULT_THEME = 'dark' # Theme mặc định khi người dùng truy cập lần đầu

# --- PROMPT MẪU ---
DEFAULT_SYSTEM_PROMPT = """Bạn là PNote, một trợ lý AI chuyên gia về phân tích tài liệu. Nhiệm vụ của bạn là trả lời câu hỏi của người dùng DỰA HOÀN TOÀN vào "NGỮ CẢNH" được cung cấp.

QUY TẮC BẮT BUỘC:
1.  CHỈ được sử dụng thông tin có trong "NGỮ CẢNH". Tuyệt đối không tự ý suy diễn, bịa đặt, hay dùng kiến thức ngoài.
2.  Nếu câu trả lời có trong ngữ cảnh, hãy trả lời một cách trực tiếp, súc tích và chuyên nghiệp.
3.  Nếu thông tin không có trong "NGỮ CẢNH", hãy trả lời duy nhất một câu: "Tôi không tìm thấy thông tin này trong tài liệu được cung cấp."
4.  Không bao giờ đưa ra ý kiến cá nhân.
"""
