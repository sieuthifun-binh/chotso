import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Chốt Sổ Pro", layout="wide")
st.title("🎯 Hệ thống Chốt Sổ tự động")

uploaded_file = st.file_uploader("Tải file dữ liệu (.xls, .xlsx, .csv):", type=["xls", "xlsx", "csv"])

def format_date(val):
    """Chuyển 06/2012 thành 201206"""
    try:
        val = str(val).strip()
        month, year = val.split('/')
        return f"{year}{month.zfill(2)}"
    except: return val

if uploaded_file:
    # 1. Đọc file với header=None để kiểm soát toàn bộ tọa độ
    df = pd.read_excel(uploaded_file, header=None) if not uploaded_file.name.endswith('.csv') else pd.read_csv(uploaded_file, header=None)
    
    # 2. Tìm điểm neo (các dòng chứa "Mã số BHXH")
    # File mẫu của bạn có cột 1 chứa Mã số BHXH
    anchor_indices = df[df[1].astype(str).str.contains(r'\d{9,10}', na=False)].index.tolist()
    anchor_indices.append(len(df)) # Kết thúc file

    tu_khoa = st.text_input("Nhập mã đơn vị (Ví dụ: NQT0000) - Để trống để quét toàn bộ:")

    if st.button("Quét và Xuất kết quả"):
        final_results = []
        
        # 3. Quét qua từng khối dữ liệu
        for i in range(len(anchor_indices) - 1):
            start, end = anchor_indices[i], anchor_indices[i+1]
            block = df.iloc[start:end]
            
            bhxh_val = str(block.iloc[0, 1]) # Mã BHXH dòng đầu khối
            
            # Lọc dữ liệu chi tiết (bỏ qua dòng tiêu đề, lấy dòng có dữ liệu)
            # Dòng dữ liệu bắt đầu từ sau tiêu đề, chứa định dạng MM/YYYY (cột 2)
            data_rows = block[block[2].astype(str).str.contains(r'\d{1,2}/\d{4}', na=False)]
            
            # Gom nhóm các dòng theo Mã đơn vị trong khối đó
            for ma_dv, group in data_rows.groupby(1):
                ma_dv = str(ma_dv).strip()
                if not tu_khoa or tu_khoa.upper() in ma_dv.upper():
                    final_results.append({
                        "MA_SO_BHXH": bhxh_val,
                        "MA_DON_VI": ma_dv,
                        "TU_THANG": format_date(group[2].iloc[0]),
                        "DEN_THANG": format_date(group[3].iloc[-1])
                    })
        
        # 4. Xuất kết quả
        if final_results:
            res_df = pd.DataFrame(final_results)
            res_df.insert(0, 'STT', range(1, len(res_df) + 1))
            st.success(f"✅ Đã tìm thấy {len(res_df)} kết quả!")
            st.dataframe(res_df)
            
            # Export
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                res_df.to_excel(writer, index=False)
            st.download_button("📥 Tải file kết quả .xlsx", output.getvalue(), "Ket_qua_chot_so.xlsx")
        else:
            st.warning("Không tìm thấy mã đơn vị tương ứng.")
