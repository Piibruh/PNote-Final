# pnote-ai-app/pages/workspace.py
import streamlit as st
from ui import utils, sidebar, onboarding
from core.services import service_manager, slugify, calculate_file_hash

# --- BƯỚC 1: KHỞI TẠO TRANG VÀ CÁC THÀNH PHẦN GIAO DIỆN CHUNG ---
utils.page_init("Workspace")
sidebar.display()

# Gọi hàm onboarding với tham số "workspace" để hiển thị nút '?' 
# và chạy đúng tour hướng dẫn khi được yêu cầu.
onboarding.display_onboarding_features("workspace") 

# --- BƯỚC 2: KIỂM TRA ĐIỀU KIỆN - ĐẢM BẢO ĐÃ CHỌN WORKSPACE ---
# Đây là một "Guard Clause" để ngăn lỗi nếu người dùng truy cập trực tiếp.
cid = st.session_state.get("cid")
if not cid:
    st.error("Chưa có không gian làm việc nào được chọn.")
    st.info("Vui lòng quay lại trang chủ và chọn một không gian làm việc từ sidebar.")
    st.page_link("app.py", label="Quay về Trang chủ", icon="🏠")
    st.stop()

# Lấy tên của không gian làm việc hiện tại để hiển thị
name = next((c['name'] for c in st.session_state.courses if c['id'] == cid), "Không xác định")
st.header(f"Workspace: {name}", divider="orange")

# --- BƯỚC 3: KHỞI TẠO CÁC TAB CHỨC NĂNG ---
tab_chat, tab_docs, tab_summary, tab_analysis, tab_learning = st.tabs([
    "💬 Trò chuyện (RAG)", 
    "📚 Quản lý Tài liệu", 
    "✨ Tóm tắt AI", 
    "📊 Phân tích & Insights", 
    "🧠 Học tập AI"
])


# --- TAB 1: TRÒ CHUYỆN (RAG) ---
with tab_chat:
    # Khởi tạo lịch sử chat cho không gian làm việc này nếu chưa có
    if cid not in st.session_state.history:
        st.session_state.history[cid] = []
    
    # Hiển thị các tin nhắn đã có
    for msg in st.session_state.history[cid]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["parts"][0])
    
    # Nhận input mới từ người dùng
    if prompt := st.chat_input("Hỏi điều gì đó về tài liệu của bạn..."):
        # Thêm và hiển thị tin nhắn của người dùng
        st.session_state.history[cid].append({"role":"user", "parts":[prompt]})
        st.chat_message("user").markdown(prompt)

        # Lấy và hiển thị phản hồi từ AI
        with st.chat_message("assistant"):
            with st.spinner("AI đang tìm kiếm câu trả lời..."):
                stream = st.session_state.sm.get_chat_stream(cid, prompt, st.session_state.history[cid][:-1])
                response = st.write_stream(stream)
        
        # Lưu lại phản hồi của AI vào lịch sử
        st.session_state.history[cid].append({"role":"model", "parts":[response]})


# --- TAB 2: QUẢN LÝ TÀI LIỆU ---
with tab_docs:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("➕ Thêm tài liệu mới")
        with st.form("add_doc", clear_on_submit=True):
            source_type = st.radio("Loại nguồn:", ["File", "Web", "YouTube"], horizontal=True, label_visibility="collapsed")
            if source_type == "File":
                files = st.file_uploader("Chọn file PDF, DOCX", type=["pdf", "docx"], accept_multiple_files=True, label_visibility="collapsed")
            else:
                url = st.text_input("Dán đường dẫn URL", label_visibility="collapsed")
            
            submitted = st.form_submit_button("Thêm vào Workspace", type="secondary", use_container_width=True)

        if submitted:
            sources = files if source_type == "File" and files else ([url] if source_type != "File" and url else [])
            if not sources:
                st.warning("Vui lòng cung cấp nguồn tài liệu.")
            else:
                stype_map = {"File": lambda f: 'pdf' if f.type=="application/pdf" else 'docx', "Web": "url", "YouTube": "youtube"}
                progress_bar = st.progress(0, "Bắt đầu...")
                for i, sdata in enumerate(sources):
                    name = getattr(sdata, 'name', sdata)
                    progress_bar.progress((i + 1) / len(sources), f"Xử lý: {name}")
                    
                    stype_key = stype_map[source_type](sdata) if source_type=="File" else stype_map[source_type]
                    file_hash = calculate_file_hash(sdata.getvalue()) if hasattr(sdata, 'getvalue') else slugify(sdata)
                    
                    if st.session_state.sm.hash_exists(cid, file_hash):
                        st.toast(f"Bỏ qua: '{name}' đã tồn tại.", icon="⚠️")
                        continue
                        
                    text, _ = st.session_state.sm.extract_text_from_source(stype_key, sdata)
                    if text:
                        st.session_state.sm.add_doc(cid, text, name, file_hash)
                        st.toast(f"Đã thêm '{name}'.", icon="✅")
                    else:
                        st.toast(f"Lỗi trích xuất '{name}'.", icon="❌")
                progress_bar.empty()
                st.rerun()

    with col2:
        st.subheader("📖 Tài liệu hiện có")
        docs = st.session_state.sm.list_docs(cid)
        if not docs:
            st.info("Không gian này chưa có tài liệu nào. Hãy thêm một vài tài liệu để bắt đầu!")
        else:
            for doc in docs:
                c1, c2 = st.columns([0.9, 0.1])
                c1.markdown(f"📄 `{doc['name']}`")
                if c2.button("🗑️", key=f"del_{doc['hash']}", help="Xóa tài liệu này"):
                    st.session_state.sm.delete_doc(cid, doc['hash'])
                    st.rerun()


# --- TAB 3: TÓM TẮT AI ---
with tab_summary:
    st.subheader("Tóm tắt & Phân tích tổng quan")
    if st.button("✨ Tạo tóm tắt ngay", use_container_width=True, type="secondary"):
        with st.spinner("AI đang đọc và phân tích toàn bộ tài liệu..."):
            summary = st.session_state.sm.summarize(cid)
        st.markdown(summary)


# --- TAB 4: PHÂN TÍCH & INSIGHTS ---
with tab_analysis:
    st.subheader("Thông số & Các chủ đề chính")
    
    col_stats, col_keywords = st.columns(2)
    
    with col_stats:
        st.markdown("#### Thống kê không gian")
        stats = st.session_state.sm.get_course_statistics(cid)
        if stats:
            st.metric("Số lượng tài liệu", stats.get("doc_count", 0))
            st.metric("Số chunk văn bản trong DB", f"{stats.get('chunk_count', 0):,}")
            st.metric("Tổng số token ước tính", f"{stats.get('token_est', 0):,}")
        else:
            st.warning("Không thể tải thống kê.")
            
    with col_keywords:
        st.markdown("#### Trích xuất từ khóa")
        if st.button("Phân tích từ khóa", use_container_width=True):
            with st.spinner("AI đang tìm các từ khóa quan trọng..."):
                keywords = st.session_state.sm.extract_keywords(cid)
            
            if isinstance(keywords, list):
                tags_html = "".join(f"<span style='background-color: var(--secondary-bg); border: 1px solid var(--border-color); border-radius: 8px; padding: 5px 10px; margin: 3px; display: inline-block;'>{kw}</span>" for kw in keywords)
                st.markdown(tags_html, unsafe_allow_html=True)
            else:
                st.error(f"Không thể trích xuất từ khóa: {keywords}")


# --- TAB 5: HỌC TẬP AI ---
with tab_learning:
    st.subheader("Công cụ học tập được hỗ trợ bởi AI")
    
    with st.expander("📝 **Tạo câu hỏi trắc nghiệm (Quiz)**", expanded=True):
        num_quiz_q = st.slider("Số lượng câu hỏi trắc nghiệm:", 1, 10, 5, key="quiz_slider")
        if st.button("Tạo bộ Quiz", use_container_width=True, type="secondary"):
            with st.spinner("AI đang soạn đề thi trắc nghiệm..."):
                quiz_data = st.session_state.sm.generate_quiz(cid, num_quiz_q)
            
            if isinstance(quiz_data, list):
                st.session_state.quiz_data = quiz_data
            else:
                st.error(f"Lỗi tạo quiz: {quiz_data}")
                if 'quiz_data' in st.session_state: del st.session_state['quiz_data']
        
        if 'quiz_data' in st.session_state:
            st.divider()
            for i, q in enumerate(st.session_state.quiz_data):
                with st.container(border=True):
                    st.radio(f"**Câu {i+1}:** {q['question']}", q['options'], index=None, key=f"q_{i}")
                    if st.toggle("Hiển thị đáp án", key=f"ans_toggle_{i}"):
                        st.success(f"**Đáp án đúng:** {q['answer']}")
    
    with st.expander("🤔 **Tạo câu hỏi học tập (Tự luận)**"):
        num_study_q = st.slider("Số lượng câu hỏi tự luận:", 1, 8, 3, key="study_q_slider")
        if st.button("Tạo câu hỏi tự luận", use_container_width=True):
            with st.spinner("AI đang tạo các câu hỏi gợi mở..."):
                study_questions = st.session_state.sm.generate_study_questions(cid, num_study_q)
            
            if isinstance(study_questions, list):
                st.session_state.study_questions = study_questions
            else:
                st.error(f"Lỗi tạo câu hỏi: {study_questions}")
                if 'study_questions' in st.session_state: del st.session_state['study_questions']

        if 'study_questions' in st.session_state:
            st.success("Dưới đây là các câu hỏi giúp bạn suy ngẫm sâu hơn:")
            for i, q in enumerate(st.session_state.study_questions, 1):
                st.markdown(f"**{i}.** {q}")
