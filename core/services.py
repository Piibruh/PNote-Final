# pages/workspace.py

# Ghi chú: Đây là file định nghĩa không gian làm việc chính của ứng dụng.
# Nó chịu trách nhiệm hiển thị giao diện Chat và Ghi chú, đồng thời quản lý
# luồng tương tác của người dùng với AI cho một khóa học cụ thể đã được chọn.

import streamlit as st
from ui.sidebar import display_sidebar
from ui.utils import page_setup
from core.services import service_manager
from config import AVAILABLE_MODELS, DEFAULT_SYSTEM_PROMPT

# --- BƯỚC 1: THIẾT LẬP TRANG VÀ KIỂM TRA ĐIỀU KIỆN TIÊN QUYẾT ---

# Ghi chú: Gọi hàm tiện ích để cấu hình trang (tiêu đề, icon) và các thành phần
# UI toàn cục (CSS, theme, nút trợ giúp, popup onboarding).
page_setup(page_title="PNote Workspace", page_icon="🧠")

# Ghi chú: Đây là một "Guard Clause" cực kỳ quan trọng. Nó đảm bảo người dùng
# không thể truy cập trang này bằng cách nhập URL trực tiếp mà chưa chọn khóa học.
# Nếu không có bước này, ứng dụng sẽ bị lỗi KeyError ở các bước sau.
if 'current_course_id' not in st.session_state or not st.session_state.current_course_id:
    st.warning("Vui lòng chọn một khóa học từ Dashboard để bắt đầu.")
    if st.button("Trở về Dashboard"):
        st.switch_page("app.py")
    st.stop() # Dừng hoàn toàn việc thực thi của trang nếu không hợp lệ.

# --- BƯỚC 2: HIỂN THỊ CÁC THÀNH PHẦN GIAO DIỆN CHÍNH ---

# Ghi chú: Giao diện của sidebar được tách ra một file riêng (ui/sidebar.py)
# để mã nguồn của trang workspace được gọn gàng, dễ đọc.
display_sidebar()

# Ghi chú: Lấy các thông tin định danh của khóa học hiện tại từ session_state.
# Các biến này sẽ được sử dụng xuyên suốt trang.
course_id = st.session_state.current_course_id
course_name = st.session_state.current_course_name

# --- BƯỚC 3: KHỞI TẠO VÀ QUẢN LÝ STATE DÀNH RIÊNG CHO WORKSPACE ---

# Ghi chú: Để mỗi khóa học có lịch sử chat, ghi chú, và cấu hình riêng,
# chúng ta tạo ra các key động trong session_state bằng cách dùng f-string.
msg_key = f"messages_{course_id}"
note_key = f"notes_{course_id}"
model_key = f"model_{course_id}"

# Ghi chú: Khởi tạo các state với giá trị mặc định NẾU chúng chưa tồn tại.
# Điều này chỉ xảy ra lần đầu tiên người dùng vào workspace của một khóa học.
if msg_key not in st.session_state:
    st.session_state[msg_key] = [{"role": "assistant", "content": f"Xin chào! Bắt đầu cuộc trò chuyện về **{course_name}**."}]
if note_key not in st.session_state:
    st.session_state[note_key] = f"# Ghi chú cho {course_name}\n\n"
if model_key not in st.session_state:
    # Lấy model đầu tiên trong danh sách làm mặc định
    st.session_state[model_key] = list(AVAILABLE_MODELS.keys())[0]

# --- BƯỚC 4: DỰNG BỐ CỤC VÀ XỬ LÝ LOGIC TƯƠNG TÁC ---

# Ghi chú: Sử dụng st.columns để chia giao diện chính thành hai phần.
# Tỷ lệ [3, 2] giúp khu vực chat rộng hơn một chút so với khu vực ghi chú.
chat_col, note_col = st.columns([3, 2])

# --- KHU VỰC CHAT ---
with chat_col:
    st.header("💬 Thảo Luận Với AI", anchor=False, divider="gray")
    
    # Nút xóa lịch sử trò chuyện.
    # Nó sẽ bị vô hiệu hóa nếu có một tác vụ nặng đang chạy (processing_lock).
    if st.button("🗑️ Xóa cuộc trò chuyện", disabled=st.session_state.get('processing_lock', False)):
        st.session_state[msg_key] = [{"role": "assistant", "content": f"Cuộc trò chuyện đã được làm mới."}]
        st.rerun() # Tải lại trang để cập nhật giao diện ngay lập tức.

    # Khung chứa nội dung chat, có chiều cao cố định để tạo thanh cuộn.
    chat_container = st.container(height=600, border=False)
    # Hiển thị tất cả các tin nhắn đã có trong lịch sử.
    for message in st.session_state[msg_key]:
        with chat_container.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Ô nhập liệu chat của người dùng.
    if prompt := st.chat_input(f"Hỏi PNote về {course_name}...", disabled=st.session_state.get('processing_lock', False)):
        # 1. Thêm tin nhắn của người dùng vào state.
        st.session_state[msg_key].append({"role": "user", "content": prompt})
        # 2. Chạy lại trang ngay lập tức để hiển thị tin nhắn vừa gửi.
        st.rerun()

# Ghi chú: Logic gọi AI được đặt bên ngoài khối `with chat_col` và sau khi
# toàn bộ giao diện đã được vẽ. Nó chỉ thực thi khi tin nhắn cuối cùng là của người dùng.
# Đây là "Vòng Lặp Sự Kiện Chat" đã được tối ưu.
if st.session_state[msg_key][-1]["role"] == "user":
    # 3. Sau khi rerun, tin nhắn người dùng đã hiển thị, giờ mới gọi AI.
    with chat_container: # Vẽ vào lại container đã định nghĩa ở trên
        with st.chat_message("assistant"):
            model_name_value = AVAILABLE_MODELS[st.session_state[model_key]]
            # 4. Gọi service để lấy câu trả lời dưới dạng stream.
            response_stream = service_manager.get_chat_answer_stream(
                course_id, st.session_state[msg_key][-1]["content"], model_name_value, DEFAULT_SYSTEM_PROMPT
            )
            # 5. Hiển thị stream và lấy về câu trả lời đầy đủ.
            full_response = st.write_stream(response_stream)
            
    # 6. Thêm câu trả lời đầy đủ của bot vào state.
    st.session_state[msg_key].append({"role": "assistant", "content": full_response})
    # 7. Rerun lần cuối để hoàn tất vòng lặp và sẵn sàng cho prompt tiếp theo.
    st.rerun()

# --- KHU VỰC GHI CHÚ ---
with note_col:
    st.header("🗒️ Ghi Chú Cá Nhân", anchor=False, divider="gray")
    
    # Nút tải xuống nội dung ghi chú dưới dạng file Markdown.
    st.download_button(
        label="📥 Tải Ghi Chú (.md)", 
        data=st.session_state.get(note_key, ""),
        file_name=f"notes_{slugify(course_name)}.md", 
        mime="text/markdown", 
        use_container_width=True
    )
    
    # Ô văn bản lớn để người dùng ghi chú.
    note_content = st.text_area(
        "Ghi chú", 
        value=st.session_state[note_key], 
        height=600, 
        label_visibility="collapsed"
    )
    
    # Ghi chú: Logic tự động lưu. So sánh nội dung hiện tại của ô text_area
    # với nội dung đã lưu trong state. Nếu khác nhau, tức là người dùng
    # đã chỉnh sửa, thì cập nhật lại state.
    if note_content != st.session_state[note_key]:
        st.session_state[note_key] = note_content
        st.toast("Đã lưu ghi chú!", icon="✅")
