# Local Video Processing Pipeline

This deployment keeps all media on the local machine under `MEDIA_ROOT`. The API, `tusd`, and `video-worker` share that directory, while Postgres stores lifecycle state and artifact paths.

## Services

- `tusd`: mature tus resumable upload receiver. It writes completed uploads into `MEDIA_ROOT/tus`.
- `backend`: FastAPI service. It verifies exact SHA-256 identity, creates `media_assets`, and queues processing jobs.
- `video-worker`: local Docker worker. It claims queued jobs from Postgres and invokes mature media tools.

The worker image is built from a Python slim base and copies static `ffmpeg` and `ffprobe` binaries from a GitHub FFmpeg build archive during the Docker build. The worker verifies those binaries before claiming jobs. Video probing, thumbnail generation, remuxing, and transcoding are delegated to FFmpeg-family tools.

## Media Layout

```text
data/media/
  tus/<upload_id>
  originals/<asset_id>/source.<ext>
  renditions/<asset_id>/learning.mp4
  thumbnails/<asset_id>.jpg
  fingerprints/<asset_id>/video-signature.bin
  tmp/<job_id>/
```

Back up Postgres and `data/media` together. A database-only backup preserves metadata but not video files.

## Upload Flow

The admin web uses Uppy with tus support when `VITE_TUS_ENDPOINT` is configured. The browser can stream a SHA-256 precheck with `hash-wasm`; the backend remains authoritative and recomputes or verifies SHA-256 after the local upload handoff.

Exact duplicates are byte-identical only. Different encodings of similar content are not exact duplicates and are never auto-skipped.

For local teacher-console builds, copy `apps/web-teacher/.env.example` to `apps/web-teacher/.env` or provide `VITE_TUS_ENDPOINT=http://127.0.0.1:10980/files/` in the build environment.

## Processing Policy

Default learning rendition:

- MP4 container
- H.264 video
- AAC audio
- `+faststart`
- max width `VIDEO_LEARNING_MAX_WIDTH` (default 1280)
- max frame rate `VIDEO_LEARNING_MAX_FPS` (default 30)
- CRF `VIDEO_LEARNING_CRF` (default 24)

Videos above `VIDEO_LEARNING_TRANSCODE_THRESHOLD_MB` or outside the compatible profile are transcoded. Already compatible MP4s are remuxed for playback. Originals are retained.

## Similarity Matching Boundary

Project code does not implement perceptual hashing, frame selection, temporal voting, or similarity math. The worker only calls the configured mature tool commands:

- `VIDEO_SIMILARITY_COMMAND`: receives `{input}` and `{output}` placeholders and must write a signature file.
- `VIDEO_SIMILARITY_COMPARE_COMMAND`: receives `{current}` and `{candidate}` placeholders and must print a numeric similarity score.
- `VIDEO_SIMILARITY_ALGORITHM`: label stored with signatures and duplicate candidates.
- `VIDEO_SIMILARITY_THRESHOLD`: score threshold for suspected duplicate rows.

The default worker image installs Meta ThreatExchange vPDQ support. Similarity tooling still stays behind a replaceable command boundary:

```text
VIDEO_SIMILARITY_COMMAND=python -m server.app.video_similarity vpdq-signature "{input}" "{output}"
VIDEO_SIMILARITY_COMPARE_COMMAND=python -m server.app.video_similarity vpdq-compare "{current}" "{candidate}"
```

The helper calls `threatexchange.extensions.vpdq.VPDQSignal` for hashing and comparison. It emits a conservative 0-1 score from the lower of the query-match and compared-match percentages, so a suspected duplicate generally needs both videos to match most of each other.

Suspected duplicates are advisory only. The system records candidates but never deletes, replaces, or skips teacher-selected media based on similarity.

## Library And License Notes

- Uppy core and Uppy tus client: MIT license; used for browser upload progress, retry, pause/resume, and tus client behavior.
- tusd: MIT license; used as the local tus receiver and offset/merge implementation.
- hash-wasm: MIT license; used for streaming SHA-256 exact duplicate precheck in the browser.
- FFmpeg/ffprobe: copied as static binaries from the configured GitHub FFmpeg archive at build time; used only as external media tools.
- Worker Python dependencies: `sqlalchemy`, `psycopg[binary]`, `threatexchange`, and `vpdq`.
- vPDQ: Meta/ThreatExchange video PDQ implementation; used for suspected duplicate video matching.
- vPDQ: optional fallback candidate; packaging requires Linux build tooling and should stay inside the worker image if enabled.

Implementation review checklist:

- No custom chunk upload protocol or merge logic in FastAPI.
- No custom thumbnail extraction or transcoding logic outside FFmpeg/ffprobe calls.
- No project-owned pHash/dHash/frame-voting/video-hash implementation.
- Similarity commands must be replaceable through `VIDEO_SIMILARITY_COMMAND` and `VIDEO_SIMILARITY_COMPARE_COMMAND`.
- Suspected duplicate candidates must remain advisory until a teacher/admin records a decision.

## Operations

Start local services:

```powershell
docker compose up -d --build backend tusd video-worker postgres
```

After the stack exists, rebuild only `video-worker` for worker code or dependency changes:

```powershell
docker compose up -d --build video-worker
```

Queue non-blocking backfill jobs for existing ready media:

```powershell
docker compose run --rm -e VIDEO_WORKER_BACKFILL=1 video-worker
```

Retry a failed asset from the admin UI or call:

```http
POST /api/admin/media/assets/{asset_id}/retry-processing
```

## Rollback

Stop `video-worker` to pause processing:

```powershell
docker compose stop video-worker
```

Existing ready media continues to serve from `media_assets.playback_relative_path` or `media_assets.relative_path`. If resumable upload needs to be disabled during rollout, unset `VITE_TUS_ENDPOINT` and use the small-file fallback upload path.
