## Context

The student product model is now documented in `docs/student-product-learning-model.md`: home is an experiment-video discovery stream, learning is the catalog/map surface, AI is the contextual tutor, assessment diagnoses weak points, and profile stores history.

The current student H5 implementation does not match that model:

- `HomeRootPage` is a generic hero/action hub that links to recommended learning, periodic-table learning, video library, AI, and assessment.
- `VideoLibraryPage` is a second-level search/browse surface backed by `searchStudentVideoLibrary`.
- The video-library Elasticsearch projection deliberately excludes video resource fields such as media ids, thumbnails, stream paths, and original filenames. This is correct for search safety, but it means search results are not a suitable playback feed payload.
- Point detail already has the authoritative video payload through `StudentPointDetailResponse.videos`.

Commercial product pattern:

- YouTube/Bilibili-style horizontal-video feeds keep media in 16:9 cards and play a muted inline preview when the card becomes the primary visible item.
- Shorts-style vertical full-screen swiping is not suitable because the source experiment media is horizontal and experimental details need spatial clarity.
- The feed is a discovery surface. Full experiment purpose, principle, equipment, equations, AI, and assessment actions belong to point detail or a later learning-player surface.

## Goals / Non-Goals

**Goals:**

- Make `/home` a single-column horizontal experiment-video feed.
- Add a dedicated student home feed API that returns playable published point videos and safe learning metadata.
- Keep every feed item catalog-backed: title, catalog path, tags/badges, and point-detail target must come from published catalog point context.
- Implement muted inline autoplay preview using one active card at a time.
- Preserve existing video-library search as search/browse, not as the home feed implementation.
- Keep the first implementation deterministic and safe while leaving ranking room for future assessment-based personalization.

**Non-Goals:**

- Do not implement vertical Shorts, full-screen snap paging, comments, likes, creator channels, or entertainment-style social features.
- Do not add media resource fields to the video-library Elasticsearch search index.
- Do not redesign point detail into the full horizontal learning player in this change.
- Do not implement a full recommendation engine from assessment data in this change; only provide the feed contract and ranking seams.
- Do not change teacher media upload, catalog editing, or preview-mode sandbox boundaries.

## Decisions

### 1. Add a dedicated home video feed API

The backend will expose a new authenticated student endpoint:

```text
GET /api/student/home-video-feed?limit=12
```

The response will contain feed items with playable media resource paths:

```text
id
node_id / placement_node_id / canonical_point_id
chapter_id
title
summary/snippet
catalog_path
badges
video.media_id
video.stream_path
video.thumbnail_path
video.duration_seconds
target
reason
```

Rationale:

- Home feed needs media playback fields.
- Search results intentionally exclude these fields.
- Feed data is a product read model, not a search index document.

Alternative considered:

- Reuse `StudentVideoLibrarySearchResponse.browse.recommended`. Rejected because it has no direct video resource fields and should stay search/action oriented.

### 2. Source feed items from published point placements with visible media

V1 feed rows will be selected from the same authoritative catalog/media tables as point detail:

- published point placement;
- published canonical point/content;
- published ancestors;
- active ready media binding;
- active ready media asset;
- student-visible thumbnail/stream route.

Only point placements with a playable video are eligible for feed cards. This differs from catalog browsing, where points without videos may still be visible.

### 3. Keep ranking deterministic first, personalization later

V1 feed ranking will prefer stable, learning-safe ordering:

- video-ready point placements;
- published catalog/chapter order;
- recent content/media updates as a secondary boost;
- deterministic id tiebreaking.

The response shape includes `reason` so later assessment personalization can emit reasons such as `weakness`, `recent`, or `recommended` without changing the card component.

### 4. Replace home hub UI with feed UI

`HomeRootPage` becomes the home feed owner:

- Fetch `getStudentHomeVideoFeed`.
- Render loading, error, empty, and feed states.
- Render a compact top bar with title and search action.
- Render single-column 16:9 cards.
- Keep bottom navigation visible because home is a root tab.

The old action hub behavior moves to the other root tabs:

- learning/catalog actions stay under `学习`;
- AI root remains under `AI`;
- assessment root remains under `测评`;
- video-library search stays reachable through the home search action and the video-library route.

### 5. Use IntersectionObserver for one active muted preview

The frontend will use an IntersectionObserver-based controller:

- observe each feed card;
- choose the card with the strongest visible ratio above a threshold;
- play only that card's video;
- pause all other feed videos;
- default to poster-only in environments where autoplay fails.

Card video attributes:

```text
muted
playsInline
preload="metadata"
poster
loop
```

Rationale:

- This mirrors mature feed behavior and respects browser autoplay policies.
- Muted inline autoplay is broadly allowed; audible autoplay is not reliable.
- A one-active-video rule avoids network and CPU overload in the phone WebView.

### 6. Route actions preserve learning context

Feed cards route to existing second-level destinations:

- tapping the media/title/detail action opens point detail with `from=home`;
- the AI action opens AI chat with point/catalog context when assistant is enabled;
- search opens `/video-library?from=home`.

Back navigation should return to home with the root tab identity intact.

## Risks / Trade-offs

- [Risk] Autoplay can still be blocked or fail in some WebViews. → Mitigation: cards always render poster/title/path; play promise failures are ignored; clicking still opens detail.
- [Risk] Loading many videos can hurt mobile performance. → Mitigation: single active video, metadata preload, poster for inactive cards, and small default limit.
- [Risk] Feed could be mistaken for entertainment short-video UI. → Mitigation: always show catalog path, experiment tags, and point-detail/AI learning actions; avoid likes/comments/social chrome in V1.
- [Risk] Ranking without assessment personalization may feel generic. → Mitigation: deterministic V1 establishes the contract; `reason` and target metadata allow later assessment-driven ranking.
- [Risk] Duplicated canonical points with multiple placements can repeat. → Mitigation: V1 may show placement-specific context; future ranking can dedupe by canonical point if needed.
- [Risk] Home root tests currently assume the old action hub. → Mitigation: update tests to assert the video feed and preserve video-library route tests separately.

## Migration Plan

1. Add backend feed schemas and route.
2. Add frontend feed API types/client.
3. Replace home root UI with feed cards and search action.
4. Add/adjust tests for feed loading, empty state, navigation, and active-video selection.
5. Validate OpenSpec, typecheck, and frontend tests.

Rollback is straightforward: route and schemas are additive, and home UI can be reverted to the previous action hub while leaving the API unused.

## Open Questions

- Exact ranking formula for assessment-driven weak-point recommendations is deferred until assessment-to-catalog-node scoring is specified.
- A full horizontal learning-player layout with a right-side three-element panel is intentionally left for a follow-up change.

