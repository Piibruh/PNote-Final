# pnote-ai-app/app.py
import streamlit as st
import os
from ui import utils, sidebar, onboarding
from core.services import service_manager
from config import CHROMA_DB_PATH, USER_DATA_PATH, GEMINI_API_KEY

# --- BƯỚC 1: KHỞI TẠO STATE & CẤU HÌNH TRANG ---
if "theme" not in st.session_state:
    st.session_state.theme = "Dark"
# State này sẽ được quản lý bởi st.tour()
if "onboarding_complete" not in st.session_state:
    st.session_state.onboarding_complete = False

utils.page_init("PNote AI - Trang chủ")

# --- BƯỚC 2: KIỂM TRA & KHỞI TẠO ---
if not GEMINI_API_KEY:
    st.error("LỖI CẤU HÌNH: Không tìm thấy GEMINI_API_KEY."); st.stop()

os.makedirs(CHROMA_DB_PATH, exist_ok=True); os.makedirs(USER_DATA_PATH, exist_ok=True)

if "sm" not in st.session_state:
    st.session_state.sm = service_manager
    st.session_state.courses = st.session_state.sm.list_courses()
    st.session_state.cid = st.session_state.courses[0]['id'] if st.session_state.courses else None
    st.session_state.history = {}
else:
    st.session_state.courses = st.session_state.sm.list_courses()

# --- BƯỚC 3: VẼ GIAO DIỆN ---
sidebar.display()
# Truyền 'home' để onboarding biết cần chạy tour cho trang chủ
onboarding.display_onboarding_features("home")

# --- BƯỚC 4: HIỂN THỊ NỘI DUNG CHÍNH ---
# Nếu người dùng chưa từng hoàn thành onboarding, hiển thị bảng chào mừng
if not st.session_state.onboarding_complete:
    onboarding.display_welcome_and_capabilities()
    st.markdown("---")


# Hiển thị nội dung tùy thuộc vào việc đã có workspace chưa
if not st.session_state.get("cid"):
    st.info("👈 Bắt đầu bằng cách tạo hoặc chọn một không gian làm việc từ thanh sidebar.")
else:
    name = next((c['name'] for c in st.session_state.courses if c['id'] == st.session_state.cid), "...")
    st.title(f"🚀 Không gian làm việc: {name}")
    st.page_link("pages/workspace.py", label="**Đi đến Workspace để bắt đầu →**", icon="📝")
