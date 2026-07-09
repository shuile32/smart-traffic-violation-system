"""Celery 异步任务：LLM 分析报告生成。"""
from celery import shared_task

from app.core.db import SessionLocal
from app.services.analysis_service import AnalysisService


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def generate_report_task(self, start_time: str | None = None,
                         end_time: str | None = None, report_type: str | None = None) -> dict:
    """异步生成 LLM 分析报告。当前 stub：调用 AnalysisService 生成固定报告。"""
    try:
        report = AnalysisService().generate_report(start_time, end_time, report_type)
        return {
            "title": report.title,
            "content": report.content,
            "author": report.author,
            "generated_at": report.generated_at.isoformat(),
        }
    except Exception as exc:
        raise self.retry(exc=exc)
