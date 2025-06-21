# pnote-ai-app/app.py
import streamlit as st
import os
from ui import utils, sidebar, onboarding
from core.services import service_manager
from config import CHROMA_DB_PATH, USER_DATA_PATH, GEMINI_API_KEY

if "theme" not in st.session_state: st.session_state.theme = "Dark"
utils.page_init("PNote AI - Trang chủ")

if not GEMINI_API_KEY:
    st.error("LỖI CẤU HÌNH: Không tìm thấy GEMINI_API_KEY.")
    st.stop()

os.makedirs(CHROMA_DB_PATH, exist_ok=True)
os.makedirs(USER_DATA_PATH, exist_ok=True)

if "sm" not in st.session_state:
    st.session_state.sm = service_manager
    st.session_state.courses = st.session_state.sm.list_courses()
    st.session_state.cid = st.session_state.courses[0]['id'] if st.session_state.courses else None
    st.session_state.history = {}
else:
    st.session_state.courses = st.session_state.sm.list_courses()

sidebar.display()

if not st.session_state.get("cid"):
    onboarding.display()
else:
    name = next((c['name'] for c in st.session_state.courses if c['id'] == st.session_state.cid), "...")
    st.title(f"🚀 Không gian làm việc: {name}")
    st.page_link("pages/workspace.py", label="**Đi đến Workspace →**", icon="📝")
