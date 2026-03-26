# 📚 Notion 자동 퀴즈 생성 시스템

> **Notion에 업로드한 강의 녹음과 PDF를 자동으로 분석하여 주간 퀴즈를 생성하는 학습 자동화 시스템**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Latest-green)](https://github.com/langchain-ai/langgraph)
[![Notion API](https://img.shields.io/badge/Notion-API-black)](https://developers.notion.com/)

---

## ✨ 주요 기능

- 🔄 **자동 수업 스캔**: Notion Courses DB의 모든 수업을 자동으로 감지
- 📝 **증분 업데이트**: 매주 새로운 강의만 읽어서 처리 (`.sync/` 디렉토리 활용)
- 🎙️ **멀티 소스 지원**: Notion AI 녹음 전사 + PDF/PPT 파일 텍스트 추출
- 🤖 **로컬 LLM**: Ollama 사용으로 비용 제로 (OpenAI 대신)
- 📤 **Notion 자동 업로드**: "오늘의 퀴즈" DB에 주차별 퀴즈 자동 생성
- 🔔 **Slack 알림**: 퀴즈 생성 완료/실패 시 실시간 알림
- 🔁 **자동 재시도**: 에러 발생 시 지수 백오프로 최대 3회 재시도
- 📊 **상세 로그**: 실행 이력을 `logs/` 디렉토리에 자동 저장

---

## 🏗️ 아키텍처

### LangGraph 파이프라인

```
┌──────────────────────────────────────────────────────────────┐
│  START                                                        │
└─────────────────────┬────────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────────────┐
│  Step 1: fetch_all_courses                                   │
│  • Courses DB에서 모든 수업 스캔                              │
│  • 제외 수업 필터링 (EXCLUDED_COURSES)                        │
│  • 각 수업의 Lecture Notes DB 찾기                            │
│  • 증분 업데이트 (.sync/last_sync_<수업명>.txt)              │
│  • 본문 + Notion AI 녹음 + PDF 텍스트 추출                   │
└─────────────────────┬────────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────────────┐
│  Step 2: generate_quiz                                        │
│  • Ollama LLM으로 퀴즈 생성                                   │
│  • 한국어 퀴즈 (영어 자료도 한국어로)                         │
│  • 10-15개 객관식 + 출처 힌트                                 │
└─────────────────────┬────────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────────────┐
│  Step 3: publish_quiz                                         │
│  • "오늘의 퀴즈" DB에 페이지 생성                             │
│  • 제목: "N주차 퀴즈 - <과목명>"                              │
│  • Notion 블록 포맷 (번호 목록, 토글 등)                      │
└─────────────────────┬────────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────────────┐
│  END                                                          │
│  • Slack 알림 전송                                            │
│  • 로그 저장                                                  │
└──────────────────────────────────────────────────────────────┘
```

---

## 🚀 빠른 시작

### 1. 설치

```bash
# 레포지토리 클론
git clone https://github.com/YOUR_USERNAME/notion-quiz-generator.git
cd notion-quiz-generator

# 의존성 설치
pip install -r requirements.txt

# Ollama 설치 (Mac)
brew install ollama

# Ollama 모델 다운로드
ollama pull exaone3.5:7.8b
# 또는
ollama pull solar
```

### 2. 환경 설정

```bash
# .env 파일 생성
cp .env.example .env
```

`.env` 파일 수정:

```bash
# === Notion API 설정 ===
NOTION_API_KEY=your_notion_integration_token

# === 2026 봄학기 수업 (자동 스캔) ===
NOTION_COURSES_DB_ID=your_courses_database_id
NOTION_QUIZ_DB_ID=your_quiz_database_id
SEMESTER_START_DATE=2026-03-03

# === 제외할 수업 (쉼표로 구분) ===
EXCLUDED_COURSES=언어공학캡스톤디자인

# === LLM 설정 ===
OLLAMA_MODEL=exaone3.5:7.8b

# === Slack 알림 (선택) ===
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### 3. Notion 연동

1. https://www.notion.so/my-integrations 에서 Integration 생성
2. `NOTION_API_KEY` 복사
3. Notion에서 Courses DB와 오늘의 퀴즈 DB를 Integration에 연결:
   - 페이지 우측 상단 `•••` → "Add connections" → Integration 선택

### 4. 실행

```bash
# 전체 파이프라인 실행 (모니터링 + Slack 알림)
python run_with_monitoring.py

# 또는 간단히
python run_full_pipeline.py
```

---

## 📊 실행 결과 예시

```
🔍 Courses DB 스캔 시작...
   ⛔ 제외할 수업: 언어공학캡스톤디자인

📚 총 6개 수업 발견

⛔ 언어공학캡스톤디자인(A01285101-01) (제외됨)

📖 언어모델을위한프롬프트엔지니어링(A01283101-01)
   📝 Lecture Notes DB: (제목 없음)
   📄 새로운 강의: 2개
      📎 PDF: Lec1_Intro.pdf (29,833자)
      📎 PDF: Lec2_LLM&PromptEngineering.pdf (78,123자)

📖 실용자연어처리(A10402201-01)
   📝 Lecture Notes DB: (제목 없음)
   ✅ 새로운 강의 없음

📖 컴퓨터수학(V41002301-01)
   📝 Lecture Notes DB: (제목 없음)
   📄 새로운 강의: 1개

✅ 스캔 완료!
   수업 수: 5개
   제외된 수업: 1개
   강의 수: 3개
   총 텍스트: 279,872자

---

🤖 퀴즈 생성 중... (Ollama exaone3.5:7.8b 모델)

✅ 12개 퀴즈 생성 완료

---

📤 Notion 업로드 시작...
   제목: 2주차 퀴즈 - 프롬프트엔지니어링

✅ 업로드 완료!
   URL: https://notion.so/...
```

---

## 🔄 자동화 설정

### cron으로 매주 자동 실행

```bash
# crontab 편집
crontab -e

# 매주 금요일 21:00에 퀴즈 생성
0 21 * * 5 cd /path/to/notion-quiz-generator && /usr/local/bin/python3 run_with_monitoring.py
```

### 워크플로우

1. **월~금**: Notion에 강의 녹음 + PDF 업로드
2. **금요일 밤 21:00**: 자동으로 퀴즈 생성 → Notion 업로드 → Slack 알림 📱
3. **주말**: 퀴즈 풀면서 복습! 🎉

---

## 📁 프로젝트 구조

```
notion-quiz-generator/
├── .env                          # 환경 변수 (gitignore)
├── .env.example                  # 환경 변수 템플릿
├── .gitignore                    # Git 제외 파일
├── README.md                     # 이 문서
├── requirements.txt              # Python 의존성
│
├── run_full_pipeline.py          # 간단 실행 스크립트
├── run_with_monitoring.py        # 모니터링 + 재시도 + Slack 알림 ✅
│
├── src/
│   ├── __init__.py
│   ├── state.py                  # LangGraph 상태 정의
│   ├── graph.py                  # LangGraph 파이프라인
│   ├── notion_client.py          # Notion API + PDF 추출
│   └── nodes/
│       ├── __init__.py
│       ├── fetch_all_courses.py  # Step 1: 모든 수업 스캔
│       ├── quiz.py               # Step 2: 퀴즈 생성
│       └── publish.py            # Step 3: Notion 업로드
│
├── .sync/                        # 수업별 동기화 시각 (gitignore)
│   ├── last_sync_프롬프트엔지니어링.txt
│   ├── last_sync_실용자연어처리.txt
│   └── ...
│
├── logs/                         # 실행 로그 (gitignore)
│   ├── run_20260310_210000.log
│   └── ...
│
└── docs/                         # 추가 문서
    ├── INCREMENTAL_UPDATE.md     # 증분 업데이트 상세 설명
    ├── WEEKLY_QUIZ_SETUP.md      # 주간 퀴즈 설정 가이드
    └── IMPLEMENTATION_NOTES.md   # 구현 노트
```

---

## 🎯 주요 기능 상세

### 1. 증분 업데이트 (Incremental Update)

매주 **새로운 강의만** 읽어서 처리합니다.

```
.sync/
├── last_sync_프롬프트엔지니어링.txt    → 2026-03-10T21:00:00Z
├── last_sync_실용자연어처리.txt        → 2026-03-10T21:00:00Z
└── last_sync_컴퓨터수학.txt            → 2026-03-10T21:00:00Z
```

**전체 재스캔이 필요한 경우**:
```bash
# .sync/ 디렉토리 삭제
rm -rf .sync

# 다음 실행 시 모든 강의를 처음부터 읽음
python run_with_monitoring.py
```

### 2. 수업 필터링

시험 안 보는 수업 등을 제외할 수 있습니다:

```bash
# .env
EXCLUDED_COURSES=언어공학캡스톤디자인,교양수업
```

### 3. Ollama 모델 변경

```bash
# .env
OLLAMA_MODEL=solar           # 빠르고 가벼움
# 또는
OLLAMA_MODEL=exaone3.5:7.8b  # 한국어 특화
```

사용 가능한 모델:
```bash
ollama list
```

새 모델 다운로드:
```bash
ollama pull llama3.1:8b
```

### 4. 모니터링 기능

`run_with_monitoring.py`는 다음 기능을 제공:

- ✅ **자동 재시도** (3회, 지수 백오프: 2초, 4초, 8초)
- ✅ **상세 로그** (`logs/run_YYYYMMDD_HHMMSS.log`)
- ✅ **Slack 알림** (성공/실패 모두)
- ✅ **실행 시간 측정**
- ✅ **에러 상세 기록**

로그 확인:
```bash
# 최신 로그 실시간 모니터링
tail -f logs/run_*.log

# 에러만 검색
grep "ERROR" logs/*.log
```

---

## 🔧 트러블슈팅

### Notion API 401 Unauthorized

**원인**: Notion Integration이 페이지/DB에 연결되지 않음

**해결**:
1. Notion에서 해당 페이지 열기
2. 우측 상단 `•••` → "Add connections"
3. 만든 Integration 선택

### Ollama 연결 실패

**원인**: Ollama 서버가 실행되지 않음

**해결**:
```bash
# Ollama 시작
ollama serve

# 또는 백그라운드 실행
ollama serve &
```

### PDF 텍스트 추출 실패

**원인**: 이미지 기반 PDF (OCR 필요)

**현재 상태**: 텍스트 기반 PDF만 지원

**향후 계획**: OCR 기능 추가 예정

### 퀴즈가 생성되지 않음

**확인 사항**:
1. `.sync/` 디렉토리 확인 → 새로운 강의가 있는지
2. `combined_transcript`가 비어있지 않은지
3. Ollama 모델이 정상 작동하는지

---

## 🛠️ 개발자 가이드

### 로컬 개발

```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 개발 의존성 설치
pip install -r requirements.txt

# 코드 실행
python run_full_pipeline.py
```

### 새로운 노드 추가

1. `src/nodes/` 아래에 파일 생성
2. `src/state.py`에 필요한 상태 추가
3. `src/graph.py`에서 그래프에 노드 연결

예시:
```python
# src/nodes/my_node.py
from src.state import StudyAgentState

def my_node(state: StudyAgentState) -> dict:
    # 로직 구현
    return {"new_field": "value"}

# src/graph.py
from src.nodes.my_node import my_node

graph.add_node("my_node", my_node)
graph.add_edge("previous_node", "my_node")
```

---

## 📝 향후 계획

- [ ] Step 4: 학습 에이전트 (틀린 문제 가이드)
- [ ] OCR 지원 (이미지 기반 PDF)
- [ ] PPT 텍스트 추출 개선
- [ ] 주관식 퀴즈 추가
- [ ] 웹 대시보드 (Flask/FastAPI)
- [ ] 복습 알고리즘 (Anki 스타일)

---

## 🤝 기여

이슈와 PR을 환영합니다!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 라이선스

MIT License - 자유롭게 사용하세요!

---

## 🙏 감사

- [LangGraph](https://github.com/langchain-ai/langgraph) - 워크플로우 프레임워크
- [Notion API](https://developers.notion.com/) - 데이터 소스
- [Ollama](https://ollama.ai/) - 로컬 LLM
- [pypdf](https://github.com/py-pdf/pypdf) - PDF 텍스트 추출

---

## 📧 문의

질문이나 제안이 있으시면 이슈를 열어주세요!

**만든 사람**: [@imeanseo](https://github.com/imeanseo)
