"""
Step 2: 강의 내용(combined_transcript)에서 퀴즈를 생성합니다.
LLM(Ollama)을 사용해 핵심 개념을 추출하고 객관식/주관식 퀴즈를 만듭니다.
"""
import os
import json
from typing import Any
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

from src.state import StudyAgentState, QuizItem


QUIZ_GENERATION_PROMPT = """당신은 대학 강의 내용을 바탕으로 학습용 퀴즈를 생성하는 교육 전문가입니다.

**중요**: 강의 자료가 영어로 되어 있어도, 반드시 **한국어로 퀴즈를 출제**하세요.

주어진 강의 텍스트(한국어 녹음 전사 + 영어 PDF 자료)에서 핵심 개념을 추출하여 **10개의 퀴즈**를 생성하세요.

**퀴즈 작성 가이드라인:**
- 영어 전문 용어는 "한글(English)" 형식으로 병기
  예: "프롬프트 엔지니어링(Prompt Engineering)", "대규모 언어 모델(LLM)"
- 강의의 핵심 개념과 중요 포인트에 집중
- 단순 암기보다는 이해를 요구하는 문제
- 수업 오리엔테이션(출석, 과제 일정 등)은 제외하고 **학습 내용만** 포함
- 객관식과 주관식을 섞어서 생성

**반드시 다음 JSON 배열 형식으로만 출력하세요 (다른 텍스트 절대 출력 금지):**

[
  {
    "question": "프롬프트 엔지니어링(Prompt Engineering)의 주요 목표는 무엇인가?",
    "kind": "multiple_choice",
    "options": ["AI 모델 훈련 속도 향상", "사용자 의도에 맞는 정확한 응답 유도", "모델 크기 축소", "데이터 수집 자동화"],
    "correct_index": 1,
    "source_hint": "Lec1_Intro.pdf"
  },
  {
    "question": "대규모 언어 모델(LLM)에서 'Large'가 의미하는 것을 간단히 설명하세요.",
    "kind": "short_answer",
    "correct_answer": "대량의 학습 데이터와 방대한 파라미터를 가진 딥러닝 모델",
    "source_hint": "강의 녹음 - LLM 소개"
  }
]

**중요 규칙:**
1. 반드시 유효한 JSON 배열만 출력하세요
2. 설명이나 마크다운 코드 블록(```)을 사용하지 마세요
3. **모든 질문과 선택지는 한국어로 작성**
4. 영어 전문 용어는 한글 번역과 함께 병기
5. source_hint에는 PDF 파일명 또는 강의 섹션명 명시"""


def generate_quiz(state: StudyAgentState) -> dict[str, Any]:
    """
    state의 combined_transcript를 읽어 퀴즈를 생성합니다.
    반환: { "quiz_items": [...] }
    """
    transcript = state.get("combined_transcript") or ""
    if not transcript.strip():
        return {
            "quiz_items": [],
            "error": "combined_transcript가 비어 있습니다.",
        }

    # Ollama 모델 선택 (환경변수로 변경 가능, 기본값: solar)
    model_name = os.environ.get("OLLAMA_MODEL", "solar")
    
    llm = ChatOllama(
        model=model_name,
        temperature=0.7,
        base_url="http://localhost:11434",  # Ollama 기본 포트
    )

    messages = [
        SystemMessage(content=QUIZ_GENERATION_PROMPT),
        HumanMessage(content=f"강의 내용:\n\n{transcript[:5000]}\n\nJSON 배열 형식으로 퀴즈를 생성하세요:"),
    ]

    try:
        response = llm.invoke(messages)
        content = response.content

        # JSON 추출 (코드 블록 안에 있을 수 있음)
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            content = content[start:end].strip()
        elif "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            content = content[start:end].strip()

        quiz_data = json.loads(content)
        
        # QuizItem 형식으로 변환
        quiz_items: list[QuizItem] = []
        for item in quiz_data:
            quiz_item: QuizItem = {
                "question": item["question"],
                "kind": item["kind"],
                "source_hint": item.get("source_hint"),
            }
            if item["kind"] == "multiple_choice":
                quiz_item["options"] = item["options"]
                quiz_item["correct_index"] = item["correct_index"]
            else:
                quiz_item["correct_answer"] = item.get("correct_answer")
            
            quiz_items.append(quiz_item)

        return {"quiz_items": quiz_items}

    except Exception as e:
        return {
            "quiz_items": [],
            "error": f"퀴즈 생성 중 오류: {str(e)}",
        }
