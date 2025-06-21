# pnote-ai-app/ui/sidebar.py
import streamlit as st
def display():
    with st.sidebar:
        st.header("PNote AI", divider="orange")
        courses = st.session_state.courses
        if courses:
            names, ids = [c['name'] for c in courses], [c['id'] for c in courses]
            try: s_idx = ids.index(st.session_state.cid) if st.session_state.cid in ids else 0
            except ValueError: s_idx = 0
            s_name = st.radio("Không gian làm việc", names, index=s_idx, label_visibility="collapsed")
            st.session_state.cid = ids[names.index(s_name)]
        else: st.info("Tạo không gian làm việc mới.")

        with st.expander("➕ Quản lý", expanded=not courses):
            with st.form("create", clear_on_submit=True):
                name = st.text_input("Tên không gian mới", placeholder="Vd: Kinh tế vĩ mô")
                if st.form_submit_button("Tạo mới", use_container_width=True, type="secondary"):
                    cid, e = st.session_state.sm.create_course(name)
                    if e: st.error(e)
                    else: st.session_state.cid = cid; st.rerun()
            if courses:
                to_del = st.selectbox("Chọn để xóa", [""]+[c['name'] for c in courses])
                if to_del and st.button("❌ Xóa vĩnh viễn", type="primary", use_container_width=True):
                    cid_del = [c['id'] for c in courses if c['name']==to_del][0]
                    st.session_state.sm.delete_course(cid_del)
                    if st.session_state.cid == cid_del: st.session_state.cid = None
                    st.rerun()
        st.divider()
        
        current_theme = st.session_state.get("theme", "Dark")
        icon, help_text = ("☀️","Sáng") if current_theme=="Dark" else ("🌙","Tối")
        st.button(f"{icon} Giao diện {help_text}", on_click=lambda: st.session_state.update(theme="Light" if st.session_state.theme == "Dark" else "Dark"), use_container_width=True)
