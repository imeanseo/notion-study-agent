"""
LangGraph 파이프라인: 강의 수집 → 퀴즈 생성 → 출력 → (선택) 채점/가이드.
Step 1만 연결한 최소 그래프로 시작합니다.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from langgraph.graph import StateGraph, START, END
from src.state import StudyAgentState
from src.nodes.fetch_all_courses import fetch_lecture_content  # 모든 수업 자동 스캔
from src.nodes.quiz import generate_quiz
from src.nodes.publish import publish_quiz_to_notion


def build_graph():
    """
    LangGraph 파이프라인:
    
    [START] 
      ↓
    [Step 1: 강의 수집] - Courses DB의 모든 수업을 스캔하고 
      ↓                   새로운 Lecture Notes만 읽기 (증분 업데이트)
    [Step 2: 퀴즈 생성] - Ollama로 한국어 퀴즈 생성
      ↓                   (영어 PDF → 한국어 퀴즈)
    [Step 3: Notion 업로드] - "오늘의 퀴즈" DB에 주차별로 업로드
      ↓
    [END]
    
    각 노드는 state를 받아서 처리 후 업데이트된 state를 반환합니다.
    """
    builder = StateGraph(StudyAgentState)

    builder.add_node("fetch_lecture_content", fetch_lecture_content)
    builder.add_node("generate_quiz", generate_quiz)
    builder.add_node("publish_quiz", publish_quiz_to_notion)

    builder.add_edge(START, "fetch_lecture_content")
    builder.add_edge("fetch_lecture_content", "generate_quiz")
    builder.add_edge("generate_quiz", "publish_quiz")
    builder.add_edge("publish_quiz", END)

    return builder.compile()


if __name__ == "__main__":
    app = build_graph()
    result = app.invoke({})
    print("lecture_pages 수:", len(result.get("lecture_pages") or []))
    print("combined_transcript 길이:", len(result.get("combined_transcript") or ""))
