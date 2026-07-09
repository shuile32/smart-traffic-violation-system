from datetime import datetime

from pydantic import BaseModel


class ReportRequest(BaseModel):
    start_time: str | None = None
    end_time: str | None = None
    report_type: str | None = None


class ReportOut(BaseModel):
    title: str
    content: str
    author: str
    generated_at: datetime
