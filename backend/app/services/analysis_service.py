from datetime import datetime, timezone

from app.schemas.report import ReportOut


class AnalysisService:
    """LLM 分析报告服务。当前为 stub 实现（返回固定报告），real 等唐高鹏 LLM。"""

    def generate_report(self, start_time: str | None,
                        end_time: str | None, report_type: str | None) -> ReportOut:
        period = f"{start_time or '开始'} 至 {end_time or '现在'}"
        return ReportOut(
            title=f"交通违章分析报告 ({report_type or '综合'})",
            content=(
                f"报告周期：{period}\n\n"
                "1. 违章总量统计：stub 数据\n\n"
                "2. 高发区域：路口A、路口B\n\n"
                "3. 主要违章类型：超速、占用专用车道\n\n"
                "4. 建议：加强重点区域执法力度\n\n"
                "（本报告由 stub 生成，real 等唐高鹏 LLM 接入。）"
            ),
            author="AI 分析助手 (stub)",
            generated_at=datetime.now(timezone.utc),
        )
