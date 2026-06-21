## Why

The current catalog video binding card treats the right side like a centered title poster, leaving weak information density and making the title feel detached from the video thumbnail. Teachers need the card to read more like a mature video product: thumbnail first, then left-aligned title and useful playback metadata.

## What Changes

- Show bound-video information in a YouTube-like layout: large playable thumbnail on the left, left-aligned title and metadata adjacent to it on the right.
- Add metadata for the student playback rendition, including actual student playback size, playback resolution when available, and precise upload time down to seconds.
- Keep management actions secondary and anchored to the lower-right of the information area.
- Do not show source file size as the primary size when a student playback rendition exists.
- Do not reintroduce duplicated title/file-name presentation in the current bound-video card.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `experiment-catalog-tree`: Point detail media binding responses include student playback rendition metadata needed by teacher authoring UI.
- `teacher-experiment-catalog-editor`: The video binding tab presents current bound video metadata with a left-aligned, YouTube-like hierarchy.

## Impact

- Backend catalog tree media binding read model.
- Teacher frontend catalog tree API types.
- Teacher frontend video binding panel and CSS.
- Contract and regression tests for catalog video binding metadata.
