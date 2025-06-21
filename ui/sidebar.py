# ui/sidebar.py

# Ghi chú: File này chịu trách nhiệm vẽ toàn bộ thanh bên trái (sidebar)
# trong không gian làm việc. Nó bao gồm các chức năng chính:
# 1. Thêm tài liệu từ nhiều nguồn (file, URL, text).
# 2. Liệt kê và quản lý các tài liệu đã thêm.
# 3. Cung cấp các công cụ AI (Tóm tắt, Tạo Quiz).
# 4. Cho phép cấu hình và thực hiện các hành động nguy hiểm (xóa khóa học).
# File này được thiết kế để tách biệt logic giao diện khỏi logic nghiệp vụ (core/services.py).

import streamlit as st
import time
import os
import uuid
from core.services import service_manager, slugify, calculate_file_hash
from config import USER_DATA_PATH, AVAILABLE_MODELS, MAX_FILE_SIZE_MB

# --- CÁC HÀM TIỆN ÍCH CỤC BỘ ---

MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

def display_sidebar():
    """
    Hàm chính để vẽ toàn bộ nội dung của sidebar.
    Sử dụng session_state để quản lý trạng thái giao diện, ví dụ như
    khóa các nút bấm khi một hành động nặng đang được xử lý.
    """
    with st.sidebar:
        # Khởi tạo cờ khóa (lock) để ngăn người dùng thực hiện nhiều hành động cùng lúc.
        if 'processing_lock' not in st.session_state:
            st.session_state.processing_lock = False
        
        # --- Phần Logo và Tiêu đề ---
        st.markdown("""<div class="logo-box"><span class="logo-text">P</span></div>""", unsafe_allow_html=True)
        st.title("PNote Workspace")
        st.caption(f"Khóa học: **{st.session_state.get('current_course_name', 'N/A')}**")
        st.markdown("---")

        # --- Giao diện Tabs để phân chia chức năng ---
        manage_tab, toolkit_tab, config_tab = st.tabs(["🗂️ Quản Lý", "🛠️ AI Toolkit", "⚙️ Cấu Hình"])

        # --- Tab 1: Quản lý Tài liệu ---
        with manage_tab:
            handle_document_management()

        # --- Tab 2: Các công cụ AI ---
        with toolkit_tab:
            handle_ai_toolkit()
        
        # --- Tab 3: Cấu hình và Tùy chọn Nâng cao ---
        with config_tab:
            handle_configuration()

        # --- Nút điều hướng chung ---
        st.markdown("<hr style='margin: 1rem 0;'>", unsafe_allow_html=True)
        if st.button("⬅️ Trở về Dashboard", use_container_width=True):
            st.switch_page("app.py")

    # --- Xử lý các hành động được kích hoạt từ giao diện ---
    # Ghi chú: Logic xử lý các hành động (như upload, xóa) được đặt bên ngoài
    # khối `with st.sidebar` để giữ cho code giao diện sạch sẽ và dễ đọc.
    if st.session_state.get('start_processing_sources'):
        process_all_sources(st.session_state.pop('sources_to_process'))
        st.session_state.processing_lock = False
        st.rerun()
    if st.session_state.get('doc_to_delete'):
        confirm_delete_document(st.session_state.pop('doc_to_delete'))
    if st.session_state.get('course_to_delete'):
        confirm_delete_course(st.session_state.pop('course_to_delete'))


def handle_document_management():
    """Vẽ các thành phần giao diện cho việc quản lý tài liệu."""
    with st.expander("➕ Thêm tài liệu mới"):
        # Vô hiệu hóa các ô nhập liệu khi đang xử lý để đảm bảo an toàn.
        disabled = st.session_state.processing_lock
        
        uploaded_files = st.file_uploader("1. Tải file (PDF, DOCX)", type=["pdf", "docx"], accept_multiple_files=True, disabled=disabled)
        url_input = st.text_input("2. Nhập URL (bài báo, YouTube)", placeholder="https://...", disabled=disabled)
        pasted_text = st.text_area("3. Dán văn bản vào đây", placeholder="Dán nội dung từ clipboard...", disabled=disabled)
        
        # Nút "Xử lý" sẽ kích hoạt luồng xử lý dữ liệu.
        if st.button("Xử lý và Thêm", use_container_width=True, type="secondary", disabled=disabled):
            sources = []
            if uploaded_files: sources.extend([("file", f) for f in uploaded_files])
            if url_input: sources.append(("url", url_input))
            if pasted_text: sources.append(("text", pasted_text))
            
            if not sources:
                st.warning("Vui lòng cung cấp ít nhất một nguồn tài liệu.")
            else:
                # Đặt cờ để bắt đầu xử lý và lưu trữ nguồn dữ liệu
                st.session_state.processing_lock = True
                st.session_state.sources_to_process = sources
                st.rerun()

    st.subheader("Tài liệu đã thêm")
    docs = service_manager.list_documents_in_course(st.session_state.current_course_id)
    if not docs:
        st.info("Chưa có tài liệu nào trong khóa học này.")
    else:
        # Hiển thị danh sách tài liệu và nút xóa cho từng tài liệu.
        for doc in docs:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"<div class='doc-item' title='{doc['name']}'>{doc['name']}</div>", unsafe_allow_html=True)
            with col2:
                if st.button("🗑️", key=f"del_doc_{doc['hash']}", help="Xóa tài liệu này", disabled=st.session_state.processing_lock):
                    st.session_state.doc_to_delete = doc
                    st.rerun()

def handle_ai_toolkit():
    """Vẽ các thành phần giao diện cho các công cụ AI."""
    course_id = st.session_state.current_course_id
    model_name_display = st.session_state.get(f"model_{course_id}", list(AVAILABLE_MODELS.keys())[0])
    model_name_value = AVAILABLE_MODELS[model_name_display]
    disabled = st.session_state.processing_lock

    with st.expander("📄 Tóm tắt Khóa học"):
        if st.button("Tạo Tóm Tắt", use_container_width=True, key="summarize_btn", disabled=disabled):
            with st.spinner("AI đang đọc và tóm tắt toàn bộ tài liệu..."):
                st.session_state[f"summary_{course_id}"] = service_manager.summarize_course(course_id, model_name_value)
        if f"summary_{course_id}" in st.session_state:
            st.text_area("Bản tóm tắt:", value=st.session_state[f"summary_{course_id}"], height=250, disabled=True)

    with st.expander("❓ Tạo Câu Hỏi Ôn Tập"):
        num_questions = st.slider("Số lượng câu hỏi:", 3, 10, 5, key="quiz_slider", disabled=disabled)
        if st.button("Bắt đầu Tạo Quiz", use_container_width=True, key="quiz_btn", disabled=disabled):
             with st.spinner("AI đang soạn câu hỏi cho bạn..."):
                st.session_state[f"quiz_{course_id}"] = service_manager.generate_quiz(course_id, model_name_value, num_questions)
        if f"quiz_{course_id}" in st.session_state:
            result = st.session_state[f"quiz_{course_id}"]
            if isinstance(result, list):
                # Hiển thị quiz ngay trong sidebar
                for i, q in enumerate(result):
                    st.write(f"**Câu {i+1}:** {q.get('question', 'N/A')}")
                    # ... (logic hiển thị radio và đáp án) ...
            else:
                st.error(str(result))


def handle_configuration():
    """Vẽ các thành phần giao diện cho cấu hình và các hành động nguy hiểm."""
    st.subheader("Tùy chỉnh AI")
    course_id = st.session_state.current_course_id
    model_key = f"model_{course_id}"
    current_model_display = st.session_state.get(model_key, list(AVAILABLE_MODELS.keys())[0])
    st.session_state[model_key] = st.selectbox(
        "Chọn mô hình AI:", options=AVAILABLE_MODELS.keys(),
        index=list(AVAILABLE_MODELS.keys()).index(current_model_display),
        disabled=st.session_state.processing_lock
    )
    
    with st.expander("⚠️ Tùy chọn Nâng cao"):
        st.warning("Hành động này không thể hoàn tác!")
        if st.button("Xóa Khóa Học Này", use_container_width=True, type="primary", disabled=st.session_state.processing_lock):
            st.session_state.course_to_delete = course_id
            st.rerun()

def process_all_sources(sources):
    """
    Hàm xử lý một danh sách các nguồn tài liệu (file, url, text).
    Đây là một hàm nặng, sẽ hiển thị thanh tiến trình.
    """
    course_id = st.session_state.current_course_id
    course_data_path = os.path.join(USER_DATA_PATH, course_id)
    total_sources = len(sources)
    success_count = 0
    progress_bar = st.progress(0, f"Bắt đầu xử lý {total_sources} nguồn...")

    for i, (source_type, data) in enumerate(sources):
        progress_text = "Đang xử lý..."
        source_name_for_hash = ""
        content_bytes = b""
        
        # --- Bước 1: Chuẩn bị dữ liệu và tính hash ---
        if source_type == "file":
            progress_text = f"Xử lý file: {data.name}"
            if data.size > MAX_FILE_SIZE_BYTES:
                st.warning(f"Bỏ qua '{data.name}': kích thước (> {MAX_FILE_SIZE_MB}MB) quá lớn.")
                continue
            content_bytes = data.getvalue()
        elif source_type == "url":
            progress_text = f"Xử lý URL: {data[:50]}..."
            content_bytes = data.encode('utf-8')
        elif source_type == "text":
            progress_text = f"Xử lý văn bản dán vào..."
            content_bytes = data.encode('utf-8')
        
        progress_bar.progress((i + 1) / total_sources, progress_text)
        file_hash = calculate_file_hash(content_bytes)
        
        # --- Bước 2: Kiểm tra trùng lặp ---
        if service_manager.check_if_hash_exists(course_id, file_hash):
            st.toast(f"Bỏ qua: Nguồn này đã tồn tại.", icon="♻️")
            continue

        # --- Bước 3: Trích xuất văn bản ---
        # Đối với file, cần đưa con trỏ về đầu trước khi đọc lại
        if source_type == "file": data.seek(0)
        
        # Xác định đúng loại để truyền vào service
        doc_type_for_extraction = data.name.split('.')[-1] if source_type == "file" else source_type
        text, original_name, _ = service_manager.extract_text_from_source(doc_type_for_extraction, data)

        if not text:
            st.error(f"Lỗi: Không thể trích xuất văn bản từ '{original_name}'.", icon="⚠️")
            continue

        # --- Bước 4: Lưu trữ (nếu là file) và thêm vào DB ---
        final_source_name = original_name
        if source_type == "file":
            unique_id = uuid.uuid4().hex[:6]
            final_source_name = f"{slugify(os.path.splitext(original_name)[0])}_{unique_id}{os.path.splitext(original_name)[1]}"
            with open(os.path.join(course_data_path, final_source_name), "wb") as f:
                f.write(content_bytes)
        
        service_manager.add_document_to_course(course_id, text, final_source_name, file_hash)
        success_count += 1

    progress_bar.empty()
    if success_count > 0:
        st.success(f"Hoàn tất! Đã thêm thành công {success_count}/{total_sources} nguồn tài liệu mới.")
    else:
        st.info("Không có tài liệu mới nào được thêm.")
    time.sleep(2)


def confirm_delete_document(doc_to_delete):
    """Hiển thị dialog xác nhận trước khi xóa một tài liệu."""
    @st.dialog("Xác nhận xóa tài liệu")
    def do_delete():
        st.write(f"Bạn có chắc chắn muốn xóa vĩnh viễn tài liệu **'{doc_to_delete['name']}'** không? Hành động này không thể hoàn tác.")
        col1, col2 = st.columns(2)
        if col1.button("Hủy bỏ", use_container_width=True): st.rerun()
        if col2.button("Xóa ngay", type="primary", use_container_width=True):
            try:
                service_manager.delete_document_from_course(st.session_state.current_course_id, doc_to_delete['hash'])
                st.toast("Đã xóa tài liệu!", icon="✅"); time.sleep(1); st.rerun()
            except Exception as e: st.error(f"Lỗi khi xóa: {e}")
    do_delete()


def confirm_delete_course(course_id):
    """Hiển thị dialog xác nhận trước khi xóa toàn bộ khóa học."""
    @st.dialog("Xác nhận xóa TOÀN BỘ khóa học")
    def do_delete():
        st.write(f"Bạn có chắc chắn muốn xóa vĩnh viễn khóa học này và tất cả tài liệu bên trong không? Hành động này không thể hoàn tác.")
        col1, col2 = st.columns(2)
        if col1.button("Hủy bỏ", use_container_width=True): st.rerun()
        if col2.button("Tôi hiểu, Xóa Ngay", type="primary", use_container_width=True):
            try:
                service_manager.delete_course(course_id)
                st.session_state.clear(); st.success("Đã xóa khóa học thành công!"); time.sleep(1); st.switch_page("app.py")
            except Exception as e: st.error(f"Lỗi khi xóa: {e}")
    do_delete()
