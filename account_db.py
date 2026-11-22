"""Lưu trữ tài khoản cục bộ và lịch sử theo từng người dùng cho AI Study Assistant.

Thiết kế cho dự án nhỏ trên một máy chủ Streamlit duy nhất.
Mật khẩu chỉ được lưu dưới dạng mã băm Argon2; các đầu vào truy vấn đều được tham số hóa.
"""

from contextlib import contextmanager #dùng để viết hàm quản lí tài nguyên
from datetime import datetime, timezone
import json
from pathlib import Path
import re #Dùng biểu thức chính quy (Regex) để kiểm tra định dạng chuỗi (như tên đăng nhập)
import sqlite3 #Thư viện chuẩn của Python để làm việc với cơ sở dữ liệu SQLite cục bộ

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError #Thuộc thư viện 
#argon2-cffi, dùng để băm mật khẩu an toàn và bắt lỗi khi xác thực mật khẩu thất bại hoặc chuỗi hash không hợp lệ.

#Xác định đường dẫn tuyệt đối tới tệp cơ sở dữ liệu study_assistant.db nằm cùng thư mục với tệp Python hiện tại
DB_PATH = Path(__file__).resolve().parent / "study_assistant.db"

#Khởi tạo bộ băm mật khẩu Argon2 với các tham số mặc định an toàn.
# Dấu gạch dưới _ ở đầu mang ý nghĩa quy ước là biến nội bộ của module.
_password_hasher = PasswordHasher()

#Biên dịch sẵn mẫu regex kiểm tra tên đăng nhập hợp lệ:

#^ và $: Khớp toàn bộ chuỗi từ đầu đến cuối.
#[A-Za-z0-9_]: Chỉ cho phép chữ cái (hoa hoặc thường), chữ số và dấu gạch dưới _.
#{3,32}: Độ dài từ 3 đến 32 ký tự (không có khoảng trắng hay ký tự đặc biệt).
_USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,32}$")

#Lấy thời điểm hiện tại theo múi giờ UTC (timezone.utc), sau đó chuyển thành chuỗi chuẩn ISO 8601 
# và cắt tới mức giây (timespec="seconds"), ví dụ: "2026-11-20T03:41:00+00:00".
#giúp sắp xếp thời gian theo thứ tự bảng chữ cái/thời gian chính xác và tránh lệch múi giờ khi triển khai máy chủ.
def _now_utc():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

# @contextmanager giúp sử dụng hàm _db() với cú pháp "with"
# Tự động quản lý việc mở, lưu thay đổi và đóng kết nối database
@contextmanager
def _db():
    # Kết nối đến database SQLite tại đường dẫn DB_PATH
    # Nếu file database chưa tồn tại, SQLite sẽ tự tạo file mới
    # timeout=15: chờ tối đa 15 giây nếu database đang bị khóa
    connection = sqlite3.connect(DB_PATH, timeout=15)
    # Cho phép lấy dữ liệu bằng tên cột thay vì chỉ dùng chỉ số
    # Ví dụ: row["username"] thay vì row[1]
    connection.row_factory = sqlite3.Row
    
    ## SQLite không luôn tự bật kiểm tra khóa ngoại
    # Lệnh này bật tính toàn vẹn tham chiếu giữa các bảng
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        # yield trả kết nối cho khối "with" sử dụng
        # Đồng thời tạm dừng hàm _db() tại đây
        yield connection

        # Nếu các thao tác không gây lỗi thì lưu thay đổi vào database
        connection.commit()

    except Exception:
        # Nếu xảy ra lỗi, hủy các thay đổi chưa được commit
        # Giúp tránh lưu dữ liệu chưa hoàn chỉnh
        connection.rollback()

        # Ném lại lỗi để chương trình bên ngoài biết và xử lý
        raise

    finally:
        # Dù thành công hay thất bại cũng đóng kết nối
        # Tránh để kết nối database mở không cần thiết
        connection.close()


def init_db():
    """
    Khởi tạo các bảng trong database nếu chưa tồn tại.
    Có thể gọi lại nhiều lần mà không tạo trùng bảng.
    """

    # Mở kết nối bằng hàm _db()
    # Khi thoát khỏi with, kết nối được đóng tự động
    with _db() as con:

        # executescript() cho phép thực thi nhiều câu lệnh SQL cùng lúc
        con.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE COLLATE NOCASE, -- COLLATE NOCASE: so sánh không phân biệt hoa/thường
                -- Lưu mã băm của mật khẩu, KHÔNG lưu mật khẩu gốc
                password_hash TEXT NOT NULL,

                -- Thời điểm tài khoản được tạo
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS summary_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,  -- ON DELETE CASCADE: nếu xóa tài khoản
                -- thì tự động xóa lịch sử tóm tắt của tài khoản đó
                filename TEXT NOT NULL,
                summary TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS quiz_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, -- Nếu xóa tài khoản thì xóa lịch sử quiz tương ứng
                filename TEXT NOT NULL,
                score INTEGER NOT NULL,
                total INTEGER NOT NULL,
                questions_json TEXT NOT NULL,-- Lưu danh sách câu hỏi dưới dạng chuỗi JSON
                -- Ví dụ: [{"question": "...", "answer": "B"}]
                selected_json TEXT NOT NULL, -- Lưu những đáp án người dùng đã chọn dưới dạng JSON
                -- Ví dụ: ["A", "C", "B"]
                created_at TEXT NOT NULL
            );
            --TẠO INDEX (CHỈ MỤC) ĐỂ TĂNG TỐC TRUY VẤN
            CREATE INDEX IF NOT EXISTS ix_summary_user_date -- Index giúp tìm lịch sử tóm tắt theo user_id
            -- và thời gian nhanh hơn khi dữ liệu tăng
                ON summary_history(user_id, created_at DESC); --DESC: sắp xếp thời gian từ mới nhất đến cũ nhất
            CREATE INDEX IF NOT EXISTS ix_quiz_user_date --Index phục vụ việc lấy lịch sử quiz theo tài khoản
            -- và sắp xếp các lượt làm bài theo thời gian
                ON quiz_history(user_id, created_at DESC);
        """)


def register_user(username, password):
    """
    Đăng ký tài khoản mới.
    Nếu thành công: trả về ID của tài khoản vừa tạo.
    Nếu dữ liệu không hợp lệ: báo lỗi ValueError.
    """
    username = username.strip() if isinstance(username, str) else ""
    #_USERNAME_RE :dòng 30
    if not _USERNAME_RE.fullmatch(username): #fullmatch() kiểm tra TOÀN BỘ username có khớp mẫu hay không.    
        raise ValueError("Tên đăng nhập cần 3–32 ký tự, chỉ gồm chữ không dấu, số hoặc dấu _.")
    if not isinstance(password, str) or len(password) < 8:
        raise ValueError("Mật khẩu phải có ít nhất 8 ký tự.")
    if len(password) > 128:
        raise ValueError("Mật khẩu quá dài (tối đa 128 ký tự).")

    # Chuyển mật khẩu gốc thành chuỗi băm bằng bộ băm mật khẩu.
    # Không lưu trực tiếp mật khẩu người dùng vào database.
    hashed_password = _password_hasher.hash(password)
    try:
        #gọi lại _db()
        with _db() as con:
            #con.execute() thực thi một câu lệnh SQL.
            #Ở đây dùng INSERT INTO để thêm tài khoản mới.
            cursor = con.execute(
                "INSERT INTO users(username, password_hash, created_at) VALUES (?, ?, ?)",
                (username, hashed_password, _now_utc()),
            )
            # lastrowid lấy ID của dòng vừa được thêm.
            # Ví dụ đăng ký tài khoản đầu tiên có thể nhận ID = 1.
            # Đây là ID trong bảng users, không phải username.
            return cursor.lastrowid
    except sqlite3.IntegrityError as exc:
        raise ValueError("Tên đăng nhập đã được sử dụng.") from exc


def authenticate_user(username, password):
    """
    Xác thực tài khoản khi đăng nhập.

    - Đúng tên đăng nhập và mật khẩu:
      Trả về dict chứa id và username.
    - Sai tên đăng nhập hoặc mật khẩu:
      Trả về None.
    """
    if not isinstance(username, str) or not isinstance(password, str):
        return None
    with _db() as con:
        # Tìm tài khoản có username khớp với tên người dùng nhập.
        row = con.execute(
            # WHERE username = ?: chỉ lấy tài khoản có tên khớp.
            # COLLATE NOCASE: không phân biệt chữ hoa, chữ thường.
            "SELECT id, username, password_hash FROM users WHERE username = ? COLLATE NOCASE",
            # Dấu ? được thay bằng username sau khi loại bỏ khoảng trắng ở hai đầu.
            # (username.strip(),) là tuple có một phần tử.
            # Dấu phẩy giúp Python hiểu đây là tuple, không phải chuỗi.
            (username.strip(),),
        ).fetchone() # fetchone() lấy một dòng kết quả đầu tiên.
        # Nếu không tìm được tài khoản thì trả về None.
        if row is None:
            return None
        try:
            # verify() so sánh mật khẩu vừa nhập với mã băm đã lưu trong database.
            _password_hasher.verify(row["password_hash"], password)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return None
        # check_needs_rehash() kiểm tra mã băm hiện tại
        # có cần được tạo lại theo cấu hình bảo mật mới không.
        # Ví dụ: sau này nhóm thay đổi tham số thuật toán băm.
        if _password_hasher.check_needs_rehash(row["password_hash"]):
            con.execute(
            # Nếu cần, tạo lại mã băm từ mật khẩu vừa xác thực.
            # Sau đó cập nhật vào database.
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (_password_hasher.hash(password), row["id"]),
            )
        return {"id": row["id"], "username": row["username"]}


def save_summary(user_id, filename, summary):
    """Lưu bản tóm tắt thành công vào database.
    Không lưu nội dung gốc của file PDF/TXT đã tải lên.

    Trả về ID của bản tóm tắt vừa được lưu."""
    if not isinstance(summary, str) or not summary.strip():
        raise ValueError("Bản tóm tắt rỗng.")
    with _db() as con:
        cursor = con.execute(
            "INSERT INTO summary_history(user_id, filename, summary, created_at) VALUES (?, ?, ?, ?)",
            (user_id, filename, summary, _now_utc()),
        )
        return cursor.lastrowid


def save_quiz_attempt(user_id, filename, questions, selected_letters, score):
    """Lưu kết quả một lượt làm quiz vào database.

    Chỉ gọi hàm sau khi người dùng nhấn nút "Nộp bài",
    không gọi ngay khi Gemini vừa tạo câu hỏi.

    Trả về ID của lượt làm quiz vừa được lưu."""
    if not questions or len(questions) != len(selected_letters):
        raise ValueError("Bộ câu hỏi và câu trả lời không khớp.")
    if not (0 <= score <= len(questions)):
        raise ValueError("Điểm không hợp lệ.")
    with _db() as con:
        cursor = con.execute(
            """INSERT INTO quiz_history
                (user_id, filename, score, total, questions_json, selected_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id, filename, score, len(questions),
                # Chuyển danh sách câu hỏi,đáp án đã chọn Python thành chuỗi JSON
                # để lưu vào cột TEXT của SQLite.
                # ensure_ascii=False giúp giữ chữ tiếng Việt
                json.dumps(questions, ensure_ascii=False),
                json.dumps(selected_letters, ensure_ascii=False),
                _now_utc(),
            ),
        )
        return cursor.lastrowid


def get_summary_history(user_id, limit=50):
    """
    Lấy lịch sử tóm tắt của một tài khoản.

    user_id: ID tài khoản đang đăng nhập.
    limit=50: mặc định chỉ lấy tối đa 50 bản tóm tắt.

    Trả về danh sách các dictionary.
    """
    with _db() as con:
        
        rows = con.execute(
            """SELECT id, filename, summary, created_at
               FROM summary_history WHERE user_id = ?
               ORDER BY id DESC LIMIT ?""",
            (user_id, limit),
        ).fetchall() # fetchall() lấy tất cả dòng kết quả của truy vấn.
        # Vì có LIMIT nên tối đa lấy 'limit' dòng.
        return [dict(r) for r in rows]


def get_quiz_history(user_id, limit=50):
    """
    Lấy lịch sử các lần làm quiz của một tài khoản.

    Trả về danh sách dictionary chứa:
    - ID lượt làm bài
    - Tên tài liệu
    - Điểm số và tổng số câu
    - Danh sách câu hỏi
    - Đáp án người dùng đã chọn
    - Thời gian nộp bài
    """
    with _db() as con:
        rows = con.execute(
            """SELECT id, filename, score, total, questions_json,
                      selected_json, created_at
               FROM quiz_history WHERE user_id = ?
               ORDER BY id DESC LIMIT ?""",
            (user_id, limit),
        ).fetchall()
    records = []
    for row in rows:
        record = dict(row)
        record["questions"] = json.loads(record.pop("questions_json"))
        record["selected"] = json.loads(record.pop("selected_json"))
        records.append(record)
    return records
# record.pop("questions_json"):
        # Lấy giá trị của khóa questions_json
        # đồng thời xóa khóa đó khỏi dictionary.
        #
        # json.loads(...):
        # Chuyển chuỗi JSON thành dữ liệu Python.
        #
        # Ví dụ:
        # '[{"question": "AI là gì?", "answer": "A"}]'
        # trở thành list chứa dictionary.
        #
        # Sau đó lưu vào khóa mới tên là "questions".
