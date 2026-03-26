# 증분 업데이트 구현 완료 ✅

## 요약

**날짜 기반 필터링 방식**으로 증분 업데이트를 구현했습니다. 별도 DB 없이 Notion API의 `last_edited_time` 필터만 사용합니다.

---

## 구현 내용

### 1. `src/notion_client.py`
- `query_database()`에 `last_edited_after` 파라미터 추가
- ISO 8601 날짜 이후 수정된 페이지만 필터링

### 2. `src/nodes/fetch_notion.py`
- `.last_sync` 파일로 마지막 동기화 시각 저장
- 증분 모드에서는 해당 시각 이후 변경만 가져옴
- Race condition 방지: 쿼리 **전**에 시각 기록

### 3. `run_step1.py`
- `--full` 옵션: 전체 동기화 강제
- 증분/전체 모드 표시

---

## 테스트 결과

### ✅ 첫 실행 (전체 동기화)
```
📥 전체 동기화 (첫 실행)
   총 18개 페이지
```

### ✅ 두 번째 실행 (증분)
```
📥 증분 업데이트 (마지막 동기화: 2026-03-02T03:58:26...)
   변경된 페이지: 0개
✅ 새로운 변경사항이 없습니다.
```

### ✅ 강제 전체 동기화
```bash
python run_step1.py --full
🔄 전체 동기화 모드
📥 전체 동기화 (첫 실행)
   총 18개 페이지
```

---

## 파일 구조

```
notion/
├── .last_sync              # 마지막 동기화 시각 (자동 생성)
├── .gitignore              # .last_sync 제외
├── INCREMENTAL_UPDATE.md   # 상세 가이드
└── ...
```

---

## 실전 활용

### 매일 자동 실행 (cron)
```bash
# 매일 오전 9시 - 변경된 강의만 퀴즈 생성
0 9 * * * cd /path/to/notion && python run_step1.py && python run_step2.py

# 주말 전체 리뷰 - 모든 강의로 종합 퀴즈
0 10 * * 6 cd /path/to/notion && python run_step1.py --full && python run_step2.py
```

---

## 추후 확장 (필요 시)

### 로컬 DB 방식으로 전환
- **SQLite** 또는 **TinyDB** 사용
- 페이지 ID, 제목, 마지막 수정 시각 저장
- 삭제된 페이지 감지 가능
- 수정 이력 추적

```python
# 예시 스키마
CREATE TABLE pages (
    page_id TEXT PRIMARY KEY,
    title TEXT,
    last_edited_time TEXT,
    synced_at TEXT
);
```

하지만 현재 구현(날짜 필터)만으로도 대부분의 경우 충분합니다! 🚀
