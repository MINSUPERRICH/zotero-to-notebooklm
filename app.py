import os
import streamlit as st
from dotenv import load_dotenv
import main

# 환경 변수 및 Streamlit Secrets 로드
load_dotenv()

# Streamlit 비밀 값(st.secrets)이 있으면 우선 사용하고, 없으면 .env 사용
def get_secret(key_name, default=""):
    if key_name in st.secrets:
        return st.secrets[key_name]
    return os.getenv(key_name, default)

st.set_page_config(page_title="Zotero to NotebookLM Sync", page_icon="📚", layout="centered")

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
        # 환경 변수 세팅
        os.environ["ZOTERO_USER_ID"] = zotero_user_id
        os.environ["ZOTERO_API_KEY"] = zotero_api_key
        os.environ["NOTEBOOKLM_NOTEBOOK_ID"] = notebook_id

        with st.spinner("Zotero 및 NotebookLM 동기화 진행 중..."):
            try:
                # main.py의 동기화 함수 실행
                main.sync_zotero_to_notebooklm(limit=limit)
                st.success("✅ 동기화가 성공적으로 완료되었습니다!")
            except Exception as e:
                st.error(f"❌ 동기화 중 오류가 발생했습니다: {e}")