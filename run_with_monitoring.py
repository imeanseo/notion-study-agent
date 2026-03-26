#!/usr/bin/env python3
"""
간단한 모니터링 기능이 추가된 실행 스크립트

기능:
1. 실행 시간 측정
2. 에러 로깅
3. Slack 알림 (선택)
4. 자동 재시도
"""

import sys
import os
import time
import logging
from datetime import datetime
from pathlib import Path

# 로그 디렉토리 생성
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)

# 로그 파일 설정
log_file = log_dir / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv
load_dotenv()


def send_slack_notification(message: str, is_error: bool = False):
    """Slack 알림 전송 (선택 사항)"""
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook_url:
        return
    
    try:
        import httpx
        emoji = "🚨" if is_error else "✅"
        payload = {
            "text": f"{emoji} 퀴즈 생성 시스템\n\n{message}"
        }
        httpx.post(webhook_url, json=payload, timeout=10)
    except Exception as e:
        logger.warning(f"Slack 알림 실패: {e}")


def run_pipeline_with_retry(max_retries: int = 3):
    """재시도 로직이 있는 파이프라인 실행"""
    from src.graph import build_graph
    
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"🚀 파이프라인 시작 (시도 {attempt}/{max_retries})")
            start_time = time.time()
            
            # LangGraph 실행
            graph = build_graph()
            result = graph.invoke({"lecture_pages": [], "combined_transcript": ""})
            
            elapsed = time.time() - start_time
            
            # 결과 확인
            if not result.get("combined_transcript"):
                logger.warning("⚠️  새로운 강의 없음 (퀴즈 생성 안 함)")
                send_slack_notification(
                    f"새로운 강의가 없어서 퀴즈를 생성하지 않았습니다.\n"
                    f"실행 시간: {elapsed:.1f}초"
                )
                return True
            
            # 성공
            quiz_count = len(result.get("quiz_items", []))
            courses = result.get("courses_scanned", [])
            excluded = result.get("courses_excluded", [])
            
            success_msg = (
                f"✅ 퀴즈 생성 완료!\n\n"
                f"• 수업 수: {len(courses)}개\n"
                f"• 제외된 수업: {len(excluded)}개\n"
                f"• 퀴즈 수: {quiz_count}개\n"
                f"• 실행 시간: {elapsed:.1f}초\n"
                f"• Notion URL: {result.get('notion_quiz_url', 'N/A')}"
            )
            
            logger.info(success_msg)
            send_slack_notification(success_msg)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 에러 발생 (시도 {attempt}/{max_retries}): {e}", exc_info=True)
            
            if attempt == max_retries:
                error_msg = (
                    f"❌ 퀴즈 생성 실패 (최대 재시도 횟수 초과)\n\n"
                    f"에러: {str(e)}\n"
                    f"로그 파일: {log_file}"
                )
                logger.error(error_msg)
                send_slack_notification(error_msg, is_error=True)
                return False
            
            # 재시도 전 대기
            wait_time = 2 ** attempt  # 지수 백오프: 2초, 4초, 8초...
            logger.info(f"⏳ {wait_time}초 후 재시도...")
            time.sleep(wait_time)
    
    return False


def main():
    logger.info("=" * 60)
    logger.info("📚 Notion 퀴즈 생성 시스템 시작")
    logger.info(f"⏰ 실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    success = run_pipeline_with_retry(max_retries=3)
    
    if success:
        logger.info("✅ 정상 종료")
        sys.exit(0)
    else:
        logger.error("❌ 비정상 종료")
        sys.exit(1)


if __name__ == "__main__":
    main()
