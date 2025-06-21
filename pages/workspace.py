# pnote-ai-app/pages/workspace.py
import streamlit as st
from ui import utils, sidebar, onboarding
from core.services import service_manager, slugify, calculate_file_hash

utils.page_init("Workspace")
sidebar.display()
onboarding.display_onboarding_features()

cid = st.session_state.get("cid")
if not cid:
    st.error("Chưa có không gian làm việc nào được chọn."); st.page_link("app.py", label="Quay về trang chủ", icon="🏠"); st.stop()

name = next((c['name'] for c in st.session_state.courses if c['id'] == cid), "...")
st.header(f"Workspace: {name}", divider="orange")

tab_chat, tab_docs, tab_summary, tab_analysis, tab_learning = st.tabs(["💬 Trò chuyện", "📚 Tài liệu", "✨ Tóm tắt", "📊 Phân tích", "🧠 Học tập"])

with tab_chat:
    if cid not in st.session_state.history: st.session_state.history[cid] = []
    for msg in st.session_state.history[cid]:
        with st.chat_message(msg["role"]): st.markdown(msg["parts"][0])
    if prompt := st.chat_input("Hỏi điều gì đó..."):
        st.session_state.history[cid].append({"role":"user","parts":[prompt]}); st.chat_message("user").markdown(prompt)
        with st.chat_message("assistant"):
            stream = st.session_state.sm.get_chat_stream(cid, prompt, st.session_state.history[cid][:-1])
            response = st.write_stream(stream)
        st.session_state.history[cid].append({"role":"model","parts":[response]})

with tab_docs:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("➕ Thêm tài liệu mới")
        with st.form("add_doc", clear_on_submit=True):
            stype = st.radio("Loại:", ["File", "Web", "YouTube"], horizontal=True, label_visibility="collapsed")
            if stype == "File": files = st.file_uploader("PDF, DOCX", ["pdf","docx"], True, label_visibility="collapsed")
            else: url = st.text_input("URL", label_visibility="collapsed")
            if st.form_submit_button("Thêm vào Workspace", type="secondary", use_container_width=True):
                srcs = files if stype == "File" and files else ([url] if stype != "File" and url else [])
                if not srcs: st.warning("Vui lòng cung cấp nguồn.")
                else:
                    stype_map = {"File": lambda f: 'pdf' if f.type=="application/pdf" else 'docx', "Web": "url", "YouTube": "youtube"}
                    prog = st.progress(0); i=0
                    for sdata in srcs:
                        i+=1; name=getattr(sdata,'name',sdata); prog.progress(i/len(srcs), f"Xử lý: {name}")
                        stype_key = stype_map[stype](sdata) if stype=="File" else stype_map[stype]
                        fhash = calculate_file_hash(sdata.getvalue()) if hasattr(sdata,'getvalue') else slugify(sdata)
                        if st.session_state.sm.hash_exists(cid,fhash): st.toast(f"Đã tồn tại.",icon="⚠️"); continue
                        text, _ = st.session_state.sm.extract_text_from_source(stype_key, sdata)
                        if text: st.session_state.sm.add_doc(cid,text,name,fhash); st.toast(f"Đã thêm '{name}'.", icon="✅")
                        else: st.toast(f"Lỗi trích xuất '{name}'.", icon="❌")
                    prog.empty(); st.rerun()
    with c2:
        st.subheader("📖 Tài liệu hiện có")
        docs = st.session_state.sm.list_docs(cid)
        if not docs: st.info("Không gian này chưa có tài liệu.")
        else:
            for doc in docs:
                c1,c2 = st.columns([0.9,0.1]); c1.markdown(f"📄 `{doc['name']}`")
                if c2.button("🗑️", key=f"d_{doc['hash']}", help="Xóa"): st.session_state.sm.delete_doc(cid,doc['hash']); st.rerun()

with tab_summary:
    st.subheader("Tóm tắt & Phân tích tổng quan")
    if st.button("✨ Tạo tóm tắt ngay", use_container_width=True, type="secondary"):
        with st.spinner("AI đang phân tích..."): summary = st.session_state.sm.summarize(cid)
        st.markdown(summary)

with tab_analysis:
    st.subheader("Thông số & Các chủ đề chính")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Thống kê không gian")
        if stats := st.session_state.sm.get_course_statistics(cid):
            st.metric("Số tài liệu", stats.get("doc_count",0)); st.metric("Số chunk văn bản", f"{stats.get('chunk_count',0):,}"); st.metric("Tokens ước tính", f"{stats.get('token_est',0):,}")
        else: st.warning("Không thể tải thống kê.")
    with c2:
        st.markdown("#### Trích xuất từ khóa")
        if st.button("Phân tích từ khóa", use_container_width=True):
            with st.spinner("AI đang tìm từ khóa..."): keywords = st.session_state.sm.extract_keywords(cid)
            if isinstance(keywords, list): st.markdown("".join(f"<span style='background-color: var(--secondary-bg); border: 1px solid var(--border-color); border-radius: 8px; padding: 5px 10px; margin: 3px; display: inline-block;'>{kw}</span>" for kw in keywords), unsafe_allow_html=True)
            else: st.error(f"Lỗi: {keywords}")

with tab_learning:
    st.subheader("Công cụ học tập được hỗ trợ bởi AI")
    with st.expander("📝 **Tạo câu hỏi trắc nghiệm (Quiz)**", expanded=True):
        num_q = st.slider("Số câu hỏi:", 1, 10, 5, key="q_slider")
        if st.button("Tạo bộ Quiz", use_container_width=True, type="secondary"):
            with st.spinner("AI đang soạn đề..."): quiz = st.session_state.sm.generate_quiz(cid, num_q)
            st.session_state.quiz = quiz if isinstance(quiz, list) else st.error(f"Lỗi: {quiz}")
        if 'quiz' in st.session_state and isinstance(st.session_state.quiz, list):
            for i, q in enumerate(st.session_state.quiz):
                with st.container(border=True):
                    st.radio(f"**Câu {i+1}:** {q['question']}", q['options'], None, key=f"q_{i}")
                    if st.toggle("Đáp án", key=f"a_{i}"): st.success(f"**Đúng:** {q['answer']}")
    with st.expander("🤔 **Tạo câu hỏi học tập (Tự luận)**"):
        num_sq = st.slider("Số câu hỏi:", 1, 8, 3, key="sq_slider")
        if st.button("Tạo câu hỏi tự luận", use_container_width=True):
            with st.spinner("AI đang tạo câu hỏi..."): sq = st.session_state.sm.generate_study_questions(cid, num_sq)
            st.session_state.sq = sq if isinstance(sq, list) else st.error(f"Lỗi: {sq}")
        if 'sq' in st.session_state and isinstance(st.session_state.sq, list):
            st.success("Các câu hỏi gợi mở để bạn suy ngẫm:"); [st.markdown(f"**{i}.** {q}") for i, q in enumerate(st.session_state.sq, 1)]
