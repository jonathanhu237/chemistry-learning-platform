from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path

from server.app.auth import AuthUser, require_roles
from server.app.domains.assessments.reports import get_student_assessment_report, list_student_assessment_reports
from server.app.student_assessment_report_schemas import StudentAssessmentReport, StudentAssessmentReportListResponse


router = APIRouter(prefix="/api/student", tags=["student-assessment-reports"])
StudentUser = Annotated[AuthUser, Depends(require_roles("student"))]


@router.get("/assessment-reports", response_model=StudentAssessmentReportListResponse)
def student_list_assessment_reports(user: StudentUser) -> StudentAssessmentReportListResponse:
    return list_student_assessment_reports(user)


@router.get("/assessment-reports/{report_id}", response_model=StudentAssessmentReport)
def student_get_assessment_report(
    report_id: Annotated[str, Path(min_length=1)],
    user: StudentUser,
) -> StudentAssessmentReport:
    return get_student_assessment_report(report_id, user)
