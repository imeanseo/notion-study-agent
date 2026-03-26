# 주간 통합 퀴즈 시스템 - 구현 개요

## 📋 요구사항 최종 정리

### 사용자 워크플로우
1. **화수목**: 수업 듣고 강의 노트 + PDF 자료를 Notion에 업로드
2. **금요일 아침**: 자동으로 이번 주 전체 과목 통합 퀴즈가 Notion에 생성됨
3. **사용자**: 퀴즈 풀기 (문제만 먼저 표시)
4. **완료 후**: 맨 아래 토글을 열어 정답 및 해설 확인

### 퀴즈 형식
```
📝 3월 1주차 주간 퀴즈 (2026.03.07)

## 프롬프트 엔지니어링
1. [객관식 문제]
   1) 선택지1
   2) 선택지2
   3) 선택지3
   4) 선택지4

2. [주관식 문제]
   답: _____________

...10문제

## 실용 자연어처리
1. [문제...]
...

---
📌 정답 및 해설 (클릭하여 펼치기)
  ▶ 프롬프트 엔지니어링
    1. 정답: 2번
       해설: [강의 내용 기반 설명]
       출처: [강의 페이지 링크]
    2. 정답: ...
```

---

## ✅ 현재 완료된 기능

### Step 1: Notion 데이터 수집 ✅
- `src/nodes/fetch_notion.py`
- 증분 업데이트 (`.last_sync` 파일 기반)
- 텍스트 블록 추출
- 여러 Lecture Notes DB 지원

### Step 2: LLM 퀴즈 생성 ✅
- `src/nodes/quiz.py`
- Ollama (exaone3.5:7.8b) 연동
- 객관식 + 주관식 혼합 (10문제)
- 출처 힌트 포함
- 수업 오리엔테이션 제외

### 기타
- `src/state.py` - LangGraph 상태 정의
- `src/notion_client.py` - Notion API 래퍼
- `src/pdf_extractor.py` - PDF 텍스트 추출기 (신규 추가)

---

## 🔧 다음 구현 단계

### 1. PDF 통합 (우선순위: 높음)
**목표**: 강의 노트 + PDF 자료를 통합하여 퀴즈 생성

**구현 계획**:
```python
# src/nodes/fetch_notion.py 수정
def fetch_lecture_content(state):
    # 1. 텍스트 블록 수집 (기존)
    # 2. PDF 파일 블록 감지
    # 3. PDF 다운로드 및 텍스트 추출
    # 4. 병합: combined_transcript = 텍스트 + PDF 내용
```

**Notion API PDF 처리**:
- `file` 타입 블록 감지: `block["type"] == "file"`
- URL 추출: `block["file"]["file"]["url"]` (만료 시간 있음)
- `pdf_extractor.extract_text_from_pdf_url()` 호출

**필요 작업**:
- [ ] `fetch_notion.py`에 PDF 블록 감지 로직 추가
- [ ] `notion_client.py`에 파일 다운로드 함수 추가
- [ ] 테스트: PDF 포함된 페이지로 퀴즈 생성

---

### 2. 과목별 퀴즈 통합 (우선순위: 높음)
**목표**: 여러 Lecture Notes DB를 쿼리하여 과목별 퀴즈 생성

**구현 계획**:
```python
# 새 노드: src/nodes/fetch_weekly.py
def fetch_weekly_content(state):
    """이번 주 모든 과목의 강의 노트 수집"""
    courses = {
        "프롬프트엔지니어링": os.getenv("LECTURE_NOTES_프롬프트"),
        "실용NLP": os.getenv("LECTURE_NOTES_실용NLP"),
        "컴퓨터수학": os.getenv("LECTURE_NOTES_컴퓨터수학"),
        "영어DB": os.getenv("LECTURE_NOTES_영어DB"),
        "미국시": os.getenv("LECTURE_NOTES_미국시"),
        # 캡스톤 제외 (프로젝트 수업)
    }
    
    courses_data = {}
    for name, db_id in courses.items():
        # 이번 주(월~목) 페이지만 필터링
        pages = query_database(db_id, last_edited_after="2026-03-03")
        courses_data[name] = combine_texts(pages)
    
    return {"courses_data": courses_data}

# 수정: src/nodes/quiz.py
def generate_weekly_quiz(state):
    """과목별로 퀴즈 생성"""
    course_quizzes = []
    for course_name, transcript in state["courses_data"].items():
        quiz_items = generate_quiz_for_course(course_name, transcript)
        course_quizzes.append({
            "course_name": course_name,
            "quiz_items": quiz_items
        })
    
    return {"course_quizzes": course_quizzes}
```

**필요 작업**:
- [ ] `fetch_weekly.py` 노드 생성
- [ ] 날짜 필터링 (이번 주만)
- [ ] `quiz.py` 수정: 과목별 반복 생성
- [ ] `state.py` 업데이트 완료 ✅

---

### 3. Notion 업로드 (우선순위: 중간)
**목표**: 생성된 퀴즈를 Notion 페이지로 업로드

**구현 계획**:
```python
# 신규: src/nodes/publish.py
def publish_to_notion(state):
    """주간 퀴즈를 Notion 페이지로 생성"""
    # 1. 페이지 생성 (제목: "3월 1주차 주간 퀴즈")
    # 2. 과목별 섹션 추가 (heading_2)
    # 3. 문제 블록 추가 (numbered_list_item)
    # 4. 답안 토글 블록 추가 (toggle)
    
    page_id = create_quiz_page(title, blocks)
    return {"notion_quiz_page_id": page_id}
```

**Notion 블록 구조**:
```python
blocks = [
    # 제목
    {"type": "heading_1", "heading_1": {"rich_text": [{"text": {"content": "📝 3월 1주차 주간 퀴즈"}}]}},
    
    # 과목 섹션
    {"type": "heading_2", "heading_2": {"rich_text": [{"text": {"content": "프롬프트 엔지니어링"}}]}},
    
    # 문제
    {"type": "numbered_list_item", "numbered_list_item": {"rich_text": [{"text": {"content": "질문..."}}]}},
    
    # 답안 토글
    {"type": "toggle", "toggle": {
        "rich_text": [{"text": {"content": "📌 정답 및 해설"}}],
        "children": [
            {"type": "paragraph", "paragraph": {"rich_text": [{"text": {"content": "1. 정답: 2번"}}]}}
        ]
    }}
]
```

**필요 작업**:
- [ ] `publish.py` 노드 생성
- [ ] `notion_client.py`에 페이지/블록 생성 함수 추가
- [ ] 토글 블록 테스트
- [ ] 퀴즈 DB 생성 (메타데이터 저장용)

---

### 4. 자동화 (우선순위: 낮음)
**목표**: 금요일 아침 자동 실행

**방법 1: macOS Launchd** (추천)
```xml
<!-- ~/Library/LaunchAgents/com.user.weekly-quiz.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.weekly-quiz</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/path/to/run_weekly_quiz.py</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Weekday</key>
        <integer>5</integer>  <!-- 금요일 -->
        <key>Hour</key>
        <integer>7</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
</dict>
</plist>
```

**방법 2: GitHub Actions** (클라우드)
```yaml
# .github/workflows/weekly-quiz.yml
name: Weekly Quiz
on:
  schedule:
    - cron: '0 22 * * 4'  # 목요일 22:00 UTC (금요일 07:00 KST)
  workflow_dispatch:
jobs:
  generate-quiz:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install -r requirements.txt
      - run: python run_weekly_quiz.py
```

---

## 🗂️ 파일 구조 (최종)

```
notion/
├── PLAN.md                      # 전체 계획
├── IMPLEMENTATION_SUMMARY.md    # 이 파일
├── requirements.txt
├── .env
├── src/
│   ├── state.py                 # ✅ State 정의 (업데이트됨)
│   ├── notion_client.py         # ✅ Notion API 래퍼
│   ├── pdf_extractor.py         # ✅ PDF 텍스트 추출 (신규)
│   ├── nodes/
│   │   ├── fetch_notion.py      # ✅ 단일 DB 수집
│   │   ├── fetch_weekly.py      # 🔲 주간 통합 수집 (TODO)
│   │   ├── quiz.py              # ✅ 퀴즈 생성
│   │   └── publish.py           # 🔲 Notion 업로드 (TODO)
│   └── graph.py                 # 🔲 그래프 업데이트 필요
├── run_step1.py                 # ✅ 테스트용
├── run_step2.py                 # ✅ 테스트용
└── run_weekly_quiz.py           # 🔲 메인 실행 스크립트 (TODO)
```

---

## 📊 진행 상황

| 단계 | 기능 | 상태 | 비고 |
|------|------|------|------|
| Step 1 | Notion 텍스트 수집 | ✅ 완료 | 증분 업데이트 지원 |
| Step 2 | LLM 퀴즈 생성 | ✅ 완료 | Ollama exaone3.5 |
| - | PDF 텍스트 추출기 | ✅ 완료 | PyMuPDF 사용 |
| - | State 업데이트 | ✅ 완료 | 과목별 데이터 지원 |
| Step 3 | PDF 통합 | 🔲 TODO | fetch_notion.py 수정 필요 |
| Step 4 | 과목별 퀴즈 통합 | 🔲 TODO | fetch_weekly.py 신규 |
| Step 5 | Notion 업로드 | 🔲 TODO | publish.py 신규 |
| Step 6 | 자동화 | 🔲 TODO | Launchd 또는 GitHub Actions |

---

## 🎯 다음 액션 아이템

1. **PDF 통합 테스트**
   ```bash
   pip install pymupdf
   python -c "from src.pdf_extractor import extract_text_from_pdf; print(extract_text_from_pdf('test.pdf')[:500])"
   ```

2. **과목별 수집 구현**
   - `src/nodes/fetch_weekly.py` 생성
   - 이번 주 날짜 필터링 로직

3. **Notion 업로드 프로토타입**
   - 간단한 페이지 생성 테스트
   - 토글 블록 형식 확인

어느 것부터 진행하시겠습니까?
