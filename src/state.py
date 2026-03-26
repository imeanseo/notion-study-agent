"""
LangGraph 상태 정의.
퀴즈 생성 파이프라인과 학습 에이전트에서 공유하는 상태.
"""
from typing import TypedDict, Annotated, Optional
from langgraph.graph.message import add_messages


class LecturePage(TypedDict):
    """Notion에서 가져온 강의 페이지 한 건."""
    page_id: str
    title: str
    plain_text: str  # 블록에서 추출한 본문 텍스트
    course_name: Optional[str]  # 과목명 (예: "프롬프트엔지니어링")


class QuizItem(TypedDict, total=False):
    """퀴즈 한 문항."""
    question: str
    options: list[str]  # 객관식일 때
    correct_index: Optional[int]  # 객관식 정답 인덱스
    correct_answer: Optional[str]  # 주관식 정답
    kind: str  # "multiple_choice" | "short_answer"
    course_name: Optional[str]  # 과목명
    source_page_id: Optional[str]  # 출처 페이지 ID (학습 에이전트용)
    source_hint: Optional[str]    # 예: "강의 15분 지점"


class CourseQuizzes(TypedDict):
    """과목별 퀴즈 묶음."""
    course_name: str
    quiz_items: list[QuizItem]


class StudyAgentState(TypedDict, total=False):
    """전체 그래프 상태."""
    # Step 1: 주간 데이터 수집
    lecture_pages: list[LecturePage]
    combined_transcript: str  # 모든 강의 텍스트를 합친 문자열
    
    # 과목별 데이터 (주간 통합 퀴즈용)
    courses_data: dict[str, str]  # {"프롬프트": "강의내용...", "실용NLP": "..."}
    pdf_texts: dict[str, list[str]]  # {"프롬프트": ["pdf1 내용", ...]}

    # Step 2: 퀴즈 생성
    quiz_items: list[QuizItem]  # 전체 퀴즈 (과목 구분 없이)
    course_quizzes: list[CourseQuizzes]  # 과목별 퀴즈

    # Step 3: 출력 대상 (선택)
    notion_quiz_page_id: Optional[str]
    slack_sent: bool

    # Step 4: 사용자 답안 및 피드백
    user_answers: list[str]  # 문항 순서대로 제출된 답
    wrong_indices: list[int]  # 틀린 문항 인덱스
    feedback_messages: Annotated[list[str], add_messages]  # 학습 에이전트가 준 가이드 문구
