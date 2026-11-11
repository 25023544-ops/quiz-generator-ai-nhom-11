def summarize(text):
    if not text.strip():
        raise ValueError("Văn bản đầu vào rỗng.")

    return """
    ### Bản tóm tắt mẫu

    1. AI là lĩnh vực nghiên cứu hệ thống thông minh.
    2. Machine Learning giúp máy học từ dữ liệu.
    3. AI có nhiều ứng dụng trong thực tế.

    Đây là dữ liệu giả lập, chưa được tạo bởi AI.
    """