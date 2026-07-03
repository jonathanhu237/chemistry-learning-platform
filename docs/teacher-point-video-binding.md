# Teacher Point Video Binding

## Decision

The legacy teacher backend manages videos from the chapter catalog point editor. A teacher uploads one video file from a point, and the system creates a media asset before binding it to that point through `experiment_catalog_point_media_bindings`.

The current video for a point is singular. Binding a new media asset archives the previous active binding for the same canonical point or placement node, then publishes the new binding. The separate `/videos` resource management entry remains out of scope for the simplified legacy backend.

## Domain Terms

- Point: a catalog node with `node_kind = "point"` that can own learning content and a current video.
- Media asset: the uploaded source video and its processing state in `media_assets`.
- Point video binding: the relationship between a point and the current media asset in `experiment_catalog_point_media_bindings`.
- Current video: the first non-archived point video binding returned by the catalog node detail API.

## Boundaries

- Teachers add or replace a point video only inside the point editor on the "章节目录与点位" page.
- Directory nodes cannot bind videos.
- Upload validation and processing remain in the media domain.
- Student playback only depends on ready, active media assets exposed through the student catalog read model.
