import os
import streamlit as st
from dotenv import load_dotenv
import main

# 환경 변수 및 Streamlit Secrets 로드
load_dotenv()

def get_secret(key_name, default=""):
    if key_name in st.secrets:
        return st.secrets[key_name]
    return os.getenv(key_name, default)

st.set_page_config(page_title="Zotero to NotebookLM Sync", page_icon="📚", layout="centered")

# --- 비밀번호 인증 함수 ---
def check_password():
    """사용자가 입력한 비밀번호가 올바른지 확인합니다."""
    def password_entered():
        if st.session_state["password"] == get_secret("APP_PASSWORD", "1234"):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # 메모리에서 비밀번호 삭제
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # 처음 접속 시 비밀번호 입력 폼 표시
        st.text_input("🔒 앱 비밀번호를 입력하세요", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        # 비밀번호가 틀렸을 때
        st.text_input("🔒 앱 비밀번호를 입력하세요", type="password", on_change=password_entered, key="password")
        st.error("❌ 비밀번호가 올바르지 않습니다.")
        return False
    else:
        # 비밀번호가 맞았을 때
        return True

# --- 메인 앱 로직 ---
if check_password():
    st.title("📚 Zotero ➡️ NotebookLM Sync Tool")
    st.markdown("Zotero 클라우드 라이브러리의 PDF 자료를 Google NotebookLM으로 자동 동기화합니다.")

    st.sidebar.header("🔑 API Settings")
    zotero_user_id = st.sidebar.text_input("Zotero User ID", value=get_secret("ZOTERO_USER_ID"))
    zotero_api_key = st.sidebar.text_input("Zotero API Key", value=get_secret("ZOTERO_API_KEY"), type="password")
    notebook_id = st.sidebar.text_input("NotebookLM Notebook ID", value=get_secret("NOTEBOOKLM_NOTEBOOK_ID"))

    st.subheader("⚙️ 동기화 옵션")
    limit = st.slider("가져올 Zotero 항목 개수 (최신순)", min_value=5, max_value=100, value=20, step=5)

    if st.button("🚀 동기화 시작", type="primary"):
        if not zotero_user_id or not zotero_api_key or not notebook_id:
            st.error("API 키와 Notebook ID를 모두 입력해주세요.")
        else:
            os.environ["ZOTERO_USER_ID"] = zotero_user_id
            os.environ["ZOTERO_API_KEY"] = zotero_api_key
            os.environ["NOTEBOOKLM_NOTEBOOK_ID"] = notebook_id

            with st.spinner("Zotero 및 NotebookLM 동기화 진행 중..."):
                try:
                    main.sync_zotero_to_notebooklm(limit=limit)
                    st.success("✅ 동기화가 성공적으로 완료되었습니다!")
                except Exception as e:
                    st.error(f"❌ 동기화 중 오류가 발생했습니다: {e}")
