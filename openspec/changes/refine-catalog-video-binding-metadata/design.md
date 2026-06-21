## Context

The catalog video tab already uses a single current-video slot with a large playable thumbnail and secondary replace/remove actions. The remaining problem is the information column: it currently behaves like a centered title poster, so the title feels detached from the thumbnail and the card wastes the right side.

The teacher needs the card to follow the familiar video-product pattern: thumbnail first, title and facts beside it, management actions secondary. The facts must describe the file students actually play, not the uploaded source file when a processed learning rendition exists.

## Goals

- Keep one bound video card for one point.
- Place the title and metadata left-aligned next to the thumbnail, close to the video visual.
- Show the student playback file size, playback resolution when available, and upload time with seconds.
- Keep replace/remove actions in the lower-right of the information column.
- Avoid duplicate title/file-name presentation and avoid source-size wording when a student playback rendition exists.

## Non-Goals

- Do not add binding-level publish/unpublish controls.
- Do not add upload controls inside the catalog editor.
- Do not redesign the media resource upload page.
- Do not add another request from the video panel just to hydrate metadata.

## Decisions

### Backend detail payload owns playback metadata

The catalog point detail media binding read model will include the metadata needed by the teacher card. This keeps the frontend from making a second media-detail request and keeps the definition of "student playback source" near the stream/read-model logic.

For each current binding, the read model selects the preferred ready rendition:

1. ready `learning` rendition,
2. any other ready rendition,
3. the asset's own playback/source fields as fallback.

The response exposes:

- `playback_file_size_bytes`
- `playback_width`
- `playback_height`
- `playback_duration_seconds`
- `playback_fps`
- `playback_bitrate`
- `playback_video_codec`
- `playback_audio_codec`
- existing `created_at` as upload time

This means the frontend can format "student playback source" from playback fields without accidentally showing the uploaded source size as the primary fact.

### Frontend uses one title plus a detailed metadata list

The current-video card keeps the thumbnail on the left. The right side becomes a three-part grid:

- title and a detailed property list aligned left near the thumbnail,
- flexible whitespace,
- replace/remove actions anchored bottom-right.

The title remains the only prominent name. The original file name is not shown as a second title line in the current card. The metadata uses a compact statistics-panel rhythm, one property per row:

- `播放源: 学生播放源`
- `文件大小: 12.4 MB`
- `分辨率: 1280 x 720 @ 30.000 fps`
- `码率: 2,007 Kbps`
- `视频编码: H.264`
- `音频编码: AAC`
- `上传时间: 2026-06-22 14:31:09`

When a field is missing, omit only that fact. If playback size is missing, show a neutral "学生播放源大小待生成" rather than a misleading source-size label.

### Time formatting is deterministic to seconds

The teacher UI formats upload time as local `YYYY-MM-DD HH:mm:ss`. This is precise enough for upload/debug conversations and avoids locale formats that may drop seconds.

## Risks

- Existing assets may not have a processed rendition yet. The backend must still return safe fallback/null values so the card does not fail.
- Long titles can collide with actions on narrower admin widths. CSS must clamp/wrap the title and let metadata wrap without resizing the video thumbnail.
- The repository has existing media lifecycle work in progress. This change should only depend on already-existing `media_renditions` and `media_assets` columns.
