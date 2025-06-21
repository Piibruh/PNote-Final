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
    """
    Hàm nội bộ để hiển thị st.dialog.
    Sửa lỗi bằng cách loại bỏ tham số on_dismiss và xử lý việc đóng dialog.
    """
    
    # st.dialog trả về True nếu đang mở, False nếu đã đóng.
    # Chúng ta lưu trạng thái này vào một biến.
    dialog_is_open = st.dialog("Hướng dẫn cho người mới bắt đầu")

    if dialog_is_open:
        # Nếu dialog đang mở, hiển thị nội dung bên trong
        st.markdown(ONBOARDING_HTML, unsafe_allow_html=True)
        if st.button("Tôi đã hiểu!", use_container_width=True, type="secondary"):
            st.session_state.onboarding_complete = True
            st.rerun() # Chạy lại để đóng dialog và cập nhật app
    else:
        # Nếu dialog đã bị người dùng đóng (nhấn 'X' hoặc Esc)
        # Chúng ta cũng cần cập nhật state và rerun để đảm bảo nó không hiện lại
        st.session_state.onboarding_complete = True
        st.rerun()


def display_onboarding_features():
    """Hàm chính để quản lý và hiển thị các tính năng onboarding."""
    
    # Tạo một key riêng để quyết định có nên mở dialog hay không
    # Điều này giúp tránh việc rerun vô hạn
    if 'show_dialog_flag' not in st.session_state:
        # Lần đầu tiên chạy, nếu chưa hoàn thành onboarding thì set flag
        st.session_state.show_dialog_flag = not st.session_state.get("onboarding_complete", False)

    # Nếu nút '?' được nhấn, set flag để mở dialog
    if st.button("Show Onboarding", key="show-onboarding-button"):
        st.session_state.show_dialog_flag = True

    # Chỉ gọi _show_dialog nếu flag được bật
    if st.session_state.get("show_dialog_flag", False):
        _show_dialog()

    # Hiển thị nút trợ giúp nổi
    st.markdown("""
        <div class="help-button-container">
            <button class="help-button" onclick="document.getElementById('show-onboarding-button').click();">?</button>
        </div>
    """, unsafe_allow_html=True)
