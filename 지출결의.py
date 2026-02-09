import streamlit as st
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
import streamlit.components.v1 as components
import base64

# --- 1. 보안 및 사인 데이터 로드 ---
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔒 원준프로듀스 시스템")
        st.text_input("비밀번호", type="password", on_change=lambda: st.session_state.update({"password_correct": st.session_state.password == st.secrets["MY_PASSWORD"]}), key="password")
        return False
    return st.session_state["password_correct"]

if check_password():
    st.set_page_config(page_title="원준프로듀스 지출결의서", layout="wide")

    # --- 2. 사인 이미지 가져오기 로직 ---
    # 클라우드 Secrets에 저장된 사인이 있으면 쓰고, 없으면 업로드 받음
    manager_sig_base64 = st.secrets.get("MANAGER_SIG", "")
    ceo_sig_base64 = st.secrets.get("CEO_SIG", "")

    # 3. 스타일 설정
    st.markdown("""<style>
        .stTextInput label, .stDateInput label, .stTextArea label { font-size: 1.3rem !important; font-weight: bold !important; }
        input, textarea { font-size: 1.2rem !important; }
        .stDownloadButton button { width: 100%; background-color: #007bff; color: white; font-weight: bold; height: 3.5rem; }
    </style>""", unsafe_allow_html=True)

    # --- 데이터 및 날짜 설정 ---
    today = datetime.now()
    default_app, default_exp = today.replace(day=10), today - relativedelta(months=1)
    if 'bulk_input' not in st.session_state:
        st.session_state.bulk_input = "판매수수료, 제이원 인터내셔널\n내륙 운송료, KJ LOGIS"

    # --- 레이아웃 분할 ---
    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.title("⚙️ 입력 센터")
        
        # 사인이 설정 안 되어 있을 때만 업로드 창 표시
        if not manager_sig_base64 or not ceo_sig_base64:
            st.info("💡 팁: 클라우드 Secrets에 사인을 등록하면 이 업로드 창이 사라집니다.")
            c_img1, c_img2 = st.columns(2)
            u_m = c_img1.file_uploader("담당자 사인 업로드")
            u_c = c_img2.file_uploader("대표이사 사인 업로드")
            if u_m: manager_sig_base64 = f"data:image/png;base64,{base64.b64encode(u_m.read()).decode()}"
            if u_c: ceo_sig_base64 = f"data:image/png;base64,{base64.b64encode(u_c.read()).decode()}"

        raw_text = st.text_area("내역, 거래처 (엔터)", value=st.session_state.bulk_input, height=150)
        st.session_state.bulk_input = raw_text
        
        w1, w2 = st.columns(2)
        writer, dept = w1.text_input("작성자", "홍길동"), w2.text_input("소속", "경영지원부")
        d1, d2 = st.columns(2)
        exp_date, app_date = d1.date_input("지출일자", default_exp), d2.date_input("결재일자", default_app)

        master_rows = [l.split(',', 1) if ',' in l else [l, ""] for l in raw_text.split('\n') if l.strip()]
        df = pd.DataFrame(master_rows, columns=["지출내역", "거래처"])
        df.insert(0, "선택", False); df["금액"] = 0; df["비고"] = ""
        edited = st.data_editor(df, hide_index=True, use_container_width=True, height=350)
        selected = edited[edited["선택"] == True]; total = selected["금액"].sum()

    with col_right:
        st.title("📄 지출결의서 미리보기")
        
        # 사인 태그 생성
        m_tag = f'<img src="{manager_sig_base64}" style="width:55px;">' if manager_sig_base64 else ""
        c_tag = f'<img src="{ceo_sig_base64}" style="width:55px;">' if ceo_sig_base64 else ""

        html_code = f"""
        <script src="https://html2canvas.hertzen.com/dist/html2canvas.min.js"></script>
        <script>
        function saveImage() {{
            html2canvas(document.getElementById('doc'), {{ scale: 2 }}).then(canvas => {{
                const link = document.createElement('a');
                link.download = '지출결의서_{app_date.strftime("%Y%m%d")}.png';
                link.href = canvas.toDataURL(); link.click();
            }});
        }}
        </script>
        <button onclick="saveImage()" style="width:100%; padding:15px; background:#28a745; color:white; border:none; border-radius:5px; cursor:pointer; font-weight:bold; font-size:18px; margin-bottom:15px;">📸 이미지로 저장하기 (띡!)</button>
        <div id="doc" style="background:#fff; padding:40px; border:1px solid #000; font-family:'Malgun Gothic'; color:#000; width:600px; margin:0 auto;">
            <table style="width:100%; margin-bottom:20px;">
                <tr>
                    <td style="font-size:30px; font-weight:bold;">지 출 결 의 서</td>
                    <td style="width:180px;">
                        <table style="width:100%; border-collapse:collapse; text-align:center; font-size:11px;">
                            <tr><td rowspan="2" style="border:1px solid #000; width:25px; background:#eee;">결<br>재</td><td style="border:1px solid #000;">담 당</td><td style="border:1px solid #000;">대 표 이 사</td></tr>
                            <tr><td style="border:1px solid #000; height:60px;">{m_tag}</td><td style="border:1px solid #000;">{c_tag}</td></tr>
                        </table>
                    </td>
                </tr>
            </table>
            <table style="width:100%; border-collapse:collapse; border:1px solid #000; font-size:13px; margin-bottom:10px;">
                <tr style="height:35px;"><td style="border:1px solid #000; background:#eee; font-weight:bold; text-align:center;">지출일자</td><td style="border:1px solid #000; text-align:center;">{exp_date.strftime("%Y년 %m월")}</td><td style="border:1px solid #000; background:#eee; font-weight:bold; text-align:center;">작성자</td><td style="border:1px solid #000; text-align:center;">{writer}</td></tr>
                <tr style="height:35px;"><td style="border:1px solid #000; background:#eee; font-weight:bold; text-align:center;">결재일자</td><td style="border:1px solid #000; text-align:center;">{app_date.strftime("%Y년 %m월 %d일")}</td><td style="border:1px solid #000; background:#eee; font-weight:bold; text-align:center;">소속</td><td style="border:1px solid #000; text-align:center;">{dept}</td></tr>
            </table>
            <div style="border:1px solid #000; padding:12px; margin-bottom:10px;"><b>결제금액:</b> &nbsp; 영 ( ₩ <b>{total:,}</b> )</div>
            <table style="width:100%; border-collapse:collapse; border:1px solid #000; font-size:12px; text-align:center;">
                <tr style="background:#eee; font-weight:bold; height:30px;"><td style="border:1px solid #000;">지 출 내 역</td><td style="border:1px solid #000;">거 래 처</td><td style="border:1px solid #000;">금 액</td><td style="border:1px solid #000;">비 고</td></tr>
                {"".join([f"<tr style='height:30px;'><td style='border:1px solid #000;'>{r['지출내역']}</td><td style='border:1px solid #000;'>{r['거래처']}</td><td style='border:1px solid #000;'>₩{r['금액']:,}</td><td style='border:1px solid #000;'>{r['비고']}</td></tr>" for _, r in selected.iterrows()])}
                {"".join(["<tr style='height:30px;'><td style='border:1px solid #000;'></td><td style='border:1px solid #000;'></td><td style='border:1px solid #000;'></td><td style='border:1px solid #000;'></td></tr>" for _ in range(max(0, 10-len(selected)))])}
            </table>
            <div style="text-align:center; font-size:18px; font-weight:bold; margin-top:50px;">(주) 원준프로듀스</div>
        </div>
        """
        components.html(html_code, height=1100, scrolling=True)