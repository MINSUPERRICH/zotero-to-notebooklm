import os
import asyncio
from pyzotero import zotero
from notebooklm import NotebookLMClient
from dotenv import load_dotenv

# 보안을 위해 환경 변수(.env 또는 Streamlit Secrets)에서 키를 불러옵니다.
load_dotenv()

ZOTERO_USER_ID = os.getenv("ZOTERO_USER_ID")
ZOTERO_API_KEY = os.getenv("ZOTERO_API_KEY")
NOTEBOOKLM_NOTEBOOK_ID = os.getenv("NOTEBOOKLM_NOTEBOOK_ID")

async def sync_zotero_to_notebooklm(limit: int = 50):
    print("1. Zotero 연동 및 파일 탐색 준비...")
    zot = zotero.Zotero(ZOTERO_USER_ID, 'user', ZOTERO_API_KEY)
    items = zot.top(limit=limit)
    
    os.makedirs("downloads", exist_ok=True)
    
    print("2. NotebookLM 로컬 로그인 세션 불러오는 중...")
    try:
        async with NotebookLMClient.from_storage() as client:
            print("✅ NotebookLM 로그인 세션 확인 완료!")
            
            print(f"3. 최대 {limit}개의 Zotero 항목 동기화 시작...")
            for item in items:
                attachments = zot.children(item['key'])
                for att in attachments:
                    if att.get('data', {}).get('contentType') == 'application/pdf':
                        title = item['data'].get('title', att['data'].get('filename', 'Untitled PDF'))
                        filename = att['data'].get('filename')
                        
                        if filename:
                            file_path = os.path.join("downloads", filename)
                            display_name = f"[Zotero] {title}"
                            
                            if not os.path.exists(file_path):
                                print(f"\n📥 다운로드 중 (Zotero -> Local): {filename}")
                                zot.dump(att['key'], filename, './downloads')
                            else:
                                print(f"\n📁 로컬에 이미 다운로드된 파일: {filename}")
                            
                            print(f"🚀 NotebookLM 업로드 시도: {display_name}")
                            try:
                                await client.sources.add_file(NOTEBOOKLM_NOTEBOOK_ID, file_path)
                                print(f"✅ 성공적으로 업로드되었습니다: {filename}")
                            except Exception as e:
                                print(f"❌ 업로드 실패 ({filename}): {e}")
                                
    except Exception as e:
        print(f"\n❌ NotebookLM 클라이언트 연결 실패: {e}")
        print("터미널에서 'notebooklm login' 명령어를 실행하여 구글 로그인을 먼저 완료했는지 확인해주세요.")

if __name__ == "__main__":
    asyncio.run(sync_zotero_to_notebooklm(limit=50))
