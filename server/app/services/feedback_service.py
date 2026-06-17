from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import text

from server.app.auth import AuthUser
from server.app.database import db_session
from server.app.feedback import (
    FEEDBACK_STATUSES,
    feedback_row_to_item,
    feedback_visibility_sql,
    list_feedback_attachments,
    load_feedback_attachment_file,
    normalize_feedback_type,
)
from server.app.schemas import FeedbackListResponse, FeedbackSummaryResponse, FeedbackUpdateRequest


def _dump_model(model: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump(exclude_unset=True)
    return model.dict(exclude_unset=True)


def _feedback_filters(
    user: AuthUser,
    *,
    status_filter: str | None = None,
    feedback_type: str | None = None,
    class_id: str | None = None,
    search: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> tuple[list[str], dict[str, Any]]:
    visibility_sql, params = feedback_visibility_sql(user, "sf")
    filters = [visibility_sql]
    if status_filter:
        if status_filter not in FEEDBACK_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid feedback status")
        filters.append("sf.status = :status_filter")
        params["status_filter"] = status_filter
    if feedback_type:
        filters.append("sf.feedback_type = :feedback_type")
        params["feedback_type"] = normalize_feedback_type(feedback_type)
    if class_id:
        filters.append("sf.class_id = :class_id")
        params["class_id"] = class_id
    if search:
        filters.append(
            """
            (
              sf.content ILIKE :search
              OR sf.student_id ILIKE :search
              OR sf.student_name_snapshot ILIKE :search
              OR sf.class_name_snapshot ILIKE :search
            )
            """
        )
        params["search"] = f"%{search.strip()}%"
    if date_from:
        filters.append("sf.created_at >= CAST(:date_from AS timestamptz)")
        params["date_from"] = date_from
    if date_to:
        filters.append("sf.created_at <= CAST(:date_to AS timestamptz)")
        params["date_to"] = date_to
    return filters, params


def _feedback_select_sql(where_sql: str) -> str:
    return f"""
        SELECT sf.*,
               au.display_name AS handler_display_name,
               COALESCE((
                 SELECT COUNT(*)
                 FROM feedback_attachments fa
                 WHERE fa.feedback_id = sf.id
               ), 0) AS attachment_count
        FROM student_feedback sf
        LEFT JOIN app_users au ON au.id = sf.handler_user_id
        WHERE {where_sql}
    """


def _load_visible_feedback(session: Any, feedback_id: str, user: AuthUser) -> dict[str, Any]:
    visibility_sql, params = feedback_visibility_sql(user, "sf")
    params["feedback_id"] = feedback_id
    row = (
        session.execute(
            text(_feedback_select_sql(f"sf.id = CAST(:feedback_id AS uuid) AND {visibility_sql}")),
            params,
        )
        .mappings()
        .first()
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found")
    item = feedback_row_to_item(dict(row))
    item["attachments"] = list_feedback_attachments(session, feedback_id)
    item["attachment_count"] = len(item["attachments"])
    return item


def feedback_summary(user: AuthUser) -> FeedbackSummaryResponse:
    visibility_sql, params = feedback_visibility_sql(user, "sf")
    with db_session() as session:
        row = (
            session.execute(
                text(
                    f"""
                    SELECT
                      COUNT(*) AS total_count,
                      COUNT(*) FILTER (WHERE status = 'open') AS open_count,
                      COUNT(*) FILTER (WHERE status = 'in_progress') AS in_progress_count,
                      COUNT(*) FILTER (WHERE status = 'resolved') AS resolved_count,
                      COUNT(*) FILTER (WHERE status = 'archived') AS archived_count,
                      COUNT(*) FILTER (WHERE created_at >= now() - interval '7 days') AS recent_count
                    FROM student_feedback sf
                    WHERE {visibility_sql}
                    """
                ),
                params,
            )
            .mappings()
            .one()
        )
    summary_fields = getattr(FeedbackSummaryResponse, "model_fields", None) or getattr(FeedbackSummaryResponse, "__fields__", {})
    return FeedbackSummaryResponse(**{key: int(row.get(key) or 0) for key in summary_fields})


def list_feedback(
    user: AuthUser,
    *,
    status_filter: str | None = None,
    feedback_type: str | None = None,
    class_id: str | None = None,
    search: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> FeedbackListResponse:
    filters, params = _feedback_filters(
        user,
        status_filter=status_filter,
        feedback_type=feedback_type,
        class_id=class_id,
        search=search,
        date_from=date_from,
        date_to=date_to,
    )
    where_sql = " AND ".join(f"({item})" for item in filters)
    with db_session() as session:
        total = int(
            session.execute(
                text(f"SELECT COUNT(*) FROM student_feedback sf WHERE {where_sql}"),
                params,
            ).scalar_one()
            or 0
        )
        rows = [
            feedback_row_to_item(dict(row))
            for row in session.execute(
                text(
                    _feedback_select_sql(where_sql)
                    + """
                    ORDER BY sf.created_at DESC, sf.id DESC
                    LIMIT :limit OFFSET :offset
                    """
                ),
                {**params, "limit": limit, "offset": offset},
            )
            .mappings()
            .all()
        ]
    return FeedbackListResponse(items=rows, total=total)


def get_feedback(feedback_id: str, user: AuthUser) -> dict[str, Any]:
    with db_session() as session:
        return _load_visible_feedback(session, feedback_id, user)


def update_feedback(payload: FeedbackUpdateRequest, feedback_id: str, user: AuthUser) -> dict[str, Any]:
    data = _dump_model(payload)
    with db_session() as session:
        _load_visible_feedback(session, feedback_id, user)
        set_clauses = ["handler_user_id = CAST(:handler_user_id AS uuid)", "updated_at = now()"]
        params: dict[str, Any] = {"feedback_id": feedback_id, "handler_user_id": user.id}
        if "status" in data and data["status"] is not None:
            if data["status"] not in FEEDBACK_STATUSES:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid feedback status")
            set_clauses.append("status = :next_status")
            set_clauses.append(
                "resolved_at = CASE WHEN :next_status = 'resolved' THEN COALESCE(resolved_at, now()) ELSE NULL END"
            )
            params["next_status"] = data["status"]
        if "internal_note" in data:
            set_clauses.append("internal_note = :internal_note")
            params["internal_note"] = data.get("internal_note")
        if len(set_clauses) > 2:
            session.execute(
                text(
                    f"""
                    UPDATE student_feedback
                    SET {", ".join(set_clauses)}
                    WHERE id = CAST(:feedback_id AS uuid)
                    """
                ),
                params,
            )
        return _load_visible_feedback(session, feedback_id, user)


def get_feedback_attachment(feedback_id: str, attachment_id: str, user: AuthUser) -> dict[str, Any]:
    with db_session() as session:
        _load_visible_feedback(session, feedback_id, user)
        return load_feedback_attachment_file(session, feedback_id, attachment_id)
