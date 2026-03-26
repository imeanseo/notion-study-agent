"""
Notion API 클라이언트.
공식 REST API를 사용하며, NOTION_API_KEY가 필요합니다.
(MCP는 Cursor 세션에서 사용하고, 이 클라이언트는 스크립트/배치 실행용)
"""
import os
import httpx
import tempfile
from typing import Any
from pathlib import Path

try:
    from pypdf import PdfReader
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


NOTION_VERSION = "2022-06-28"
BASE_URL = "https://api.notion.com/v1"


def _headers() -> dict[str, str]:
    token = os.environ.get("NOTION_API_KEY")
    if not token:
        raise ValueError("NOTION_API_KEY가 설정되지 않았습니다. .env 또는 환경 변수를 확인하세요.")
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def query_database(
    database_id: str,
    page_size: int = 100,
    start_cursor: str | None = None,
    last_edited_after: str | None = None,
) -> dict[str, Any]:
    """
    데이터베이스를 쿼리해 페이지 목록을 가져옵니다.
    
    Args:
        database_id: Notion DB URL에 있는 32자리 ID (하이픈 제거해도 됨)
        page_size: 한 번에 가져올 페이지 수 (최대 100)
        start_cursor: 페이지네이션용 커서
        last_edited_after: ISO 8601 날짜 (예: "2024-03-01T00:00:00Z")
                          이 시각 이후 수정된 페이지만 가져옴
    """
    url = f"{BASE_URL}/databases/{database_id}/query"
    payload: dict[str, Any] = {"page_size": page_size}
    
    if start_cursor:
        payload["start_cursor"] = start_cursor
    
    # 날짜 필터 추가
    if last_edited_after:
        payload["filter"] = {
            "timestamp": "last_edited_time",
            "last_edited_time": {
                "after": last_edited_after
            }
        }

    with httpx.Client(timeout=30.0) as client:
        resp = client.post(url, json=payload, headers=_headers())
        resp.raise_for_status()
        return resp.json()


def get_block_children(block_id: str, page_size: int = 100, start_cursor: str | None = None) -> dict[str, Any]:
    """
    블록(또는 페이지)의 자식 블록 목록을 가져옵니다.
    페이지 본문을 읽을 때 페이지 ID를 block_id로 넣으면 됩니다.
    """
    url = f"{BASE_URL}/blocks/{block_id}/children"
    params: dict[str, Any] = {"page_size": page_size}
    if start_cursor:
        params["start_cursor"] = start_cursor

    with httpx.Client(timeout=30.0) as client:
        resp = client.get(url, params=params, headers=_headers())
        resp.raise_for_status()
        return resp.json()


def retrieve_page(page_id: str) -> dict[str, Any]:
    """페이지 메타데이터를 가져옵니다 (제목 등 properties)."""
    url = f"{BASE_URL}/pages/{page_id}"
    with httpx.Client(timeout=30.0) as client:
        resp = client.get(url, headers=_headers())
        resp.raise_for_status()
        return resp.json()


def _extract_rich_text(block: dict[str, Any]) -> str:
    """블록에서 rich_text가 있으면 텍스트만 이어서 반환."""
    # 일반 텍스트 블록
    for key in ("paragraph", "heading_1", "heading_2", "heading_3", "bulleted_list_item", "numbered_list_item", "quote", "callout", "to_do"):
        if key in block:
            rich = block[key].get("rich_text") or []
            return "".join(
                (r.get("plain_text") or "")
                for r in rich
            )
    
    # Notion AI transcription 블록 처리
    if "transcription" in block:
        transcription = block["transcription"]
        rich = transcription.get("rich_text") or []
        text = "".join((r.get("plain_text") or "") for r in rich)
        if text:
            return f"[녹음 전사]\n{text}"
    
    # PDF/파일 블록 처리
    if "file" in block or "pdf" in block:
        file_key = "file" if "file" in block else "pdf"
        file_data = block[file_key]
        
        # 캡션 추출
        caption = file_data.get("caption", [])
        caption_text = "".join((c.get("plain_text") or "") for c in caption)
        
        # URL 추출
        file_type = file_data.get("type")
        url = ""
        if file_type == "file":
            url = file_data.get("file", {}).get("url", "")
        elif file_type == "external":
            url = file_data.get("external", {}).get("url", "")
        
        if url:
            # PDF 텍스트 추출
            try:
                # PDF 파일인지 확인 (URL 또는 캡션에서)
                is_pdf = url.lower().endswith('.pdf') or 'pdf' in caption_text.lower()
                
                if is_pdf:
                    from src.pdf_extractor import extract_text_from_pdf_url
                    pdf_text = extract_text_from_pdf_url(url)
                    return f"[PDF 파일: {caption_text or '제목 없음'}]\n\n{pdf_text}"
                else:
                    return f"[첨부 파일: {caption_text or '제목 없음'}]\nURL: {url}"
            except Exception as e:
                # PDF 추출 실패 시 URL만 반환
                return f"[첨부 파일: {caption_text or '제목 없음'}]\nURL: {url}\n(PDF 추출 실패: {e})"
    
    return ""


def get_page_plain_text(page_id: str, max_pages: int = 10) -> str:
    """
    한 페이지의 본문을 모두 가져와 plain text로 합칩니다.
    페이지네이션을 하며 최대 max_pages 블록 페이지만큼만 요청합니다.
    
    재귀적으로 자식 블록(transcription 등)도 읽습니다.
    """
    combined: list[str] = []
    cursor: str | None = None
    page_count = 0

    while page_count < max_pages:
        data = get_block_children(page_id, page_size=100, start_cursor=cursor)
        results = data.get("results") or []
        for block in results:
            if block.get("type") == "child_page":
                continue
            
            text = _extract_rich_text(block)
            if text.strip():
                combined.append(text)
            
            # 자식 블록이 있으면 재귀 조회 (transcription 등)
            if block.get("has_children"):
                block_id = block["id"]
                try:
                    child_text = _get_children_text(block_id, max_depth=3)
                    if child_text.strip():
                        combined.append(child_text)
                except Exception as e:
                    combined.append(f"[자식 블록 로드 실패: {e}]")

        cursor = data.get("next_cursor")
        page_count += 1
        if not cursor:
            break

    return "\n\n".join(combined)


def _get_children_text(block_id: str, max_depth: int = 3, current_depth: int = 0) -> str:
    """
    블록의 자식 블록들을 재귀적으로 읽어 텍스트로 반환합니다.
    transcription 블록의 실제 내용이 자식에 있을 때 사용합니다.
    """
    if current_depth >= max_depth:
        return ""
    
    combined: list[str] = []
    
    try:
        data = get_block_children(block_id, page_size=100)
        results = data.get("results") or []
        
        for block in results:
            text = _extract_rich_text(block)
            if text.strip():
                combined.append(text)
            
            # 재귀
            if block.get("has_children"):
                child_id = block["id"]
                child_text = _get_children_text(child_id, max_depth, current_depth + 1)
                if child_text.strip():
                    combined.append(child_text)
    except Exception:
        pass
    
    return "\n\n".join(combined)


def get_page_title(page: dict[str, Any]) -> str:
    """Notion 페이지 객체에서 title 속성의 plain_text를 반환."""
    props = page.get("properties") or {}
    # 제목 속성 이름이 "title"이거나 "Name" 등일 수 있음
    for prop in props.values():
        if prop.get("type") == "title":
            titles = prop.get("title") or []
            return "".join((t.get("plain_text") or "") for t in titles)
    return "(제목 없음)"


def get_page_files(page: dict[str, Any]) -> list[dict[str, str]]:
    """
    Notion 페이지 객체에서 files 속성의 파일 목록을 반환.
    반환: [{"name": "file.pdf", "url": "https://...", "type": "pdf|ppt|file"}, ...]
    """
    props = page.get("properties") or {}
    files = []
    
    for prop_name, prop in props.items():
        if prop.get("type") == "files":
            file_list = prop.get("files") or []
            for f in file_list:
                name = f.get("name", "")
                file_type = f.get("type", "")
                
                url = ""
                if file_type == "file":
                    url = f.get("file", {}).get("url", "")
                elif file_type == "external":
                    url = f.get("external", {}).get("url", "")
                
                # 파일 타입 판별
                ext = "file"
                name_lower = name.lower()
                if ".pdf" in name_lower:
                    ext = "pdf"
                elif ".ppt" in name_lower or ".pptx" in name_lower:
                    ext = "ppt"
                
                if url:
                    files.append({"name": name, "url": url, "type": ext})
    
    return files


def extract_pdf_text(url: str) -> str:
    """
    PDF URL에서 텍스트를 추출합니다.
    Notion의 signed URL은 유효 기간이 있으므로 즉시 다운로드합니다.
    """
    if not PDF_AVAILABLE:
        return "[PDF 텍스트 추출 불가: pypdf 미설치]"
    
    try:
        # PDF 다운로드
        with httpx.Client(timeout=60.0) as client:
            resp = client.get(url)
            resp.raise_for_status()
            pdf_content = resp.content
        
        # 임시 파일로 저장
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(pdf_content)
            tmp_path = tmp.name
        
        # PDF 텍스트 추출
        try:
            reader = PdfReader(tmp_path)
            texts = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    texts.append(text)
            
            return "\n\n".join(texts)
        finally:
            # 임시 파일 삭제
            Path(tmp_path).unlink(missing_ok=True)
    
    except Exception as e:
        return f"[PDF 텍스트 추출 실패: {e}]"


def get_page_files(page_data: dict[str, Any]) -> list[dict[str, str]]:
    """
    페이지 속성에서 파일 목록을 추출합니다.
    
    Returns:
        [{"name": "파일명", "url": "다운로드 URL", "type": "file/external"}, ...]
    """
    props = page_data.get("properties") or {}
    files = []
    
    # 가능한 파일 필드 이름들
    for key, prop in props.items():
        prop_type = prop.get("type")
        
        if prop_type == "files":
            file_items = prop.get("files") or []
            for item in file_items:
                file_type = item.get("type")  # "file" 또는 "external"
                name = item.get("name", "")
                url = ""
                
                if file_type == "file":
                    url = item.get("file", {}).get("url", "")
                elif file_type == "external":
                    url = item.get("external", {}).get("url", "")
                
                if url:
                    files.append({
                        "name": name,
                        "url": url,
                        "type": file_type
                    })
    
    return files

