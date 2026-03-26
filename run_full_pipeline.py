#!/usr/bin/env python3
"""
전체 파이프라인 실행: 강의 수집 → 퀴즈 생성 → Notion 업로드
사용법:
  .env에 OLLAMA_MODEL, NOTION_COURSES_DB_ID 설정 후
  python run_full_pipeline.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv
load_dotenv()

from src.graph import build_graph


def main():
    print("🚀 전체 파이프라인 시작\n")
    print("=" * 60)
    
    app = build_graph()
    result = app.invoke({})

    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 파이프라인 완료\n")
    
    if result.get("error"):
        print(f"❌ 오류: {result['error']}")
        return
    
    pages = result.get("lecture_pages") or []
    quiz_items = result.get("quiz_items") or []
    quiz_week = result.get("quiz_week", "?")
    
    print(f"✅ 강의 페이지: {len(pages)}개")
    print(f"✅ 생성된 퀴즈: {len(quiz_items)}개")
    print(f"✅ 주차: {quiz_week}주차")
    
    # 퀴즈 미리보기
    if quiz_items:
        print(f"\n📝 퀴즈 미리보기 (처음 3개):\n")
        for i, quiz in enumerate(quiz_items[:3], 1):
            print(f"[문제 {i}] {quiz['question']}")
            if quiz["kind"] == "multiple_choice":
                for j, opt in enumerate(quiz.get("options", [])):
                    marker = "✓" if j == quiz.get("correct_index") else " "
                    print(f"  {marker} {j+1}. {opt}")
            else:
                print(f"  정답: {quiz.get('correct_answer')}")
            print(f"  💡 출처: {quiz.get('source_hint', '(없음)')}\n")


if __name__ == "__main__":
    main()
