# ui/utils.py
import streamlit as st
from core.services import service_manager
from .onboarding import onboarding_popup, help_button
from config import DEFAULT_THEME

def apply_theme():
    theme = st.session_state.get('theme', DEFAULT_THEME)
    st.markdown(f"<script>document.querySelector('body').classList.remove('light-theme', 'dark-theme'); document.querySelector('body').classList.add('{theme}-theme');</script>", unsafe_allow_html=True)

def theme_toggle_button():
    if 'theme' not in st.session_state: st.session_state.theme = DEFAULT_THEME
    icon = "🌑" if st.session_state.theme == 'dark' else "💡"
    tooltip = "Chuyển sang Light Mode" if st.session_state.theme == 'dark' else "Chuyển sang Dark Mode"
    
    # Nút ẩn của Streamlit để xử lý logic trong Python
    if st.button("Theme Toggle Callback", key="theme_toggle_callback", help="Internal callback"):
        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
        st.rerun()

    st.markdown(f"""
        <style>
            .theme-toggle-container {{ position: fixed; top: 1rem; right: 1.5rem; z-index: 9999; }}
            .theme-toggle-button {{
                background: var(--secondary-bg); color: var(--text-color); border: 1px solid var(--border-color);
                border-radius: 50%; width: 45px; height: 45px; font-size: 24px; cursor: pointer;
                transition: all 0.2s ease;
            }}
            .theme-toggle-button:hover {{ transform: scale(1.1) rotate(15deg); border-color: var(--primary-color); }}
            button[key="theme_toggle_callback"] {{ display: none; }}
        </style>
        <div class="theme-toggle-container">
            <button id="theme-toggle-btn" class="theme-toggle-button" title="{tooltip}"
                    onclick="window.parent.document.querySelector('[data-testid=\"stButton\"][key=\"theme_toggle_callback\"]').click();">
                {icon}
            </button>
        </div>
    """, unsafe_allow_html=True)


def page_setup(page_title: str, page_icon: str, initial_sidebar_state: str = "expanded"):
    st.set_page_config(page_title=page_title, page_icon=page_icon, layout="wide", initial_sidebar_state=initial_sidebar_state)
    apply_theme()
    with open("styles.css") as f: st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    if "courses" not in st.session_state: st.session_state.courses = service_manager.list_courses()
    if "onboarding_complete" not in st.session_state: st.session_state.onboarding_complete = False
    if not st.session_state.onboarding_complete: onboarding_popup()
    help_button()
    theme_toggle_button()
