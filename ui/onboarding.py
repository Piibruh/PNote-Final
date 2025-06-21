# pnote-ai-app/ui/onboarding.py
import streamlit as st

# --- BẢNG CHỨC NĂNG (THEO GỢI Ý CỦA BẠN) ---
def display_welcome_and_capabilities():
    """Hiển thị một bảng chào mừng và các chức năng chính của PNote AI."""
    st.success("🎉 Chào mừng bạn đến với PNote AI! Dưới đây là những gì bạn có thể làm:")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        #### 💬 Tương tác & Hỏi đáp
        - **Trò chuyện với tài liệu:** Hỏi đáp trực tiếp với nội dung bạn tải lên.
        - **Hỗ trợ đa định dạng:** Tải lên file PDF, DOCX hoặc dán link web, YouTube.
        - **Lịch sử trò chuyện:** Lưu lại toàn bộ cuộc hội thoại cho từng không gian làm việc.
        """)
    with col2:
        st.markdown("""
        #### 🧠 Phân tích & Học tập
        - **Tóm tắt thông minh:** Yêu cầu AI tóm tắt toàn bộ tài liệu chỉ bằng một cú nhấp chuột.
        - **Trích xuất từ khóa:** Tự động tìm ra các chủ đề chính.
        - **Tạo bộ câu hỏi:** Sinh ra các câu hỏi trắc nghiệm và tự luận để bạn ôn tập.
        """)
        
    st.info("💡 **Mẹo:** Bạn có thể bắt đầu **Tour Hướng dẫn Tương tác** bất cứ lúc nào bằng cách nhấn vào nút **?** ở góc dưới bên phải màn hình.")


# --- TOUR HƯỚNG DẪN TƯƠNG TÁC ---
def run_interactive_tour(page: str):
    """Chạy một tour hướng dẫn dựa trên trang hiện tại ('home' hoặc 'workspace')."""
    
    tour_steps = []
    if page == "home":
        tour_steps = [
            st.TourStep(
                "section[data-testid='stSidebar']",
                "Chào mừng bạn! Đây là **Sidebar**, trung tâm điều khiển của bạn. Mọi thứ bắt đầu từ đây.",
            ),
            st.TourStep(
                '[data-testid="stExpander"]',
                "Để bắt đầu, hãy mở mục **'Quản lý'** và tạo một **Không gian làm việc** mới cho môn học hoặc dự án của bạn.",
                placement="right",
            ),
            st.TourStep(
                '[data-testid="stPageLink"]',
                "Sau khi tạo và chọn một không gian, hãy nhấn vào đây để đi đến **Workspace**, nơi điều kỳ diệu xảy ra!",
            ),
        ]
    elif page == "workspace":
        tour_steps = [
            st.TourStep(
                "[data-testid='stTabs']",
                "Chào mừng đến Workspace! Các chức năng chính được sắp xếp trong các **Tab** này.",
            ),
            st.TourStep(
                # Selector này nhắm đến tab thứ hai
                "[data-testid='stTabs'] .st-emotion-cache-110fgir:nth-of-type(2)",
                "Hãy bắt đầu bằng cách vào tab **'Tài liệu'** để 'dạy' cho AI bằng cách tải lên file hoặc dán link.",
            ),
            st.TourStep(
                # Selector này nhắm đến tab đầu tiên
                "[data-testid='stTabs'] .st-emotion-cache-110fgir:nth-of-type(1)",
                "Sau khi có tài liệu, bạn có thể quay lại tab **'Trò chuyện'** để hỏi đáp với AI.",
            ),
            st.TourStep(
                # Selector này nhắm đến tab cuối cùng
                "[data-testid='stTabs'] .st-emotion-cache-110fgir:nth-of-type(5)",
                "Đừng quên khám phá các công cụ học tập mạnh mẽ như tạo Quiz và câu hỏi tự luận ở tab **'Học tập AI'** nhé!",
            ),
        ]

    # Bắt đầu tour
    if tour_steps:
        st.tour(tour_steps)
        # Đánh dấu là đã hoàn thành để không tự động hiện lại
        st.session_state.onboarding_complete = True


def display_onboarding_features(page: str):
    """
    Hàm quản lý chính:
    1. Hiển thị nút trợ giúp nổi (?).
    2. Xử lý logic khi nút ? được nhấn để bắt đầu tour.
    """
    
    # Luôn hiển thị nút trợ giúp
    st.markdown("""
        <div class="help-button-container">
            <button class="help-button" onclick="document.getElementById('start-interactive-tour-button').click();">?</button>
        </div>
    """, unsafe_allow_html=True)

    # Nút ẩn, được kích hoạt bởi nút '?'
    if st.button("Start Tour", key="start-interactive-tour-button"):
        run_interactive_tour(page)
