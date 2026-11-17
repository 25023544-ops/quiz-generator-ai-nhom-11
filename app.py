import hashlib
import tempfile
from pathlib import Path
import streamlit as st

from document_processor import extract_text
from ai_summarizer import summarize
from quiz_generator import generate_questions

#HÀM KIỂM TRA CẤU TRÚC CÂU HỎI
def validate_quiz(questions):
    if not isinstance(questions,list) or not questions:
        raise ValueError("Bộ câu hỏi phải là danh sách không rỗng.")
    for i, q in enumerate(questions,start=1):
        if not isinstance(q,dict):
            raise ValueError(f"Câu {i} không phải dict.")
        question=q.get("question")
        if not isinstance(question,str) or not question.strip():
            raise ValueError(f"Câu {i} thiếu nội dung câu hỏi.")
        
        options=q.get("options")
        if not isinstance(options,list) or len(options)!=4:
            raise ValueError(f"Câu {i} có lựa chọn không hợp lệ.")
        
        if not all(isinstance(x,str) for x in options):
            raise ValueError(f"Câu {i} có đáp án không hợp lệ.")

        explanation = q.get("explanation")
        if not isinstance(explanation, str) or not explanation.strip():
            raise ValueError(f"Câu {i} thiếu phần giải thích.")

def reset_quiz():
    st.session_state["submitted"] = False

    # tăng quiz_version lên 1 sẽ làm thay đổi key của tất cả các nút radio 
    #Streamlit sẽ coi đây là một bộ nút radio hoàn toàn mới và tự động đưa chúng về trạng thái chưa chọn gì.
    st.session_state["quiz_version"] = (
        st.session_state.get("quiz_version", 0) + 1
    )
        
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
    "Đang sử dụng các module thật: "
    "đọc tài liệu, tóm tắt bằng Gemini và tạo câu hỏi AI."
)

#1.Nhận file
uploaded_file=st.file_uploader("Tải tài liệu PDF/TXT",type=["pdf","txt"],max_upload_size=20)

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
    
    reset_quiz()
            
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
            with st.spinner("Đang tạo câu hỏi bằng Gemini..."):
                result=generate_questions(st.session_state["text"],so_cau=5)
                
            validate_quiz(result)
            
            st.session_state["questions"]=result
            
            reset_quiz()
            
            st.success(f"Đã tạo {len(result)} câu hỏi!")
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
    submitted=st.session_state.get("submitted",False)
    
    
    version = st.session_state.get("quiz_version", 0)
    for i,q in enumerate(questions):
        st.write(f"**Câu {i + 1}: {q['question']}**")
        
        options_hien_thi = [
            f"{label}. {option}"
            for label, option in zip("ABCD", q["options"])
        ]

        
        #in ra các nút chọn đáp án chưa được tick sẵn, 
        # đồng thời lưu lựa chọn của người dùng theo từng key tương ứng.
        #chưa ấn nạp bài thì để giá trị mặc định là disabled=false->vẫn cho phép chọn đáp án
        st.radio(f"Đáp án câu {i+1}",options_hien_thi,index=None,key=f"answer_{version}_{i}",disabled=submitted)
        
    #nút nộp bài
    if not submitted:
        if st.button("Nộp bài"):
            st.session_state["submitted"]=True
            st.rerun()
    
    # Chỉ chấm sau khi nộp bài
    else:
        score = 0

        for i, q in enumerate(questions):
            selected = st.session_state.get(f"answer_{version}_{i}")
            
            dap_an_chon = (
                selected.split(".", 1)[0]
                if selected is not None
                else None
            )


            if dap_an_chon == q["answer"]: 
            
                score += 1
                st.success(f"Câu {i + 1}: Chính xác!")
            else:
                st.error(
                    f"Câu {i + 1}: Chưa chính xác. "
                    f"Đáp án đúng: {q['answer']}"
                )
            # Hiển thị giải thích từ AI
            st.caption(
                f"Giải thích: {q['explanation']}"
            )

        st.subheader(f"Kết quả: {score}/{len(questions)} câu đúng")

        st.button("Làm lại", on_click=reset_quiz)
        
        
#Mẹo phổ biến trong Streamlit: 
# Trong Streamlit, các widget như st.radio ghi nhớ lựa chọn của người dùng 
# dựa vào tham số key. Khi gán key động theo phiên bản việc tăng quiz_version
# lên 1 sẽ làm thay đổi key của tất cả các nút radio.
# Streamlit sẽ coi đây là một bộ nút radio hoàn toàn mới và tự động đưa chúng
# về trạng thái chưa chọn gì.
        