from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import text

from server.app.domains.media.files import PROCESSING_JOB_TYPE, json_param
from server.app.infrastructure.database import db_session
from server.app.infrastructure.settings import get_settings


PHASE_PROGRESS = {
    "starting": 1,
    "validating": 5,
    "probing": 15,
    "thumbnailing": 30,
    "transcoding": 60,
    "fingerprinting": 78,
    "comparing": 90,
    "ready": 100,
    "failed": 0,
}


@dataclass(frozen=True)
class WorkerJob:
    id: str
    media_asset_id: str
    attempts: int
    job_type: str = PROCESSING_JOB_TYPE

    @property
    def preserves_ready_playback(self) -> bool:
        return self.job_type == "backfill_legacy_video"


def relative_media_path(path: Path) -> str:
    root = get_settings().media_root.resolve()
    return path.resolve().relative_to(root).as_posix()


def claim_next_job(worker_id: str) -> WorkerJob | None:
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    UPDATE media_processing_jobs
                    SET status = 'processing',
                        phase = 'starting',
                        progress = 1,
                        attempts = attempts + 1,
                        worker_id = :worker_id,
                        started_at = now(),
                        updated_at = now()
                    WHERE id = (
                      SELECT mpj.id
                      FROM media_processing_jobs mpj
                      JOIN media_assets ma ON ma.id = mpj.media_asset_id
                      WHERE mpj.status = 'queued'
                        AND mpj.attempts < mpj.max_attempts
                        AND COALESCE(ma.lifecycle_status, 'active') = 'active'
                      ORDER BY mpj.created_at
                      FOR UPDATE SKIP LOCKED
                      LIMIT 1
                    )
                    RETURNING id, media_asset_id, attempts, job_type
                    """
                ),
                {"worker_id": worker_id},
            )
            .mappings()
            .first()
        )
    if not row:
        return None
    return WorkerJob(
        id=str(row["id"]),
        media_asset_id=str(row["media_asset_id"]),
        attempts=int(row["attempts"]),
        job_type=str(row["job_type"] or PROCESSING_JOB_TYPE),
    )


def update_phase(job: WorkerJob, phase: str, progress: int | None = None, metadata: dict[str, Any] | None = None) -> None:
    next_progress = PHASE_PROGRESS.get(phase, progress or 0) if progress is None else progress
    with db_session() as session:
        session.execute(
            text(
                """
                UPDATE media_processing_jobs
                SET phase = :phase,
                    progress = :progress,
                    metadata = metadata || CAST(:metadata AS jsonb),
                    updated_at = now()
                WHERE id = CAST(:job_id AS uuid)
                """
            ),
            {
                "job_id": job.id,
                "phase": phase,
                "progress": next_progress,
                "metadata": json_param(metadata or {}),
            },
        )
        session.execute(
            text(
                """
                UPDATE media_assets
                SET upload_status = CASE
                      WHEN :preserve_ready_playback THEN upload_status
                      ELSE 'processing'
                    END,
                    processing_phase = :phase,
                    processing_progress = :progress,
                    updated_at = now()
                WHERE id = CAST(:asset_id AS uuid)
                  AND upload_status <> 'replaced'
                """
            ),
            {
                "asset_id": job.media_asset_id,
                "phase": phase,
                "progress": next_progress,
                "preserve_ready_playback": job.preserves_ready_playback,
            },
        )


def fail_job(job: WorkerJob, error: str) -> None:
    message = error[:1000]
    with db_session() as session:
        session.execute(
            text(
                """
                UPDATE media_processing_jobs
                SET status = 'failed',
                    phase = 'failed',
                    progress = 0,
                    error_reason = :error_reason,
                    finished_at = now(),
                    updated_at = now()
                WHERE id = CAST(:job_id AS uuid)
                """
            ),
            {"job_id": job.id, "error_reason": message},
        )
        session.execute(
            text(
                """
                UPDATE media_assets
                SET upload_status = CASE
                      WHEN :preserve_ready_playback THEN upload_status
                      ELSE 'failed'
                    END,
                    processing_phase = 'failed',
                    processing_progress = 0,
                    error_reason = :error_reason,
                    updated_at = now()
                WHERE id = CAST(:asset_id AS uuid)
                  AND upload_status <> 'replaced'
                """
            ),
            {
                "asset_id": job.media_asset_id,
                "error_reason": message,
                "preserve_ready_playback": job.preserves_ready_playback,
            },
        )


def finish_job(job: WorkerJob, outputs: dict[str, Any]) -> None:
    with db_session() as session:
        session.execute(
            text(
                """
                UPDATE media_processing_jobs
                SET status = 'ready',
                    phase = 'ready',
                    progress = 100,
                    outputs = CAST(:outputs AS jsonb),
                    finished_at = now(),
                    updated_at = now()
                WHERE id = CAST(:job_id AS uuid)
                """
            ),
            {"job_id": job.id, "outputs": json_param(outputs)},
        )
        session.execute(
            text(
                """
                UPDATE media_assets
                SET upload_status = 'ready',
                    processing_phase = 'ready',
                    processing_progress = 100,
                    error_reason = NULL,
                    processed_at = now(),
                    updated_at = now()
                WHERE id = CAST(:asset_id AS uuid)
                  AND upload_status <> 'replaced'
                """
            ),
            {"asset_id": job.media_asset_id},
        )


def load_processing_asset(asset_id: str) -> dict[str, Any]:
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    SELECT id, title, original_file_name, relative_path, source_relative_path,
                           checksum_sha256, mime_type, file_size_bytes
                    FROM media_assets
                    WHERE id = CAST(:asset_id AS uuid)
                    """
                ),
                {"asset_id": asset_id},
            )
            .mappings()
            .first()
        )
    if not row:
        raise RuntimeError("Media asset not found")
    return dict(row)


def persist_video_probe(asset_id: str, metadata: dict[str, Any]) -> None:
    with db_session() as session:
        session.execute(
            text(
                """
                UPDATE media_assets
                SET duration_seconds = :duration_seconds,
                    width = :width,
                    height = :height,
                    fps = :fps,
                    bitrate = :bitrate,
                    video_codec = :video_codec,
                    audio_codec = :audio_codec,
                    metadata = metadata || CAST(:metadata AS jsonb),
                    updated_at = now()
                WHERE id = CAST(:asset_id AS uuid)
                """
            ),
            {
                "asset_id": asset_id,
                "duration_seconds": metadata.get("duration_seconds"),
                "width": metadata.get("width"),
                "height": metadata.get("height"),
                "fps": metadata.get("fps"),
                "bitrate": metadata.get("bitrate"),
                "video_codec": metadata.get("video_codec"),
                "audio_codec": metadata.get("audio_codec"),
                "metadata": json_param({"video_probe": metadata}),
            },
        )


def persist_learning_rendition(asset_id: str, rendition: Path, metadata: dict[str, Any], policy: dict[str, Any]) -> None:
    relative_path = relative_media_path(rendition)
    with db_session() as session:
        session.execute(
            text(
                """
                INSERT INTO media_renditions (
                  media_asset_id, kind, relative_path, mime_type, file_size_bytes,
                  duration_seconds, width, height, fps, bitrate, video_codec, audio_codec,
                  status, metadata
                )
                VALUES (
                  CAST(:asset_id AS uuid), 'learning', :relative_path, 'video/mp4',
                  :file_size_bytes, :duration_seconds, :width, :height, :fps,
                  :bitrate, :video_codec, :audio_codec, 'ready', CAST(:metadata AS jsonb)
                )
                ON CONFLICT (media_asset_id, kind) DO UPDATE SET
                  relative_path = EXCLUDED.relative_path,
                  mime_type = EXCLUDED.mime_type,
                  file_size_bytes = EXCLUDED.file_size_bytes,
                  duration_seconds = EXCLUDED.duration_seconds,
                  width = EXCLUDED.width,
                  height = EXCLUDED.height,
                  fps = EXCLUDED.fps,
                  bitrate = EXCLUDED.bitrate,
                  video_codec = EXCLUDED.video_codec,
                  audio_codec = EXCLUDED.audio_codec,
                  status = 'ready',
                  metadata = EXCLUDED.metadata,
                  updated_at = now()
                """
            ),
            {
                "asset_id": asset_id,
                "relative_path": relative_path,
                "file_size_bytes": rendition.stat().st_size,
                "duration_seconds": metadata.get("duration_seconds"),
                "width": metadata.get("width"),
                "height": metadata.get("height"),
                "fps": metadata.get("fps"),
                "bitrate": metadata.get("bitrate"),
                "video_codec": metadata.get("video_codec"),
                "audio_codec": metadata.get("audio_codec"),
                "metadata": json_param(policy),
            },
        )
        session.execute(
            text(
                """
                UPDATE media_assets
                SET playback_relative_path = :playback_relative_path,
                    playback_mime_type = 'video/mp4',
                    updated_at = now()
                WHERE id = CAST(:asset_id AS uuid)
                """
            ),
            {"asset_id": asset_id, "playback_relative_path": relative_path},
        )


def persist_thumbnail(asset_id: str, thumbnail: Path) -> None:
    with db_session() as session:
        session.execute(
            text(
                """
                UPDATE media_assets
                SET thumbnail_relative_path = :thumbnail_relative_path,
                    updated_at = now()
                WHERE id = CAST(:asset_id AS uuid)
                """
            ),
            {"asset_id": asset_id, "thumbnail_relative_path": relative_media_path(thumbnail)},
        )


def persist_video_fingerprint(
    asset_id: str,
    *,
    algorithm: str,
    status: str,
    relative_path: str | None,
    signature_hash: str | None,
    metadata: dict[str, Any],
) -> None:
    with db_session() as session:
        session.execute(
            text(
                """
                INSERT INTO media_video_fingerprints (
                  media_asset_id, algorithm, algorithm_version, relative_path,
                  status, signature_hash, metadata
                )
                VALUES (
                  CAST(:asset_id AS uuid), :algorithm, :algorithm_version,
                  :relative_path, :status, :signature_hash, CAST(:metadata AS jsonb)
                )
                ON CONFLICT (media_asset_id, algorithm) DO UPDATE SET
                  algorithm_version = EXCLUDED.algorithm_version,
                  relative_path = EXCLUDED.relative_path,
                  status = EXCLUDED.status,
                  signature_hash = EXCLUDED.signature_hash,
                  metadata = EXCLUDED.metadata,
                  updated_at = now()
                """
            ),
            {
                "asset_id": asset_id,
                "algorithm": algorithm,
                "algorithm_version": "external",
                "relative_path": relative_path,
                "status": status,
                "signature_hash": signature_hash,
                "metadata": json_param(metadata),
            },
        )


def persist_duplicate_candidate(asset_id: str, match: dict[str, Any]) -> None:
    with db_session() as session:
        session.execute(
            text(
                """
                INSERT INTO media_duplicate_candidates (
                  media_asset_id, candidate_asset_id, duplicate_type, score,
                  algorithm, status, metadata
                )
                VALUES (
                  CAST(:asset_id AS uuid), CAST(:candidate_asset_id AS uuid),
                  'suspected', :score, :algorithm, 'pending', CAST(:metadata AS jsonb)
                )
                ON CONFLICT (media_asset_id, candidate_asset_id, duplicate_type, algorithm)
                DO UPDATE SET
                  score = EXCLUDED.score,
                  status = 'pending',
                  metadata = EXCLUDED.metadata,
                  updated_at = now()
                """
            ),
            {
                "asset_id": asset_id,
                "candidate_asset_id": match["candidate_asset_id"],
                "score": match["score"],
                "algorithm": match["algorithm"],
                "metadata": json_param({"source": "video_worker"}),
            },
        )


def queue_legacy_backfill(limit: int = 200) -> int:
    settings = get_settings()
    with db_session() as session:
        rows = (
            session.execute(
                text(
                    """
                    WITH candidates AS (
                      SELECT ma.id
                      FROM media_assets ma
                      WHERE ma.upload_status = 'ready'
                        AND COALESCE(ma.lifecycle_status, 'active') = 'active'
                        AND (
                          ma.thumbnail_relative_path IS NULL
                          OR ma.playback_relative_path IS NULL
                          OR NOT EXISTS (
                            SELECT 1 FROM media_video_fingerprints mf
                            WHERE mf.media_asset_id = ma.id
                              AND mf.algorithm = :algorithm
                              AND mf.status IN ('ready', 'skipped')
                          )
                        )
                        AND NOT EXISTS (
                          SELECT 1
                          FROM media_processing_jobs existing
                          WHERE existing.media_asset_id = ma.id
                            AND existing.job_type = 'backfill_legacy_video'
                            AND existing.status IN ('queued', 'processing')
                        )
                      ORDER BY ma.updated_at DESC
                      LIMIT :limit
                    )
                    INSERT INTO media_processing_jobs (
                      media_asset_id, job_type, status, phase, progress, metadata
                    )
                    SELECT id, 'backfill_legacy_video', 'queued', 'queued', 0,
                           '{"source":"legacy_backfill"}'::jsonb
                    FROM candidates
                    RETURNING id
                    """
                ),
                {"limit": limit, "algorithm": settings.video_similarity_algorithm},
            )
            .mappings()
            .all()
        )
    return len(rows)


def enqueue_processing_job(asset_id: str, *, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    INSERT INTO media_processing_jobs (
                      media_asset_id, job_type, status, phase, progress, metadata
                    )
                    VALUES (
                      CAST(:asset_id AS uuid), :job_type, 'queued', 'queued', 0,
                      CAST(:metadata AS jsonb)
                    )
                    RETURNING id, media_asset_id, job_type, status, phase, progress,
                              attempts, error_reason, created_at, updated_at
                    """
                ),
                {
                    "asset_id": asset_id,
                    "job_type": PROCESSING_JOB_TYPE,
                    "metadata": json_param(metadata or {}),
                },
            )
            .mappings()
            .one()
        )
        session.execute(
            text(
                """
                UPDATE media_assets
                SET upload_status = 'processing',
                    processing_phase = 'queued',
                    processing_progress = 0,
                    updated_at = now()
                WHERE id = CAST(:asset_id AS uuid)
                  AND upload_status <> 'replaced'
                """
            ),
            {"asset_id": asset_id},
        )
    return dict(row)


def active_media_processing_status(limit: int = 200) -> dict[str, Any]:
    with db_session() as session:
        rows = [
            dict(row)
            for row in session.execute(
                text(
                    """
                    SELECT ma.id, ma.upload_status, ma.processing_phase, ma.processing_progress,
                           ma.error_reason, ma.thumbnail_relative_path, ma.playback_relative_path,
                           mpj.id AS job_id, mpj.status AS job_status, mpj.phase AS job_phase,
                           mpj.progress AS job_progress, mpj.error_reason AS job_error_reason,
                           mpj.updated_at AS job_updated_at
                    FROM media_assets ma
                    LEFT JOIN LATERAL (
                      SELECT id, status, phase, progress, error_reason, updated_at
                      FROM media_processing_jobs
                      WHERE media_asset_id = ma.id
                      ORDER BY created_at DESC
                      LIMIT 1
                    ) mpj ON true
                    WHERE ma.upload_status IN ('pending', 'processing', 'failed')
                      AND COALESCE(ma.lifecycle_status, 'active') = 'active'
                    ORDER BY ma.updated_at DESC
                    LIMIT :limit
                    """
                ),
                {"limit": limit},
            )
            .mappings()
            .all()
        ]
    return {"items": rows, "total": len(rows)}


def retry_media_processing(asset_id: str) -> dict[str, Any]:
    with db_session() as session:
        asset = (
            session.execute(
                text(
                    """
                    SELECT id
                    FROM media_assets
                    WHERE id = CAST(:asset_id AS uuid)
                      AND COALESCE(lifecycle_status, 'active') = 'active'
                    """
                ),
                {"asset_id": asset_id},
            )
            .mappings()
            .first()
        )
    if not asset:
        raise ValueError("Media asset not found")
    return enqueue_processing_job(asset_id, metadata={"source": "admin_retry"})
