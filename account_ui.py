
"""
Module xây dựng giao diện quản lý tài khoản bằng Streamlit.

Chức năng:
1. Đăng nhập và đăng ký tài khoản.
2. Đăng xuất và xóa trạng thái học tập cũ.
3. Hiển thị menu điều hướng.
4. Xem lịch sử tóm tắt tài liệu.
5. Xem lịch sử làm quiz của từng tài khoản.
"""

# timedelta: biểu diễn khoảng thời gian.
# timezone: định nghĩa múi giờ.
from datetime import datetime, timedelta, timezone

import streamlit as st

from account_db import (
    authenticate_user,       # Kiểm tra thông tin đăng nhập
    get_quiz_history,        # Lấy lịch sử làm quiz
    get_summary_history,     # Lấy lịch sử tóm tắt
    init_db,                 # Khởi tạo các bảng SQLite
    register_user,           # Tạo tài khoản mới
)


# Danh sách các trang chức năng của ứng dụng.
# PAGES[0]: trang học tập chính.
# PAGES[1]: trang xem lịch sử tóm tắt.
# PAGES[2]: trang xem lịch sử làm quiz.
PAGES = [
    "📚 Học tập",
    "📖 Lịch sử tóm tắt",
    "📝 Lịch sử làm quiz"
]


# HÀM 1: XÓA TRẠNG THÁI HỌC TẬP CŨ


def _clear_learning_state():
    """
    Xóa dữ liệu học tập tạm thời của phiên hiện tại.

    Mục đích:
    Tránh hiển thị dữ liệu của tài khoản trước khi
    một tài khoản khác đăng nhập trên cùng phiên trình duyệt.
    """
    # Việc tạo list giúp tránh lỗi khi xóa phần tử trong lúc đang duyệt.
    for key in list(st.session_state):
        if key in {
            "file_id",
            "text",
            "summary",
            "questions",
            "submitted",
            "quiz_version"
        } or key.startswith("answer_"):

            # Xóa biến khỏi Session State.
            del st.session_state[key]

# HÀM 2: YÊU CẦU ĐĂNG NHẬP HOẶC ĐĂNG KÝ

def require_login():
    """
    Hiển thị giao diện đăng nhập/đăng ký.

    Nếu đã đăng nhập: cho phép tiếp tục chạy app.py.
    Nếu chưa đăng nhập: hiển thị form và dừng phần
    còn lại của ứng dụng bằng st.stop().
    """
    init_db()
    if st.session_state.get("user_id") is not None:
        return

    st.title("📚 AI Study Assistant")
    st.caption("Đăng nhập để lưu và xem lại kết quả học tập của riêng bạn.")

    # Tạo hai tab: tab_login: giao diện đăng nhập.
    # tab_signup: giao diện đăng ký.
    tab_login, tab_signup = st.tabs([
        "Đăng nhập",
        "Đăng ký"
    ])

    # XỬ LÝ ĐĂNG NHẬP
    # Các thành phần bên trong được hiển thị ở tab Đăng nhập.
    with tab_login:

        # st.form() gom nhiều ô nhập vào một biểu mẫu.
        # Các giá trị được gửi xử lý khi nhấn nút submit.
        with st.form("account_login_form"):
            username = st.text_input("Tên đăng nhập")
            # type="password": ẩn ký tự khi nhập.
            password = st.text_input(
                "Mật khẩu",
                type="password"
            )
            # Nút gửi form.login = True tại lượt chạy khi người dùng nhấn nút.
            login = st.form_submit_button("Đăng nhập")

        # Chỉ xử lý xác thực sau khi nhấn Đăng nhập.
        if login:

            # Gọi hàm authenticate_user() từ account_db.py.
            # Nếu thành công: trả về {"id": ..., "username": ...}.
            # Nếu thất bại: trả về None.
            user = authenticate_user(username, password)

            # Nếu tài khoản không tồn tại hoặc sai mật khẩu.
            if user is None:
                st.error("Tên đăng nhập hoặc mật khẩu không đúng.")

            else:
                # Xóa dữ liệu học tập cũ trước khi đăng nhập.
                _clear_learning_state()

                # Lưu ID tài khoản vào Session State.
                st.session_state["user_id"] = user["id"]

                # Lưu tên đăng nhập để hiển thị trên giao diện.
                st.session_state["username"] = user["username"]

                # Chạy lại app.py từ đầu.
                # Lần chạy mới sẽ nhận ra user_id đã tồn tại,
                # do đó bỏ qua màn hình đăng nhập.
                st.rerun()

    #XỬ LÝ ĐĂNG KÝ
    # Các thành phần bên trong hiển thị ở tab Đăng ký.
    with tab_signup:

        # Tạo form đăng ký riêng.
        with st.form("account_signup_form"):

            # Ô nhập tên đăng nhập muốn tạo.
            new_username = st.text_input("Tên đăng nhập mới")

            # Ô nhập mật khẩu mới.
            new_password = st.text_input(
                "Mật khẩu mới (ít nhất 8 ký tự)",
                type="password"
            )

            # Ô yêu cầu nhập lại mật khẩu để xác nhận.
            confirm = st.text_input(
                "Nhập lại mật khẩu",
                type="password"
            )

            # Nút tạo tài khoản.
            signup = st.form_submit_button("Tạo tài khoản")

        # Chỉ xử lý khi người dùng nhấn Tạo tài khoản.
        if signup:
            if new_password != confirm:
                st.error("Hai mật khẩu không trùng nhau.")

            else:
                try:
                    user_id = register_user(
                        new_username,
                        new_password
                    )

                # Bắt lỗi ValueError từ register_user().
                # Ví dụ: username trùng hoặc mật khẩu quá ngắn.
                except ValueError as exc:
                    # Hiển thị thông báo lỗi cho người dùng.
                    st.error(str(exc))

                else:
                    # Xóa dữ liệu học tập của phiên trước.
                    _clear_learning_state()

                    # Lưu ID tài khoản vừa đăng ký.
                    st.session_state["user_id"] = user_id

                    # Lưu username sau khi bỏ khoảng trắng hai đầu.
                    st.session_state["username"] = new_username.strip()

                    # Chạy lại ứng dụng và chuyển vào trang học tập.
                    st.rerun()

    # CHẶN TRUY CẬP KHI CHƯA ĐĂNG NHẬP 

    st.stop()


# HÀM 3: MENU BÊN TRÁI VÀ ĐĂNG XUẤT

def sidebar_menu():
    """
    Hiển thị menu trong thanh sidebar.

    Trả về tên trang mà người dùng đã chọn.
    """

    # st.sidebar tạo khu vực thanh bên trái giao diện.
    with st.sidebar:
        # Hiển thị tên tài khoản đang đăng nhập.
        # **...** là cú pháp Markdown để in đậm.
        st.write(f"👤 **{st.session_state['username']}**")

        # Hiển thị các trang có trong danh sách PAGES.(dòng 32)
        # st.radio(): chỉ được chọn một mục tại một thời điểm.
        # key="account_page":
        # Lưu lựa chọn trang vào Session State.
        page = st.radio(
            "Chức năng",
            PAGES,
            key="account_page"
        )

        # Hiển thị nút Đăng xuất.
        if st.button("Đăng xuất"):

            # Xóa dữ liệu học tập tạm thời.
            _clear_learning_state()

            # Xóa key user_id khỏi Session State.
            # Nếu key không tồn tại thì không gây lỗi.
            st.session_state.pop("user_id", None)

            # Xóa tên đăng nhập khỏi Session State.
            st.session_state.pop("username", None)

            # Chạy lại app.py.
            # Vì không còn user_id nên require_login() sẽ hiển thị lại màn hình đăng nhập.
            st.rerun()

    # Trả về trang đã chọn.
    # app.py dùng giá trị này để quyết định nội dung hiển thị.
    return page

# HÀM 4: CHUYỂN THỜI GIAN UTC SANG GIỜ VIỆT NAM

def _display_time(utc_iso):
    """
    Chuyển chuỗi thời gian ISO sang dạng dd/mm/yyyy HH:MM.

    Ví dụ:
    2026-11-20T04:00:00+00:00
    -> 20/11/2026 11:00
    """

    try:
        # datetime.fromisoformat():
        # Chuyển chuỗi ISO 8601 thành đối tượng datetime.
        moment = datetime.fromisoformat(utc_iso)

        # timezone(timedelta(hours=7)): Tạo múi giờ UTC+7 của Việt Nam.
        # astimezone(): chuyển thời gian sang UTC+7.
        # strftime(): định dạng ngày giờ thành chuỗi.
        return moment.astimezone(
            timezone(timedelta(hours=7))
        ).strftime("%d/%m/%Y %H:%M")

    # Nếu chuỗi thời gian không hợp lệ hoặc sai kiểu.
    except (ValueError, TypeError):

        # Trả về dữ liệu đầu vào thay vì làm chương trình lỗi.
        return utc_iso



# HÀM 5: HIỂN THỊ LỊCH SỬ HỌC TẬP


def show_history_page(page):
    """
    Hiển thị trang lịch sử của tài khoản đang đăng nhập.

    page = PAGES[1]: lịch sử tóm tắt.
    page = PAGES[2]: lịch sử làm quiz.
    """

    # Lấy ID tài khoản đã đăng nhập từ Session State.
    #
    # ID này được dùng để chỉ truy vấn lịch sử
    # thuộc tài khoản hiện tại.
    user_id = st.session_state["user_id"]

    #LỊCH SỬ TÓM TẮT

    # Kiểm tra người dùng có chọn trang lịch sử tóm tắt không.
    if page == PAGES[1]:
        st.title("📖 Lịch sử tra cứu / tóm tắt")

        # Gọi hàm get_summary_history() từ account_db.py.
        records = get_summary_history(user_id)

        if not records:
            st.info("Bạn chưa có bản tóm tắt nào được lưu.")

        # Duyệt từng bản tóm tắt trong danh sách.
        for record in records:
            # Lấy tên file PDF/TXT.
            name = record["filename"]

            # Lấy thời gian lưu và chuyển sang UTC+7.
            time_text = _display_time(record["created_at"])

            # st.expander() tạo khung có thể mở/thu gọn.
            # Tiêu đề khung gồm tên tài liệu và thời gian lưu.
            with st.expander(f"📄 {name} — {time_text}"):

                # Hiển thị nội dung bản tóm tắt.
                # st.markdown() xử lý các ký hiệu Markdown như #, ##, **, danh sách...
                st.markdown(record["summary"])

        # Kết thúc xử lý trang lịch sử tóm tắt.
        # Không chạy xuống phần lịch sử quiz.
        return

    # LỊCH SỬ LÀM QUIZ 

    # Kiểm tra người dùng có chọn trang lịch sử quiz không.
    if page == PAGES[2]:

        # Hiển thị tiêu đề trang.
        st.title("📝 Lịch sử làm quiz")

        # Lấy các lượt làm quiz của tài khoản đang đăng nhập.
        records = get_quiz_history(user_id)

        if not records:
            st.info("Bạn chưa nộp bài quiz nào.")

        # Duyệt từng lượt làm quiz.
        for record in records:

            # Tên tài liệu đã dùng để tạo quiz.
            name = record["filename"]

            # Chuyển thời gian nộp bài sang giờ Việt Nam.
            time_text = _display_time(record["created_at"])

            # Tạo tiêu đề gồm:
            # tên file - số câu đúng/tổng số câu - thời gian.
            title = (
                f"{name} — "
                f"{record['score']}/{record['total']} — "
                f"{time_text}"
            )

            # Mỗi lượt làm bài có một khung mở rộng riêng.
            with st.expander(title):

                # HIỂN THỊ TỪNG CÂU HỎI
                # zip() ghép câu hỏi với đáp án được chọn theo cùng vị trí trong hai danh sách.
                #bắt đầu từ câu 1
                for i, (q, selected) in enumerate(
                    zip(
                        record["questions"],
                        record["selected"]
                    ),
                    1
                ):

                    # Hiển thị số thứ tự và nội dung câu hỏi.
                    # q.get("question", ""):
                    # Lấy nội dung câu hỏi.
                    # Nếu thiếu key "question", dùng chuỗi rỗng.
                    st.markdown(
                        f"**Câu {i}. {q.get('question', '')}**"
                    )

                    # HIỂN THỊ 4 LỰA CHỌN
                    for letter, option in zip(
                        "ABCD",
                        q.get("options", [])
                    ):
                        st.write(f"{letter}. {option}")

                    #HIỂN THỊ KẾT QUẢ TỪNG CÂU

                    st.caption(
                        f"Bạn chọn: {selected or 'Chưa chọn'} | "
                        f"Đáp án đúng: {q.get('answer', '?')}"
                    )

                    # Nếu câu hỏi có phần giải thích đáp án.
                    if q.get("explanation"):
                        st.caption(
                            f"Giải thích: {q['explanation']}"
                        )

                #HIỂN THỊ TỔNG ĐIỂM

                # Hiển thị số câu đúng và tổng số câu
                st.write(
                    f"**Kết quả: "
                    f"{record['score']}/{record['total']}**"
                )
