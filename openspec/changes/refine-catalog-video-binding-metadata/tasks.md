## 1. Specification

- [x] 1.1 Validate the OpenSpec change with strict validation.

## 2. Backend Contract

- [x] 2.1 Extend catalog point media binding read model with student playback size, resolution, and duration fields.
- [x] 2.2 Add backend contract coverage for preferred ready rendition metadata and fallback behavior.
- [x] 2.3 Extend current binding metadata with bitrate, frame rate, and codec fields.

## 3. Teacher Frontend

- [x] 3.1 Extend catalog tree API types for current video playback metadata.
- [x] 3.2 Render left-aligned YouTube-like title and metadata beside the thumbnail.
- [x] 3.3 Adjust CSS so title/metadata sit near the video and actions remain lower-right.
- [x] 3.4 Update frontend contract tests to protect metadata display without restoring duplicate file-name rows.
- [x] 3.5 Render current video metadata as a one-property-per-line details list.

## 4. Verification

- [x] 4.1 Run focused backend and frontend tests.
- [x] 4.2 Update running containers for the changed services.
