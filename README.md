# quiz-generator-ai-nh-m-11
AI Study Assistant
Ứng dụng Streamlit + Gemini API hỗ trợ sinh viên đọc tài liệu PDF/TXT, tạo đề cương ôn tập và câu hỏi trắc nghiệm 4 lựa chọn kèm chấm điểm, giải thích.
1. Chức năng
- Đọc tài liệu: Trích xuất văn bản từ PDF hoặc TXT; giới hạn xử lý 20 MB/file.
- Tóm tắt AI: Dùng Gemini tóm tắt bài giảng; tài liệu dài được chia bằng chunk_text().
- Tạo quiz AI: Sinh câu hỏi với đáp án A/B/C/D, giải thích; người dùng có thể nộp bài và làm lại.
Giới hạn: Chưa hỗ trợ OCR cho PDF scan ảnh. Kết quả AI cần đối chiếu với tài liệu gốc; tốc độ và khả năng gọi API tùy mạng, model và hạn mức Gemini.
2. Cấu trúc dự án
quiz-generator-ai-nh-m-11/
├── app.py                 # Giao diện Streamlit
├── document_processor.py  # Đọc PDF/TXT, chia đoạn
├── ai_summarizer.py       # Gọi Gemini, tóm tắt
├── quiz_generator.py      # Tạo câu hỏi trắc nghiệm
├── requirements.txt       # Thư viện cần cài
├── .env.example           # Mẫu cấu hình
├── .gitignore
└── README.md
3. Cài đặt và chạy
Yêu cầu: Python 3.11–3.13, Internet, API key Gemini từ Google AI Studio.

Bước 1 – Tải mã nguồn: Clone repository của nhóm hoặc tải ZIP, sau đó mở Terminal trong thư mục chứa app.py.

Bước 2 – Tạo môi trường và cài thư viện (Windows PowerShell):
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Trên macOS/Linux:
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
Bước 3 – Cấu hình API key: Sao chép .env.example thành .env trong thư mục gốc (Windows: Copy-Item .env.example .env; macOS/Linux: cp .env.example .env). Mở .env và điền:
GEMINI_API_KEY=KHOA_API_THAT_CUA_BAN
GEMINI_MODELS=TEN_MODEL_GEMINI_DA_KIEM_THU
Thay giá trị minh họa bằng key và tên model thực sự dùng được với tài khoản của bạn. Code Người 2 sử dụng biến GEMINI_MODELS (số nhiều). Không commit file .env hoặc công khai API key; kiểm tra .gitignore có .env và .venv/.

Bước 4 – Chạy ứng dụng:

Windows:
.\.venv\Scripts\python.exe -m streamlit run app.py
macOS/Linux (sau khi kích hoạt .venv):
python -m streamlit run app.py
Mở địa chỉ trong Terminal, thường là http://localhost:8501.
4. Cách sử dụng
1. Tải lên TXT UTF-8 hoặc PDF có lớp văn bản.
2. Nhấn Đọc tài liệu và kiểm tra nội dung.
3. Nhấn Tóm tắt để nhận đề cương do Gemini tạo.
4. Nhấn Tạo câu hỏi, chọn đáp án → Nộp bài để xem điểm và giải thích; nhấn Làm lại nếu cần.
5. Kết nối các module
File	Hàm chính	Kết quả
document_processor.py	extract_text(path)	Văn bản str từ đường dẫn file
document_processor.py	chunk_text(text)	Danh sách các đoạn văn bản
ai_summarizer.py	summarize(text, on_progress=None)	Bản tóm tắt str
quiz_generator.py	generate_questions(text, so_cau=10)	Danh sách câu hỏi list[dict]


Lưu ý tích hợp:extract_text() nhận đường dẫn, nên giao diện cần lưu file upload vào file tạm trước khi gọi.
6. Kiểm tra nhanh và xử lý lỗi
.\.venv\Scripts\python.exe -c "from document_processor import extract_text; from ai_summarizer import summarize; from quiz_generator import generate_questions; print('Import OK')"
Vấn đề	Cách kiểm tra
Thiếu thư viện Python	Cài lại bằng requirements.txt trong đúng .venv
Thiếu GEMINI_API_KEY	Kiểm tra file .env cùng cấp với app.py
Lỗi model 404 hoặc quota 429	Kiểm tra tên model, quyền truy cập và hạn mức API
PDF không đọc được chữ	Kiểm tra PDF scan ảnh hoặc file rỗng
Quiz không hiển thị/chấm đúng	Kiểm tra generate_questions(), trường question và định dạng options


