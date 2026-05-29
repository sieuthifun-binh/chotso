
import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Chốt Sổ Batch Processor", layout="wide")
st.title("🚀 Chốt Sổ: Xử lý hàng loạt (Batch Processing)")

uploaded_file = st.file_uploader("Tải file Excel dữ liệu:", type=["xlsx"])

def format_date(date_str):
    """Chuyển 06/2012 -> 201206"""
    try:
        # Xử lý trường hợp dữ liệu là string hoặc date
        date_str = str(date_str)
        month, year = date_str.split('/')
        return f"{year}{month.zfill(2)}"
    except:
        return date_str

if uploaded_file:
    if st.button("Xử lý hàng loạt toàn bộ file"):
        # Đọc file, bỏ qua header nếu cần (header=3 dựa trên ảnh)
        df = pd.read_excel(uploaded_file, header=3) 
        
        # Giả định cột: 1=Mã đơn vị, 2=Từ tháng, 3=Đến tháng
        # Chúng ta rename để dễ xử lý
        df.columns = ['STT', 'MA_DV', 'TU_THANG', 'DEN_THANG', 'LOAI', 'PA', 'BHXH', 'BHTN', 'CHUC_DANH', 'LUONG', 'LUONG_TN', 'HSL']
        
        # Trích xuất BHXH từ dòng đầu tiên (nếu có)
        bhxh_val = pd.read_excel(uploaded_file, header=None).iloc[2, 1] 
        
        # Nhóm dữ liệu theo Mã đơn vị
        results = []
        for ma_dv, group in df.groupby('MA_DV'):
            if pd.isna(ma_dv): continue
            
            tu_thang = format_date(group['TU_THANG'].iloc[0])
            den_thang = format_date(group['DEN_THANG'].iloc[-1])
            
            results.append({
                "MA_SO_BHXH": bhxh_val,
                "MA_DON_VI": ma_dv,
                "TU_THANG": tu_thang,
                "DEN_THANG": den_thang
            })
        
        final_df = pd.DataFrame(results)
        st.success(f"✅ Đã xử lý xong {len(final_df)} mã đơn vị!")
        st.dataframe(final_df)
        
        # Export
        output = io.BytesIO()
        final_df.to_excel(output, index=False)
        st.download_button("📥 Tải danh sách kết quả", output.getvalue(), "Ket_qua_chot_so.xlsx")
