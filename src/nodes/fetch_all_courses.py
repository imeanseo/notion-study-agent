"""
Step 1: Courses DB의 모든 수업을 스캔하고, 각 수업의 Lecture Notes에서
새로운 강의 페이지를 자동으로 수집합니다.

증분 업데이트:
- 각 수업별로 .last_sync_<수업명> 파일에 마지막 동기화 시각 저장
- 해당 시각 이후 수정된 페이지만 가져옴
"""
import os
from datetime import datetime, timezone
from pathlib import Path
from src.state import LecturePage, StudyAgentState
from src.notion_client import (
    query_database,
    get_page_plain_text,
    get_page_title,
    get_page_files,
    extract_pdf_text,
    get_block_children,
)


SYNC_DIR = Path(__file__).parent.parent.parent / ".sync"
SYNC_DIR.mkdir(exist_ok=True)


def _get_last_sync_time(course_name: str) -> str | None:
    """특정 수업의 마지막 동기화 시각을 읽어옵니다."""
    sync_file = SYNC_DIR / f"last_sync_{course_name}.txt"
    if not sync_file.exists():
        return None
    return sync_file.read_text().strip()


def _save_sync_time(course_name: str, timestamp: str | None = None):
    """현재 시각을 동기화 시각으로 저장합니다."""
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat()
    sync_file = SYNC_DIR / f"last_sync_{course_name}.txt"
    sync_file.write_text(timestamp)


def fetch_lecture_content(state: StudyAgentState) -> dict:
    """
    Courses DB의 모든 수업을 스캔하여 Lecture Notes를 수집합니다.
    
    워크플로우:
    1. Courses DB 쿼리 (모든 수업 목록)
    2. 제외할 수업 필터링 (EXCLUDED_COURSES)
    3. 각 수업 페이지의 자식 블록 확인
    4. "Lecture Notes" 또는 3번째 DB 찾기
    5. 해당 DB에서 새로운 강의 페이지만 읽기 (증분 업데이트)
    6. 본문 + PDF 텍스트 추출
    
    반환: { 
        "lecture_pages": [...],  # 모든 수업의 강의 페이지
        "combined_transcript": "...",  # 전체 합친 텍스트
        "courses_scanned": ["수업1", "수업2"],  # 스캔한 수업 목록
        "courses_excluded": ["제외수업1"],  # 제외된 수업 목록
    }
    """
    courses_db_id = os.environ.get("NOTION_COURSES_DB_ID")
    if not courses_db_id:
        return {
            "lecture_pages": [],
            "combined_transcript": "",
            "error": "NOTION_COURSES_DB_ID가 설정되지 않았습니다.",
        }
    
    # 제외할 수업 목록 (환경변수에서 읽기)
    excluded_str = os.environ.get("EXCLUDED_COURSES", "")
    excluded_courses = [x.strip() for x in excluded_str.split(",") if x.strip()]
    
    print("🔍 Courses DB 스캔 시작...")
    if excluded_courses:
        print(f"   ⛔ 제외할 수업: {', '.join(excluded_courses)}")
    print()
    
    try:
        # 1. Courses DB에서 모든 수업 조회
        courses_data = query_database(courses_db_id, page_size=50)
        courses = courses_data.get("results", [])
        
        print(f"📚 총 {len(courses)}개 수업 발견\n")
        
        all_lecture_pages = []
        all_texts = []
        courses_scanned = []
        courses_excluded_list = []
        
        for course in courses:
            course_id = course["id"]
            course_title = get_page_title(course)
            
            if not course_title.strip():
                continue
            
            # 2. 제외할 수업인지 확인
            should_exclude = False
            for excluded in excluded_courses:
                if excluded in course_title:
                    should_exclude = True
                    break
            
            if should_exclude:
                print(f"⛔ {course_title} (제외됨)")
                courses_excluded_list.append(course_title)
                continue
            
            print(f"📖 {course_title}")
            
            # 2. 수업 페이지의 자식 DB 찾기
            try:
                children = get_block_children(course_id, page_size=20)
                child_dbs = []
                
                for block in children.get("results", []):
                    if block.get("type") == "child_database":
                        db_title = block.get("child_database", {}).get("title", "")
                        child_dbs.append({
                            "id": block["id"],
                            "title": db_title
                        })
                
                # 3번째 DB를 Lecture Notes로 가정 (또는 "Lecture Notes" 이름 매칭)
                lecture_notes_db = None
                for db in child_dbs:
                    if "lecture" in db["title"].lower() or "note" in db["title"].lower():
                        lecture_notes_db = db
                        break
                
                if not lecture_notes_db and len(child_dbs) >= 3:
                    lecture_notes_db = child_dbs[2]  # 3번째 DB
                
                if not lecture_notes_db:
                    print(f"   ⚠️  Lecture Notes DB를 찾을 수 없습니다.\n")
                    continue
                
                lecture_db_id = lecture_notes_db["id"]
                print(f"   📝 Lecture Notes DB: {lecture_notes_db['title'] or '(제목 없음)'}")
                
                # 3. 증분 업데이트: 마지막 동기화 이후만
                last_sync = _get_last_sync_time(course_title)
                sync_start_time = datetime.now(timezone.utc).isoformat()
                
                # 4. Lecture Notes DB 쿼리
                lecture_data = query_database(
                    lecture_db_id,
                    page_size=50,
                    last_edited_after=last_sync
                )
                
                lecture_pages = lecture_data.get("results", [])
                new_count = len(lecture_pages)
                
                if new_count == 0:
                    print(f"   ✅ 새로운 강의 없음\n")
                    continue
                
                print(f"   📄 새로운 강의: {new_count}개")
                
                # 5. 각 강의 페이지 처리
                for item in lecture_pages:
                    page_id = item["id"]
                    title = get_page_title(item)
                    
                    # 본문 텍스트
                    try:
                        plain_text = get_page_plain_text(page_id, max_pages=20)
                    except Exception as e:
                        plain_text = f"[본문 로드 실패: {e}]"
                    
                    # PDF 파일
                    pdf_texts = []
                    try:
                        files = get_page_files(item)
                        for file_info in files:
                            if file_info["name"].lower().endswith('.pdf'):
                                try:
                                    pdf_text = extract_pdf_text(file_info["url"])
                                    pdf_texts.append(f"[PDF: {file_info['name']}]\n\n{pdf_text}")
                                    print(f"      📎 PDF: {file_info['name']} ({len(pdf_text):,}자)")
                                except Exception:
                                    pass
                    except Exception:
                        pass
                    
                    # 통합
                    combined_text = plain_text
                    if pdf_texts:
                        combined_text = f"{plain_text}\n\n{'='*60}\n📎 첨부 PDF\n{'='*60}\n\n" + "\n\n".join(pdf_texts)
                    
                    all_lecture_pages.append({
                        "page_id": page_id,
                        "title": f"[{course_title}] {title}",
                        "plain_text": combined_text,
                    })
                    
                    if combined_text.strip():
                        all_texts.append(f"# [{course_title}] {title}\n\n{combined_text}")
                
                # 동기화 시각 저장
                _save_sync_time(course_title, sync_start_time)
                courses_scanned.append(course_title)
                print()
                
            except Exception as e:
                print(f"   ❌ 오류: {e}\n")
                continue
        
        combined = "\n\n---\n\n".join(all_texts) if all_texts else ""
        
        print(f"✅ 스캔 완료!")
        print(f"   수업 수: {len(courses_scanned)}개")
        if courses_excluded_list:
            print(f"   제외된 수업: {len(courses_excluded_list)}개")
        print(f"   강의 수: {len(all_lecture_pages)}개")
        print(f"   총 텍스트: {len(combined):,}자\n")
        
        return {
            "lecture_pages": all_lecture_pages,
            "combined_transcript": combined,
            "courses_scanned": courses_scanned,
            "courses_excluded": courses_excluded_list,
            "is_incremental": True,
        }
    
    except Exception as e:
        return {
            "lecture_pages": [],
            "combined_transcript": "",
            "error": str(e),
        }
