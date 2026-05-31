import streamlit as st
import pandas as pd
import io
import re

# =================================================================
# 1. CẤU HÌNH GIAO DIỆN HỆ MÀU SẮC PREMIUM ENTERPRISE (V3.9)
# =================================================================
st.set_page_config(page_title="Chốt Sổ Pro v3.9", layout="wide", page_icon="🎯")

st.html("""
    <style>
        .block-container { padding-top: 1.5rem !important; padding-bottom: 2rem !important; }
        .stForm { border-radius: 12px !important; border: 1px solid #E0E0E0 !important; padding: 1.5rem !important; background-color: #F8F9FA; }
        .stButton>button { width: 100%; border-radius: 8px; height: 3em; font-weight: bold; transition: all 0.3s ease; }
        div[data-testid="stMetricValue"] { font-size: 32px !important; font-weight: 700 !important; color: #0066CC !important; }
        div[data-testid="stMetricLabel"] { font-size: 14px !important; color: #555555 !important; font-weight: 600; }
    </style>
""")

st.markdown("""
    <div style="background: linear-gradient(135deg, #1E3A8A 0%, #0D1B3E 100%); padding: 25px; border-radius: 12px; color: white; margin-bottom: 25px;">
        <h1 style="margin: 0; font-size: 28px; font-weight: 700;">🎯 Hệ thống Lọc & Đối Chiếu Dữ Liệu Tự Động</h1>
        <p style="margin: 5px 0 0 0; opacity: 0.9; font-size: 14px;">Phiên bản v1.0: Định dạng chuẩn hóa đầu ra YYYYMM (Ví dụ: 202605) cho tất cả các tệp xuất bản</p>
    </div>
""", unsafe_allow_html=True)

# =================================================================
# 2. BỘ ĐỊNH DẠNG VÀ PHÒNG THỦ DỮ LIỆU CẤP CAO (PREMIUM UTILITIES)
# =================================================================
def parse_to_datetime(val):
    """Chuyển đổi mọi định dạng ngày tháng về đối tượng Datetime để so sánh trục thời gian"""
    if pd.isna(val): return None
    val_str = str(val).strip().replace('.', '').replace('-', '')
    
    if len(val_str) == 8 and val_str.isdigit():
        val_str = val_str[:6]
        
    try:
        if '/' in val_str:
            month, year = val_str.split('/')
            return pd.to_datetime(f"{year}-{month.zfill(2)}-01")
        elif len(val_str) == 6 and val_str.isdigit():
            return pd.to_datetime(f"{val_str[:4]}-{val_str[4:]}-01")
        else:
            return pd.to_datetime(val_str)
    except:
        return None

def format_dt_to_str(dt_obj):
    """[ÉP KIỂU ĐẦU RA]: Khóa chặt định dạng chuỗi YYYYMM (Ví dụ: 202605)"""
    if dt_obj is None or pd.isna(dt_obj): return ""
    return str(dt_obj.strftime("%Y%m"))

def get_next_month_from_dt(dt_obj):
    """Tính tháng tiếp theo và trả về chuỗi định dạng YYYYMM (Ví dụ: 202605)"""
    if dt_obj is None or pd.isna(dt_obj): return ""
    try:
        next_month_dt = dt_obj + pd.Timedelta(days=32)
        return str(next_month_dt.strftime("%Y%m"))
    except:
        return ""

def clean_string_code(val):
    """Xử lý triệt để phần thập phân lai tạp của số sổ hoặc mã đơn vị từ Pandas"""
    if pd.isna(val): return ""
    val_str = str(val).strip()
    if re.match(r'^\d+\.0$', val_str):
        return val_str[:-2]
    return val_str

def normalize_column_name(col_name):
    """Xóa bỏ khoảng trắng thừa, ký tự xuống dòng dính trong tên cột"""
    return re.sub(r'\s+', '', str(col_name))

# =================================================================
# 3. THUẬT TOÁN ĐỌC FILE LÕI (CORE ENGINES)
# =================================================================
@st.cache_data(ttl=300, show_spinner=False)
def parse_file_1_block(uploaded_file):
    """Đọc File 1 dạng khối thô và định dạng sẵn cột ngày tháng thành YYYYMM"""
    try:
        if not uploaded_file.name.endswith('.csv'):
            df = pd.read_excel(uploaded_file, header=None, dtype=str)
        else:
            file_bytes = uploaded_file.getvalue()
            df = pd.read_csv(io.BytesIO(file_bytes), header=None, dtype=str)
            if df.shape[1] <= 1:
                df = pd.read_csv(io.BytesIO(file_bytes), header=None, sep=';', dtype=str)
                
        if df is None or df.shape[1] < 4:
            return None
            
        df[1] = df[1].apply(clean_string_code)
        df[2] = df[2].apply(clean_string_code)
        
        anchor_indices = df[df[1].str.contains(r'^\d{9,10}$', na=False)].index.tolist()
        if not anchor_indices:
            return None
            
        anchor_indices.append(len(df))
        results = []
        
        for i in range(len(anchor_indices) - 1):
            start, end = anchor_indices[i], anchor_indices[i+1]
            block = df.iloc[start:end]
            
            bhxh_row = block[block[1].str.contains(r'^\d{9,10}$', na=False)]
            bhxh_val = clean_string_code(bhxh_row.iloc[0, 1]) if not bhxh_row.empty else clean_string_code(block.iloc[0, 1])
            
            data_rows = block[block[2].str.contains(r'\d{1,2}/\d{4}', na=False)]
            if data_rows.empty: 
                continue
            
            for ma_dv, group in data_rows.groupby(1):
                ma_dv_str = clean_string_code(ma_dv)
                dt_tu = parse_to_datetime(group[2].iloc[0])
                dt_den = parse_to_datetime(group[3].iloc[-1]) if df.shape[1] > 3 else None
                
                # Ép chuỗi định dạng YYYYMM ngay tại đây
                results.append({
                    "MA_SO_BHXH": bhxh_val,
                    "MA_DON_VI": ma_dv_str,
                    "TU_THANG": format_dt_to_str(dt_tu),
                    "DEN_THANG": format_dt_to_str(dt_den)
                })
        
        res_df = pd.DataFrame(results)
        if not res_df.empty:
            res_df["MA_SO_BHXH"] = res_df["MA_SO_BHXH"].astype(str)
            res_df["MA_DON_VI"] = res_df["MA_DON_VI"].astype(str)
            res_df["TU_THANG"] = res_df["TU_THANG"].astype(str)
            res_df["DEN_THANG"] = res_df["DEN_THANG"].astype(str)
        return res_df
    except:
        return None

@st.cache_data(ttl=300, show_spinner=False)
def parse_file_2_flat(uploaded_file):
    """Đọc File 2 phẳng - Tìm kiếm mốc Datetime muộn nhất của từng số sổ"""
    try:
        if not uploaded_file.name.endswith('.csv'):
            df = pd.read_excel(uploaded_file, dtype=str)
        else:
            file_bytes = uploaded_file.getvalue()
            df = pd.read_csv(io.BytesIO(file_bytes), dtype=str)
            
        if df is None or df.empty:
            return None
            
        df.columns = [normalize_column_name(c) for c in df.columns]
        
        if 'soSoBhxh' not in df.columns or 'denThang' not in df.columns:
            st.error("❌ Cấu trúc File 2 lỗi: Thiếu cột 'soSoBhxh' hoặc 'denThang'.")
            return None
            
        flat_results = []
        for _, row in df.iterrows():
            sbhxh = clean_string_code(row['soSoBhxh'])
            if not sbhxh.isdigit() or len(sbhxh) < 9 or len(sbhxh) > 10: 
                continue
                
            dt_den = parse_to_datetime(row['denThang'])
            if dt_den is None: 
                continue
                
            flat_results.append({
                "MA_SO_BHXH": sbhxh,
                "DT_DEN_OBJ": dt_den
            })
            
        if not flat_results: return None
        
        df_flat = pd.DataFrame(flat_results)
        df_flat = df_flat.sort_values(by="DT_DEN_OBJ")
        dict_latest = df_flat.groupby("MA_SO_BHXH")["DT_DEN_OBJ"].last().to_dict()
        return dict_latest
    except:
        return None

# =================================================================
# 4. QUẢN LÝ BIẾN PHIÊN HỆ THỐNG
# =================================================================
if 'res_goc' not in st.session_state: st.session_state.res_goc = None
if 'res_dc' not in st.session_state: st.session_state.res_dc = None
if 'has_run' not in st.session_state: st.session_state.has_run = False

# =================================================================
# 5. KHU VỰC ĐIỀU KHIỂN CHỨC NĂNG
# =================================================================
st.markdown("### 📥 1. Khu vực nạp dữ liệu đầu vào")
col_f1, col_f2 = st.columns(2)
with col_f1:
    uploaded_file_1 = st.file_uploader("📂 Tải file dữ liệu GỐC (Dạng khối thô):", type=["xls", "xlsx", "csv"], key="file_1")
with col_f2:
    uploaded_file_2 = st.file_uploader("📊 Tải file DỮ LIỆU MỚI đối chiếu (Dạng phẳng - Ảnh 2):", type=["xls", "xlsx", "csv"], key="file_2")

if uploaded_file_1:
    df_1_parsed = parse_file_1_block(uploaded_file_1)
    
    if df_1_parsed is not None and not df_1_parsed.empty:
        with st.form(key="filter_form"):
            st.markdown("##### 🔍 2. Điều kiện trích xuất")
            tu_khoa = st.text_input("Nhập mã đơn vị cần lọc (Để trống nếu muốn quét toàn bộ file):", placeholder="Ví dụ: NQT0001, TST...").strip()
            submit_button = st.form_submit_button(label="🚀 KHỞI CHẠY HỆ THỐNG ĐỐI CHIẾU", type="primary")

        if submit_button:
            st.session_state.res_goc = None
            st.session_state.res_dc = None
            
            with st.status("🔄 Hệ thống đang xử lý thuật toán thời gian tầng sâu...", expanded=True) as status:
                # Bước 1: Trích xuất dữ liệu gốc
                if tu_khoa:
                    filtered_goc = df_1_parsed[df_1_parsed["MA_DON_VI"].str.upper().str.contains(tu_khoa.upper())].copy()
                else:
                    filtered_goc = df_1_parsed.copy()
                
                if not filtered_goc.empty:
                    filtered_goc = filtered_goc.sort_values(by=["MA_SO_BHXH", "TU_THANG"])
                    filtered_goc.insert(0, 'STT', range(1, len(filtered_goc) + 1))
                    st.session_state.res_goc = filtered_goc
                    st.session_state.has_run = True
                    
                    # Bước 2: Khớp nối và tịnh tiến trục thời gian thực với File 2
                    if uploaded_file_2:
                        df_2_latest_dt_dict = parse_file_2_flat(uploaded_file_2)
                        if df_2_latest_dt_dict:
                            adjusted_results = []
                            for _, row in filtered_goc.iterrows():
                                new_row = row.copy()
                                so_so = str(new_row["MA_SO_BHXH"]).strip()
                                
                                if so_so in df_2_latest_dt_dict:
                                    dt_obj_moi_nhat = df_2_latest_dt_dict[so_so]
                                    tu_thang_noi_tiep = get_next_month_from_dt(dt_obj_moi_nhat)
                                    if tu_thang_noi_tiep:
                                        new_row["TU_THANG"] = tu_thang_noi_tiep # Đã định dạng chuỗi YYYYMM từ hàm gốc
                                adjusted_results.append(new_row)
                                
                            if adjusted_results:
                                filtered_dc = pd.DataFrame(adjusted_results)
                                filtered_dc["MA_SO_BHXH"] = filtered_dc["MA_SO_BHXH"].astype(str)
                                filtered_dc["MA_DON_VI"] = filtered_dc["MA_DON_VI"].astype(str)
                                filtered_dc["TU_THANG"] = filtered_dc["TU_THANG"].astype(str)
                                filtered_dc["DEN_THANG"] = filtered_dc["DEN_THANG"].astype(str)
                                
                                if 'STT' in filtered_dc.columns: filtered_dc = filtered_dc.drop(columns=['STT'])
                                filtered_dc.insert(0, 'STT', range(1, len(filtered_dc) + 1))
                                st.session_state.res_dc = filtered_dc
                        else:
                            st.session_state.res_dc = None
                    else:
                        st.session_state.res_dc = None
                else:
                    st.session_state.res_goc = "EMPTY"
                    st.session_state.res_dc = None
                    st.session_state.has_run = True
                
                status.update(label="✅ Hệ thống đã hoàn thành đối chiếu!", state="complete")

        # =================================================================
        # 6. HIỂN THỊ KẾT QUẢ ĐẦY ĐỦ VÀ LUỒNG XUẤT EXCEL AN TOÀN TRUYỆT ĐỐI
        # =================================================================
        if st.session_state.has_run:
            st.markdown("---")
            st.markdown("### 📊 3. Kết quả phân tích dữ liệu thực tế")
            
            if isinstance(st.session_state.res_goc, pd.DataFrame):
                m1, m2 = st.columns(2)
                with m1: st.metric(label="Tổng số dòng kết quả thỏa mãn", value=f"{len(st.session_state.res_goc)} dòng")
                with m2: 
                    status_text = "ĐỐI CHIẾU NỐI TIẾP (2 FILE)" if st.session_state.res_dc is not None else "TIÊU CHUẨN (1 FILE)"
                    st.metric(label="Chế độ xử lý hiện tại", value=status_text)
                st.write("")
                
                # TRƯỜNG HỢP 1: CÓ FILE ĐỐI CHIẾU NỐI TIẾP
                if st.session_state.res_dc is not None:
                    st.info("💡 **Trạng thái định dạng đầu ra:** Toàn bộ cột thời gian đã được khóa cứng định dạng chuỗi văn bản `YYYYMM`. File Excel tải về sẽ hiển thị chuẩn xác dạng số/chuỗi liên mạch (Ví dụ: 202605).")
                    st.markdown("**Bảng hiển thị xem trước dữ liệu (Đã đối chiếu):**")
                    
                    # .astype(str) một lần nữa trước khi hiển thị lên giao diện Streamlit
                    st.dataframe(st.session_state.res_dc.astype(str), use_container_width=True, hide_index=True)
                    
                    st.write("")
                    st.markdown("##### 📥 Tải xuống tệp tin kết quả:")
                    col_b1, col_b2 = st.columns(2)
                    
                    with col_b1:
                        out_goc = io.BytesIO()
                        with pd.ExcelWriter(out_goc, engine='xlsxwriter') as writer:
                            # Khóa định dạng chuỗi trước khi viết vào Excel
                            st.session_state.res_goc.astype(str).to_excel(writer, index=False, sheet_name="Ket_Qua_Goc")
                            ws = writer.sheets['Ket_Qua_Goc']
                            for idx, col in enumerate(st.session_state.res_goc.columns):
                                max_len = max(st.session_state.res_goc[col].astype(str).map(len).max(), len(col)) + 4
                                ws.set_column(idx, idx, max_len)
                        st.download_button(label="📊 TẢI FILE KẾT QUẢ GỐC BAN ĐẦU (FILE 1)", data=out_goc.getvalue(), file_name="1_Ket_qua_chot_so_GOC.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="dl_goc")
                    
                    with col_b2:
                        out_dc = io.BytesIO()
                        with pd.ExcelWriter(out_dc, engine='xlsxwriter') as writer:
                            # Khóa định dạng chuỗi trước khi viết vào Excel
                            st.session_state.res_dc.astype(str).to_excel(writer, index=False, sheet_name="Ket_Qua_Doi_Chieu")
                            ws = writer.sheets['Ket_Qua_Doi_Chieu']
                            for idx, col in enumerate(st.session_state.res_dc.columns):
                                max_len = max(st.session_state.res_dc[col].astype(str).map(len).max(), len(col)) + 4
                                ws.set_column(idx, idx, max_len)
                        st.download_button(label="📥 TẢI FILE ĐỐI CHIẾU NỐI TIẾP (THÁNG MỚI)", data=out_dc.getvalue(), file_name="2_Ket_qua_doi_chieu_THANG_MOI_NHAT.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary", key="dl_dc")
                
                # TRƯỜNG HỢP 2: CHỈ CHẠY FILE 1
                else:
                    st.markdown("**Bảng hiển thị xem trước dữ liệu:**")
                    st.dataframe(st.session_state.res_goc.astype(str), use_container_width=True, hide_index=True)
                    st.write("")
                    st.markdown("##### 📥 Tải xuống tệp tin kết quả:")
                    
                    out_goc = io.BytesIO()
                    with pd.ExcelWriter(out_goc, engine='xlsxwriter') as writer:
                        st.session_state.res_goc.astype(str).to_excel(writer, index=False, sheet_name="Ket_Qua_Chot")
                        ws = writer.sheets['Ket_Qua_Chot']
                        for idx, col in enumerate(st.session_state.res_goc.columns):
                            max_len = max(st.session_state.res_goc[col].astype(str).map(len).max(), len(col)) + 4
                            ws.set_column(idx, idx, max_len)
                    st.download_button(label="📥 BẤM ĐỂ TẢI FILE EXCEL KẾT QUẢ (.XLSX)", data=out_goc.getvalue(), file_name="Ket_qua_chot_so.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary", key="dl_goc_single")
                    
            elif st.session_state.res_goc == "EMPTY":
                st.warning("⚠️ Không tìm thấy kết quả nào trùng khớp với mã đơn vị yêu cầu lọc.")
    else:
        st.error("❌ Cấu trúc File 1 không đúng định dạng khối thô. Vui lòng chọn tệp tin khác.")
st.markdown("<br><hr><p style='text-align: center; color: #475569; font-size: 20px; font-weight: bold; font-family: sans-serif;'>Copyright © Vũ Quốc Bình :)</p>", unsafe_allow_html=True)
