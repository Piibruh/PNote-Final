# pnote-ai-app/ui/utils.py
import streamlit as st
def load_css(file):
    try:
        with open(file) as f: st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError: st.error(f"Lỗi: Không tìm thấy file CSS.")
def page_init(title, icon="📚"):
    st.set_page_config(page_title=title, page_icon=icon, layout="wide")
    load_css("styles.css")
    theme = "dark-theme" if st.session_state.get("theme", "Dark") == "Dark" else "light-theme"
    st.html(f"<script>document.body.className='{theme}';</script>")
