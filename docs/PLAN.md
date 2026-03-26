# 주간 통합 퀴즈 생성 & 학습 에이전트

## 목표
- **매주 금요일 아침** 이번 주 모든 수업(화수목) 내용을 통합한 퀴즈 자동 생성
- 강의 녹음 텍스트 + **교수님 제공 PDF 자료**를 모두 활용
- AI가 핵심 개념을 추출해 **객관식/주관식 퀴즈** 생성 (과목당 10문제)
- **문제와 답안을 분리**하여 Notion에 업로드 (답안은 토글로 숨김)
- 틀린 문제에 대해 **"강의 15분 지점에서 설명한 내용"** 식의 **학습 에이전트** 가이드 제공

---

## 수업 일정
- **화수목**: 수업 (프롬프트엔지니어링, 실용NLP, 컴퓨터수학 등)
- **금요일 아침**: 주간 통합 퀴즈 자동 생성 및 Notion 업로드

---

## 아키텍처 (LangGraph)

```
[이번 주 Lecture Notes] → [강의 텍스트 + PDF 수집] → [과목별 퀴즈 생성]
         ↓                           ↓                        ↓
   [화수목 3일간]              [증분 업데이트]         [통합 퀴즈 문서 생성]
         ↓                                                     ↓
   [금요일 아침] ←────────────── [Notion 업로드: 문제 + 답안(토글)]
         ↓
   [사용자 퀴즈 풀이]
         ↓
   [채점 + 틀린 문제 → 학습 에이전트]
         ↓
   [강의 위치 가이드] (해당 구간 링크/요약)
```

### LangGraph 노드 구성
1. **fetch_weekly_content** – 이번 주(월~목) 모든 수업의 Lecture Notes 수집
   - 각 수업의 Lecture Notes DB 쿼리
   - 텍스트 블록 + PDF 파일 추출
2. **extract_pdf_text** – PDF 자료를 텍스트로 변환 (PyMuPDF 또는 pdfplumber)
3. **generate_weekly_quiz** – 과목별로 10문제씩 생성 → 통합 퀴즈 문서 생성
4. **publish_to_notion** – Notion에 퀴즈 페이지 생성 (문제 먼저, 답안은 맨 아래 토글)
5. **grade_and_guide** – 사용자 답안 채점, 틀린 문제에 대해 학습 가이드

---

## 단계별 실행 계획

### Step 1: 주간 학습 자료 수집 ✅ 완료
- [x] 각 수업의 Lecture Notes DB ID 확인 (.env에 저장됨)
- [x] 증분 업데이트: 마지막 동기화 이후 변경된 페이지만 가져오기
- [x] 텍스트 블록 추출
- [ ] **PDF 파일 다운로드 및 텍스트 추출** (다음 단계)

**산출물**: `fetch_notion.py` 완료, 텍스트 수집 작동 확인

---

### Step 2: 퀴즈 생성 ✅ 완료
- [x] Ollama (exaone3.5:7.8b) 연동
- [x] 강의 내용 기반 퀴즈 생성 (과목당 10문제)
- [x] 객관식(4지선다) + 주관식(단답) 혼합
- [x] 출처 힌트 포함
- [ ] **과목별 퀴즈 생성 및 통합** (다음 단계)
- [ ] **PDF 내용 포함** (다음 단계)

**산출물**: `quiz.py` 완료, 퀴즈 생성 작동 확인

---

### Step 3: Notion 업로드 (진행 예정)
- [ ] 주간 통합 퀴즈 페이지 생성
- [ ] 형식: 과목별 섹션 → 문제 10개 → 맨 아래 "정답 및 해설" 토글
- [ ] 금요일 아침 자동 실행 (cron 설정)
- [ ] 퀴즈 DB에 저장 (과목명, 주차, 생성일시 메타데이터)

**Notion 페이지 구조 예시**:
```
📝 3월 1주차 주간 퀴즈 (2026.03.07)

## 프롬프트 엔지니어링
1. [문제...]
2. [문제...]
...

## 실용 자연어처리
1. [문제...]
...

---
📌 정답 및 해설 (토글)
  - 프롬프트 엔지니어링
    1. 정답: 2번 / 해설: ...
  - 실용 자연어처리
    1. 정답: ...
```

---

### Step 4: PDF 텍스트 추출 (진행 예정)
- [ ] Notion에 첨부된 PDF 파일 감지 (file block)
- [ ] PDF 다운로드 (Notion API 파일 URL)
- [ ] 텍스트 추출 (PyMuPDF 또는 pdfplumber)
- [ ] 강의 녹음 텍스트와 병합

**필요 라이브러리**: `pymupdf` 또는 `pdfplumber`

---

### Step 5: 학습 에이전트 (향후 계획)
- [ ] 사용자가 제출한 답안을 채점 (정답/오답 판별)
- [ ] 틀린 문제에 대해:
  - 해당 문항의 **출처(강의 페이지/구간)** 조회
  - "이 부분은 강의 15분 지점에서 설명한 내용입니다" 형식의 안내 문구 생성
  - 가능하면 해당 Notion 페이지 링크 포함

---

## 환경 설정

- **NOTION_API_KEY**: Notion 연동 시크릿 (Integration 토큰)
- **각 수업의 Lecture Notes DB ID** (주간 퀴즈 생성 대상):
  - `LECTURE_NOTES_프롬프트`
  - `LECTURE_NOTES_실용NLP`
  - `LECTURE_NOTES_컴퓨터수학`
  - `LECTURE_NOTES_영어DB`
  - `LECTURE_NOTES_미국시`
  - ~~`LECTURE_NOTES_캡스톤`~~ (프로젝트 수업 - 제외)
- **OLLAMA_MODEL**: 로컬 LLM 모델 (기본값: exaone3.5:7.8b)
- **NOTION_QUIZ_DB_ID**: 주간 퀴즈를 저장할 DB ID (생성 필요)
- **CRON_SCHEDULE**: 금요일 아침 실행 스케줄 (예: `0 7 * * 5` = 매주 금요일 오전 7시)

---

## 디렉터리 구조

```
notion/
├── PLAN.md                 # 이 파일
├── requirements.txt
├── .env
├── src/
│   ├── state.py            # LangGraph State 정의
│   ├── notion_client.py    # Notion API 래퍼
│   ├── pdf_extractor.py    # PDF 텍스트 추출 (신규)
│   ├── nodes/
│   │   ├── fetch_notion.py # Step 1: 강의 내용 수집
│   │   ├── quiz.py         # Step 2: 퀴즈 생성
│   │   ├── publish.py      # Step 3: Notion 업로드
│   │   └── guide.py        # Step 5: 채점 및 학습 가이드
│   └── graph.py            # StateGraph 조립
├── run_step1.py            # Step 1 단독 테스트
├── run_step2.py            # Step 2 단독 테스트
├── run_weekly_quiz.py      # 주간 퀴즈 생성 실행 (금요일 cron)
└── .last_sync              # 증분 업데이트용 타임스탬프
```

---

## 다음 단계

1. **PDF 추출 구현** (Step 4)
2. **과목별 퀴즈 통합** (여러 Lecture Notes DB 쿼리)
3. **Notion 업로드** (Step 3)
4. **Cron 설정** (금요일 아침 자동 실행)
