# Notion 자동 퀴즈 생성 시스템 - 구현 요약

## 프로젝트 개요

Notion에 업로드한 강의 녹음과 PDF를 자동으로 분석하여 주간 퀴즈를 생성하는 학습 자동화 시스템입니다.

## 핵심 기능

### 1. 자동 수업 스캔
- Notion Courses DB의 모든 수업을 자동으로 감지
- 제외할 수업 필터링 가능 (`EXCLUDED_COURSES`)
- 각 수업의 Lecture Notes DB 자동 탐색

### 2. 증분 업데이트
- `.sync/` 디렉토리에 수업별 마지막 동기화 시각 저장
- 매주 새로운 강의만 읽어서 처리 (비용 절감)
- 전체 재스캔도 가능 (`.sync/` 삭제)

### 3. 멀티 소스 텍스트 추출
- **Notion AI 녹음 전사**: 재귀적으로 children 블록 읽기
- **PDF 파일**: `pypdf`로 다운로드 후 텍스트 추출
- **페이지 본문**: 일반 텍스트 블록

### 4. 로컬 LLM (Ollama)
- OpenAI 대신 Ollama 사용으로 비용 제로
- 한국어 특화 모델: `exaone3.5:7.8b`, `solar`
- 영어 자료도 한국어 퀴즈로 생성

### 5. Notion 자동 업로드
- "오늘의 퀴즈" DB에 주차별 퀴즈 생성
- Notion 블록 포맷: 번호 목록, 토글, 구분선
- 제목: "N주차 퀴즈 - <과목명>"

### 6. 모니터링 & 알림
- 자동 재시도 (최대 3회, 지수 백오프)
- 상세 로그 저장 (`logs/` 디렉토리)
- Slack 알림 (성공/실패)

## 기술 스택

- **LangGraph**: 워크플로우 관리
- **Notion API**: 데이터 읽기/쓰기
- **Ollama**: 로컬 LLM
- **pypdf**: PDF 텍스트 추출
- **httpx**: HTTP 클라이언트
- **python-dotenv**: 환경 변수 관리

## 워크플로우

```
1. fetch_all_courses
   ↓
2. generate_quiz
   ↓
3. publish_quiz
   ↓
4. Slack 알림
```

## 실행 방법

```bash
# 모니터링 포함 (추천)
python run_with_monitoring.py

# 간단 실행
python run_full_pipeline.py
```

## 자동화

```bash
# crontab: 매주 금요일 21:00
0 21 * * 5 cd /path/to/project && python3 run_with_monitoring.py
```

## 주요 파일

- `src/graph.py`: LangGraph 파이프라인
- `src/nodes/fetch_all_courses.py`: 수업 스캔 + 텍스트 추출
- `src/nodes/quiz.py`: 퀴즈 생성
- `src/nodes/publish.py`: Notion 업로드
- `src/notion_client.py`: Notion API 래퍼
- `run_with_monitoring.py`: 모니터링 + 재시도

## 트러블슈팅

### Notion API 401 에러
- 해결: Notion 페이지/DB에 Integration 연결

### PDF 추출 실패
- 현재: 텍스트 기반 PDF만 지원
- 향후: OCR 추가 예정

### 퀴즈 미생성
- 확인: `.sync/` 디렉토리, 새 강의 여부

## 향후 계획

- [ ] 학습 에이전트 (틀린 문제 가이드)
- [ ] OCR 지원
- [ ] PPT 텍스트 추출 개선
- [ ] 웹 대시보드
