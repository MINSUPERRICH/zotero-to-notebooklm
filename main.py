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
    print("1. Zotero API 연결 중...")
    zot = zotero.Zotero(ZOTERO_USER_ID, 'user', ZOTERO_API_KEY)
    
    if collection_id:
        items = zot.collection_items(collection_id, limit=limit)
    else:
        items = zot.top(limit=limit)

    pdf_files = []
    print(f"2. Zotero에서 PDF 첨부 파일 탐색 중... (가져온 아이템: {len(items)}개)")
    
    for item in items:
        attachments = zot.children(item['key'])
        for att in attachments:
            if att.get('data', {}).get('contentType') == 'application/pdf':
                title = item['data'].get('title', att['data'].get('filename', 'Untitled PDF'))
                filename = att['data'].get('filename')
                if filename:
                    pdf_files.append({
                        "displayName": f"[Zotero] {title}",
                        "fileReference": filename
                    })

    if not pdf_files:
        print("업로드할 PDF 파일을 찾지 못했습니다.")
        return

    print(f"3. NotebookLM 연결 및 소스 배치 생성 중... (총 {len(pdf_files)}개 PDF)")
    client = NotebookLMClient()
    
    parent_notebook = f"notebooks/{NOTEBOOKLM_NOTEBOOK_ID}"
    
    try:
        response = client.batch_create_sources(
            parent=parent_notebook,
            sources=pdf_files
        )
        print("✅ 성공적으로 Zotero PDF 소스들이 NotebookLM에 추가되었습니다!")
    except Exception as e:
        print(f"❌ NotebookLM 업로드 중 오류 발생: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Zotero PDF to NotebookLM Sync Tool")
    parser.add_argument("--collection", type=str, help="Zotero Collection ID (선택)", default=None)
    parser.add_argument("--limit", type=int, help="가져올 최대 아이템 수", default=10)
    args = parser.parse_args()

    sync_zotero_to_notebooklm(collection_id=args.collection, limit=args.limit)
