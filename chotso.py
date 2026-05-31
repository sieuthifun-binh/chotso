import streamlit as st
import pandas as pd
import io

# =========================================================================
# 1. CẤU HÌNH GIAO DIỆN CHUẨN ENTERPRISE
# =========================================================================
st.set_page_config(
    page_title="Chốt Sổ Pro v2.0", 
    layout="wide", 
    page_icon="💼",
    initial_sidebar_state="expanded"
)

# Sử dụng st.html để nhúng CSS an toàn (Hàm này được Streamlit cho phép chính thức)
st.html("""
    <style>
        .block-container { padding-top: 2rem !important; padding-bottom: 2rem !important; }
        .stButton>button { width: 100%; border-radius: 8px; height: 3em; font-weight: bold; }
        div[data-testid="stMetricValue"] { font-size: 28px; color: #1E88E5; }
    </style>
""")

# =========================================================================
# 2. THANH SIDEBAR (BẢNG ĐIỀU KHIỂN TRÁI)
# =========================================================================
with st.sidebar:
    st.markdown("## ⚙️ BẢNG ĐIỀU KHIỂN")
    st.subheader("Cấu hình bộ lọc")
    
    # Gom bộ lọc vào Sidebar để màn hình chính gọn gàng hơn
    tu_khoa = st.text_input(
        "Mã đơn vị cần lọc:", 
        placeholder="Ví dụ: NQT0000",
        help="Để trống nếu bạn muốn quét và gom nhóm tất cả các mã đơn vị có trong file."
    ).strip()
    
    st.markdown("---")
    st.markdown("### 📘 Hướng dẫn nhanh:")
    st.caption("1. Tải file xuất từ hệ thống TST (.xlsx, .xls, .csv).")
    st.caption("2. Nhập mã đơn vị ở ô phía trên (nếu cần lọc cụ thể).")
    st.caption("3. Bấm 'BẮT ĐẦU PHÂN TÍCH' và tải file kết quả.")
    st.info("💡 Hệ thống tự động nhận diện cấu hình Dòng cha (Mã BHXH) và Dòng con (Chi tiết).")

# =========================================================================
# 3. MÀN HÌNH CHÍNH (MAIN CONTENT)
# =========================================================================
# Đã thay thế st.markdown HTML bằng hàm bản địa của Streamlit để chống lỗi bảo mật
st.title("🎯 HỆ THỐNG XỬ LÝ & LỌC DỮ LIỆU BHXH TỰ ĐỘNG")
st.subheader("Giải pháp tối ưu hóa dữ liệu chốt sổ - Tốc độ cao, chính xác tuyệt đối")
st.markdown("---")

# Hàm bổ trợ chuyển đổi ngày tháng
def format_date(val):
    if pd.isna(val): return ""
    try:
        val = str(val).strip()
        if '/' in val:
            month, year = val.split('/')
            return f"{year}{month.zfill(2)}"
        return val
    except Exception: return val

# Hàm đọc file tối ưu hóa với Cache
@st.cache_data(ttl=3600)
def load_and_parse_data(file_bytes, file_name):
    if file_name.endswith(('.xls', '.xlsx')):
        return pd.read_excel(io.BytesIO(file_bytes), header=None)
    elif file_name.endswith('.csv'):
        return pd.read_csv(io.BytesIO(file_bytes), header=None)
    return None

# Khu vực Tải tệp lên
uploaded_file = st.file_uploader(
    "📥 Kéo và thả file dữ liệu vào đây:", 
    type=["xls", "xlsx", "csv"]
)

if uploaded_file:
    file_bytes = uploaded_file.read()
    df = load_and_parse_data(file_bytes, uploaded_file.name)
    
    if df is not None and not df.empty:
        # Khởi tạo Session State để giữ trạng thái dữ liệu khi bấm nút hoặc tương tác
        if 'processed_data' not in st.session_state:
            st.session_state.processed_data = None
        if 'total_blocks' not in st.session_state:
            st.session_state.total_blocks = 0

        # Phân tách không gian bằng cột cho nút bấm hành động
        col_space1, col_btn, col_space2 = st.columns([1, 2, 1])
        with col_btn:
            execute_click = st.button("🚀 BẮT ĐẦU PHÂN TÍCH VÀ TRÍCH XUẤT", type="primary")

        if execute_click:
            # Sử dụng st.status để hiển thị tiến trình chuyên nghiệp thay vì spinner đơn điệu
            with st.status("🔄 Hệ thống đang xử lý cấu hình dữ liệu...", expanded=True) as status:
                df[1] = df[1].astype(str).str.strip()
                anchor_indices = df[df[1].str.contains(r'^\d{9,10}$', na=False)].index.tolist()
                
                if not anchor_indices:
                    status.update(label="❌ Thất bại: Không tìm thấy dữ liệu hợp lệ!", state="error")
                    st.error("Không tìm thấy cột chứa 'Mã số BHXH' (định dạng 9-10 chữ số liền nhau). Vui lòng kiểm tra lại cấu trúc file mẫu.")
                else:
                    anchor_indices.append(len(df))
                    final_results = []
                    
                    for i in range(len(anchor_indices) - 1):
                        start, end = anchor_indices[i], anchor_indices[i+1]
                        block = df.iloc[start:end]
                        bhxh_val = block.iloc[0, 1] 
                        
                        # Lọc các dòng con chứa dữ liệu thời gian (định dạng tháng/năm) ở cột số 2
                        data_rows = block[block[2].astype(str).str.contains(r'\d{1,2}/\d{4}', na=False)].copy()
                        if data_rows.empty: continue
                            
                        for ma_dv, group in data_rows.groupby(1):
                            ma_dv_str = str(ma_dv).strip()
                            if not tu_khoa or tu_khoa.upper() in ma_dv_str.upper():
                                # Phòng thủ lỗi bằng cách kiểm tra số lượng dòng thực tế
                                tu_thang_raw = group[2].iloc[0] if len(group) > 0 else ""
                                den_thang_raw = group[3].iloc[-1] if len(group) > 0 else ""
                                
                                final_results.append({
                                    "MA_SO_BHXH": bhxh_val,
                                    "MA_DON_VI": ma_dv_str,
                                    "TU_THANG": format_date(tu_thang_raw),
                                    "DEN_THANG": format_date(den_thang_raw)
                                })
                    
                    st.session_state.processed_data = final_results
                    st.session_state.total_blocks = len(anchor_indices) - 1
                    status.update(label="✅ Xử lý hoàn tất!", state="complete")

        # =========================================================================
        # 4. KHU VỰC HIỂN THỊ KẾT QUẢ NÂNG CAO (Giữ trạng thái nhờ Session State)
        # =========================================================================
        if st.session_state.processed_data is not None:
            st.markdown("### 📊 Kết quả phân tích")
            
            if st.session_state.processed_data:
                res_df = pd.DataFrame(st.session_state.processed_data)
                res_df.insert(0, 'STT', range(1, len(res_df) + 1))
                
                # Widget số liệu (Metrics) hiển thị tổng quan dữ liệu
                m1, m2, m3 = st.columns(3)
                with m1:
                    st.metric(label="Tổng số hồ sơ (Khối) đã quét", value=st.session_state.total_blocks)
                with m2:
                    st.metric(label="Số dòng kết quả thỏa mãn", value=len(res_df))
                with m3:
                    st.metric(label="Bộ lọc hiện tại", value=tu_khoa if tu_khoa else "TẤT CẢ")
                
                st.markdown("<br>", unsafe_with_html=True)
                
                # Chia Tabs tách biệt giữa việc Xem dữ liệu và Tải tệp xuống
                tab_view, tab_download = st.tabs(["👀 Xem trước dữ liệu", "📥 Xuất dữ liệu & Tải về"])
                
                with tab_view:
                    st.caption("Mẹo: Bạn có thể nhấn vào tiêu đề cột để sắp xếp hoặc nhấn đôi vào ô để sao chép nhanh.")
                    st.dataframe(res_df, use_container_width=True, hide_index=True)
                
                with tab_download:
                    st.info("File xuất ra đã được hệ thống tự động tối ưu hóa định dạng độ rộng cột (Auto-fit width).")
                    
                    # Tạo file Excel trong bộ nhớ bằng XlsxWriter
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        res_df.to_excel(writer, index=False, sheet_name="Ket_Qua_Chot_So")
                        worksheet = writer.sheets['Ket_Qua_Chot_So']
                        
                        # Tự động căn lề độ rộng cột dựa trên dữ liệu dài nhất
                        for idx, col in enumerate(res_df.columns):
                            max_len = max(res_df[col].astype(str).map(len).max(), len(col)) + 4
                            worksheet.set_column(idx, idx, max_len)
                    
                    st.download_button(
                        label="📥 BẤM VÀO ĐÂY ĐỂ TẢI FILE EXCEL (.XLSX)", 
                        data=output.getvalue(), 
                        file_name=f"Ket_qua_chot_so_{tu_khoa if tu_khoa else 'ALL'}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="secondary"
                    )
            else:
                st.warning("⚠️ Hệ thống đã quét hết file nhưng không tìm thấy mã đơn vị nào trùng khớp với từ khóa của bạn.")
    else:
        st.error("❌ Tệp lỗi: Tệp tải lên trống hoặc bị sai cấu trúc bảng dữ liệu.")
