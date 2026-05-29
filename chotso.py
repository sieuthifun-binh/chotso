import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Chốt Sổ Universal", layout="wide")
st.title("📂 Chốt Sổ: Hỗ trợ mọi phiên bản Excel")

uploaded_file = st.file_uploader("Tải file Excel (hỗ trợ .xls, .xlsx):", type=["xlsx", "xls"])

if uploaded_file:
    try:
        # Cải tiến: Tự động chọn engine dựa trên đuôi file
        file_ext = uploaded_file.name.split('.')[-1].lower()
        
        if file_ext == 'xls':
            # Đối với Excel 2003 cũ
            df = pd.read_excel(uploaded_file, header=3, engine='xlrd')
        else:
            # Đối với Excel 2007 trở lên
            df = pd.read_excel(uploaded_file, header=3, engine='openpyxl')
            
        st.success(f"Đã đọc thành công file {uploaded_file.name}")
        st.dataframe(df.head())
        
        # ... logic xử lý Batch Processing như cũ ...
        
    except Exception as e:
        st.error(f"Lỗi đọc file: {e}")
        st.info("Lưu ý: Nếu dùng file .xls, hãy chắc chắn đã cài thư viện 'xlrd' trong requirements.txt")
