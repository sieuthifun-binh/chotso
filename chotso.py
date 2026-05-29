import streamlit as st
import pandas as pd
import io

# Tối ưu hóa: Dùng thư viện nhanh nhất để đọc file
def process_data(file_input, target_code):
    # Đọc file bỏ qua header rác
    df = pd.read_excel(file_input, header=None)
    
    # Tìm tọa độ các dòng bắt đầu vùng (nơi có 'Mã số BHXH')
    # Giả sử từ khóa này nằm ở cột 0 (cột A)
    anchor_indices = df[df[0].astype(str).str.contains("Mã số BHXH", na=False)].index.tolist()
    
    results = []
    
    for i, start_idx in enumerate(anchor_indices):
        # Xác định phạm vi vùng (từ start_idx đến start_idx của vùng tiếp theo)
        end_idx = anchor_indices[i+1] if i + 1 < len(anchor_indices) else len(df)
        block = df.iloc[start_idx:end_idx]
        
        # Trích xuất thông tin
        # Dòng 0: Mã số BHXH, Dòng 1: Mã đơn vị
        bhxh = str(block.iloc[0, 1])
        ma_dv = str(block.iloc[1, 1]).strip()
        
        # Chỉ xử lý nếu khớp mã đơn vị (hoặc nếu để trống thì lấy tất cả)
        if not target_code or target_code.upper() in ma_dv.upper():
            # Lấy các dòng dữ liệu (thường bắt đầu sau 2-3 dòng tiêu đề)
            data_rows = block.iloc[2:] 
            data_rows = data_rows[data_rows[2].notna()] # Bỏ dòng trống
            
            if not data_rows.empty:
                # Đảm bảo định dạng YYYYMM
                def clean_month(val):
                    try:
                        val = str(val).split('.')[0] # Bỏ phần thập phân nếu có
                        m, y = val.split('/')
                        return f"{y}{m.zfill(2)}"
                    except: return val
                
                results.append({
                    "MA_SO_BHXH": bhxh,
                    "MA_DON_VI": ma_dv,
                    "TU_THANG": clean_month(data_rows.iloc[0, 2]),
                    "DEN_THANG": clean_month(data_rows.iloc[-1, 3])
                })
    return pd.DataFrame(results)

# Giao diện chính
st.title("⚡ Quét dữ liệu siêu tốc")
file = st.file_uploader("Tải file Excel:")
code = st.text_input("Mã đơn vị (để trống để quét sạch):")

if st.button("Quét ngay"):
    if file:
        final_df = process_data(file, code)
        st.dataframe(final_df)
        
        # Xuất file nhanh
        buf = io.BytesIO()
        final_df.to_excel(buf, index=False)
        st.download_button("📥 Tải file kết quả", buf.getvalue(), "Ket_qua_quet_nhanh.xlsx")
