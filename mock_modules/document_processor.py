def extract_text(file):
    if file is None:
        raise ValueError("Chưa tải tài liệu.")

    data = file.getvalue()

    if not data:
        raise ValueError("File rỗng.")

    filename = file.name.lower()

    if filename.endswith(".txt"):
        try:
            text = data.decode("utf-8-sig").strip()
        except UnicodeDecodeError:
            raise ValueError("TXT phải sử dụng UTF-8.")

    elif filename.endswith(".pdf"):
        # Mô phỏng, CHƯA đọc PDF thật
        text = (
            "Nội dung PDF giả lập để kiểm thử. "
            "Trí tuệ nhân tạo là lĩnh vực nghiên cứu "
            "các hệ thống có khả năng thực hiện "
            "những nhiệm vụ thông minh."
        )

    else:
        raise ValueError("Chỉ hỗ trợ PDF và TXT.")

    if not text:
        raise ValueError("Không tìm thấy nội dung văn bản.")

    return text