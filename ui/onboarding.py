# pnote-ai-app/ui/onboarding.py

import streamlit as st

ONBOARDING_HTML="""
<div class="onboarding-container">
    <div class="onboarding-header">
        <h2>Chào mừng bạn đến với PNote AI! 🚀</h2>
        <p>Đây là trợ lý học tập cá nhân của bạn. Hãy xem qua 3 bước để bắt đầu nhé.</p>
    </div>
    <div class="onboarding-steps">
        <div class="step">
            <div class="step-icon">1️⃣</div>
            <div class="step-text">
                <h3>Tạo Không gian làm việc</h3>
                <p>Mỗi không gian làm việc là nơi riêng cho một môn học. Hãy bắt đầu bằng cách <strong>tạo một không gian mới</strong> ở thanh sidebar.</p>
            </div>
        </div>
        <div class="step">
            <div class="step-icon">2️⃣</div>
            <div class="step-text">
                <h3>Thêm Tài liệu</h3>
                <p>Sau khi vào Workspace, hãy đến tab <strong>"📚 Tài liệu"</strong> để "dạy" cho AI. Bạn có thể tải lên file hoặc dán link web, YouTube.</p>
            </div>
        </div>
        <div class="step">
            <div class="step-icon">3️⃣</div>
            <div class="step-text">
                <h3>Khám phá & Học tập</h3>
                <p>Giờ đây, bạn có thể <strong>trò chuyện, tóm tắt, phân tích,</strong> hoặc tạo <strong>bộ câu hỏi ôn tập</strong>. Tất cả đều nằm trong các tab của Workspace!</p>
            </div>
        </div>
    </div>
    <div class="onboarding-footer">
        <p>Sẵn sàng chưa? Hãy đóng cửa sổ này và khám phá nhé!</p>
    </div>
</div>
"""

def _show_dialog():
    """Hàm nội bộ để hiển thị st.dialog bằng cú pháp context manager đúng."""
    
    # Sử dụng 'with' thay vì '@'
    with st.dialog("Hướng dẫn cho người mới bắt đầu", on_dismiss=lambda: st.session_state.update(onboarding_complete=True)):
        st.markdown(ONBOARDING_HTML, unsafe_allow_html=True)
        # Khi nhấn nút này, state sẽ được set và rerun để đóng dialog
        if st.button("Tôi đã hiểu!", use_container_width=True, type="secondary"):
            st.session_state.onboarding_complete = True
            st.rerun()

def display_onboarding_features():
    """Hàm chính để quản lý và hiển thị các tính năng onboarding."""
    
    # Tự động hiển thị dialog cho người dùng mới
    if not st.session_state.get("onboarding_complete"):
        _show_dialog()
    
    # Hiển thị nút trợ giúp nổi
    st.markdown("""
        <div class="help-button-container">
            <button class="help-button" onclick="document.getElementById('show-onboarding-button').click();">?</button>
        </div>
    """, unsafe_allow_html=True)
    
    # Nút ẩn để kích hoạt lại dialog từ nút trợ giúp
    if st.button("Show Onboarding", key="show-onboarding-button"):
        _show_dialog()
