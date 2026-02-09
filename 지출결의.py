import streamlit as st
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
import streamlit.components.v1 as components
import base64
from io import BytesIO

# [필수] 최상단 배치
st.set_page_config(page_title="Monthly Expenses", layout="wide")

# --- 1. 보안 설정 ---
def check_password():
    if "MY_PASSWORD" not in st.secrets:
        st.error("Secrets 설정에서 'MY_PASSWORD'를 등록해주세요.")
        return False
    if "password_correct" not in st.session_state:
        st.title("🔒 Monthly Expenses")
        pw = st.text_input("Password", type="password")
        if st.button("Login"):
            if pw == st.secrets["MY_PASSWORD"]:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("Invalid Password")
        return False
    return True

# --- 2. 엑셀 생성 함수 (데이터 복구용 컬럼 포함) ---
def to_excel(df, writer_name, dept_name, exp_date, app_date, total_amt):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # 요약 정보 저장
        summary_df = pd.DataFrame({
            '항목': ['작성자', '소속', '지출일자', '결재일자', '총 합계'],
            '내용': [writer_name, dept_name, exp_date.strftime("%Y-%m"), app_date.strftime("%Y-%m-%d"), int(total_amt)]
        })
        summary_df.to_excel(writer, sheet_name='Monthly_Expenses', index=False, startrow=0)
        
        # 상세 내역 저장 (8번째 줄부터 헤더 시작)
        df_to_save = df[['선택', '지출내역', '거래처', '금액', '비고']].copy()
        df_to_save['금액'] = df_to_save['금액'].fillna(0).astype(int)
        df_to_save.to_excel(writer, sheet_name='Monthly_Expenses', index=False, startrow=7)
    return output.getvalue()

# --- 메인 앱 실행 ---
if check_password():
    manager_sig = st.secrets.get("MANAGER_SIG", "")
    ceo_sig = st.secrets.get("CEO_SIG", "")
    
    # 마스터 목록 고정
    default_list = """판매수수료, 제이원 인터내셔널
창고료, 영남냉장
창고료, 이지화물 (고센)
보관/운송료, KJ LOGIS
컨테이너 운송료, 씨즈웨이
컨테이너 운송료, 에이스로지스틱
내륙 운송료, 경진물류
내륙 운송료, 재용화물
써베이, 창대검정
써베이, 오믹(해양검정)
관리비, 제일오피스텔
세무기장료, 한경회계법인
전산유지비, 유일소프트웨어
이자지급, 김은정
조화, 유혜린(007꽃배달)
통관비, 성림종합물류
지방세, 
국세, """
    
    master_content = st.secrets.get("MASTER_LIST", default_list)
    if 'bulk_input' not in st.session_state:
        st.session_state.bulk_input = master_content

    # CSS 설정
    st.markdown("""
        <style>
        .stTextInput label, .stDateInput label, .stTextArea label { font-size: 1.2rem !important; font-weight: bold !important; }
        input, textarea { font-size: 1.1rem !important; }
        .stDownloadButton button { width: 100%; font-weight: bold; height: 3.5rem; }
        </style>
        """, unsafe_allow_html=True)

    today = datetime.now()
    default_app = today.replace(day=10)
    default_exp = today - relativedelta(months=1)

    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.title("⚙️ Input Center")
        
        # [데이터 불러오기 로직 강화]
        st.subheader("📂 Load Excel File")
        uploaded_excel = st.file_uploader("이전에 다운로드한 엑셀 파일을 업로드하세요.", type="xlsx")
        
        excel_data_map = {}
        if uploaded_excel:
            try:
                # 1. 작성자/소속 정보 읽기 (B열에서 값 추출)
                meta_df = pd.read_excel(uploaded_excel, sheet_name='Monthly_Expenses', nrows=5, header=None)
                excel_data_map['writer'] = meta_df.iloc[1, 1] # 2행 2열
                excel_data_map['dept'] = meta_df.iloc[2, 1]   # 3행 2열
                
                # 2. 지출 내역 읽기 (8번째 행부터 데이터가 있다고 가정)
                items_df = pd.read_excel(uploaded_excel, sheet_name='Monthly_Expenses', skiprows=7)
                # 컬럼명 앞뒤 공백 제거
                items_df.columns = [c.strip() for c in items_df.columns]
                excel_data_map['items'] = items_df.to_dict('records')
                st.success("✅ 데이터를 성공적으로 불러왔습니다!")
            except Exception as e:
                st.error(f"❌ 파일을 읽는 중 오류가 발생했습니다: {e}")

        raw_text = st.text_area("Master List", value=st.session_state.bulk_input, height=150)
        st.session_state.bulk_input = raw_text
        
        master_rows = [l.split(',', 1) if ',' in l else [l, ""] for l in raw_text.split('\n') if l.strip()]
        
        # UI 입력칸 (불러온 데이터가 있으면 우선 적용)
        w1, w2 = st.columns(2)
        writer_name = w1.text_input("Writer", excel_data_map.get("writer", ""))
        dept_name = w2.text_input("Department", excel_data_map.get("dept", "경영지원부"))
        
        d1, d2 = st.columns(2)
        exp_date = d1.date_input("Expenditure Date", default_exp)
        app_date = d2.date_input("Approval Date", default_app)

        # 기본 데이터프레임 초기화
        df_items = pd.DataFrame(master_rows, columns=["지출내역", "거래처"])
        df_items["선택"] = False
        df_items["금액"] = 0
        df_items["비고"] = ""

        # 엑셀 데이터 매칭 및 병합
        if "items" in excel_data_map:
            temp_df = pd.DataFrame(excel_data_map["items"])
            for _, row in temp_df.iterrows():
                # 데이터 타입 보정 (None 처리 및 문자열 변환)
                ex_item = str(row.get("지출내역", "")).strip()
                ex_client = str(row.get("거래처", "")).strip() if pd.notna(row.get("거래처")) else ""
                
                # 원본 목록에서 동일한 내역/거래처 찾기
                match = (df_items["지출내역"].str.strip() == ex_item) & (df_items["거래처"].str.strip() == ex_client)
                if match.any():
                    df_items.loc[match, "선택"] = row.get("선택", True)
                    df_items.loc[match, "금액"] = int(row.get("금액", 0))
                    df_items.loc[match, "비고"] = row.get("비고", "")

        edited = st.data_editor(
            df_items[["선택", "지출내역", "거래처", "금액", "비고"]], 
            hide_index=True, use_container_width=True, height=400
        )
        
        selected = edited[edited["선택"] == True].copy()
        selected["금액"] = selected["금액"].fillna(0).astype(int)
        total_amt = int(selected["금액"].sum())

        st.divider()
        # 엑셀 다운로드 (이제 이 파일이 나중에 '불러오기'용 파일이 됨)
        excel_file_data = to_excel(edited, writer_name, dept_name, exp_date, app_date, total_amt)
        st.download_button(
            label="📊 Download as Excel", 
            data=excel_file_data, 
            file_name=f"Expenses_{app_date.strftime('%Y%m%d')}.xlsx"
        )

    with col_right:
        st.title("📄 Preview")
        # --- 미리보기 HTML 디자인 ---
        m_tag = f'<img src="{manager_sig}" style="width:55px;">' if manager_sig else ""
        c_tag = f'<img src="{ceo_sig}" style="width:55px;">' if ceo_sig else ""
        
        html_code = f"""
        <script src="https://html2canvas.hertzen.com/dist/html2canvas.min.js"></script>
        <script>
        function saveImage() {{
            html2canvas(document.getElementById('capture-area'), {{ scale: 2 }}).then(canvas => {{
                const link = document.createElement('a');
                link.download = 'Monthly_Expenses_{app_date.strftime("%Y%m%d")}.png';
                link.href = canvas.toDataURL('image/png');
                link.click();
            }});
        }}
        </script>
        <button onclick="saveImage()" style="width:100%; padding:15px; background:#28a745; color:white; border:none; border-radius:5px; cursor:pointer; font-weight:bold; font-size:18px; margin-bottom:15px;">
            📸 Save as Image
        </button>
        <div id="capture-area" style="background:#fff; padding:40px; border:1px solid #eee; font-family:'Malgun Gothic'; color:#000; width:650px; margin:0 auto;">
            <div style="font-size:32px; font-weight:normal; margin-bottom:25px; text-align:center;">지 출 결 의 서</div>
            <table style="width:100%; border-collapse:collapse; margin-bottom:20px;">
                <tr><td style="width:60%;"></td><td style="width:40%;">
                    <table style="width:100%; border-collapse:collapse; font-size:12px; text-align:center;">
                        <tr style="height:30px;"><td rowspan="2" style="border:1px solid #ddd; width:30px; background:#f9f9f9;">결<br>재</td><td style="border:1px solid #ddd; background:#f9f9f9;">담 당</td><td style="border:1px solid #ddd; background:#f9f9f9;">대 표 이 사</td></tr>
                        <tr style="height:60px;"><td style="border:1px solid #ddd;">{m_tag}</td><td style="border:1px solid #ddd;">{c_tag}</td></tr>
                    </table>
                </td></tr>
            </table>
            <table style="width:100%; border-collapse:collapse; border:1px solid #ddd; font-size:14px; margin-bottom:20px;">
                <tr style="height:50px;"><td style="border:1px solid #ddd; background:#f9f9f9; width:18%; text-align:center;">지출일자</td><td style="border:1px solid #ddd; text-align:center;">{exp_date.strftime("%Y년 %m월")}</td>
                <td style="border:1px solid #ddd; background:#f9f9f9; width:18%; text-align:center;">작성자</td><td style="border:1px solid #ddd; text-align:center;">{writer_name}</td></tr>
                <tr style="height:50px;"><td style="border:1px solid #ddd; background:#f9f9f9; text-align:center;">결재일자</td><td style="border:1px solid #ddd; text-align:center;">{app_date.strftime("%Y년 %m월 %d일")}</td>
                <td style="border:1px solid #ddd; background:#f9f9f9; text-align:center;">소속</td><td style="border:1px solid #ddd; text-align:center;">{dept_name}</td></tr>
            </table>
            <div style="border:1px solid #ddd; padding:20px; font-size:17px; margin-bottom:20px; background:#f9f9f9;">
                <span style="font-weight:bold;">결제금액: &nbsp;&nbsp; 일금 &nbsp;&nbsp; <span style="font-size:22px; color:#000;">{total_amt:,}</span> &nbsp;&nbsp; 원정</span>
            </div>
            <table style="width:100%; border-collapse:collapse; border:1px solid #ddd; font-size:13px;">
                <tr style="background:#f9f9f9; text-align:center; height:45px;">
                    <td style="border:1px solid #ddd; width:25%;">지 출 내 역</td><td style="border:1px solid #ddd; width:25%;">거 래 처</td><td style="border:1px solid #ddd; width:20%;">금 액</td><td style="border:1px solid #ddd;">비 고</td>
                </tr>
                {"".join([f"<tr style='height:45px; text-align:center;'><td style='border:1px solid #ddd;'>{r['지출내역']}</td><td style='border:1px solid #ddd;'>{r['거래처']}</td><td style='border:1px solid #ddd;'>{int(r['금액']):,}</td><td style='border:1px solid #ddd;'>{r['비고']}</td></tr>" for _, r in selected.iterrows()])}
                <tr style="background:#f9f9f9; text-align:center; height:50px; font-weight:bold; font-size:15px;">
                    <td colspan="2" style="border:1px solid #ddd;">합 계</td><td colspan="2" style="border:1px solid #ddd; text-align:left; padding-left:20px;">{total_amt:,}</td>
                </tr>
            </table>
            <div style="text-align:center; font-size:18px; margin-top:60px;">(주) 원준프로듀스</div>
        </div>
        """
        components.html(html_code, height=1200, scrolling=True)