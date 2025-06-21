# pnote-ai-app/core/services.py

# ==============================================================================
# BỘ NÃO TRUNG TÂM CỦA ỨNG DỤNG - SERVICE MANAGER
#
# Phiên bản này được nâng cấp với các tính năng chuyên nghiệp:
# 1. Logging: Ghi lại các sự kiện và lỗi một cách có cấu trúc.
# 2. Caching: Lưu kết quả AI để tiết kiệm chi phí và tăng tốc độ.
# 3. Phân tích Nâng cao: Trích xuất từ khóa, nhận diện thực thể.
# 4. Thống kê chi tiết: Cung cấp số liệu về không gian làm việc.
# ==============================================================================


# --- KHAI BÁO THƯ VIỆN VÀ CẤU HÌNH BAN ĐẦU ---

# BẮT BUỘC: Sửa lỗi SQLite3 trên môi trường Streamlit Cloud.
# Phải đặt ở đầu tiên để đảm bảo Python sử dụng phiên bản pysqlite3-binary.
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

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
import logging

# Import cấu hình từ file config.py
from config import (
    GEMINI_API_KEY, TEXT_CHUNK_SIZE, TEXT_CHUNK_OVERLAP, VECTOR_DB_SEARCH_RESULTS,
    CHROMA_DB_PATH, USER_DATA_PATH, DEFAULT_MODEL, DEFAULT_SYSTEM_PROMPT,
    SUMMARY_PROMPT_TEMPLATE, QUIZ_PROMPT_TEMPLATE
)


# --- CÀI ĐẶT HỆ THỐNG LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# --- CÁC HÀM TIỆN ÍCH (UTILITY FUNCTIONS) ---

def slugify(value: str) -> str:
    """Chuyển đổi chuỗi thành định dạng an toàn cho ID hoặc tên file."""
    value = normalize('NFKD', str(value)).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    return re.sub(r'[-\s]+', '-', value)

def calculate_file_hash(file_bytes: bytes) -> str:
    """Tính toán mã hash SHA256 cho nội dung của một file để chống trùng lặp."""
    return hashlib.sha256(file_bytes).hexdigest()


# --- LỚP QUẢN LÝ DỊCH VỤ CHÍNH (SINGLETON) ---

class ServiceManager:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ServiceManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized: return
        self.chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
        else:
            logger.warning("GEMINI_API_KEY chưa được cấu hình. Các tính năng AI sẽ không hoạt động.")
        self._initialized = True
        logger.info("ServiceManager đã được khởi tạo.")

    # --- NHÓM HÀM QUẢN LÝ CACHE ---
    def _get_cache_path(self, course_id: str, feature_name: str) -> str:
        """Tạo đường dẫn cho file cache dựa trên ID khóa học và tên tính năng."""
        cache_dir = os.path.join(USER_DATA_PATH, course_id, "cache")
        os.makedirs(cache_dir, exist_ok=True)
        return os.path.join(cache_dir, f"{feature_name}.json")

    def _save_to_cache(self, path: str, data: any):
        """Lưu dữ liệu vào file cache dưới dạng JSON."""
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error(f"Không thể lưu cache vào {path}: {e}")

    def _load_from_cache(self, path: str) -> any:
        """Đọc dữ liệu từ file cache nếu nó tồn tại."""
        if not os.path.exists(path):
            return None
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Không thể đọc cache từ {path}: {e}")
            return None
            
    def _invalidate_cache(self, course_id: str):
        """Xóa toàn bộ cache của một khóa học khi có sự thay đổi về tài liệu."""
        cache_dir = os.path.join(USER_DATA_PATH, course_id, "cache")
        if os.path.isdir(cache_dir):
            try:
                shutil.rmtree(cache_dir)
                logger.info(f"Đã xóa cache cho khóa học: {course_id}")
            except Exception as e:
                logger.error(f"Lỗi khi xóa cache cho khóa học {course_id}: {e}")

    # --- NHÓM HÀM XỬ LÝ TÀI LIỆU ---
    def extract_text_from_source(self, source_type: str, source_data: any) -> tuple[str | None, str]:
        text, original_name = None, "N/A"
        try:
            if source_type == 'pdf' and hasattr(source_data, 'read'):
                original_name = source_data.name
                pdf_reader = PdfReader(source_data)
                text = "".join(page.extract_text() for page in pdf_reader.pages if page.extract_text())
            elif source_type == 'docx' and hasattr(source_data, 'read'):
                original_name = source_data.name
                doc = docx.Document(source_data)
                text = "\n".join([para.text for para in doc.paragraphs if para.text])
            elif source_type == 'url' and isinstance(source_data, str):
                original_name = source_data
                headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.get(source_data, headers=headers, timeout=15)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                    tag.decompose()
                text = soup.get_text(separator='\n', strip=True)
            elif source_type == 'youtube' and isinstance(source_data, str):
                video_id_match = re.search(r"(?<=v=)[\w-]+|(?<=youtu.be/)[\w-]+", source_data)
                if not video_id_match:
                    raise ValueError("URL YouTube không hợp lệ.")
                video_id = video_id_match.group(0)
                original_name = f"youtube_{video_id}"
                transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['vi', 'en'])
                text = " ".join([item['text'] for item in transcript])
            
            if not text or not text.strip():
                return None, original_name
            return text, original_name
        except Exception as e:
            logger.error(f"Lỗi khi trích xuất từ '{original_name}': {e}")
            return None, original_name

    def list_courses(self) -> list[dict]:
        try:
            collections = self.chroma_client.list_collections()
            return [{"id": col.name, "name": col.metadata.get("display_name", col.name)} for col in collections]
        except Exception as e:
            logger.error(f"Lỗi khi liệt kê khóa học: {e}")
            return []

    def create_course(self, display_name: str) -> tuple[str | None, str | None]:
        if not display_name.strip():
            return None, "Tên không gian làm việc không được để trống."
        course_id = slugify(display_name)
        try:
            self.chroma_client.get_or_create_collection(name=course_id, metadata={"display_name": display_name})
            os.makedirs(os.path.join(USER_DATA_PATH, course_id), exist_ok=True)
            return course_id, None
        except Exception as e:
            logger.error(f"Lỗi khi tạo khóa học '{display_name}': {e}")
            return None, f"Lỗi không xác định khi tạo không gian làm việc."

    def delete_course(self, course_id: str):
        try:
            self.chroma_client.delete_collection(name=course_id)
        except Exception as e:
            logger.info(f"Không tìm thấy collection '{course_id}' để xóa hoặc có lỗi: {e}")
        try:
            self._invalidate_cache(course_id) # Xóa cache liên quan
            course_data_path = os.path.join(USER_DATA_PATH, course_id)
            if os.path.isdir(course_data_path):
                shutil.rmtree(course_data_path)
        except Exception as e:
            logger.error(f"Lỗi khi xóa dữ liệu người dùng cho khóa học {course_id}: {e}")

    def add_doc(self, course_id: str, doc_text: str, source_name: str, file_hash: str) -> int:
        collection = self.chroma_client.get_collection(name=course_id)
        tokens = self.tokenizer.encode(doc_text)
        chunks = [self.tokenizer.decode(tokens[i:i + TEXT_CHUNK_SIZE]) for i in range(0, len(tokens), TEXT_CHUNK_SIZE - TEXT_CHUNK_OVERLAP)]
        if not chunks: return 0
        
        doc_ids = [f"{slugify(source_name)}-{i}-{int(time.time() * 1000)}" for i in range(len(chunks))]
        metadatas = [{"source": source_name, "file_hash": file_hash}] * len(chunks)
        collection.add(documents=chunks, metadatas=metadatas, ids=doc_ids)
        self._invalidate_cache(course_id)
        return len(chunks)

    def hash_exists(self, course_id: str, file_hash: str) -> bool:
        try:
            collection = self.chroma_client.get_collection(name=course_id)
            return len(collection.get(where={"file_hash": file_hash}, limit=1)['ids']) > 0
        except Exception: return False

    def list_docs(self, course_id: str) -> list[dict]:
        try:
            collection = self.chroma_client.get_collection(name=course_id)
            if collection.count() == 0: return []
            metadatas = collection.get(include=["metadatas"])['metadatas']
            unique_docs = {meta['file_hash']: meta['source'] for meta in metadatas if 'file_hash' in meta}
            return [{"hash": h, "name": n} for h, n in unique_docs.items()]
        except Exception: return []

    def delete_doc(self, course_id: str, file_hash: str):
        collection = self.chroma_client.get_collection(name=course_id)
        collection.delete(where={"file_hash": file_hash})
        self._invalidate_cache(course_id)
        logger.info(f"Đã xóa tài liệu hash={file_hash} khỏi khóa học {course_id}")

    def _get_context(self, course_id: str, max_chunks: int = 30) -> str | None:
        try:
            collection = self.chroma_client.get_collection(name=course_id)
            if (count := collection.count()) == 0: return None
            documents = collection.get(limit=min(count, max_chunks))
            return "\n---\n".join(documents['documents'])
        except Exception as e:
            logger.error(f"Lỗi khi lấy ngữ cảnh đầy đủ cho {course_id}: {e}")
            return None

    def get_chat_stream(self, course_id: str, question: str, history: list):
        if not GEMINI_API_KEY: yield "Lỗi: API Key chưa được cấu hình."; return
        try:
            model = genai.GenerativeModel(DEFAULT_MODEL, system_instruction=DEFAULT_SYSTEM_PROMPT)
            collection = self.chroma_client.get_collection(name=course_id)
            context_results = collection.query(query_texts=[question], n_results=VECTOR_DB_SEARCH_RESULTS)
            context = "\n---\n".join(context_results['documents'][0])
            prompt = f"NGỮ CẢNH:\n{context}\n\nCÂU HỎI: {question}"
            chat_session = model.start_chat(history=history)
            for chunk in chat_session.send_message(prompt, stream=True): yield chunk.text
        except Exception as e: yield f"Lỗi: {e}"

    def summarize(self, course_id: str) -> str:
        path = self._get_cache_path(course_id, "summary")
        if cached := self._load_from_cache(path): return cached
        if not (context := self._get_context(course_id)): return "Không có dữ liệu."
        try:
            model = genai.GenerativeModel(DEFAULT_MODEL)
            response = model.generate_content(SUMMARY_PROMPT_TEMPLATE.format(context=context))
            text = response.text
            self._save_to_cache(path, text)
            return text
        except Exception as e: return f"Lỗi: {e}"

    def generate_quiz(self, course_id: str, num_q: int) -> list | str:
        path = self._get_cache_path(course_id, f"quiz_{num_q}")
        if cached := self._load_from_cache(path): return cached
        if not (context := self._get_context(course_id)): return "Không có dữ liệu."
        try:
            model = genai.GenerativeModel(DEFAULT_MODEL)
            response = model.generate_content(QUIZ_PROMPT_TEMPLATE.format(num_questions=num_q, context=context), generation_config={"response_mime_type": "application/json"})
            data = json.loads(response.text)
            self._save_to_cache(path, data)
            return data
        except Exception as e: return f"Lỗi: {e}"

    def extract_keywords(self, course_id: str) -> list | str:
        path = self._get_cache_path(course_id, "keywords")
        if cached := self._load_from_cache(path): return cached
        if not (context := self._get_context(course_id, 20)): return "Không có dữ liệu."
        prompt = f"""Trích xuất 10-15 từ khóa/cụm từ khóa quan trọng từ ngữ cảnh. Trả về dưới dạng danh sách JSON. NGỮ CẢNH:\n{context}\n\nDANH SÁCH JSON:"""
        try:
            model = genai.GenerativeModel(DEFAULT_MODEL)
            response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            data = json.loads(response.text)
            self._save_to_cache(path, data)
            return data
        except Exception as e: return f"Lỗi: {e}"

    def generate_study_questions(self, course_id: str, num_q: int = 5) -> list | str:
        path = self._get_cache_path(course_id, f"study_q_{num_q}")
        if cached := self._load_from_cache(path): return cached
        if not (context := self._get_context(course_id)): return "Không có dữ liệu."
        prompt = f"""Tạo {num_q} câu hỏi mở, sâu sắc từ ngữ cảnh để hỗ trợ học tập. Trả về dưới dạng danh sách JSON. NGỮ CẢNH:\n{context}\n\nDANH SÁCH JSON:"""
        try:
            model = genai.GenerativeModel(DEFAULT_MODEL)
            response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            data = json.loads(response.text)
            self._save_to_cache(path, data)
            return data
        except Exception as e: return f"Lỗi: {e}"

    def get_course_statistics(self, course_id: str) -> dict | None:
        try:
            collection = self.chroma_client.get_collection(name=course_id)
            chunks = collection.count()
            docs = self.list_docs(course_id)
            return {"doc_count": len(docs), "chunk_count": chunks, "token_est": chunks * TEXT_CHUNK_SIZE}
        except Exception as e:
            logger.error(f"Lỗi lấy thống kê {course_id}: {e}")
            return None

service_manager = ServiceManager()
