# core/services.py

# ==============================================================================
# BỘ NÃO TRUNG TÂM CỦA ỨNG DỤNG - SERVICE MANAGER
#
# KIẾN TRÚC:
# File này được thiết kế theo Singleton Pattern thông qua class ServiceManager.
# Điều này đảm bảo rằng trong toàn bộ vòng đời của ứng dụng, chỉ có một đối tượng
# duy nhất quản lý các kết nối nặng (đến ChromaDB) và các client đắt đỏ (Gemini API).
# Cách làm này giúp tiết kiệm tài nguyên và tránh các xung đột tiềm tàng.
#
# CHỨC NĂNG:
# 1. Quản lý Khóa học: Tạo, xóa, liệt kê các không gian làm việc.
# 2. Xử lý Tài liệu: Trích xuất văn bản từ nhiều nguồn, chống trùng lặp qua hash.
# 3. Quản lý VectorDB: Thêm, xóa, truy vấn các đoạn văn bản (chunks) trong ChromaDB.
# 4. Tích hợp AI: Cung cấp các phương thức để tương tác với Google Gemini, bao gồm
#    hỏi-đáp (RAG), tóm tắt, và tạo câu hỏi trắc nghiệm.
# ==============================================================================


# --- KHAI BÁO THƯ VIỆN VÀ CẤU HÌNH BAN ĐẦU ---

# ĐOẠN CODE BẮT BUỘC ĐỂ SỬA LỖI SQLITE3 TRÊN STREAMLIT CLOUD
# Phải đặt ở đầu tiên để đảm bảo Python sử dụng phiên bản SQLite đúng.
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

# Các thư viện chuẩn và bên thứ ba
import google.api_core.exceptions
import google.generativeai as genai
import chromadb
from pypdf import PdfReader
import docx
import requests
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi
import tiktoken
import time
import re
import json
from unicodedata import normalize
import hashlib
import os
import shutil
import uuid

# Import cấu hình từ file config.py
from config import (
    GEMINI_API_KEY, TEXT_CHUNK_SIZE, TEXT_CHUNK_OVERLAP,
    VECTOR_DB_SEARCH_RESULTS, CHROMA_DB_PATH, USER_DATA_PATH, DEFAULT_SYSTEM_PROMPT
)


# --- CÁC HÀM TIỆN ÍCH (UTILITY FUNCTIONS) ---

def slugify(value: str) -> str:
    """
    Chuyển đổi chuỗi Unicode thành một chuỗi an toàn (ASCII, không dấu, gạch ngang)
    để dùng làm ID hoặc tên file, đảm bảo tính tương thích hệ thống.
    """
    value = normalize('NFKD', str(value)).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    value = re.sub(r'[-\s]+', '-', value)
    return value

def calculate_file_hash(file_bytes: bytes) -> str:
    """
    Tính toán mã hash SHA256 cho nội dung của một file.
    Đây là phương pháp cốt lõi để xác định sự trùng lặp của tài liệu,
    hiệu quả hơn nhiều so với việc chỉ kiểm tra tên file.
    """
    sha256_hash = hashlib.sha256()
    sha256_hash.update(file_bytes)
    return sha256_hash.hexdigest()


# --- LỚP QUẢN LÝ DỊCH VỤ CHÍNH (SINGLETON) ---

class ServiceManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ServiceManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        # Ngăn việc khởi tạo lại các thuộc tính không cần thiết
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        # Khởi tạo các client kết nối
        self.chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)

    # --- NHÓM HÀM QUẢN LÝ MODEL ---
    def get_generative_model(self, model_name: str):
        if not GEMINI_API_KEY: return None
        return genai.GenerativeModel(model_name)

    # --- NHÓM HÀM XỬ LÝ TÀI LIỆU ---
    def extract_text_from_source(self, source_type: str, source_data: any) -> tuple[str | None, str, str]:
        # (Giữ nguyên code hàm này từ phiên bản trước - đã rất đầy đủ)
        original_name = getattr(source_data, 'name', str(source_data))
        safe_name = slugify(original_name)
        try:
            text = ""
            # ... (logic if/elif/else cho pdf, docx, url...) ...
            return text, original_name, safe_name
        except Exception as e:
            # ... (xử lý lỗi) ...
            return None, "Lỗi", "error"

    # --- NHÓM HÀM QUẢN LÝ KHÓA HỌC & VECTORDB ---
    def list_courses(self) -> list[dict]:
        # (Giữ nguyên)
        collections = self.chroma_client.list_collections()
        return [{"id": col.name, "name": col.metadata.get("display_name", col.name)} for col in collections]

    def create_course(self, course_id: str, display_name: str):
        # (Giữ nguyên)
        self.chroma_client.get_or_create_collection(name=course_id, metadata={"display_name": display_name})
        os.makedirs(os.path.join(USER_DATA_PATH, course_id), exist_ok=True)

    def delete_course(self, course_id: str):
        # (Giữ nguyên)
        try:
            self.chroma_client.delete_collection(name=course_id)
            course_data_path = os.path.join(USER_DATA_PATH, course_id)
            if os.path.isdir(course_data_path):
                shutil.rmtree(course_data_path)
        except ValueError: pass
        except Exception as e: raise e

    def check_if_hash_exists(self, course_id: str, file_hash: str) -> bool:
        # (Giữ nguyên)
        try:
            collection = self.chroma_client.get_collection(name=course_id)
            return len(collection.get(where={"file_hash": file_hash}, limit=1)['ids']) > 0
        except Exception: return False

    def add_document_to_course(self, course_id: str, doc_text: str, source_name: str, file_hash: str) -> int:
        # (Giữ nguyên)
        collection = self.chroma_client.get_collection(name=course_id)
        tokens = self.tokenizer.encode(doc_text)
        chunks = [self.tokenizer.decode(tokens[i:i + TEXT_CHUNK_SIZE]) for i in range(0, len(tokens), TEXT_CHUNK_SIZE - TEXT_CHUNK_OVERLAP)]
        if not chunks: return 0
        doc_ids = [f"{slugify(source_name)}-{i}-{int(time.time() * 1000)}" for i in range(len(chunks))]
        metadatas = [{"source": source_name, "file_hash": file_hash}] * len(chunks)
        collection.add(documents=chunks, metadatas=metadatas, ids=doc_ids)
        return len(chunks)

    def list_documents_in_course(self, course_id: str) -> list[dict]:
        # (Giữ nguyên)
        try:
            collection = self.chroma_client.get_collection(name=course_id)
            if collection.count() == 0: return []
            metadatas = collection.get(include=["metadatas"])['metadatas']
            unique_docs = {meta['file_hash']: meta['source'] for meta in metadatas if 'file_hash' in meta and 'source' in meta}
            return [{"hash": file_hash, "name": source_name} for file_hash, source_name in unique_docs.items()]
        except Exception: return []

    def delete_document_from_course(self, course_id: str, file_hash: str):
        # (Giữ nguyên)
        collection = self.chroma_client.get_collection(name=course_id)
        results = collection.get(where={"file_hash": file_hash}, limit=1, include=["metadatas"])
        if not results['ids']: raise ValueError("Không tìm thấy tài liệu với mã hash này để xóa.")
        source_name = results['metadatas'][0]['source']
        collection.delete(where={"file_hash": file_hash})
        course_data_path = os.path.join(USER_DATA_PATH, course_id)
        for f in os.listdir(course_data_path):
            if source_name in f:
                os.remove(os.path.join(course_data_path, f)); break
    
    # --- HÀM HELPER LẤY NGỮ CẢNH ---
    def _get_full_context(self, course_id: str, max_chunks: int = 25) -> str | None:
        """
        Hàm nội bộ để lấy một lượng lớn ngữ cảnh từ database.
        Được dùng chung cho các chức năng tóm tắt và tạo câu hỏi.
        """
        try:
            collection = self.chroma_client.get_collection(name=course_id)
            count = collection.count()
            if count == 0: return None
            # Lấy một lượng mẫu đại diện, tối đa là max_chunks
            limit = min(count, max_chunks)
            documents = collection.get(limit=limit)
            return "\n---\n".join(documents['documents'])
        except Exception as e:
            print(f"Lỗi khi lấy ngữ cảnh đầy đủ: {e}")
            return None

    # --- NHÓM HÀM TÍCH HỢP AI (HOÀN THIỆN) ---
    def get_chat_answer_stream(self, course_id: str, question: str, model_name: str, system_prompt: str):
        # (Giữ nguyên, đã rất đầy đủ)
        model = self.get_generative_model(model_name)
        if not model: yield "Lỗi: Mô hình AI chưa được cấu hình."; return
        try:
            # ... (logic RAG) ...
            yield "..."
        except Exception as e:
            # ... (xử lý lỗi) ...
            yield "Lỗi"

    def summarize_course(self, course_id: str, model_name: str) -> str:
        """
        HOÀN THIỆN: Tạo bản tóm tắt cho toàn bộ khóa học dựa trên
        một mẫu ngữ cảnh đại diện.
        """
        model = self.get_generative_model(model_name)
        if not model: return "Lỗi: Mô hình AI chưa được cấu hình."
        
        context = self._get_full_context(course_id)
        if not context:
            return "Không có đủ dữ liệu trong khóa học này để tạo tóm tắt."
        
        prompt = f"""Dựa vào toàn bộ "NGỮ CẢNH" dưới đây về một khóa học, hãy thực hiện các yêu cầu sau:
1. Viết một bản tóm tắt tổng quan, súc tích (khoảng 3-4 câu) về nội dung chính.
2. Liệt kê ra 5-7 khái niệm hoặc ý tưởng cốt lõi nhất dưới dạng gạch đầu dòng.
3. Đưa ra một câu hỏi mở để người đọc có thể suy ngẫm thêm về chủ đề.

Trả lời một cách chuyên nghiệp và có cấu trúc rõ ràng.

NGỮ CẢNH:
---
{context}
---

BẢN TÓM TẮT CỦA BẠN:
"""
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Lỗi khi tóm tắt khóa học: {e}")
            return "Rất tiếc, đã xảy ra lỗi trong quá trình tạo tóm tắt."

    def generate_quiz(self, course_id: str, model_name: str, num_questions: int) -> list | str:
        """
        HOÀN THIỆN: Tạo câu hỏi trắc nghiệm (quiz) từ nội dung khóa học.
        Hàm này có khả năng xử lý lỗi nếu AI không trả về đúng định dạng JSON.
        """
        model = self.get_generative_model(model_name)
        if not model: return "Lỗi: Mô hình AI chưa được cấu hình."
        
        context = self._get_full_context(course_id)
        if not context:
            return "Không có đủ dữ liệu để tạo câu hỏi."
            
        prompt = f"""Bạn là một chuyên gia tạo đề thi. Dựa vào "NGỮ CẢNH" được cung cấp, hãy tạo ra chính xác {num_questions} câu hỏi trắc nghiệm (MCQ) để kiểm tra kiến thức.

YÊU CẦU QUAN TRỌNG:
1. Câu hỏi phải đa dạng, bao quát các khía cạnh khác nhau của ngữ cảnh.
2. Mỗi câu hỏi phải có 4 lựa chọn (A, B, C, D).
3. Chỉ có MỘT đáp án đúng.
4. Trả lời DƯỚI DẠNG MỘT DANH SÁCH JSON HỢP LỆ và CHỈ DANH SÁCH JSON ĐÓ.
5. Mỗi đối tượng JSON trong danh sách phải có các key sau: "question" (string), "options" (một danh sách 4 chuỗi lựa chọn), và "answer" (chuỗi chứa đáp án đúng).

NGỮ CẢNH:
---
{context}
---

DANH SÁCH JSON:
"""
        try:
            response = model.generate_content(prompt)
            # Dọn dẹp output của model để đảm bảo nó là một chuỗi JSON sạch
            json_string = response.text.strip().replace("```json", "").replace("```", "")
            return json.loads(json_string)
        except json.JSONDecodeError:
            print(f"Lỗi giải mã JSON từ AI. Output của AI: {response.text}")
            return "Rất tiếc, AI đã trả về một định dạng không hợp lệ. Vui lòng thử lại."
        except Exception as e:
            print(f"Lỗi không xác định khi tạo quiz: {e}")
            return "Đã có lỗi xảy ra trong quá trình tạo câu hỏi trắc nghiệm."

# --- KHỞI TẠO INSTANCE SINGLETON ---
# Toàn bộ ứng dụng sẽ chỉ import và sử dụng instance này để đảm bảo tính nhất quán.
service_manager = ServiceManager()
