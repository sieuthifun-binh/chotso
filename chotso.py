import streamlit as st
import pandas as pd
import io

# 1. Cấu hình trang chuẩn Enterprise
st.set_page_config(page_title="Chốt Sổ Pro v2.7", layout="wide", page_icon="🎯")

# Nhúng CSS an toàn qua st.html (Hàm này được Streamlit hỗ trợ chính thức, không lo bị chặn)
st.html("""
    <style>
        .block-container { padding-top: 2rem !important; padding-bottom: 2rem !important; }
        .stButton>button { width: 100%; border-radius: 8px; height: 3em; font-weight: bold; }
        div[data-testid="stMetricValue"] { font-size: 28px; color: #1E88E5; }
    </style>
""")

st.title("🎯 Hệ thống Lọc Dữ Liệu Tự Động Pro")
st.subheader("Phiên bản tối ưu hóa hiệu năng Ver 1.0 ")
st.markdown("---")

def format_date(val):
    """Chuyển đổi an toàn định dạng 'MM/YYYY' thành 'YYYYMM'"""
    if pd.isna(val): return ""
    try:
        val = str(val).strip()
        if '/' in val:
            month, year = val.split('/')
            return f"{year}{month.zfill(2)}"
        return val
    except: 
        return val

# --- HÀM ĐỌC FILE TỐI ƯU HÓA CACHE ĐA PHIÊN ---
@st.cache_data(ttl=1800, show_spinner=False)
def load_data_optimized(uploaded_file):
    try:
        if not uploaded_file.name.endswith('.csv'):
            return pd.read_excel(uploaded_file, header=None)
        else:
            # Tự động nhận diện dấu phân cách thông minh cho CSV
            file_bytes = uploaded_file.getvalue()
            df = pd.read_csv(io.BytesIO(file_bytes), header=None)
            if df.shape[1] <= 1:
                df = pd.read_csv(io.BytesIO(file_bytes), header=None, sep=';')
            return df
    except Exception:
        return None

# Khởi tạo Session State cô lập cho từng người dùng
if 'final_df_results' not in st.session_state:
    st.session_state.final_df_results = None
if 'total_blocks' not in st.session_state:
    st.session_state.total_blocks = 0

uploaded_file = st.file_uploader("Tải file dữ liệu (.xls, .xlsx, .csv):", type=["xls", "xlsx", "csv"])

if uploaded_file:
    # Đọc dữ liệu siêu tốc bằng bộ nhớ Cache
    df = load_data_optimized(uploaded_file)
    
    if df is not None and df.shape[1] >= 3:
        
        with st.form(key="filter_form"):
            tu_khoa = st.text_input(
                "Nhập mã đơn vị (Ví dụ: NQT0000) - Để trống để quét toàn bộ:",
                help="Nhập xong từ khóa rồi bấm nút Quét bên dưới. Hệ thống sẽ không bị tải lại liên tục khi bạn đang gõ."
            ).strip()
            
            submit_button = st.form_submit_button(label="🚀 BẮT ĐẦU QUÉT VÀ TRÍCH XUẤT", type="primary")

        if submit_button:
            with st.status("🔄 Hệ thống đang xử lý dữ liệu...", expanded=True) as status:
                
                # Ép kiểu chuỗi 1 lần duy nhất ngoài vòng lặp để giải phóng RAM/CPU
                df[1] = df[1].astype(str).str.strip()
                df[2] = df[2].astype(str).str.strip()
                
                # Định vị chính xác các dòng chứa Mã số BHXH (9-10 chữ số)
                anchor_indices = df[df[1].str.contains(r'^\d{9,10}$', na=False)].index.tolist()
                
                if not anchor_indices:
                    status.update(label="❌ Thất bại: Không tìm thấy Mã số BHXH!", state="error")
                    st.error("Không tìm thấy dữ liệu 'Mã số BHXH' hợp lệ tại cột thứ 2. Vui lòng kiểm tra lại cấu trúc file.")
                else:
                    anchor_indices.append(len(df))
                    final_results = []
                    
                    # Quét qua từng khối dữ liệu
                    for i in range(len(anchor_indices) - 1):
                        start, end = anchor_indices[i], anchor_indices[i+1]
                        block = df.iloc[start:end]
                        
                        # Tìm ô chứa số đầu tiên trong cột 1 để làm Mã BHXH
                        bhxh_row = block[block[1].str.contains(r'^\d{9,10}$', na=False)]
                        bhxh_val = str(bhxh_row.iloc[0, 1]) if not bhxh_row.empty else str(block.iloc[0, 1])
                        
                        # Lọc các dòng dữ liệu chi tiết
                        data_rows = block[block[2].str.contains(r'\d{1,2}/\d{4}', na=False)]
                        if data_rows.empty: 
                            continue
                        
                        # Gom nhóm theo mã đơn vị
                        for ma_dv, group in data_rows.groupby(1):
                            ma_dv_str = str(ma_dv).strip()
                            if not tu_khoa or tu_khoa.upper() in ma_dv_str.upper():
                                # Trích xuất an toàn chống sập dòng rỗng
                                tu_thang_raw = group[2].iloc[0] if len(group) > 0 else ""
                                den_thang_raw = group[3].iloc[-1] if len(group) > 0 and df.shape[1] > 3 else ""
                                
                                final_results.append({
                                    "MA_SO_BHXH": bhxh_val,
                                    "MA_DON_VI": ma_dv_str,
                                    "TU_THANG": format_date(tu_thang_raw),
                                    "DEN_THANG": format_date(den_thang_raw)
                                })
                    
                    # Lưu trữ kết quả an toàn vào State riêng biệt của phiên truy cập
                    if final_results:
                        res_df = pd.DataFrame(final_results)
                        res_df.insert(0, 'STT', range(1, len(res_df) + 1))
                        st.session_state.final_df_results = res_df
                    else:
                        st.session_state.final_df_results = "EMPTY"
                        
                    st.session_state.total_blocks = len(anchor_indices) - 1
                    status.update(label="✅ Xử lý hoàn tất!", state="complete")

        # --- HIỂN THỊ KẾT QUẢ PHẲNG (KHÔNG DÙNG TAB) ---
        if st.session_state.final_df_results is not None:
            if isinstance(st.session_state.final_df_results, pd.DataFrame):
                current_df = st.session_state.final_df_results
                
                # Bảng thông số trực quan
                m1, m2 = st.columns(2)
                with m1: st.metric(label="📊 Tổng số hồ sơ đã quét", value=st.session_state.total_blocks)
                with m2: st.metric(label="✅ Kết quả tìm thấy", value=len(current_df))
                
                st.write("")
                
                # 1. Hiển thị bảng xem trước dữ liệu lên trước
                st.markdown("### 👀 Xem trước dữ liệu kết quả:")
                st.dataframe(current_df, use_container_width=True, hide_index=True)
                
                st.write("")
                
                # 2. Đưa nút tải file Excel xuống ngay dưới mục hiển thị kết quả
                st.markdown("### 📥 Xuất bản file kết quả:")
                
                # Tạo file Excel bằng XlsxWriter trong bộ nhớ ẩn
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    current_df.to_excel(writer, index=False, sheet_name="Ket_Qua_Chot_So")
                    worksheet = writer.sheets['Ket_Qua_Chot_So']
                    # Tự động căn rộng cột
                    for idx, col in enumerate(current_df.columns):
                        max_len = max(current_df[col].astype(str).map(len).max(), len(col)) + 4
                        worksheet.set_column(idx, idx, max_len)
                
                st.download_button(
                    label="📥 BẤM VÀO ĐÂY ĐỂ TẢI FILE EXCEL KẾT QUẢ (.XLSX)", 
                    data=output.getvalue(), 
                    file_name="Ket_qua_chot_so_FINAL.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
            elif st.session_state.final_df_results == "EMPTY":
                st.warning("⚠️ Không tìm thấy mã đơn vị tương ứng trong tệp dữ liệu.")
    else:
        st.error("❌ Cấu trúc file không hợp lệ hoặc file trống. Vui lòng kiểm tra lại file đầu vào!")
st.markdown("<br><hr><p style='text-align: center; color: #475569; font-size: 20px; font-weight: bold; font-family: sans-serif;'>Copyright © Vũ Quốc Bình :)</p>", unsafe_allow_html=True)
