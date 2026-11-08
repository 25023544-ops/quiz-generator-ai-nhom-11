import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")  # đổi nếu model không còn dùng được
TIMEOUT_MS = 30000  # chờ tối đa 30 giây mỗi lần gọi

_client = None


def _get_client():
    global _client
    if _client is None:
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            raise RuntimeError("Thiếu GEMINI_API_KEY, kiểm tra file .env")
        _client = genai.Client(
            api_key=key,
            http_options=types.HttpOptions(timeout=TIMEOUT_MS),
        )
    return _client


def call_llm(prompt, retries=3, wait=2):
    """Gửi prompt cho Gemini, trả về văn bản. Dùng chung cho cả nhóm."""
    if not prompt or not prompt.strip():
        raise ValueError("Prompt rỗng")
    client = _get_client()  # lỗi thiếu key báo ngay, không thử lại

    for attempt in range(1, retries + 1):
        try:
            resp = client.models.generate_content(model=MODEL, contents=prompt)
            if not resp.text:
                raise RuntimeError("AI trả về rỗng (có thể bị bộ lọc chặn)")
            return resp.text
        except Exception as e:
            if attempt == retries:
                raise RuntimeError(f"Gọi AI thất bại sau {retries} lần: {e}") from e
            time.sleep(wait * attempt)  # chờ 2s, 4s, ... rồi thử lại