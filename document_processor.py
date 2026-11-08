import os #operation system liên kết với chính hệ điều hành giúp quản lý file

from pypdf import PdfReader #sử dụng pypdf để đọc pdf
from pypdf.errors import PdfReadError #pypdf.errors (module con của pypdf) chuyên chứa lỗi liên quan đến các file pdf

#Khai báo hằng số
GIOI_HAN_MB=20 #dungluong file tối đa
SO_KY_TU_TOI_THIEU=20 #tổng chữ ít hơn thì coi như file đấy sẽ ko có chữ

#Đọc pdf
def _doc_pdf(duong_dan): # _ chỉ đây là 1 hàm nội bộ
    try:
        reader = PdfReader(duong_dan)
        cac_trang = [page.extract_text() or "" for page in reader.pages]
    except PdfReadError as loi: #nếu try k được sẽ nhảy xuống except,bắt lỗi và lưu thông tin lỗi vào loi
        raise ValueError("File PDF bị hỏng hoặc không đọc được.") from loi # chủ động ném ra lỗi để hiển thị và lưu PdfError(lỗi gốc) vao loi để sau người sửa có thể biết được lỗi sai ở đâu
    return "\n".join(cac_trang) #nối các trang lại với nhau thành 1 dòng mỗi trang sẽ phân biệt nhau bằng dấu xuống dòng

#Đọc TXT
def _doc_txt(duong_dan):
    try:
        with open(duong_dan,"r",encoding="utf-8-sig") as f: #with để tự động đóng file sau khi mở,"r " tức là chỉ dùng để đọc, chỉ định mã để đọc sau đó đặt tên biến cho cái file vừa mở để sau thuận tiện
            return f.read() #hàm này đọc sau đó in ra String,file được đóng lại an toàn nhờ with
    except UnicodeDecodeError as loi: #bắt lỗi và cất thông tin vào loi
        raise ValueError( #ném ra lỗi để dễ hiểu
            "Không đọc được file TXT.Hãy lưu lại file với mã hóa UTF-8."
        ) from loi #vẫn lưu lại trace ban đầu để ltv có thể tìm kiếm lỗi gốc nằm ở đâu

#Hàm chính
def extract_text(duong_dan):
        """Đọc file .pdf hoặc .txt và trả về văn bản. Mọi vấn đề đều báo bằng ValueError."""
        if not os.path.isfile(duong_dan): #kiểm tra xem thực sự đường dẫn đó có nằm trog máy bạn ko và có đúng là 1 file ko
             raise ValueError("Không tìm thấy file.") # nếu ko thấy thì lập tức dừng và ném ra lỗi
        duoi=os.path.splitext(duong_dan)[1].lower() #ví dụ:baigiang.pdf thì split nó ra 0 là baigiang 1 là .pdf xong chuyển thành viết thường
        if duoi not in(".pdf",".txt"):
             raise ValueError("Chỉ hỗ trợ file .pdf và .txt")
        kich_thuoc=os.path.getsize(duong_dan) #xem kích thước của đường dẫn là bao nhiêu byte
        if kich_thuoc ==0:
             raise ValueError("File rỗng.")
        if kich_thuoc > GIOI_HAN_MB * 1024 * 1024: #chuyển từ byte sang MB:1MB=1024KB=1024x1024 Byte
             raise ValueError(f"File quá lớn (tối đa {GIOI_HAN_MB} MB).")
        van_ban=_doc_pdf(duong_dan) if duoi == ".pdf" else _doc_txt(duong_dan)
        if len(van_ban.strip()) < SO_KY_TU_TOI_THIEU : #strip bỏ hết dấu cách dầu xuống dòng thừa ở 2 đầu văn bản
             raise ValueError(
                  "File không có chữ để đọc.Nếu là PDF,có thể đây là bản Scan ảnh"
             )
        return van_ban 

        