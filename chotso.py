import streamlit as st
import pandas as pd
import io

# 1. Cấu hình giao diện
st.set_page_config(page_title="Hệ thống Chốt Sổ BHXH", layout="wide")
st.title("📂 Hệ thống Chốt Sổ: Trích xuất Dữ liệu Thông minh")
st.markdown("---")

# 2. Upload file
uploaded_file = st.file_uploader("Tải file Excel dữ liệu (Hỗ trợ .xls, .xlsx, .csv):", type=["xls", "xlsx", "csv"])

# Hàm chuyển đổi định dạng 06/2012 -> 201206
def format_date(val):
    try:
        val = str(val).strip()
        month, year = val.split('/')
        return f"{year}{month.zfill(2)}"
    except:
        return val

if uploaded_file:
    try:
        # 3. Đọc dữ liệu
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_excel(uploaded_file, header=3) # Nếu csv cần chuyển đổi dạng bảng
        else:
            df = pd.read_excel(uploaded_file, header=3)
        
        # Làm sạch tên cột
        df.columns = [str(c).strip() for c in df.columns]
        
        # Lấy Mã số BHXH từ dòng 2 (index 2)
        meta = pd.read_excel(uploaded_file, header=None)
        bhxh_val = meta.iloc[2, 1] 

        # 4. Nhập từ khóa
        tu_khoa = st.text_input("Nhập Mã đơn vị (Từ khóa) để quét:")

        if st.button("Xử lý và Xuất kết quả"):
            # Lọc dữ liệu theo Mã đơn vị
            filtered = df[df['Mã đơn vị'].astype(str).str.strip() == tu_khoa.strip()]
            
            if not filtered.empty:
                # Trích xuất
                tu_thang = format_date(filtered['Từ tháng'].iloc[0])
                den_thang = format_date(filtered['Đến tháng'].iloc[-1])
                
                # Tạo bảng kết quả
                result_df = pd.DataFrame([{
                    "STT": 1,
                    "MA_SO_BHXH": bhxh_val,
                    "MA_DON_VI": tu_khoa,
                    "TU_THANG": tu_thang,
                    "DEN_THANG": den_thang
                }])
                
                # Hiển thị
                st.success("✅ Trích xuất thành công!")
                st.table(result_df)
                
                # Export file
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    result_df.to_excel(writer, index=False, sheet_name='KetQua')
                
                st.download_button(
                    label="📥 Tải file kết quả .xlsx",
                    data=output.getvalue(),
                    file_name="Ket_qua_Chot_so.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.error("Không tìm thấy mã đơn vị này. Vui lòng kiểm tra lại từ khóa!")
                
    except Exception as e:
        st.error(f"Đã xảy ra lỗi kỹ thuật: {e}")
        st.info("Lời khuyên: Hãy kiểm tra file Excel xem cột 'Mã đơn vị', 'Từ tháng', 'Đến tháng' đã đúng tên chưa.")
