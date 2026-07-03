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
  subtitles/<asset_id>/<track_id>/source.<ext>
  subtitles/<asset_id>/<track_id>/track.vtt
  fingerprints/<asset_id>/video-signature.bin
  tmp/<job_id>/
```

Back up Postgres and `data/media` together. A database-only backup preserves metadata but not video files.

## Upload Flow

The admin web uses Uppy with tus support when `VITE_TUS_ENDPOINT` is configured. The browser can stream a SHA-256 precheck with `hash-wasm`; the backend remains authoritative and recomputes or verifies SHA-256 after the local upload handoff.

Original video uploads are limited by `MAX_MEDIA_UPLOAD_MB` (local default: 8192 MB). The teacher frontend reads the effective policy from the backend and rejects files above that size before hashing or tus upload starts. The backend still enforces the same limit for direct uploads and tus finalization.

The upload queue is owned by the teacher app page state, not by the modal surface. Closing the upload modal hides the queue while the teacher app remains mounted; explicit "cancel current file" or "cancel queue" controls are the actions that abort upload work. A browser tab close, page reload, or app unmount still stops browser-side work. tus resumability can continue later only when the teacher returns with access to the same local file.

Multi-file upload uses a bounded pipeline: stage 0 validates file type and `MAX_MEDIA_UPLOAD_MB`, checksum/precheck can run with limited concurrency, and browser upload/finalization hands each completed file to backend processing without waiting for the whole selection to finish.

Exact duplicates are byte-identical only. Different encodings of similar content are not exact duplicates and are never auto-skipped.

## Subtitle Track Policy

Student playback videos remain subtitle-free. The worker keeps generating the learning rendition with only the selected video stream and optional selected audio stream; embedded subtitle, attachment, and data streams are excluded from the MP4 with `-sn` / `-dn`. The system does not burn subtitles into video and does not automatically publish MKV/MP4 embedded subtitles to students.

External subtitles are managed as media-asset tracks:

- Supported teacher uploads: `.srt` and `.vtt`.
- `.srt` uploads are normalized to WebVTT and keep the source subtitle artifact for diagnostics.
- `.vtt` uploads are validated and served as WebVTT.
- `.ass` / `.ssa` are rejected in this first pass because styled subtitle rendering is not preserved by the browser-native track contract.
- Subtitle uploads are limited by `MAX_MEDIA_SUBTITLE_UPLOAD_MB` (default: 10 MB).

The teacher frontend can attach subtitles after a video exists, or link subtitle files to a queued video before upload starts. Upload-time linking is only a convenience: the subtitle file is not part of tus video upload. After video finalization returns the target `media_asset_id`, the frontend creates subtitle tracks through the subtitle API. If exact duplicate precheck reuses an existing asset, the teacher must explicitly choose whether to add the linked subtitle to that existing asset or reuse the video without changing subtitles.

Teacher preview and student full playback load ready subtitles with native `<track>` elements. Native track requests cannot send custom authorization headers, so subtitle stream URLs must be directly loadable using the same-origin cookie/session model or the existing access-token / preview-token query parameter pattern. Stream responses must use `text/vtt; charset=utf-8`.

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
- transcode acceleration `VIDEO_TRANSCODE_ACCELERATION` (default `auto`)

Videos above `VIDEO_LEARNING_TRANSCODE_THRESHOLD_MB` or outside the compatible profile are transcoded. Already compatible MP4s are remuxed for playback. Originals are retained.

`VIDEO_TRANSCODE_ACCELERATION=auto` probes NVIDIA NVENC at worker runtime and uses the NVIDIA path when available. For H.264/HEVC inputs the worker uses CUVID/NVDEC decode, CUVID resize when scaling is needed, and `h264_nvenc` encode. The output is still browser-compatible H.264 Main / 8-bit `yuv420p`. If the probe fails, or if an auto-selected NVIDIA transcode fails during a job, the worker falls back to CPU `libx264`. Set `VIDEO_TRANSCODE_ACCELERATION=cpu` to force CPU-only behavior. On a CPU-only Docker host, also remove or override the `video-worker` `gpus: all` compose setting before starting the worker.

Verify local GPU video encoding support with:

```powershell
docker run --rm --gpus all -e NVIDIA_DRIVER_CAPABILITIES=compute,utility,video nvidia/cuda:13.0.2-base-ubuntu24.04 nvidia-smi
docker compose run --rm video-worker sh -lc "ffmpeg -hide_banner -f lavfi -i testsrc2=size=640x360:rate=30 -t 1 -c:v h264_nvenc -f null -"
```

If Docker build cannot reach GitHub for the FFmpeg archive, download the archive on the host and place it under `server/vendor/ffmpeg/`:

```text
server/vendor/ffmpeg/ffmpeg-N-125136-gb57ff00bcf-linux64-gpl.tar.xz
```

Then build normally. The Dockerfile copies that directory into the `ffmpeg` build stage, verifies `FFMPEG_SHA256`, and only falls back to `FFMPEG_URL` when no local `*.tar.xz` archive exists. If multiple archives are present, pass `--build-arg FFMPEG_LOCAL_ARCHIVE=<filename>`.

## Duplicate Detection Boundary

The video library only tries to find true full-video duplicates. It does not try to find contained clips, partial overlaps, shared intros/outros, or generic "looks similar" relationships.

Exact duplicates are handled first through SHA-256 plus file size. Perceptual duplicate detection is only a secondary path for re-encoded copies of the same full video.

Before invoking vPDQ compare commands, the worker filters candidates to active, ready assets with the same algorithm and near-equal duration. The default tolerance is:

```text
clamp(duration_seconds * 0.001, 0.5, 2.0)
```

If a source video has no reliable duration, the worker records duplicate detection as skipped instead of scanning the whole library.

Project code does not implement perceptual hashing, frame selection, temporal voting, or duplicate math. The worker only calls configured tool commands:

- `VIDEO_DUPLICATE_DETECTION_COMMAND`: receives `{input}`, `{output}`, and `{seconds_per_hash}` placeholders and must write a signature file.
- `VIDEO_DUPLICATE_DETECTION_COMPARE_COMMAND`: receives `{current}` and `{candidate}` placeholders and must print a numeric score.
- `VIDEO_DUPLICATE_DETECTION_ALGORITHM`: label stored with signatures and duplicate candidates.
- `VIDEO_DUPLICATE_DETECTION_THRESHOLD`: score threshold for suspected full-duplicate rows.

The old `VIDEO_SIMILARITY_*` names remain accepted as compatibility aliases, but new deployments should use duplicate-detection names.

The default worker image installs Meta ThreatExchange vPDQ support. The signature sampling policy is duplicate-focused:

```text
VIDEO_DUPLICATE_DETECTION_COMMAND=python -m server.app.video_similarity vpdq-signature "{input}" "{output}" "{seconds_per_hash}"
VIDEO_DUPLICATE_DETECTION_COMPARE_COMMAND=python -m server.app.video_similarity vpdq-compare "{current}" "{candidate}"
VIDEO_DUPLICATE_DEFAULT_INTERVAL_SECONDS=3
VIDEO_DUPLICATE_MIN_SAMPLES=12
VIDEO_DUPLICATE_MIN_INTERVAL_SECONDS=0.5
VIDEO_DUPLICATE_DETECTION_THRESHOLD=0.95
```

The effective signature interval is:

```text
min(default_interval_seconds, max(min_interval_seconds, duration_seconds / minimum_hash_samples))
```

For a 24-minute video this produces roughly 480 samples at the default 3-second interval instead of roughly 1440 samples at the old 1-second policy. For very short videos, the worker lowers the interval down to the configured minimum to keep enough samples.

The helper calls `threatexchange.extensions.vpdq.VPDQSignal` for hashing and comparison. It emits a conservative 0-1 score from the lower of the query-match and compared-match percentages, so a suspected full duplicate generally needs both videos to match most of each other.

Suspected duplicates are advisory only. The system records candidates but never deletes, replaces, or skips teacher-selected media based on duplicate detection.

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
- Duplicate-detection commands must be replaceable through `VIDEO_DUPLICATE_DETECTION_COMMAND` and `VIDEO_DUPLICATE_DETECTION_COMPARE_COMMAND`.
- Suspected duplicate candidates must remain advisory until a teacher/admin records a decision.

## Operations

Start local services:

```powershell
docker compose up -d --build backend tusd video-worker postgres
```

Restart the `backend` service after changing `MAX_MEDIA_UPLOAD_MB`; the teacher frontend displays the backend runtime policy, so it updates after the backend reloads the environment.

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
POST /api/teacher/media/assets/{asset_id}/retry-processing
```

## Rollback

Stop `video-worker` to pause processing:

```powershell
docker compose stop video-worker
```

Existing ready media continues to serve from `media_assets.playback_relative_path` or `media_assets.relative_path`. If resumable upload needs to be disabled during rollout, unset `VITE_TUS_ENDPOINT` and use the small-file fallback upload path.
