# app.py

# Ghi chú: Đây là file trang Dashboard, là điểm vào đầu tiên của ứng dụng.
# Nó chịu trách nhiệm hiển thị danh sách khóa học và cho phép tạo khóa học mới.

import streamlit as st
from core.services import service_manager, slugify
from ui.utils import page_setup
# NEW: Import hàm onboarding_popup trực tiếp
from ui.onboarding import onboarding_popup
import time

# --- BƯỚC 1: THIẾT LẬP TRANG ---
# Ghi chú: Hàm này sẽ cấu hình trang, áp dụng CSS, và quan trọng nhất là
# đặt cờ "show_onboarding_popup" trong session_state nếu cần.
page_setup(page_title="PNote Dashboard", page_icon="📝", initial_sidebar_state="collapsed")

# --- BƯỚC 2: XỬ LÝ CÁC HÀNH ĐỘNG TOÀN CỤC Ở CẤP CAO NHẤT ---
# NEW: Đây là logic mới để xử lý popup một cách an toàn.
# Nó kiểm tra cờ đã được đặt bởi page_setup().
if st.session_state.get('show_onboarding_popup', False):
    # Gọi hàm hiển thị popup ở đây, tại cấp cao nhất của trang.
    onboarding_popup()
    # Sau khi dialog được gọi, tắt cờ này đi để nó không hiện lại trong các lần rerun sau.
    st.session_state.show_onboarding_popup = False


# --- BƯỚC 3: HIỂN THỊ GIAO DIỆN CHÍNH CỦA TRANG ---
# Ghi chú: Phần code dưới đây không thay đổi so với phiên bản trước.

st.markdown("""<div class="logo-box-large"><span class="logo-text-large">P</span></div>""", unsafe_allow_html=True)
st.title("PNote Workspace")
st.text("Chào mừng trở lại! Chọn một khóa học để bắt đầu hoặc tạo một không gian làm việc mới.")
st.markdown("---")

with st.expander("➕ Tạo khóa học mới", expanded=True):
    with st.form("new_course_form"):
        col1, col2 = st.columns([3, 1])
        with col1:
            name = st.text_input("Tên khóa học", placeholder="vd: Lịch sử Đảng Cộng sản Việt Nam")
        with col2:
            submitted = st.form_submit_button("Tạo Ngay", use_container_width=True, type="secondary")
        
        if submitted and name:
            safe_id = slugify(name)
            if 3 <= len(safe_id) <= 63 and not any(c['id'] == safe_id for c in st.session_state.courses):
                with st.spinner(f"Đang tạo khóa học '{name}'..."):
                    service_manager.create_course(safe_id, name)
                    st.session_state.courses = service_manager.list_courses()
                    st.session_state.current_course_id = safe_id
                    st.session_state.current_course_name = name
                    st.success(f"Đã tạo '{name}'!"); time.sleep(1); st.switch_page("pages/workspace.py")
            else:
                st.error("Tên khóa học không hợp lệ hoặc đã tồn tại.")

st.markdown("---")
st.header("Danh sách khóa học của bạn", anchor=False)

if not st.session_state.get('courses', []):
    st.info("Bạn chưa có khóa học nào. Hãy tạo một khóa học mới ở trên để bắt đầu!")
else:
    sorted_courses = sorted(st.session_state.courses, key=lambda c: c['name'])
    cols = st.columns(4)
    for i, course in enumerate(sorted_courses):
        with cols[i % 4].container():
            st.markdown(f"""<div class="course-card"><h3>{course['name']}</h3><p>ID: {course['id']}</p></div>""", unsafe_allow_html=True)
            if st.button("Mở Workspace", key=f"enter_{course['id']}", use_container_width=True):
                st.session_state.current_course_id = course['id']
                st.session_state.current_course_name = course['name']
                st.switch_page("pages/workspace.py")
