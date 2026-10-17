import os
import argparse
from dotenv import load_dotenv
from pyzotero import zotero
from notebooklm import NotebookLMClient

load_dotenv()

ZOTERO_USER_ID = os.getenv("ZOTERO_USER_ID")
ZOTERO_API_KEY = os.getenv("ZOTERO_API_KEY")
NOTEBOOKLM_NOTEBOOK_ID = os.getenv("NOTEBOOKLM_NOTEBOOK_ID")

def sync_zotero_to_notebooklm(collection_id: str = None, limit: int = 10):
    print("1. Zotero API 및 NotebookLM 클라이언트 연결 중...")
    zot = zotero.Zotero(ZOTERO_USER_ID, 'user', ZOTERO_API_KEY)
    client = NotebookLMClient()
    parent_notebook = f"notebooks/{NOTEBOOKLM_NOTEBOOK_ID}"
    
    # [수정된 부분 1] 기존 NotebookLM 소스 목록 조회 및 파싱
    print("2. NotebookLM 기존 소스 목록 조회 중...")
    existing_names = set()
    try:
        # 노트북에 존재하는 기존 소스 리스트 가져오기
        existing_sources = client.list_sources(parent=parent_notebook)
        
        # NotebookLMClient의 반환값 형태(리스트 또는 딕셔너리)에 맞게 displayName 추출
        if isinstance(existing_sources, list):
            for source in existing_sources:
                if isinstance(source, dict) and 'displayName' in source:
                    existing_names.add(source['displayName'])
        elif isinstance(existing_sources, dict) and 'sources' in existing_sources:
            for source in existing_sources['sources']:
                if isinstance(source, dict) and 'displayName' in source:
                    existing_names.add(source['displayName'])
                    
        print(f"-> 총 {len(existing_names)}개의 기존 소스가 확인되었습니다.")
    except Exception as e:
        print(f"⚠️ NotebookLM 기존 소스 조회 중 오류 발생 (처음부터 모든 파일 업로드 시도): {e}")

    # Zotero 항목 가져오기
    print("3. Zotero 데이터 가져오는 중...")
    if collection_id:
        items = zot.collection_items(collection_id, limit=limit)
    else:
        items = zot.top(limit=limit)

    pdf_files = []
    print(f"4. Zotero에서 PDF 탐색 및 중복 필터링 중... (가져온 아이템: {len(items)}개)")
    
    for item in items:
        attachments = zot.children(item['key'])
        for att in attachments:
            if att.get('data', {}).get('contentType') == 'application/pdf':
                title = item['data'].get('title', att['data'].get('filename', 'Untitled PDF'))
                filename = att['data'].get('filename')
                
                if filename:
                    # NotebookLM에 업로드할 때 사용할 이름 구성
                    display_name = f"[Zotero] {title}"
                    
                    # [수정된 부분 2] 중복 검사 로직
                    if display_name in existing_names:
                        print(f"  [-] 중복 건너뜀: {display_name}")
                    else:
                        print(f"  [+] 새 파일 추가 대상: {display_name}")
                        pdf_files.append({
                            "displayName": display_name,
                            "fileReference": filename
                        })

    if not pdf_files:
        print("새로 업로드할 PDF 파일이 없습니다. (모두 이미 동기화됨)")
        return

    # NotebookLM 업로드 처리
    print(f"5. NotebookLM 소스 배치 생성 중... (총 {len(pdf_files)}개 새 PDF)")
    try:
        response = client.batch_create_sources(
            parent=parent_notebook,
            sources=pdf_files
        )
        print("✅ 성공적으로 새로운 Zotero PDF 소스들이 NotebookLM에 추가되었습니다!")
    except Exception as e:
        print(f"❌ NotebookLM 업로드 중 오류 발생: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Zotero PDF to NotebookLM Sync Tool")
    parser.add_argument("--collection", type=str, help="Zotero Collection ID (선택)", default=None)
    parser.add_argument("--limit", type=int, help="가져올 최대 아이템 수", default=10)
    args = parser.parse_args()

    sync_zotero_to_notebooklm(collection_id=args.collection, limit=args.limit)
