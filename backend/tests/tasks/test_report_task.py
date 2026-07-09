"""测试 generate_report_task（直接调函数，不连 Celery broker）。"""
from app.tasks.report_task import generate_report_task


def test_generate_report_task_returns_dict():
    """直接调用 task 函数体验证返回结构（不连 broker）。"""
    result = generate_report_task.run("2026-01-01", "2026-07-01", "综合")
    assert result["title"]
    assert result["content"]
    assert result["author"] == "AI 分析助手 (stub)"
