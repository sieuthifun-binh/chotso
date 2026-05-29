import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Chốt Sổ Batch Processor", layout="wide")
st.title("🚀 Hệ thống Chốt Sổ: Quét toàn bộ file")

uploaded_file = st.file_uploader("Tải file Excel/CSV:", type=["xls", "xlsx", "csv"])

# Hàm chuẩn hóa tháng/năm
def format_date(val):
    try:
        val = str(val).strip()
        month, year = val.split('/')
        return f"{year}{month.zfill(2)}"
    except: return val

if uploaded_file:
    try:
        # Đọc dữ liệu
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_excel(uploaded_file, header=3)
        else:
            df = pd.read_excel(uploaded_file, header=3)
            
        df.columns = [str(c).strip() for c in df.columns]
        meta = pd.read_excel(uploaded_file, header=None) if not uploaded_file.name.endswith('.csv') else pd.read_csv(uploaded_file, header=None)
        bhxh_val = meta.iloc[2, 1] 

        # Ô nhập từ khóa (có thể nhập nhiều, phân tách bằng dấu phẩy)
        tu_khoa = st.text_input("Nhập Mã đơn vị (Từ khóa) - Để trống để quét toàn bộ file:")

        if st.button("Quét toàn bộ dữ liệu"):
            # Lọc dữ liệu: Nếu để trống thì lấy tất cả, nếu có từ khóa thì lọc theo mã
            # .str.upper() giúp không phân biệt hoa thường
            data_to_process = df.copy()
            if tu_khoa:
                list_tu_khoa = [k.strip().upper() for k in tu_khoa.split(',')]
                data_to_process = data_to_process[data_to_process['Mã đơn vị'].astype(str).str.upper().isin(list_tu_khoa)]

            if not data_to_process.empty:
                # GroupBy để xử lý hàng loạt: nhặt dòng đầu và cuối của mỗi mã
                results = []
                for ma_dv, group in data_to_process.groupby('Mã đơn vị'):
                    results.append({
                        "MA_SO_BHXH": bhxh_val,
                        "MA_DON_VI": ma_dv,
                        "TU_THANG": format_date(group['Từ tháng'].iloc[0]),
                        "DEN_THANG": format_date(group['Đến tháng'].iloc[-1])
                    })
                
                final_df = pd.DataFrame(results)
                final_df.insert(0, 'STT', range(1, len(final_df) + 1))
                
                st.success(f"✅ Đã tìm thấy {len(final_df)} mã đơn vị!")
                st.dataframe(final_df)
                
                # Export
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    final_df.to_excel(writer, index=False)
                st.download_button("📥 Tải kết quả hàng loạt", output.getvalue(), "Ket_qua_hang_loat.xlsx")
            else:
                st.warning("Không tìm thấy dữ liệu phù hợp.")
    except Exception as e:
        st.error(f"Lỗi hệ thống: {e}")
