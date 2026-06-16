from __future__ import annotations

from fastapi import APIRouter

from server.app.experiment_admin_schemas import ExperimentQuestionSubmitRequest
from server.app.services.student_experiment_service import submit_experiment_question_attempt


router = APIRouter(prefix="/api", tags=["experiment-learning"])


@router.post("/experiment-questions/submit")
async def submit_experiment_questions(payload: ExperimentQuestionSubmitRequest) -> dict[str, object]:
    return submit_experiment_question_attempt(payload)
