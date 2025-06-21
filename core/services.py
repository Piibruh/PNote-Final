# pnote-ai-app/core/services.py
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import google.api_core.exceptions, google.generativeai as genai, chromadb
from pypdf import PdfReader
import docx, requests, tiktoken, time, re, json, hashlib, os, shutil, logging
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi
from unicodedata import normalize
from config import *

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def slugify(v: str) -> str: v=normalize('NFKD',str(v)).encode('ascii','ignore').decode('ascii');v=re.sub(r'[^\w\s-]','',v).strip().lower();return re.sub(r'[-\s]+','-',v)
def calculate_file_hash(b: bytes) -> str: return hashlib.sha256(b).hexdigest()

class ServiceManager:
    _instance, _initialized = None, False
    def __new__(cls):
        if cls._instance is None: cls._instance = super(ServiceManager, cls).__new__(cls)
        return cls._instance
    def __init__(self):
        if self._initialized: return
        self.chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        if GEMINI_API_KEY: genai.configure(api_key=GEMINI_API_KEY)
        else: logger.warning("GEMINI_API_KEY chưa được cấu hình.")
        self._initialized = True; logger.info("ServiceManager đã khởi tạo.")

    def _get_cache_path(self, cid:str, fname:str) -> str: p=os.path.join(USER_DATA_PATH,cid,"cache");os.makedirs(p,exist_ok=True);return os.path.join(p,f"{fname}.json")
    def _save_to_cache(self, p:str, data:any):
        try:
            with open(p,'w',encoding='utf-8') as f: json.dump(data,f,ensure_ascii=False,indent=4)
        except Exception as e: logger.error(f"Lỗi lưu cache {p}: {e}")
    def _load_from_cache(self, p:str) -> any:
        if not os.path.exists(p): return None
        try:
            with open(p,'r',encoding='utf-8') as f: return json.load(f)
        except Exception as e: logger.error(f"Lỗi đọc cache {p}: {e}"); return None
    def _invalidate_cache(self, cid:str):
        p=os.path.join(USER_DATA_PATH,cid,"cache")
        if os.path.isdir(p):
            try: shutil.rmtree(p); logger.info(f"Đã xóa cache cho {cid}")
            except Exception as e: logger.error(f"Lỗi xóa cache cho {cid}: {e}")

    def extract_text_from_source(self, stype: str, sdata: any) -> tuple[str|None, str]:
        text, name = None, "N/A"
        try:
            if stype=='pdf': name,text = sdata.name,"".join(p.extract_text() for p in PdfReader(sdata).pages if p.extract_text())
            elif stype=='docx': name,text = sdata.name,"\n".join(p.text for p in docx.Document(sdata).paragraphs if p.text)
            elif stype=='url': name,r = sdata,requests.get(sdata, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15); r.raise_for_status(); s=BeautifulSoup(r.content,'html.parser'); [t.decompose() for t in s(["script","style","nav","footer","header","aside"])]; text=s.get_text('\n',strip=True)
            elif stype=='youtube': m=re.search(r"(?<=v=)[\w-]+|(?<=youtu.be/)[\w-]+",sdata); v=m.group(0) if m else None; name=f"youtube_{v}"; text=" ".join(i['text'] for i in YouTubeTranscriptApi.get_transcript(v,languages=['vi','en']))
            return (text,name) if text and text.strip() else (None, name)
        except Exception as e: logger.error(f"Lỗi trích xuất '{name}': {e}"); return None, name

    def list_courses(self)->list[dict]:
        try: return [{"id":c.name,"name":c.metadata.get("display_name",c.name)} for c in self.chroma_client.list_collections()]
        except Exception as e: logger.error(f"Lỗi liệt kê khóa học: {e}"); return []
    def create_course(self, name:str) -> tuple[str|None,str|None]:
        if not name.strip(): return None, "Tên không được trống."
        cid = slugify(name)
        try: self.chroma_client.get_or_create_collection(name=cid, metadata={"display_name":name}); os.makedirs(os.path.join(USER_DATA_PATH,cid),exist_ok=True); return cid, None
        except Exception as e: logger.error(f"Lỗi tạo khóa học '{name}': {e}"); return None, f"Lỗi: {e}"
    def delete_course(self, cid:str):
        try: self.chroma_client.delete_collection(name=cid)
        except Exception: pass
        try: self._invalidate_cache(cid); shutil.rmtree(os.path.join(USER_DATA_PATH,cid))
        except Exception: pass
    def add_doc(self, cid:str, txt:str, sname:str, fhash:str)->int:
        col=self.chroma_client.get_collection(name=cid);tok=self.tokenizer.encode(txt);chk=[self.tokenizer.decode(tok[i:i+TEXT_CHUNK_SIZE]) for i in range(0,len(tok),TEXT_CHUNK_SIZE-TEXT_CHUNK_OVERLAP)]
        if not chk: return 0
        ids=[f"{slugify(sname)}-{i}-{int(time.time()*1000)}" for i in range(len(chk))]; metas=[{"source":sname,"file_hash":fhash}]*len(chk)
        col.add(documents=chk, metadatas=metas, ids=ids); self._invalidate_cache(cid); return len(chk)
    def hash_exists(self, cid:str, fhash:str)->bool:
        try: return len(self.chroma_client.get_collection(name=cid).get(where={"file_hash":fhash},limit=1)['ids'])>0
        except Exception: return False
    def list_docs(self, cid:str)->list[dict]:
        try: col=self.chroma_client.get_collection(name=cid);
            if col.count()==0: return []; metas=col.get(include=["metadatas"])['metadatas']; return [{"hash":h,"name":n} for h,n in {m['file_hash']:m['source'] for m in metas if 'file_hash' in m}.items()]
        except Exception: return []
    def delete_doc(self, cid:str, fhash:str): self.chroma_client.get_collection(name=cid).delete(where={"file_hash":fhash}); self._invalidate_cache(cid)
    def _get_context(self, cid:str, max_chunks:int=30)->str|None:
        try: col=self.chroma_client.get_collection(name=cid); return "\n---\n".join(col.get(limit=min(col.count(),max_chunks))['documents']) if col.count()>0 else None
        except Exception as e: logger.error(f"Lỗi lấy ngữ cảnh {cid}: {e}"); return None
    def get_chat_stream(self, cid:str, q:str, hist:list):
        if not GEMINI_API_KEY: yield "Lỗi: API Key chưa cấu hình."; return
        try:
            ctx_r=self.chroma_client.get_collection(name=cid).query(query_texts=[q],n_results=VECTOR_DB_SEARCH_RESULTS); ctx="\n---\n".join(ctx_r['documents'][0])
            prompt=f"NGỮ CẢNH:\n{ctx}\n\nCÂU HỎI: {q}"; model=genai.GenerativeModel(DEFAULT_MODEL,system_instruction=DEFAULT_SYSTEM_PROMPT)
            for chunk in model.start_chat(history=hist).send_message(prompt,stream=True): yield chunk.text
        except Exception as e: yield f"Lỗi: {e}"
    def summarize(self, cid:str)->str:
        path=self._get_cache_path(cid,"summary");
        if cached:=self._load_from_cache(path): logger.info(f"Đã tải tóm tắt từ cache cho {cid}"); return cached
        if not (ctx:=self._get_context(cid)): return "Không có dữ liệu."
        try: model=genai.GenerativeModel(DEFAULT_MODEL); resp=model.generate_content(SUMMARY_PROMPT_TEMPLATE.format(context=ctx)).text; self._save_to_cache(path,resp); return resp
        except Exception as e: logger.error(f"Lỗi tóm tắt {cid}: {e}"); return f"Lỗi: {e}"
    def generate_quiz(self, cid:str, num_q:int)->list|str:
        path=self._get_cache_path(cid,f"quiz_{num_q}");
        if cached:=self._load_from_cache(path): logger.info(f"Đã tải quiz từ cache cho {cid}"); return cached
        if not (ctx:=self._get_context(cid)): return "Không có dữ liệu."
        try: model=genai.GenerativeModel(DEFAULT_MODEL); resp=model.generate_content(QUIZ_PROMPT_TEMPLATE.format(num_questions=num_q,context=ctx),generation_config={"response_mime_type":"application/json"}).text; data=json.loads(resp); self._save_to_cache(path,data); return data
        except Exception as e: logger.error(f"Lỗi tạo quiz {cid}: {e}"); return f"Lỗi: {e}"
    def extract_keywords(self, cid:str)->list|str:
        path=self._get_cache_path(cid,"keywords");
        if cached:=self._load_from_cache(path): logger.info(f"Đã tải keywords từ cache cho {cid}"); return cached
        if not (ctx:=self._get_context(cid,20)): return "Không có dữ liệu."
        prompt=f"""Trích xuất 10-15 từ khóa/cụm từ khóa quan trọng từ ngữ cảnh. Trả về dưới dạng danh sách JSON. NGỮ CẢNH:\n{ctx}\n\nDANH SÁCH JSON:"""
        try: model=genai.GenerativeModel(DEFAULT_MODEL); resp=model.generate_content(prompt,generation_config={"response_mime_type":"application/json"}).text; data=json.loads(resp); self._save_to_cache(path,data); return data
        except Exception as e: logger.error(f"Lỗi trích xuất keywords {cid}: {e}"); return f"Lỗi: {e}"
    def generate_study_questions(self, cid:str, num_q:int=5)->list|str:
        path=self._get_cache_path(cid,f"study_q_{num_q}");
        if cached:=self._load_from_cache(path): return cached
        if not (ctx:=self._get_context(cid)): return "Không có dữ liệu."
        prompt=f"""Tạo {num_q} câu hỏi mở, sâu sắc từ ngữ cảnh để hỗ trợ học tập. Trả về dưới dạng danh sách JSON. NGỮ CẢNH:\n{ctx}\n\nDANH SÁCH JSON:"""
        try: model=genai.GenerativeModel(DEFAULT_MODEL); resp=model.generate_content(prompt,generation_config={"response_mime_type":"application/json"}).text; data=json.loads(resp); self._save_to_cache(path,data); return data
        except Exception as e: logger.error(f"Lỗi tạo câu hỏi học tập {cid}: {e}"); return f"Lỗi: {e}"
    def get_course_statistics(self, cid:str)->dict|None:
        try: col=self.chroma_client.get_collection(name=cid); chunks=col.count(); docs=self.list_docs(cid); return {"doc_count":len(docs),"chunk_count":chunks,"token_est":chunks*TEXT_CHUNK_SIZE}
        except Exception as e: logger.error(f"Lỗi lấy thống kê {cid}: {e}"); return None
service_manager = ServiceManager()
