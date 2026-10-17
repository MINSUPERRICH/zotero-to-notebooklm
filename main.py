import os
import asyncio
import argparse
from dotenv import load_dotenv
from pyzotero import zotero
from notebooklm import NotebookLMClient

# 환경 변수 로드 (.env 파일 필요)
load_dotenv()

ZOTERO_USER_ID = os.getenv("ZOTERO_USER_ID")
ZOTERO_API_KEY = os.getenv("ZOTERO_API_KEY")
NOTEBOOKLM_NOTEBOOK_ID = os.getenv("NOTEBOOKLM_NOTEBOOK_ID")

async def sync_zotero_to_notebooklm(collection_id: str = None, limit: int = 50):
    print("1. Zotero 연동 및 파일 탐색 준비...")
    zot = zotero.Zotero(ZOTERO_USER_ID, 'user', ZOTERO_API_KEY)
    
    if collection_id:
        items = zot.collection_items(collection_id, limit=limit)
    else:
        items = zot.top(limit=limit)
    
    # 다운로드할 임시 폴더 생성
    os.makedirs("downloads", exist_ok=True)
    
    print("2. NotebookLM 로컬 로그인 세션 불러오는 중...")
    try:
        # PowerShell에서 'notebooklm login'을 통해 저장된 세션 쿠키를 사용 (비동기 방식)
        async with NotebookLMClient.from_storage() as client:
            print("✅ NotebookLM 로그인 세션 확인 완료!")
            
            # 타겟 노트북 연결
            notebook = client.notebook(NOTEBOOKLM_NOTEBOOK_ID)
            
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
                            
                            # [단계 1] Zotero에서 로컬(내 PC)로 PDF 다운로드
                            if not os.path.exists(file_path):
                                print(f"\n📥 다운로드 중 (Zotero -> Local): {filename}")
                                zot.dump(att['key'], filename, './downloads')
                            else:
                                print(f"\n📁 로컬에 이미 다운로드된 파일: {filename}")
                            
                            # [단계 2] 로컬에서 NotebookLM으로 파일 업로드
                            print(f"🚀 NotebookLM 업로드 시도: {display_name}")
                            try:
                                # teng-lin 라이브러리의 파일 소스 추가 메서드
                                await notebook.sources.add(file_path)
                                print(f"✅ 성공적으로 업로드되었습니다: {filename}")
                            except Exception as e:
                                print(f"❌ 업로드 실패 ({filename}): {e}")
                                
    except Exception as e:
        print(f"\n❌ NotebookLM 클라이언트 연결 실패: {e}")
        print("터미널에서 'notebooklm login' 명령어를 실행하여 구글 로그인을 먼저 완료했는지 확인해주세요.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Zotero PDF to NotebookLM Sync Tool (Async Version)")
    parser.add_argument("--collection", type=str, help="Zotero Collection ID (선택)", default=None)
    parser.add_argument("--limit", type=int, help="가져올 최대 아이템 수", default=50)
    args = parser.parse_args()

    # 파이썬 3.7+ 비동기 함수 실행 기본 방식
    asyncio.run(sync_zotero_to_notebooklm(collection_id=args.collection, limit=args.limit))
