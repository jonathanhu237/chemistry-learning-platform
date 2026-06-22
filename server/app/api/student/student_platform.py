from __future__ import annotations

import json
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import ValidationError

from server.app.auth import AuthUser, require_roles
from server.app.infrastructure.settings import get_settings
from server.app.infrastructure.database import db_session
from server.app.feedback import create_feedback_attachment_record, create_feedback_record, list_feedback_attachments
from server.app.domains.platform.settings import get_ai_configuration_response, get_learning_behavior_settings
from server.app.domains.preview.student_device_preview import is_preview_user, preview_policy
from server.app.schemas import FeedbackItem, FeedbackSubmitRequest
from server.app.student_app_schemas import (
    StudentAppConfigResponse,
    StudentAppFeatureFlags,
    StudentFeedbackSubmitRequest,
)


router = APIRouter(prefix="/api/student", tags=["student-platform"])
StudentUser = Annotated[AuthUser, Depends(require_roles("student"))]


def _student_identifier(user: AuthUser) -> str:
    return str(user.student_id or user.username).strip().upper()


def _parse_metadata(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid feedback metadata") from exc
    if not isinstance(value, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid feedback metadata")
    return value


def _optional_form_value(value: Any) -> str | None:
    if value is None:
        return None
    text_value = str(value).strip()
    return text_value or None


def _validated_feedback_payload(data: dict[str, Any]) -> StudentFeedbackSubmitRequest:
    try:
        return StudentFeedbackSubmitRequest(**data)
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.errors()) from exc


async def _read_optional_attachment(attachment: Any) -> tuple[str, bytes, str | None] | None:
    filename = getattr(attachment, "filename", None)
    if not attachment or not filename:
        return None
    content = await attachment.read()
    return str(filename), content, getattr(attachment, "content_type", None)


async def _feedback_request_from_http(request: Request) -> tuple[StudentFeedbackSubmitRequest, tuple[str, bytes, str | None] | None]:
    content_type = request.headers.get("content-type", "").lower()
    if "application/json" in content_type:
        data = await request.json()
        if not isinstance(data, dict):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid feedback payload")
        return _validated_feedback_payload(data), None

    form = await request.form()
    attachment = await _read_optional_attachment(form.get("attachment"))
    metadata = _parse_metadata(_optional_form_value(form.get("metadata")))
    catalog_path_value = form.get("catalog_path")
    catalog_path = metadata.get("catalog_path")
    if isinstance(catalog_path_value, str) and catalog_path_value.strip():
        try:
            parsed_catalog_path = json.loads(catalog_path_value)
            if isinstance(parsed_catalog_path, list):
                catalog_path = parsed_catalog_path
        except json.JSONDecodeError:
            catalog_path = [item.strip() for item in catalog_path_value.split("/") if item.strip()]
    return (
        _validated_feedback_payload(
            {
                "feedback_type": _optional_form_value(form.get("feedback_type")) or "other",
                "content": _optional_form_value(form.get("content")) or "",
                "chapter_id": _optional_form_value(form.get("chapter_id")),
                "unit_id": _optional_form_value(form.get("unit_id")),
                "knowledge_point_id": _optional_form_value(form.get("knowledge_point_id")),
                "experiment_id": _optional_form_value(form.get("experiment_id")),
                "point_node_id": _optional_form_value(form.get("point_node_id")),
                "catalog_path": catalog_path if isinstance(catalog_path, list) else [],
                "page_path": _optional_form_value(form.get("page_path")),
                "metadata": metadata,
            }
        ),
        attachment,
    )


@router.get("/app-config", response_model=StudentAppConfigResponse)
def student_app_config(user: StudentUser) -> StudentAppConfigResponse:
    learning = get_learning_behavior_settings()
    ai_config = get_ai_configuration_response(can_edit=False, auto_check=False)
    policy = preview_policy() if is_preview_user(user) else None
    policy_data = policy.model_dump() if policy and hasattr(policy, "model_dump") else (policy.dict() if policy else None)
    return StudentAppConfigResponse(
        features=StudentAppFeatureFlags(
            ai_assistant_enabled=learning.learning_features.ai_assistant_enabled and (policy.assistant_enabled if policy else True),
            feedback_enabled=learning.learning_features.feedback_enabled and (policy.feedback_enabled if policy else True),
            student_ai_assistant_enabled=ai_config.enabled_features.student_ai_assistant,
            rag_access_enabled=ai_config.enabled_features.rag_access_enabled,
        ),
        preview_mode=bool(policy),
        preview_policy=policy_data,
    )


def submit_student_feedback(
    payload: StudentFeedbackSubmitRequest,
    user: AuthUser,
    *,
    attachment_payload: tuple[str, bytes, str | None] | None = None,
) -> dict[str, Any]:
    learning = get_learning_behavior_settings()
    if is_preview_user(user):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="教师预览模式下不能提交真实反馈")
    if not learning.learning_features.feedback_enabled:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="学生反馈入口已关闭")

    metadata = dict(payload.metadata or {})
    metadata.update(
        {
            "point_node_id": payload.point_node_id,
            "catalog_path": payload.catalog_path,
            "client_student_id_ignored": metadata.get("student_id"),
            "client_class_id_ignored": metadata.get("class_id"),
        }
    )
    metadata.pop("student_id", None)
    metadata.pop("class_id", None)
    feedback = FeedbackSubmitRequest(
        student_id=_student_identifier(user),
        class_id=user.class_id,
        feedback_type=payload.feedback_type,
        content=payload.content,
        chapter_id=payload.chapter_id,
        unit_id=payload.unit_id,
        knowledge_point_id=payload.knowledge_point_id,
        experiment_id=payload.experiment_id,
        point_node_id=payload.point_node_id,
        catalog_path=payload.catalog_path,
        page_path=payload.page_path,
        metadata={key: value for key, value in metadata.items() if value is not None},
    )
    if not attachment_payload:
        return create_feedback_record(feedback)

    if get_settings().data_backend != "postgres":
        item = create_feedback_record(feedback)
        create_feedback_attachment_record(
            item["id"],
            filename=attachment_payload[0],
            content=attachment_payload[1],
            content_type=attachment_payload[2],
        )
        attachments = list_feedback_attachments(None, item["id"])
        item["attachments"] = attachments
        item["attachment_count"] = len(attachments)
        return item

    with db_session() as session:
        item = create_feedback_record(feedback, session=session)
        create_feedback_attachment_record(
            item["id"],
            filename=attachment_payload[0],
            content=attachment_payload[1],
            content_type=attachment_payload[2],
            session=session,
        )
        attachments = list_feedback_attachments(session, item["id"])
        item["attachments"] = attachments
        item["attachment_count"] = len(attachments)
        return item


@router.post("/feedback", response_model=FeedbackItem)
async def submit_student_feedback_endpoint(request: Request, user: StudentUser) -> dict[str, Any]:
    payload, attachment = await _feedback_request_from_http(request)
    return submit_student_feedback(payload, user, attachment_payload=attachment)
