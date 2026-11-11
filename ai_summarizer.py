import os
import re
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
from document_processor import chunk_text

load_dotenv()

# Danh sách model theo thứ tự ưu tiên: model đầu lỗi thì tự chuyển sang model sau.
# Muốn đổi thì thêm dòng GEMINI_MODELS=a,b,c vào file .env (cách nhau bằng dấu phẩy).
DANH_SACH_MODEL = [
    m.strip()
    for m in os.getenv(
        "GEMINI_MODELS", "gemini-3.6-flash,gemini-3.5-flash,gemini-3.1-flash-lite"
    ).split(",")
    if m.strip()
]
MODEL = DANH_SACH_MODEL[0]  # model ưu tiên số 1
MODEL_GOP = MODEL  # giữ lại để các file test cũ không lỗi
MODEL_DA_DUNG = None  # model thực sự trả lời ở lần gọi gần nhất
COOLDOWN_GIAY = 90  # model vừa bị quá tải thì tạm bỏ qua trong ngần này giây
_het_han = {}  # tên model -> thời điểm được thử lại

TIMEOUT_MS = 25000  # chờ tối đa 25 giây mỗi lần gọi một model
MAX_CHARS_MOT_LAN = 8000  # đoạn càng nhỏ thì tóm tắt càng chi tiết (nhưng gọi AI nhiều lần hơn)
SO_DOAN_TOI_DA = 40  # bài quá dài (quá nhiều đoạn) thì báo lỗi để tránh hết quota

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


def _ma_loi(e):
    """Lấy mã lỗi HTTP (400, 503...) từ ngoại lệ, không có thì trả None."""
    ma = getattr(e, "code", None)
    if isinstance(ma, int):
        return ma
    m = re.match(r"\s*(\d{3})\b", str(e))
    return int(m.group(1)) if m else None


def _model_san_sang(cac_model):
    """Bỏ qua các model vừa bị lỗi gần đây. Nếu tất cả đều đang nghỉ thì thử lại hết."""
    bay_gio = time.time()
    san_sang = [m for m in cac_model if _het_han.get(m, 0) <= bay_gio]
    return san_sang or cac_model


def call_llm(prompt, retries=3, wait=3, model=None):
    """Gửi prompt cho Gemini, trả về văn bản. Dùng chung cho cả nhóm.
    Thử lần lượt các model trong DANH_SACH_MODEL; model nào lỗi tạm thời
    (quá tải, hết thời gian, không còn model...) thì chuyển sang model kế tiếp
    và được cho nghỉ COOLDOWN_GIAY giây để các lần gọi sau không phí thời gian chờ nó.
    retries = số vòng thử, giữa các vòng nghỉ wait, 2*wait, ... giây.
    Truyền model=... để chỉ dùng đúng 1 model."""
    global MODEL_DA_DUNG
    if not prompt or not prompt.strip():
        raise ValueError("Prompt rỗng")
    client = _get_client()  # lỗi thiếu key báo ngay, không thử lại

    cac_model = [model] if model else DANH_SACH_MODEL
    loi_cuoi = None
    for vong in range(1, retries + 1):
        for ten in _model_san_sang(cac_model):
            try:
                resp = client.models.generate_content(model=ten, contents=prompt)
                if not resp.text:
                    raise RuntimeError("AI trả về rỗng (có thể bị bộ lọc chặn)")
                _het_han.pop(ten, None)
                MODEL_DA_DUNG = ten
                return resp.text
            except Exception as e:
                loi_cuoi = e
                if _ma_loi(e) in (400, 401, 403):
                    # Key sai hoặc yêu cầu sai: đổi model cũng vô ích, báo ngay
                    raise RuntimeError(f"Gọi AI thất bại ({ten}): {e}") from e
                _het_han[ten] = time.time() + COOLDOWN_GIAY
        if vong < retries:
            time.sleep(wait * vong)  # nghỉ rồi thử lại
    raise RuntimeError(
        f"Gọi AI thất bại sau {retries} vòng thử {len(cac_model)} model: {loi_cuoi}"
    ) from loi_cuoi


# ---------------- Tóm tắt bài giảng ----------------

PROMPT_TOM_TAT = """Bạn là trợ lý học tập. Hãy tóm tắt CHI TIẾT nội dung bài giảng dưới đây bằng tiếng Việt, đủ để ôn tập mà không cần đọc lại toàn bộ bài gốc.

Yêu cầu:
- Chỉ dùng thông tin có trong văn bản. Không thêm kiến thức bên ngoài, không bịa.
- Giữ đầy đủ: định nghĩa, khái niệm, công thức, các bước hoặc quy trình, ví dụ minh họa, so sánh, điều kiện và trường hợp đặc biệt.
- Giữ nguyên thuật ngữ chuyên ngành, ký hiệu và tên riêng.
- Viết công thức và ký hiệu bằng chữ hoặc ký tự thường (ví dụ: σ, π, ⋈), tuyệt đối không dùng LaTeX hay dấu $. Ký hiệu nào không rõ thì mô tả bằng lời.
- Nhóm theo chủ đề: mỗi chủ đề có một tiêu đề ngắn, bên dưới liệt kê các ý đầy đủ. Đừng viết quá cô đọng, mỗi ý nên giải thích đủ để hiểu.
- Độ dài khoảng một phần ba văn bản gốc.
- Nếu một đoạn bị lỗi hoặc khó hiểu, bỏ qua đoạn đó, không đoán.
{ghi_chu}
Bài giảng:
\"\"\"
{noi_dung}
\"\"\"
"""

PROMPT_GOP = """Dưới đây là các bản tóm tắt từng phần của CÙNG MỘT bài giảng (có thể trùng ý ở chỗ nối giữa các phần).
Hãy gộp thành MỘT bản tóm tắt thống nhất bằng tiếng Việt.

Yêu cầu:
- Giữ ĐẦY ĐỦ chi tiết của từng phần. Chỉ bỏ ý bị lặp lại ở chỗ nối, KHÔNG rút gọn thêm.
- Giữ đúng thứ tự nội dung của bài giảng.
- Nhóm theo chủ đề, mỗi chủ đề có tiêu đề ngắn và các ý bên dưới.
- Viết công thức và ký hiệu bằng chữ hoặc ký tự thường, không dùng LaTeX hay dấu $.
- Chỉ dùng thông tin có trong các bản tóm tắt, không thêm mới, không bịa.

Các bản tóm tắt:
\"\"\"
{noi_dung}
\"\"\"
"""


def _prompt_tom_tat(noi_dung, ghi_chu=""):
    if ghi_chu:
        ghi_chu = "\n" + ghi_chu + "\n"
    return PROMPT_TOM_TAT.format(noi_dung=noi_dung, ghi_chu=ghi_chu)


def summarize(text, on_progress=None):
    """Tóm tắt bài giảng. Bài ngắn thì gọi AI một lần, bài dài thì chia đoạn
    (chunk_text của Người 1), tóm tắt từng đoạn rồi gộp lại.
    on_progress(xong, tong) là hàm tùy chọn để app hiện tiến độ."""
    if not text or not text.strip():
        raise ValueError("Không có nội dung để tóm tắt")
    text = text.strip()

    if len(text) <= MAX_CHARS_MOT_LAN:
        ket_qua = call_llm(_prompt_tom_tat(text))
        if on_progress:
            on_progress(1, 1)
        return ket_qua

    cac_doan = chunk_text(text, max_chars=MAX_CHARS_MOT_LAN, overlap=200)
    n = len(cac_doan)
    if n > SO_DOAN_TOI_DA:
        raise ValueError(
            f"Bài quá dài ({n} đoạn, tối đa {SO_DOAN_TOI_DA}). Hãy chia nhỏ tài liệu."
        )

    cac_ban = [None] * n
    loi_cuoi = None
    for i, doan in enumerate(cac_doan, 1):
        ghi_chu = f"Đây là phần {i}/{n} của một bài giảng dài, chỉ tóm tắt phần này."
        try:
            cac_ban[i - 1] = call_llm(_prompt_tom_tat(doan, ghi_chu))
        except RuntimeError as e:
            loi_cuoi = e  # chưa dừng, lát nữa thử lại các phần lỗi
        if on_progress:
            on_progress(i, n + 1)

    # Thử lại các phần bị lỗi một lần nữa sau khi nghỉ (quá tải thường chỉ tạm thời)
    cac_loi = [i for i, b in enumerate(cac_ban) if b is None]
    if cac_loi:
        time.sleep(10)
        for i in cac_loi:
            ghi_chu = f"Đây là phần {i + 1}/{n} của một bài giảng dài, chỉ tóm tắt phần này."
            try:
                cac_ban[i] = call_llm(_prompt_tom_tat(cac_doan[i], ghi_chu))
            except RuntimeError as e:
                loi_cuoi = e
        cac_loi = [i for i, b in enumerate(cac_ban) if b is None]

    if len(cac_loi) == n:
        raise RuntimeError(f"Không tóm tắt được phần nào: {loi_cuoi}")

    if cac_loi:
        # Một vài phần vẫn lỗi: trả các phần đã có kèm cảnh báo rõ ràng, không im lặng bỏ sót
        ds = ", ".join(str(i + 1) for i in cac_loi)
        ket_qua = f"(CẢNH BÁO: phần {ds}/{n} chưa tóm tắt được vì AI quá tải, hãy thử lại sau)\n\n"
        ket_qua += "\n\n".join(
            f"### Phần {i}\n{b}" for i, b in enumerate(cac_ban, 1) if b is not None
        )
    else:
        try:
            ket_qua = call_llm(PROMPT_GOP.format(noi_dung="\n\n---\n\n".join(cac_ban)))
        except RuntimeError:
            # Bước gộp lỗi thì vẫn trả các bản tóm tắt từng phần, không làm mất công
            ket_qua = "(Không gộp được thành một bản, dưới đây là tóm tắt theo từng phần)\n\n"
            ket_qua += "\n\n".join(f"### Phần {i}\n{b}" for i, b in enumerate(cac_ban, 1))
    if on_progress:
        on_progress(n + 1, n + 1)
    return ket_qua