import hashlib
import tempfile
from pathlib import Path
import streamlit as st

#CHẾ ĐỘ CHẠY
USE_MOCK=True
#IMPORT CÁC MODULE
if USE_MOCK:
    from document_processor import extract_text
    from ai_summarizer import summarize
    from mock_modules.quiz_generator import generate_quiz
else:
    from document_processor import extract_text
    from ai_summarizer import summarize
    from quiz_generator import generate_quiz

#HÀM KIỂM TRA CẤU TRÚC CÂU HỎI
def validate_quiz(questions):
    if not isinstance(questions,list) or not questions:
        raise ValueError("Bộ câu hỏi phải là danh sách không rỗng.")
    for q in questions:
        if not isinstance(q,dict):
            raise ValueError("Mỗi câu hỏi phải là dict.")
        
        if not isinstance(q.get("questions"),str):
            raise ValueError("Thiếu nội dung câu hỏi.")
        
        options=q.get("options")
        if not isinstance(options,list) or len(options)!=4:
            raise ValueError("Mỗi câu phải có 4 lựa chọn.")
        
        if not all(isinstance(x,str) for x in options):
            raise ValueError("Các lựa chọn phải là chuỗi.")
        
        for label,option in zip("ABCD",options):
            if not option.startswith(label+"."):
                raise ValueError("Lựa chọn phải bắt đầu từ A. đến D.")
            
        if q.get("answer") not in ("A","B","C","D"):
            raise ValueError("Đáp án phải là A,B,C hoặc D.")
        
#Hàm chuyển uploadedfile thành đường dẫn.Đón nhận file UploadedFile từ giao diện 
# Streamlit-> Chuyển thành file thật lưu tạm trên ổ cứng-> Đưa
# đường dẫn file thật đó cho hàm extract_text xử lý ->
# Tự động dọn dẹp file tạm sau khi hoàn thành.
def extract_uploaded_file(uploaded_file):
    #lấy phần đuôi mở rộng của file(.pdf, .txt,...) 
    duoi=Path(uploaded_file.name).suffix.lower()
    
    if duoi not in(".pdf",".txt"):
        raise ValueError("Chỉ hỗ trợ PDF và TXT.")
    
    #Tạo thư mục tạm
    with tempfile.TemporaryDirectory() as thu_muc_tam:
        #tạo đường dẫn file tạm do ứng dụng kiểm soát
        duong_dan=Path(thu_muc_tam) / f"upload{duoi}"
        
        #ghi nội dung file upload vào dd file tạm(ghi các byte dữ liệu nhị phân vào đường dẫn)
        duong_dan.write_bytes(uploaded_file.getvalue())
        van_ban=extract_text(str(duong_dan))
        return van_ban
        
#GIAO DIỆN
st.set_page_config(
    page_title="AI Study Assistant",
    page_icon="📚"
)

st.title("📚 AI Study Assistant")

st.info(
    "Đang đọc PDF/TXT thật. "
    "Chức năng tóm tắt và tạo câu hỏi vẫn sử dụng dữ liệu mẫu."
)
    
#1.Nhận file
uploaded_file=st.file_uploader("Tải tài liệu PDF/TXT",type=["pdf","txt"])

#2.Nhận diện file
file_id=None
if uploaded_file is not None:
    data=uploaded_file.getvalue()
    file_id=(uploaded_file.name,hashlib.sha256(data).hexdigest()) 
    #tính mã băm từ nội dung file,trả về chuỗi kí tự.
    #Mã đại diện cho đúng nội dung bên trong file(chỉ cần file thay đổi 1 kí tự mã sẽ khác)

#st.session_state:là nơi lưu trữ thông tin tạm thời qua các lần giao diện tự động chạy lại   

#cập nhật file_id (khi người dùng vừa đổi sang file mới)
if st.session_state.get("file_id")!=file_id:
    st.session_state["file_id"]=file_id
    
    #xóa các thông tin chính của file cũ
    for key in ("text","summary","questions"):
        st.session_state.pop(key,None)
    
    st.session_state["submitted"] = False
    
    #xóa các câu trả lời động liên quan đến file cũ
    for key in list(st.session_state.keys()):
        if key.startswith("answer_"):
            del st.session_state[key]
            
#3.Gọi module của Hiếu Nguyễn(thao tác trên giao diện khi up file lên)
if uploaded_file is not None:
    st.write("Tên file:",uploaded_file.name)
    st.write(f"Dung lượng: {uploaded_file.size / 1024:.2f} KB")
    
    if st.button("📄 Đọc tài liệu"):
        try:
            with st.spinner("Đang đọc tài liệu..."): #hiện biểu tượng vòng tròn xoay kèm thông báo đang load 
                text=extract_uploaded_file(uploaded_file)
            
            if not isinstance(text,str) or not text.strip():
                raise ValueError("Module không trả về văn bản hợp lệ.")
            
            #xử lí khi người dùng nhấn đọc lại 
            st.session_state["text"]=text
            st.session_state.pop("summary",None)
            st.session_state.pop("questions",None)
            
        
            
            st.success("Đọc tài liệu thành công.")
        
        except Exception as e:
            st.error(f"Không thể đọc tài liệu: {e}")
            
#4.xem trước văn bản(chỉ đối với text,giới hạn 2000 kí tự đầu)
if st.session_state.get("text"):
    st.text_area(
        "Nội dung đã trích xuất",
        st.session_state["text"][:2000],height=150
    )
    
#5.2 nút xử lí AI (tóm tắt văn bản, tạo câu hỏi)
st.subheader("Chọn chức năng")

ready=bool(st.session_state.get("text"))         

col1, col2=st.columns(2)

with col1:
    if st.button("📝 Tóm tắt",disabled=not ready):
        try:
            with st.spinner("Đang tạo bản tóm tắt..."):
                result=summarize(st.session_state["text"])
        
            if not isinstance(result,str) or not result.strip():
                raise ValueError("Bản tắt không hợp lệ.")
        
            st.session_state["summary"]=result 
        except Exception as e:
            st.error(f"Lỗi tóm tắt:{e}")

with col2:
    if st.button("❓ Tạo câu hỏi",disabled=not ready):
        try:
            with st.spinner("Đang tạo câu hỏi..."):
                result=generate_quiz(st.session_state["text"])
                
            validate_quiz(result)
            
            st.session_state["questions"]=result
            
            st.session_state["submitted"] = False
            
            #Xóa lựa chọn trắc nghiệm cũ
            for key in list(st.session_state.keys()):
                if key.startswith("answer_"):
                    del st.session_state[key]
        except Exception as e:
            st.error(f"Lỗi tạo câu hỏi: {e}")

#6.Hiển thị tóm tắt
if st.session_state.get("summary"):
    st.subheader("Bản tóm tắt")
    st.markdown(st.session_state["summary"])

#7.hiển thị câu hỏi
if st.session_state.get("questions"):
    st.subheader("Câu hỏi trắc nghiệm")
    
    questions=st.session_state["questions"]
    
    for i,q in enumerate(questions):
        st.write(f"**Câu {i + 1}: {q['questions']}**")
        
        #in ra các nút chọn đáp án chưa được tick sẵn, 
        # đồng thời lưu lựa chọn của người dùng theo từng key tương ứng.
        #chưa ấn nạp bài thì để giá trị mặc định là disabled=false->vẫn cho phép chọn đáp án
        st.radio(f"Đáp án câu {i+1}",q["options"],index=None,key=f"answer_{i}",disabled=st.session_state.get("submitted",False))
        
    #nút nộp bài
    if not st.session_state.get("submitted",False):
        if st.button("Nộp bài"):
            st.session_state["submitted"]=True
            st.rerun()
    
    # Chỉ chấm sau khi nộp bài
    else:
        score = 0

        for i, q in enumerate(questions):
            selected = st.session_state.get(f"answer_{i}")

            if selected is not None and selected.startswith(
                q["answer"] + "."
            ):
                score += 1
                st.success(f"Câu {i + 1}: Chính xác!")
            else:
                st.error(
                    f"Câu {i + 1}: Chưa chính xác. "
                    f"Đáp án đúng: {q['answer']}"
                )

        st.subheader(f"Kết quả: {score}/{len(questions)} câu đúng")

        if st.button("Làm lại"):
            st.session_state["submitted"] = False

            for i in range(len(questions)):
                st.session_state.pop(f"answer_{i}", None)

            st.rerun()
        