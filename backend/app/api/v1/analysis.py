from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import require_role
from app.models.user import User
from app.schemas.report import ReportOut, ReportRequest
from app.services.analysis_service import AnalysisService

router = APIRouter(tags=["analysis"])


@router.post("/analysis/reports", response_model=ReportOut, status_code=200)
def generate_report(body: ReportRequest | None = None,
                    db: Session = Depends(get_db),
                    _: User = Depends(require_role("admin", "reviewer"))) -> ReportOut:
    req = body or ReportRequest()
    return AnalysisService().generate_report(req.start_time, req.end_time, req.report_type)
