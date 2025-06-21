# ui/onboarding.py
import streamlit as st

ONBOARDING_CONTENT_HTML = """
<div class="onboarding-container">
    <div class="onboarding-header">
        <h2>Chào mừng bạn đến với PNote AI! 🚀</h2>
        <p>Đây là trợ lý học tập cá nhân của bạn. Hãy dành một phút để xem qua các tính năng chính nhé.</p>
    </div>
    <div class="onboarding-steps">
        <div class="step">
            <div class="step-icon">1️⃣</div>
            <div class="step-text">
                <h3>Tạo một "Khóa học"</h3>
                <p>Mỗi khóa học là một không gian làm việc riêng biệt. Hãy bắt đầu bằng cách <strong>tạo một khóa học mới</strong> ở trang Dashboard (ví dụ: "Lịch sử Thế giới", "Hóa học Đại cương").</p>
            </div>
        </div>
        <div class="step">
            <div class="step-icon">2️⃣</div>
            <div class="step-text">
                <h3>"Dạy" cho AI</h3>
                <p>Sau khi vào Workspace, hãy dùng thanh bên trái (sidebar) để <strong>thêm tài liệu</strong> vào khóa học của bạn. Bạn có thể tải lên file PDF, DOCX hoặc dán link bài báo, video YouTube.</p>
            </div>
        </div>
        <div class="step">
            <div class="step-icon">3️⃣</div>
            <div class="step-text">
                <h3>Bắt đầu Hỏi & Đáp</h3>
                <p>Giờ đây, bạn có thể <strong>trò chuyện với AI</strong> về nội dung tài liệu bạn vừa thêm. AI sẽ chỉ trả lời dựa trên những gì bạn đã "dạy" nó. Đừng quên sử dụng các công cụ AI khác trong sidebar nhé!</p>
            </div>
        </div>
    </div>
    <div class="onboarding-footer">
        <p>Sẵn sàng để bắt đầu chưa? Hãy đóng cửa sổ này và khám phá nhé!</p>
    </div>
</div>
"""

def onboarding_popup():
    @st.dialog("Hướng dẫn cho người mới bắt đầu", on_dismiss=lambda: st.session_state.update(onboarding_complete=True))
    def show_guide():
        st.markdown(ONBOARDING_CONTENT_HTML, unsafe_allow_html=True)
        if st.button("Tôi đã hiểu, hãy bắt đầu!", use_container_width=True, type="secondary"):
            st.rerun()
    show_guide()

def help_button():
    st.markdown("""
        <style>
            .help-button-container { position: fixed; bottom: 20px; right: 20px; z-index: 9999; }
            .help-button {
                background-color: var(--primary-color); color: white; border: none; border-radius: 50%;
                width: 50px; height: 50px; font-size: 24px; font-weight: bold; cursor: pointer;
                box-shadow: 0 4px 12px rgba(0,0,0,0.4); transition: transform 0.2s ease;
            }
            .help-button:hover { transform: scale(1.1); }
        </style>
        <div class="help-button-container">
            <button class="help-button" onclick="document.getElementById('show-onboarding-button').click();">?</button>
        </div>
    """, unsafe_allow_html=True)
    if st.button("Show Onboarding", key="show-onboarding-button"):
        onboarding_popup()
