import streamlit as st
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
import streamlit.components.v1 as components
import base64
from io import BytesIO

# --- 1. 보안 설정 (제목: Monthly Expenses) ---
def check_password():
    if "password_correct" not in st.session_state:
        st.set_page_config(page_title="Monthly Expenses", layout="centered")
        st.title("🔒 Monthly Expenses")
        st.text_input("Password", type="password", on_change=lambda: st.session_state.update({"password_correct": st.session_state.password == st.secrets["MY_PASSWORD"]}), key="password")
        return False
    return st.session_state["password_correct"]

# --- 엑셀 변환 함수 ---
def to_excel(df, writer_name, dept_name, exp_date, app_date, total_amt):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        summary_df = pd.DataFrame({
            '항목': ['작성자', '소속', '지출일자', '결재일자', '총 합계'],
            '내용': [writer_name, dept_name, exp_date.strftime("%Y-%m"), app_date.strftime("%Y-%m-%d"), total_amt]
        })
        summary_df.to_excel(writer, sheet_name='Monthly_Expenses', index=False, startrow=0)
        df[['지출내역', '거래처', '금액', '비고']].to_excel(writer, sheet_name='Monthly_Expenses', index=False, startrow=7)
    return output.getvalue()

if check_password():
    st.set_page_config(page_title="Monthly Expenses", layout="wide")

    # --- 2. 환경 설정 로드 (Secrets) ---
    manager_sig_base64 = st.secrets.get("MANAGER_SIG", "")
    ceo_sig_base64 = st.secrets.get("CEO_SIG", "")
    
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
    
    master_list_content = st.secrets.get("MASTER_LIST", default_list)

    if 'bulk_input' not in st.session_state:
        st.session_state.bulk_input = master_list_content

    # --- 스타일 설정 ---
    st.markdown("""
        <style>
        .stTextInput label, .stDateInput label, .stTextArea label { font-size: 1.2rem !important; font-weight: bold !important; }
        input, textarea { font-size: 1.1rem !important; }
        .stDownloadButton button { width: 100%; background-color: #1D6F42; color: white; font-weight: bold; height: 3.5rem; border: none; }
        .stDownloadButton button:hover { background-color: #145230; color: white; }
        </style>
        """, unsafe_allow_html=True)

    today = datetime.now()
    default_app = today.replace(day=10)
    default_exp = today - relativedelta(months=1)

    # --- 3. 화면 레이아웃 (5:5 분할) ---
    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.title("⚙️ Input Center")
        
        raw_text = st.text_area("Master List (Edit/Add here)", value=st.session_state.bulk_input, height=200)
        st.session_state.bulk_input = raw_text
        master_rows = [l.split(',', 1) if ',' in l else [l, ""] for l in raw_text.split('\n') if l.strip()]
        
        w1, w2 = st.columns(2)
        writer_name = w1.text_input("Writer", "홍길동")
        dept_name = w2.text_input("Department", "경영지원부")
        
        d1, d2 = st.columns(2)
        exp_date = d1.date_input("Expenditure Date", default_exp)
        app_date = d2.date_input("Approval Date", default_app)

        df_items = pd.DataFrame(master_rows, columns=["지출내역", "거래처"])
        df_items.insert(0, "선택", False); df_items["금액"] = 0; df_items["비고"] = ""
        
        edited = st.data_editor(df_items, hide_index=True, use_container_width=True, height=350)
        selected = edited[edited["선택"] == True]
        total_amt = selected["금액"].sum()

        st.divider()
        if not selected.empty:
            excel_data = to_excel(selected, writer_name, dept_name, exp_date, app_date, total_amt)
            st.download_button(
                label="📊 Download as Excel",
                data=excel_data,
                file_name=f"Expenses_{app_date.strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    with col_right:
        st.title("📄 Preview")
        m_tag = f'<img src="{manager_sig_base64}" style="width:55px;">' if manager_sig_base64 else ""
        c_tag = f'<img src="{ceo_sig_base64}" style="width:55px;">' if ceo_sig_base64 else ""
        
        # HTML 디자인 수정: 얇은 선, 넓은 간격
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
        <div id="capture-area" style="background:#fff; padding:40px; border:1px solid #000; font-family:'Malgun Gothic'; color:#000; width:650px; margin:0 auto;">
            <div style="font-size:32px; font-weight:normal; margin-bottom:25px; text-align:center;">지 출 결 의 서</div>
            
            <table style="width:100%; border-collapse:collapse; margin-bottom:20px;">
                <tr>
                    <td style="width:60%;"></td>
                    <td style="width:40%;">
                        <table style="width:100%; border-collapse:collapse; font-size:12px; text-align:center;">
                            <tr style="height:30px;"><td rowspan="2" style="border:1px solid #000; width:30px; background:#f9f9f9; padding:5px;">결<br>재</td><td style="border:1px solid #000; padding:5px; background:#f9f9f9;">담 당</td><td style="border:1px solid #000; padding:5px; background:#f9f9f9;">대 표 이 사</td></tr>
                            <tr style="height:60px;"><td style="border:1px solid #000;">{m_tag}</td><td style="border:1px solid #000;">{c_tag}</td></tr>
                        </table>
                    </td>
                </tr>
            </table>

            <table style="width:100%; border-collapse:collapse; border:1px solid #000; font-size:14px; margin-bottom:20px;">
                <tr style="height:45px;">
                    <td style="border:1px solid #000; background:#f9f9f9; width:18%; text-align:center; padding:5px;">지출일자</td><td style="border:1px solid #000; width:32%; text-align:center; padding:5px;">{exp_date.strftime("%Y년 %m월")}</td>
                    <td style="border:1px solid #000; background:#f9f9f9; width:18%; text-align:center; padding:5px;">작성자</td><td style="border:1px solid #000; width:32%; text-align:center; padding:5px;">{writer_name}</td>
                </tr>
                <tr style="height:45px;">
                    <td style="border:1px solid #000; background:#f9f9f9; text-align:center; padding:5px;">결재일자</td><td style="border:1px solid #000; text-align:center; padding:5px;">{app_date.strftime("%Y년 %m월 %d일")}</td>
                    <td style="border:1px solid #000; background:#f9f9f9; text-align:center; padding:5px;">소속</td><td style="border:1px solid #000; text-align:center; padding:5px;">{dept_name}</td>
                </tr>
            </table>

            <div style="border:1px solid #000; padding:15px; font-size:15px; margin-bottom:20px; background:#f9f9f9;">
                결제금액: &nbsp;&nbsp; 일금 &nbsp;&nbsp; ₩ <b>{total_amt:,}</b> &nbsp;&nbsp; 원정 (부가세 별도)
            </div>

            <table style="width:100%; border-collapse:collapse; border:1px solid #000; font-size:13px;">
                <tr style="background:#f9f9f9; text-align:center; height:40px;">
                    <td style="border:1px solid #000; width:25%; padding:5px;">지 출 내 역</td><td style="border:1px solid #000; width:25%; padding:5px;">거 래 처</td><td style="border:1px solid #000; width:20%; padding:5px;">금 액</td><td style="border:1px solid #000; padding:5px;">비 고</td>
                </tr>
                {"".join([f"<tr style='height:38px; text-align:center;'><td style='border:1px solid #000; padding:5px;'>{r['지출내역']}</td><td style='border:1px solid #000; padding:5px;'>{r['거래처']}</td><td style='border:1px solid #000; padding:5px;'>₩{r['금액']:,}</td><td style='border:1px solid #000; padding:5px;'>{r['비고']}</td></tr>" for _, r in selected.iterrows()])}
                <tr style="background:#f9f9f9; text-align:center; height:45px;">
                    <td colspan="2" style="border:1px solid #000; padding:5px;">합 계</td><td colspan="2" style="border:1px solid #000; text-align:left; padding-left:20px;">₩ {total_amt:,}</td>
                </tr>
            </table>
            <div style="text-align:center; font-size:20px; margin-top:50px;">(주) 원준프로듀스</div>
        </div>
        """
        components.html(html_code, height=1200, scrolling=True)