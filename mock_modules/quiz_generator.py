def generate_quiz(text):
    if not text.strip():
        raise ValueError("Văn bản đầu vào rỗng.")

    return [
        {
            "questions": "AI là gì?",
            "options": [
                "A. Một hệ điều hành",
                "B. Lĩnh vực nghiên cứu hệ thống thông minh",
                "C. Một loại phần cứng",
                "D. Một ngôn ngữ lập trình"
            ],
            "answer": "B"
        },
        {
            "questions": "Machine Learning là gì?",
            "options": [
                "A. Phương pháp giúp máy học từ dữ liệu",
                "B. Một trình duyệt",
                "C. Một hệ điều hành",
                "D. Một thiết bị ngoại vi"
            ],
            "answer": "A"
        },
        {
            "questions": "Đâu là ứng dụng của AI?",
            "options": [
                "A. Ổ cắm điện",
                "B. Dây cáp",
                "C. Nhận dạng giọng nói",
                "D. Công tắc điện"
            ],
            "answer": "C"
        }
    ]