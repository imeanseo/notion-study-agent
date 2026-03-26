# 증분 업데이트 (Incremental Update) 가이드

## 개요

매번 전체 강의를 다시 읽는 대신, **변경된 페이지만** 가져오는 기능입니다.

---

## 동작 방식

### 1. 첫 실행 (전체 동기화)
```bash
python run_step1.py
```
- 모든 페이지를 읽어옴 (18개)
- `.last_sync` 파일에 현재 시각 저장

### 2. 이후 실행 (증분 업데이트)
```bash
python run_step1.py
```
- `.last_sync` 시각 **이후 수정된 페이지만** 가져옴
- 변경사항이 없으면 "✅ 새로운 변경사항이 없습니다" 출력
- API 호출 수 감소 = 속도 향상 ⚡

### 3. 강제 전체 동기화
```bash
python run_step1.py --full
```
- `.last_sync` 파일 삭제 후 전체 페이지 다시 읽기
- 문제가 생겼을 때 유용

---

## 기술 구현

### Notion API 필터
```python
# src/notion_client.py
payload = {
    "filter": {
        "timestamp": "last_edited_time",
        "last_edited_time": {
            "after": "2026-03-02T00:00:00Z"  # 이 시각 이후만
        }
    }
}
```

### 동기화 시각 저장
```python
# src/nodes/fetch_notion.py
LAST_SYNC_FILE = Path(".last_sync")

# 쿼리 전 현재 시각 기록
sync_start_time = datetime.now(timezone.utc).isoformat()

# ... Notion API 호출 ...

# 성공하면 저장
LAST_SYNC_FILE.write_text(sync_start_time)
```

---

## 장점 vs 로컬 DB

| 방식 | 장점 | 단점 |
|------|------|------|
| **날짜 필터** (현재) | • 구현 간단<br>• 별도 저장소 불필요<br>• Notion = 단일 진실 공급원 | • 삭제 감지 불가<br>• 수정 이력 없음 |
| **로컬 DB** | • 정확한 변경 추적<br>• 삭제 감지 가능<br>• 오프라인 접근 | • SQLite 등 추가 구현<br>• 동기화 로직 복잡 |

---

## 퀴즈 생성에 미치는 영향

### 증분 모드 (추천)
- **새로운/수정된 강의만** 퀴즈 생성
- 매일 실행 시 변경사항만 반영
- LLM 비용 절감 💰

### 전체 모드
- 모든 강의를 다시 읽고 퀴즈 재생성
- 주 1회 "전체 복습 퀴즈" 생성 시 유용

---

## 실전 활용 예시

### 매일 아침 자동 실행 (cron)
```bash
# crontab -e
# 매일 오전 9시
0 9 * * * cd /path/to/notion && python run_step1.py && python run_step2.py
```

### 주말 전체 리뷰
```bash
# 토요일 오전 10시 - 전체 퀴즈 재생성
0 10 * * 6 cd /path/to/notion && python run_step1.py --full && python run_step2.py
```

---

## FAQ

**Q: `.last_sync` 파일을 삭제하면?**  
A: 다음 실행 시 전체 동기화됩니다.

**Q: Notion에서 페이지를 삭제하면?**  
A: 증분 업데이트로는 감지 불가. 로컬 DB가 필요하면 나중에 추가 가능.

**Q: 여러 DB를 동시에 추적하려면?**  
A: DB별로 `.last_sync_<db_name>` 파일 사용 (구현 필요)
