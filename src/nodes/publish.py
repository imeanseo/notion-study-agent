"""
Step 3: 생성된 퀴즈를 Notion "오늘의 퀴즈" DB에 주차별로 업로드합니다.
"""
import os
import httpx
from datetime import datetime
from src.state import StudyAgentState


NOTION_VERSION = "2022-06-28"
BASE_URL = "https://api.notion.com/v1"


def _get_headers() -> dict[str, str]:
    token = os.environ.get("NOTION_API_KEY")
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def publish_quiz_to_notion(state: StudyAgentState) -> dict:
    """
    state의 quiz_items를 Notion "오늘의 퀴즈" DB에 업로드합니다.
    
    주차 계산:
    - 학기 시작일을 기준으로 현재 주차 계산
    
    Notion 구조:
    - "오늘의 퀴즈" DB에 "N주차 퀴즈 - 프롬프트엔지니어링" 페이지 생성
    - 페이지 내부에 표 형태로 퀴즈 작성
    
    반환: {"notion_quiz_page_id": "...", "quiz_week": N}
    """
    quiz_items = state.get("quiz_items") or []
    if not quiz_items:
        return {
            "notion_quiz_page_id": None,
            "error": "퀴즈가 생성되지 않았습니다.",
        }
    
    # 환경변수에서 설정 읽기
    quiz_db_id = os.environ.get("NOTION_QUIZ_DB_ID")
    semester_start = os.environ.get("SEMESTER_START_DATE", "2026-03-03")
    
    if not quiz_db_id:
        return {
            "notion_quiz_page_id": None,
            "error": "NOTION_QUIZ_DB_ID가 설정되지 않았습니다.",
        }
    
    # 현재 주차 계산
    try:
        start_date = datetime.fromisoformat(semester_start).date()
        today = datetime.now().date()
        days_diff = (today - start_date).days
        week_number = (days_diff // 7) + 1
    except Exception:
        week_number = 1
    
    # 페이지 제목
    page_title = f"{week_number}주차 퀴즈 - 프롬프트엔지니어링"
    
    print(f"\n📤 Notion 업로드 시작...")
    print(f"   제목: {page_title}")
    print(f"   퀴즈 수: {len(quiz_items)}개")
    
    try:
        # 1. 페이지 생성
        page_data = {
            "parent": {"database_id": quiz_db_id},
            "properties": {
                "Name": {
                    "title": [{"text": {"content": page_title}}]
                }
            },
            "children": _build_quiz_blocks(quiz_items)
        }
        
        headers = _get_headers()
        resp = httpx.post(
            f"{BASE_URL}/pages",
            json=page_data,
            headers=headers,
            timeout=30
        )
        resp.raise_for_status()
        
        page_id = resp.json()["id"]
        page_url = resp.json()["url"]
        
        print(f"✅ 업로드 완료!")
        print(f"   페이지 ID: {page_id}")
        print(f"   URL: {page_url}\n")
        
        return {
            "notion_quiz_page_id": page_id,
            "notion_quiz_url": page_url,
            "quiz_week": week_number,
            "quiz_count": len(quiz_items),
        }
    
    except Exception as e:
        print(f"❌ 업로드 실패: {e}\n")
        return {
            "notion_quiz_page_id": None,
            "error": f"Notion 업로드 실패: {str(e)}",
            "quiz_week": week_number,
        }


def _build_quiz_blocks(quiz_items: list) -> list:
    """
    퀴즈 목록을 Notion 블록 형식으로 변환합니다.
    
    구조:
    - heading_2: "퀴즈"
    - numbered_list: 각 문제
      - 객관식: 선택지를 bulleted_list로
      - 주관식: "정답: ..."
    - toggle: "정답 및 출처" (접기)
    """
    blocks = [
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"text": {"content": "📝 퀴즈"}}]
            }
        }
    ]
    
    for i, quiz in enumerate(quiz_items, 1):
        question = quiz["question"]
        kind = quiz["kind"]
        
        # 문제 번호와 질문
        question_block = {
            "object": "block",
            "type": "numbered_list_item",
            "numbered_list_item": {
                "rich_text": [{"text": {"content": question}}]
            }
        }
        blocks.append(question_block)
        
        # 객관식 선택지
        if kind == "multiple_choice":
            options = quiz.get("options", [])
            for opt in options:
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"text": {"content": opt}}]
                    }
                })
        
        # 정답 (토글로 숨김)
        correct_text = ""
        if kind == "multiple_choice":
            correct_idx = quiz.get("correct_index", 0)
            options = quiz.get("options", [])
            if correct_idx < len(options):
                correct_text = f"정답: {correct_idx + 1}. {options[correct_idx]}"
        else:
            correct_text = f"정답: {quiz.get('correct_answer', '')}"
        
        source_hint = quiz.get("source_hint", "")
        toggle_content = f"{correct_text}\n💡 출처: {source_hint}" if source_hint else correct_text
        
        blocks.append({
            "object": "block",
            "type": "toggle",
            "toggle": {
                "rich_text": [{"text": {"content": "정답 보기"}}],
                "children": [{
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"text": {"content": toggle_content}}]
                    }
                }]
            }
        })
        
        # 구분선
        if i < len(quiz_items):
            blocks.append({
                "object": "block",
                "type": "divider",
                "divider": {}
            })
    
    return blocks
