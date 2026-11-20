# quiz-generator-ai-nh-m-11
AI Study Assistant
Ứng dụng Streamlit + Gemini API hỗ trợ sinh viên đọc tài liệu PDF/TXT, tạo đề cương ôn tập và câu hỏi trắc nghiệm 4 lựa chọn kèm chấm điểm, giải thích.
1. Chức năng
- Đọc tài liệu: Trích xuất văn bản từ PDF hoặc TXT; giới hạn xử lý 20 MB/file.
- Tóm tắt AI: Dùng Gemini tóm tắt bài giảng; tài liệu dài được chia bằng chunk_text().
- Tạo quiz AI: Sinh câu hỏi với đáp án A/B/C/D, giải thích; người dùng có thể nộp bài và làm lại.
-Lịch sử cá nhân: Xem lại bản tóm tắt; xem các lần làm quiz, số câu đúng, đáp án đã chọn và giải thích.
Giới hạn: Chưa hỗ trợ OCR cho PDF scan ảnh. Kết quả AI cần đối chiếu với tài liệu gốc; tốc độ và khả năng gọi API tùy mạng, model và hạn mức Gemini.SQLite lưu trên máy chạy ứng dụng, không tự đồng bộ giữa các máy.
2. Cấu trúc dự án
quiz-generator-ai-nh-m-11/
├── app.py                 # Giao diện học tập, tích hợp các module
├── account_ui.py          # Đăng nhập/đăng ký, menu, trang lịch sử
├── account_db.py          # SQLite, xác thực tài khoản, lưu/truy vấn lịch sử
├── document_processor.py  # Đọc PDF/TXT, chia đoạn văn bản
├── ai_summarizer.py       # Gọi Gemini, tóm tắt
├── quiz_generator.py      # Tạo câu hỏi trắc nghiệm
├── requirements.txt       # Thư viện cần cài
├── .env.example           # Mẫu biến môi trường (không chứa khóa thật)
├── .gitignore
└── README.md
Sau khi chạy, SQLite tự tạo file cơ sở dữ liệu (ví dụ study_assistant.db) theo DB_PATH trong account_db.py.
3. Cài đặt và chạy
Yêu cầu: Python 3.11–3.13, Internet, Gemini API key từ Google AI Studio. Mở Terminal tại thư mục chứa app.py.

Windows PowerShell:
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
macOS/Linux:
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
requirements.txt cần có các thư viện: streamlit, pypdf, google-genai, python-dotenv, argon2-cffi. Nếu thiếu Argon2: python -m pip install argon2-cffi (trên Windows, dùng Python trong .venv). Thư viện sqlite3 có sẵn trong Python, không phải cài thêm.

Cấu hình Gemini: Sao chép .env.example thành .env, sau đó điền:
GEMINI_API_KEY=KHOA_API_CUA_BAN
GEMINI_MODELS=TEN_MODEL_DANG_DUNG_DUOC
Đổi giá trị minh họa thành API key và model thực tế. Module tóm tắt sử dụng tên biến GEMINI_MODELS (số nhiều).

Chạy ứng dụng:
# Windows
.\.venv\Scripts\python.exe -m streamlit run app.py
# macOS/Linux (đã kích hoạt .venv)
python -m streamlit run app.py
Truy cập địa chỉ được in trong Terminal, thường là http://localhost:8501.
4. Cách sử dụng
1. Chọn Đăng ký để tạo tài khoản hoặc Đăng nhập nếu đã có tài khoản. Username gồm 3–32 ký tự không dấu, số hoặc _; mật khẩu tối thiểu 8 ký tự.
2. Vào 📚 Học tập → tải PDF/TXT → nhấn Đọc tài liệu.
3. Nhấn Tóm tắt để tạo đề cương; kết quả thành công được lưu vào 📖 Lịch sử tóm tắt.
4. Nhấn Tạo câu hỏi → chọn A/B/C/D → Nộp bài để xem điểm và giải thích. Kết quả nộp được lưu vào 📝 Lịch sử làm quiz; có thể nhấn Làm lại.
5. Dùng thanh bên trái để xem lịch sử hoặc Đăng xuất. Mỗi tài khoản chỉ xem được lịch sử gắn với tài khoản đó.
5. Các module và lưu trữ
File	Hàm chính	Vai trò
document_processor.py	extract_text(path), chunk_text(text)	Đọc và chia văn bản
ai_summarizer.py	summarize(text, on_progress=None)	Tóm tắt bằng Gemini
quiz_generator.py	generate_questions(text, so_cau=10)	Sinh danh sách câu hỏi
account_db.py	init_db(), register_user(), authenticate_user()	Khởi tạo SQLite, đăng ký/đăng nhập
account_db.py	save_summary(), save_quiz_attempt(), get_summary_history(), get_quiz_history()	Lưu và lấy lịch sử theo user_id
account_ui.py	require_login(), sidebar_menu(), show_history_page()	Giao diện tài khoản và lịch sử


SQLite gồm 3 bảng: users, summary_history, quiz_history. Mật khẩu chỉ được lưu dưới dạng mã băm. app.py dùng file tạm vì extract_text() nhận đường dẫn; quiz sử dụng question, options (4 chuỗi không có nhãn), answer (A–D) và explanation.

Bảo mật: Đảm bảo .gitignore có ít nhất:
.env
.venv/
study_assistant.db*
__pycache__/
Không tải API key, mật khẩu hay dữ liệu tài khoản thực lên GitHub. Nếu triển khai trên Streamlit Community Cloud, SQLite cục bộ có thể mất dữ liệu khi ứng dụng được khởi động/triển khai lại; nên dùng cơ sở dữ liệu lưu trữ bền vững bên ngoài khi cần giữ lịch sử lâu dài.
6. Kiểm tra nhanh và lỗi thường gặp
# Windows: kiểm tra import các module
.\.venv\Scripts\python.exe -c "from document_processor import extract_text; from ai_summarizer import summarize; from quiz_generator import generate_questions; from account_db import init_db; print('Import OK')"
Vấn đề	Cách xử lý
Thiếu thư viện hoặc argon2	Cài lại requirements.txt trong đúng .venv
Thiếu GEMINI_API_KEY, model 404, quota 429	Kiểm tra .env, model, mạng và quota API
PDF không đọc được	Kiểm tra file rỗng hoặc PDF scan ảnh
Không đăng ký được	Username không dấu, 3–32 ký tự; mật khẩu ít nhất 8 ký tự; kiểm tra tên đã tồn tại
Lỗi SQLite duplicate column name	Kiểm tra khai báo trùng cột trong init_db(); không xóa database khi chưa sao lưu
Quiz không chấm/lưu lịch sử	Kiểm tra answer A–D và chỉ gọi save_quiz_attempt() khi nhấn Nộp bài


Kiểm thử trước bàn giao: Tạo hai tài khoản khác nhau; với tài khoản A hãy tóm tắt và nộp quiz, sau đó đăng xuất và đăng nhập B để xác nhận B không thấy lịch sử của A. Đăng nhập lại A để kiểm tra lịch sử vẫn còn sau khi khởi động lại ứng dụng.