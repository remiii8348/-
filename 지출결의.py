import streamlit as st
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
import streamlit.components.v1 as components
import base64

# --- 1. 보안 설정 (제목: Monthly Expenses) ---
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔒 Monthly Expenses")
        st.text_input("Password", type="password", on_change=lambda: st.session_state.update({"password_correct": st.session_state.password == st.secrets["MY_PASSWORD"]}), key="password")
        return False
    return st.session_state["password_correct"]

if check_password():
    # 2. 페이지 설정
    st.set_page_config(page_title="Monthly Expenses", layout="wide")

    # 3. 스타일 조정 (5:5 분할 및 글씨 확대)
    st.markdown("""
        <style>
        .stTextInput label, .stDateInput label, .stTextArea label { font-size: 1.3rem !important; font-weight: bold !important; }
        input, textarea { font-size: 1.2rem !important; }
        .block-container { padding-top: 2rem; }
        </style>
        """, unsafe_allow_html=True)

    # --- 사인 이미지 데이터 (Secrets에서 로드) ---
    manager_sig_base64 = st.secrets.get("MANAGER_SIG", "")
    ceo_sig_base64 = st.secrets.get("CEO_SIG", "")

    # --- 날짜 자동 계산 (2026년 기준) ---
    today = datetime.now()
    default_app = today.replace(day=10) # 26년 2월 10일
    default_exp = today - relativedelta(months=1) # 26년 1월

    # --- 4. 마스터 목록 고정 (사용자 요청 목록) ---
    fixed_list = """판매수수료, 제이원 인터내셔널
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

    if 'bulk_input' not in st.session_state:
        st.session_state.bulk_input = fixed_list

    # --- 화면 레이아웃 (5:5 분할) ---
    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.title("⚙️ Input Center")
        
        # 목록 입력 (고정된 목록이 기본으로 뜸)
        raw_text = st.text_area("Master List (Item, Client)", value=st.session_state.bulk_input, height=250)
        st.session_state.bulk_input = raw_text

        master_rows = [l.split(',', 1) if ',' in l else [l, ""] for l in raw_text.split('\n') if l.strip()]
        
        # 정보 입력
        w1, w2 = st.columns(2)
        writer = w1.text_input("Writer", "홍길동")
        dept = w2.text_input("Department", "경영지원부")
        
        d1, d2 = st.columns(2)
        exp_date = d1.date_input("Expenditure Date", default_exp)
        app_date = d2.date_input("Approval Date", default_app)

        # 금액 및 체크
        df = pd.DataFrame(master_rows, columns=["지출내역", "거래처"])
        df.insert(0, "선택", False); df["금액"] = 0; df["비고"] = ""
        edited = st.data_editor(df, hide_index=True, use_container_width=True, height=400)
        selected = edited[edited["선택"] == True]
        total = selected["금액"].sum()

    with col_right:
        st.title("📄 Preview")
        
        m_tag = f'<img src="{manager_sig_base64}" style="width:55px;">' if manager_sig_base64 else ""
        c_tag = f'<img src="{ceo_sig_base64}" style="width:55px;">' if ceo_sig_base64 else ""

        # 캡처 및 저장 기능 포함 HTML
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
        
        <button onclick="saveImage()" style="width:100%; padding:15px; background:#28a745; color:white; border:none; border-radius:5px; cursor:pointer; font-weight:bold; font-size:18px; margin-bottom:10px;">
            📸 Save as Image (띡!)
        </button>

        <div id="capture-area" style="background:#fff; padding:35px; border:1px solid #000; font-family:'Malgun Gothic'; color:#000; width:600px; margin:0 auto;">
            <table style="width:100%; border-collapse:collapse; margin-bottom:15px;">
                <tr>
                    <td style="font-size:30px; font-weight:bold;">지 출 결 의 서</td>
                    <td style="width:180px;">
                        <table style="width:100%; border-collapse:collapse; font-size:11px; text-align:center;">
                            <tr><td rowspan="2" style="border:1px solid #000; width:25px; background:#eee;">결<br>재</td><td style="border:1px solid #000;">담 당</td><td style="border:1px solid #000;">대 표 이 사</td></tr>
                            <tr><td style="border:1px solid #000; height:55px;">{m_tag}</td><td style="border:1px solid #000; height:55px;">{c_tag}</td></tr>
                        </table>
                    </td>
                </tr>
            </table>
            <table style="width:100%; border-collapse:collapse; border:1px solid #000; font-size:13px; margin-bottom:10px;">
                <tr style="height:32px;">
                    <td style="border:1px solid #000; background:#eee; width:18%; font-weight:bold; text-align:center;">지출일자</td><td style="border:1px solid #000; width:32%; text-align:center;">{exp_date.strftime("%Y년 %m월")}</td>
                    <td style="border:1px solid #000; background:#eee; width:18%; font-weight:bold; text-align:center;">작성자</td><td style="border:1px solid #000; width:32%; text-align:center;">{writer}</td>
                </tr>
                <tr style="height:32px;">
                    <td style="border:1px solid #000; background:#eee; font-weight:bold; text-align:center;">결재일자</td><td style="border:1px solid #000; text-align:center;">{app_date.strftime("%Y년 %m월 %d일")}</td>
                    <td style="border:1px solid #000; background:#eee; font-weight:bold; text-align:center;">소속</td><td style="border:1px solid #000; text-align:center;">{dept}</td>
                </tr>
            </table>
            <div style="border:1px solid #000; padding:10px; font-size:14px; margin-bottom:10px;">
                <b>결제금액:</b> &nbsp;&nbsp; 영 ( ₩ <b>{total:,}</b> )
            </div>
            <table style="width:100%; border-collapse:collapse; border:1px solid #000; font-size:12px;">
                <tr style="background:#eee; font-weight:bold; text-align:center; height:28px;">
                    <td style="border:1px solid #000; width:25%;">지 출 내 역</td><td style="border:1px solid #000; width:25%;">거 래 처</td><td style="border:1px solid #000; width:20%;">금 액</td><td style="border:1px solid #000;">비 고</td>
                </tr>
                {"".join([f"<tr style='height:28px; text-align:center;'><td style='border:1px solid #000;'>{r['지출내역']}</td><td style='border:1px solid #000;'>{r['거래처']}</td><td style='border:1px solid #000;'>₩{r['금액']:,}</td><td style='border:1px solid #000;'>{r['비고']}</td></tr>" for _, r in selected.iterrows()])}
                {"".join(["<tr style='height:28px;'><td style='border:1px solid #000;'></td><td style='border:1px solid #000;'></td><td style='border:1px solid #000;'></td><td style='border:1px solid #000;'></td></tr>" for _ in range(max(0, 12-len(selected)))])}
                <tr style="background:#eee; font-weight:bold; text-align:center; height:32px;">
                    <td colspan="2" style="border:1px solid #000;">합 계</td><td colspan="2" style="border:1px solid #000; text-align:left; padding-left:15px;">₩ {total:,}</td>
                </tr>
            </table>
            <div style="text-align:center; font-size:18px; font-weight:bold; margin-top:40px;">(주) 원준프로듀스</div>
        </div>
        """
        components.html(html_code, height=1100, scrolling=True)