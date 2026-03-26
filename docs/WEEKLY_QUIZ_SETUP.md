# 매주 자동 퀴즈 생성 시스템

이제 **프롬프트엔지니어링 수업**에서 매주 자동으로 퀴즈를 생성하도록 설정되었습니다!

## 현재 설정

- **수업**: 언어모델을위한프롬프트엔지니어링(A01283101-01)
- **DB**: Lecture Notes for 03/03/2026
- **DB ID**: `2fa5ddaf-3b4b-8112-a2c5-d52ed8850ebd`

## 지원하는 콘텐츠

1. ✅ **Notion AI 녹음 전사** (`transcription` 블록)
2. ✅ **PDF 파일** (URL 추출, 향후 텍스트 추출 예정)
3. ✅ **일반 텍스트** (paragraph, heading 등)

---

## 매주 자동 실행 설정

### 1. 매주 금요일 저녁 9시 - 퀴즈 생성
```bash
# crontab -e
0 21 * * 5 cd /Users/imeanseo/Documents/projects/notion && python run_step2.py
```

### 2. 매주 일요일 아침 9시 - 복습 알림
```bash
# crontab -e (Slack 알림 추가 시)
0 9 * * 0 cd /Users/imeanseo/Documents/projects/notion && python send_quiz_reminder.py
```

---

## 워크플로우

### 1단계: 수업 후 (수업이 끝나면)
- Notion에 **녹음 파일** 업로드 → Notion AI가 자동 전사
- **PDF 강의 자료** 업로드

### 2단계: 매주 금요일 자동 실행
```bash
python run_step1.py  # 이번 주 새로운 강의 노트만 읽기 (증분)
python run_step2.py  # 퀴즈 생성
```

### 3단계: 퀴즈 확인
생성된 퀴즈가 콘솔에 출력됩니다. 나중에 Notion "오늘의 퀴즈" 페이지로 자동 업로드 가능 (Step 3 구현 시).

---

## 다음 구현 사항

### Step 3: Notion에 퀴즈 자동 업로드
- "오늘의 퀴즈" 페이지 생성
- 생성된 퀴즈를 블록으로 추가

### Step 4: 학습 에이전트
- 틀린 문제에 대해 "강의 15분 지점 참고" 가이드

### PDF 텍스트 추출
- PyPDF2 또는 pdfplumber 사용
- Notion에서 PDF URL 다운로드 → 텍스트 추출

---

## 테스트 방법

### 지금 바로 테스트 (OpenAI 키 필요)
```bash
# .env에 OPENAI_API_KEY 추가 후
python run_step2.py
```

현재는 녹음 전사가 비어있지만, 실제 수업 녹음을 업로드하면 자동으로 퀴즈가 생성됩니다!
