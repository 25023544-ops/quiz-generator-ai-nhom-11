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
    return "\n\n".join(cac_trang) #nối các trang lại với nhau thành 1 dòng mỗi trang sẽ phân biệt nhau bằng dấu xuống dòng và cách nhau 1 dòng ở giữa

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
def _cat_khoi_dai(khoi,gioi_han):
     """Cắt 1 khối dài hơn giới hạn thành nhiều mảnh nhỏ.
        Cắt ở chỗ hết câu,rồi đến khoảng trắng,cuối cùng mới cắt cứng.   
     """
     cac_manh=[]
     while len(khoi)>gioi_han:
          vung=khoi[:gioi_han]
          vi_tri= max(vung.rfind(". "), vung.rfind("? "), vung.rfind("! "))
          #r find sẽ trả về chỉ số của dấu ko trả về chỉ số của khoảng trắng
          # r find:reverse find ,tìm vị trí xuất hiện của chuỗi con tính từ bên phải sang
          if vi_tri != -1:
               vi_tri+=1 #vì vi_tri dg chỉ vào vị trí dấu nên phải +=1 để lấy được thêm cả dấu câu vào khi tách
          else:
               vi_tri=vung.rfind(" ") #Không có hết câu thì cắt ở khoảng trắng vì bắt buộc
          if vi_tri <= 0:
               vi_tri=gioi_han #ko có khoảng trắng nào đành cắt cứng
          cac_manh.append(khoi[:vi_tri].strip()) #cắt đến đoạn đầu vi tri
          khoi=khoi[vi_tri:].strip() #cập nhật lại mảng mới
     if khoi: #nếu nó ko rỗng
          cac_manh.append(khoi)
     return cac_manh

def _lay_duoi(doan, overlap):
     """Lấy phần đuôi khoảng overlap ký tự của 1 đoạn,bắt đầu ở đầu 1 từ"""
     if overlap == 0:
          return ""
     duoi= doan[-overlap:] #đếm ngc từ cuối chuỗi overlap kí tự rồi lấy toàn bộ trí đó cho đến hết
     vi_tri = duoi.find(" ")
     if vi_tri != -1: #tìm vị trí có dấu cách đó vì nó có thể làm mất ý nghĩa
          duoi=duoi[vi_tri+1:] #+1 để bỏ qua dấu cách và các từ dg bị ghép dở chỉ lấy từ có ý nghĩa
     return duoi.strip() #cắt bỏ khoảng trắng thừa ở 2 đầu

def chunk_text(van_ban,max_chars=3000,overlap=200):
     """Cắt văn bản dài thành danh sách các đoạn,mỗi đoạn tối đa max_chars ký tự.
        Mỗi đoạn(trừ đoạn đầu) bắt đầu bằng khoảng overlap ký tự cuối của đoạn trước
        Tham số sai thì báo ValueError
     """
     if max_chars <=0 :
          raise ValueError("max_chars phải lớn hơn 0.")
     if overlap < 0:
          raise ValueError("overlap không được âm.")
     if overlap + 3 > max_chars:
          raise ValueError("overlap phải nhỏ hơn max_chars ít nhất 3 ký tự.")
     #1 khối cộng phần gối đầu + phần phân cách và phần mới vẫn phải thỏa mãn max_chars
     gioi_han_khoi= max_chars - overlap -2

     cac_khoi=[]
     for khoi in van_ban.split("\n\n"):
          khoi=khoi.strip()
          if khoi:
               cac_khoi.extend(_cat_khoi_dai(khoi, gioi_han_khoi))

     cac_doan=[]
     hien_tai=""
     for khoi in cac_khoi:
          if hien_tai and len(hien_tai) + 2 +len(khoi) >max_chars:
               cac_doan.append(hien_tai)
               hien_tai = _lay_duoi(hien_tai,overlap)
          hien_tai=hien_tai + "\n\n" + khoi if hien_tai else khoi     
     if hien_tai :
          cac_doan.append(hien_tai)
     return cac_doan     
         
        