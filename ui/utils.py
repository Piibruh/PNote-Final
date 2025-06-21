# ui/utils.py

# Ghi chú: File này chứa các hàm tiện ích được sử dụng trên nhiều trang.
# Việc tách các hàm này ra giúp tránh lặp code và làm cho mã nguồn trang chính
# (app.py, pages/workspace.py) sạch sẽ, dễ đọc và bảo trì.

import streamlit as st
from core.services import service_manager
from .onboarding import onboarding_popup
from config import DEFAULT_THEME

def apply_theme():
    """
    Hàm này inject một đoạn mã JavaScript nhỏ vào trang để thêm CSS class
    vào thẻ <body>. Điều này cho phép file styles.css áp dụng các biến màu
    tương ứng cho chế độ Sáng (light-theme) hoặc Tối (dark-theme).
    """
    theme = st.session_state.get('theme', DEFAULT_THEME)
    st.markdown(
        f"""
        <script>
            document.querySelector('body').classList.remove('light-theme', 'dark-theme');
            document.querySelector('body').classList.add('{theme}-theme');
        </script>
        """,
        unsafe_allow_html=True
    )

def theme_toggle_button():
    """
    Hàm này tạo nút chuyển đổi theme ở góc trên bên phải.
    Nó sử dụng một mẹo "nút ẩn" để kết hợp giao diện HTML/CSS tùy chỉnh
    với logic xử lý sự kiện của Python trong Streamlit.
    """
    if 'theme' not in st.session_state:
        st.session_state.theme = DEFAULT_THEME
    
    # Xác định icon và tooltip dựa trên theme hiện tại
    icon = "🌑" if st.session_state.theme == 'dark' else "💡"
    tooltip = "Chuyển sang Light Mode" if st.session_state.theme == 'dark' else "Chuyển sang Dark Mode"

    # Đây là nút ẩn của Streamlit, nó sẽ được kích hoạt bởi JavaScript.
    if st.button("Theme Toggle Callback", key="theme_toggle_callback", help="Internal callback for theme switching"):
        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
        st.rerun()

    # Đây là nút bấm thật mà người dùng nhìn thấy, được tạo bằng HTML/CSS.
    st.markdown(f"""
        <style>
            .theme-toggle-container {{ position: fixed; top: 1rem; right: 1.5rem; z-index: 9999; }}
            .theme-toggle-button {{
                background: var(--secondary-bg); color: var(--text-color); border: 1px solid var(--border-color);
                border-radius: 50%; width: 45px; height: 45px; font-size: 24px; cursor: pointer;
                transition: all 0.2s ease;
            }}
            .theme-toggle-button:hover {{ transform: scale(1.1) rotate(15deg); border-color: var(--primary-color); }}
            /* Ẩn nút callback của Streamlit khỏi giao diện */
            button[key="theme_toggle_callback"] {{ display: none; }}
        </style>
        <div class="theme-toggle-container">
            <button id="theme-toggle-btn" class="theme-toggle-button" title="{tooltip}"
                    onclick="window.parent.document.querySelector('[data-testid=\"stButton\"][key=\"theme_toggle_callback\"]').click();">
                {icon}
            </button>
        </div>
    """, unsafe_allow_html=True)

def help_button():
    """Hàm tạo nút "?" cố định ở góc dưới bên phải để xem lại hướng dẫn."""
    # Nút ẩn của Streamlit để kích hoạt lại popup
    if st.button("Show Onboarding", key="show-onboarding-button"):
        # Đặt cờ để báo hiệu cho app.py rằng cần hiển thị popup
        st.session_state.onboarding_status = 'showing'
        st.rerun()

    # Nút bấm thật mà người dùng nhìn thấy
    st.markdown("""
        <style>
            .help-button-container {{ position: fixed; bottom: 20px; right: 20px; z-index: 9999; }}
            .help-button {{
                background-color: var(--primary-color); color: white; border: none; border-radius: 50%;
                width: 50px; height: 50px; font-size: 24px; font-weight: bold; cursor: pointer;
                box-shadow: 0 4px 12px rgba(0,0,0,0.4); transition: transform 0.2s ease;
            }}
            .help-button:hover {{ transform: scale(1.1); }}
        </style>
        <div class="help-button-container">
            <button class="help-button" onclick="window.parent.document.querySelector('[data-testid=\"stButton\"][key=\"show-onboarding-button\"]').click();">?</button>
        </div>
    """, unsafe_allow_html=True)


def page_setup(page_title: str, page_icon: str, initial_sidebar_state: str = "expanded"):
    """
    Hàm thiết lập trang toàn diện, được gọi ở đầu mỗi file trang.
    Đây là phiên bản đã được sửa lỗi "timing" của st.dialog.
    """
    st.set_page_config(
        page_title=page_title,
        page_icon=page_icon,
        layout="wide",
        initial_sidebar_state=initial_sidebar_state
    )

    # Áp dụng theme và CSS tùy chỉnh vào trang
    apply_theme()
    with open("styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    # --- SỬA LỖI: Logic khởi tạo state 2 bước cho onboarding ---
    # Khởi tạo các state cốt lõi nếu chúng chưa tồn tại
    if "courses" not in st.session_state:
        st.session_state.courses = service_manager.list_courses()
    
    # State này quản lý luồng hiển thị popup hướng dẫn
    if "onboarding_status" not in st.session_state:
        # Lần đầu tiên người dùng truy cập, đặt trạng thái là 'needed'.
        # 'needed' có nghĩa là: "cần hiển thị, nhưng chưa phải bây giờ".
        st.session_state.onboarding_status = 'needed'
    
    # Hiển thị các nút cố định trên giao diện.
    help_button()
    theme_toggle_button()
