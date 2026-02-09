import streamlit as st
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
import streamlit.components.v1 as components
import base64
from io import BytesIO

# 1. 페이지 설정 (반드시 최상단)
st.set_page_config(page_title="Monthly Expenses", layout="wide")

# --- 보안 설정 ---
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔒 Monthly Expenses")
        pw = st.text_input("Password", type="password")
        if st.button("Login"):
            # Secrets에 MY_PASSWORD가 있는지 확인
            if "MY_PASSWORD" in st.secrets and pw == st.secrets["MY_PASSWORD"]:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("Invalid Password")
        return False
    return True

# --- 엑셀 변환 함수 ---
def to_excel(df, writer_name, dept_name, exp_date, app_date, total_amt):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        summary_df = pd.DataFrame({
            '항목': ['작성자', '소속', '지출일자', '결재일자', '총 합계'],
            '내용': [writer_name, dept_name, exp_date.strftime("%Y-%m"), app_date.strftime("%Y-%m-%d"), int(total_amt)]
        })
        summary_df.to_excel(writer, sheet_name='Monthly_Expenses', index=False, startrow=0)
        df_to_save = df[['지출내역', '거래처', '금액', '비고']].copy()
        df_to_save['금액'] = df_to_save['금액'].fillna(0).astype(int)
        df_to_save.to_excel(writer, sheet_name='Monthly_Expenses', index=False, startrow=7)
    return output.getvalue()

# --- 메인 앱 실행 ---
if check_password():
    # Secrets 데이터 로드
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

    # CSS: 입력창 글씨 키우기 및 엑셀 버튼 색상
    st.markdown("""
        <style>
        .stTextInput label, .stDateInput label, .stTextArea label { font-size: 1.2rem !important; font-weight: bold !important; }
        input, textarea { font-size: 1.1rem !important; }
        .stDownloadButton button { width: 100%; background-color: #1D6F42 !important; color: white !important; font-weight: bold; height: 3.5rem; }
        </style>
        """, unsafe_allow_html=True)

    today = datetime.now()
    default_app = today.replace(day=10)
    default_exp = today - relativedelta(months=1)

    # 5:5 분할
    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.title("⚙️ Input Center")
        raw_text = st.text_area("Master List", value=st.session_state.bulk_input, height=180)
        st.session_state.bulk_input = raw_text
        
        # 데이터 파싱
        lines = [line for line in raw_text.split('\n') if line.strip()]
        master_rows = [l.split(',', 1) if ',' in l else [l, ""] for l in lines]
        
        w1, w2 = st.columns(2)
        writer_name = w1.text_input("Writer", "홍길동")
        dept_name = w2.text_input("Department", "경영지원부")
        
        d1, d2 = st.columns(2)
        exp_date = d1.date_input("Expenditure Date", default_exp)
        app_date = d2.date_input("Approval Date", default_app)

        # 데이터프레임 구성
        df_items = pd.DataFrame(master_rows, columns=["지출내역", "거래처"])
        df_items.insert(0, "선택", False)
        df_items["금액"] = 0
        df_items["비고"] = ""
        
        edited = st.data_editor(df_items, hide_index=True, use_container_width=True, height=400)
        selected = edited[edited["선택"] == True].copy()
        selected["금액"] = selected["금액"].fillna(0).astype(int)
        total_amt = int(selected["금액"].sum())

        st.divider()
        if not selected.empty:
            excel_data = to_excel(selected, writer_name, dept_name, exp_date, app_date, total_amt)
            st.download_button("📊 Download as Excel", excel_data, f"Expenses_{app_date.strftime('%Y%m%d')}.xlsx")
        else:
            st.info("💡 항목을 선택하면 엑셀 다운로드 버튼이 생깁니다.")

    with col_right:
        st.title("📄 Preview")
        
        # 사인 태그 생성
        m_tag = f'<img src="{manager_sig}" style="width:55px;">' if manager_sig else ""
        c_tag = f'<img src="{ceo_sig}" style="width:55px;">' if ceo_sig else ""
        
        # HTML 렌더링 (디자인: 얇은 선, 넓은 간격, 소수점 제거)
        html_code = f"""
        <script src="https://html2canvas.hertzen.com/dist/html2canvas.min.js"></script>
        <script>
        function saveImage() {{
            const element = document.getElementById('capture-area');
            html2canvas(element, {{ scale: 2 }}).then(canvas => {{
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
                <tr style="height:50px;"><td style="border:1px solid #ddd; background:#f9f9f9; width:18%; text-align:center;">지출일자</td><td style="border:1px solid #ddd; width:32%; text-align:center;">{exp_date.strftime("%Y년 %m월")}</td>
                <td style="border:1px solid #ddd; background:#f9f9f9; width:18%; text-align:center;">작성자</td><td style="border:1px solid #ddd; width:32%; text-align:center;">{writer_name}</td></tr>
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