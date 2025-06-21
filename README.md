# PNote - AI-Powered Learning Assistant

PNote là một ứng dụng học tập thông minh được xây dựng bằng Streamlit và tích hợp AI để giúp bạn quản lý, phân tích và tương tác với tài liệu học tập một cách hiệu quả.

## 🌟 Tính năng chính

### 📚 Quản lý Khóa học
- Tạo và quản lý nhiều không gian làm việc (khóa học) riêng biệt
- Mỗi khóa học có thể chứa nhiều loại tài liệu khác nhau
- Giao diện trực quan và dễ sử dụng

### 📄 Hỗ trợ Đa dạng Tài liệu
- **File PDF**: Trích xuất văn bản từ tài liệu PDF
- **File DOCX**: Xử lý tài liệu Word
- **URL**: Tự động trích xuất nội dung từ bài báo, trang web
- **YouTube**: Lấy transcript từ video YouTube
- **Văn bản thô**: Dán trực tiếp nội dung từ clipboard

### 🤖 AI-Powered Features
- **Chat thông minh**: Hỏi đáp về nội dung tài liệu với AI
- **Tóm tắt tự động**: AI tạo bản tóm tắt toàn bộ khóa học
- **Tạo câu hỏi ôn tập**: Tự động sinh câu hỏi trắc nghiệm
- **Hỗ trợ đa mô hình**: Gemini Flash (nhanh) và Gemini Pro (mạnh)

### 🎨 Giao diện Hiện đại
- **Dark/Light Theme**: Chuyển đổi giao diện sáng/tối
- **Responsive Design**: Tương thích với nhiều thiết bị
- **Real-time Updates**: Cập nhật giao diện theo thời gian thực
- **Ghi chú cá nhân**: Tích hợp ghi chú với khả năng tải xuống

## 🚀 Cài đặt và Chạy

### Yêu cầu hệ thống
- Python 3.8+
- Git

### Bước 1: Clone repository
```bash
git clone https://github.com/Piibruh/PNote-Final.git
cd PNote-Final
```

### Bước 2: Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### Bước 3: Cấu hình API Key
Tạo file `.env` trong thư mục gốc và thêm API key của Google Gemini:
```
GEMINI_API_KEY=your_gemini_api_key_here
```

**Lưu ý**: Bạn cần đăng ký Google AI Studio để lấy API key: https://makersuite.google.com/app/apikey

### Bước 4: Chạy ứng dụng
```bash
streamlit run app.py
```

Ứng dụng sẽ chạy tại: http://localhost:8501

## 📖 Hướng dẫn sử dụng

### 1. Tạo khóa học mới
- Truy cập Dashboard
- Nhập tên khóa học và nhấn "Tạo Ngay"
- Hệ thống sẽ tạo một không gian làm việc riêng biệt

### 2. Thêm tài liệu
- Vào Workspace của khóa học
- Sử dụng sidebar bên trái để thêm tài liệu:
  - Tải file PDF/DOCX
  - Dán URL bài báo/YouTube
  - Dán văn bản trực tiếp

### 3. Tương tác với AI
- Chat với AI về nội dung tài liệu
- Sử dụng công cụ "Tóm tắt" để có cái nhìn tổng quan
- Tạo câu hỏi ôn tập với "AI Toolkit"

### 4. Ghi chú cá nhân
- Sử dụng khu vực ghi chú bên phải
- Tự động lưu khi chỉnh sửa
- Tải xuống dưới dạng file Markdown

## 🏗️ Kiến trúc hệ thống

```
PNote-Final/
├── app.py                 # Entry point chính
├── config.py             # Cấu hình hệ thống
├── requirements.txt      # Dependencies
├── styles.css           # CSS styling
├── core/
│   ├── __init__.py
│   └── services.py      # Business logic & AI integration
├── pages/
│   ├── __init__.py
│   └── workspace.py     # Workspace page
└── ui/
    ├── __init__.py
    ├── onboarding.py    # Onboarding UI
    ├── sidebar.py       # Sidebar components
    └── utils.py         # UI utilities
```

### Công nghệ sử dụng
- **Frontend**: Streamlit
- **AI**: Google Gemini API
- **Database**: ChromaDB (Vector Database)
- **Text Processing**: PyPDF, python-docx, BeautifulSoup
- **Styling**: Custom CSS với CSS Variables

## 🔧 Cấu hình nâng cao

### Thay đổi mô hình AI
Trong `config.py`, bạn có thể thay đổi các mô hình AI:
```python
AVAILABLE_MODELS = {
    "Nhanh & Tối ưu (Flash)": "gemini-1.5-flash-latest",
    "Mạnh & Thông minh (Pro)": "gemini-1.5-pro-latest"
}
```

### Tùy chỉnh xử lý văn bản
```python
TEXT_CHUNK_SIZE = 1000        # Kích thước chunk văn bản
TEXT_CHUNK_OVERLAP = 150      # Độ chồng lấp giữa các chunk
VECTOR_DB_SEARCH_RESULTS = 7  # Số kết quả tìm kiếm
```

## 🚀 Deploy lên Streamlit Cloud

1. Push code lên GitHub repository
2. Đăng ký tài khoản Streamlit Cloud
3. Connect repository và deploy
4. Thêm `GEMINI_API_KEY` vào Streamlit Secrets

## 🤝 Đóng góp

Mọi đóng góp đều được chào đón! Hãy:
1. Fork repository
2. Tạo feature branch
3. Commit changes
4. Push và tạo Pull Request

## 📄 License

MIT License - xem file LICENSE để biết thêm chi tiết.

## 🙏 Cảm ơn

- Google AI Studio cho Gemini API
- Streamlit team cho framework tuyệt vời
- ChromaDB cho vector database
- Cộng đồng open source

---

**PNote** - Biến việc học tập trở nên thông minh hơn! 🚀 