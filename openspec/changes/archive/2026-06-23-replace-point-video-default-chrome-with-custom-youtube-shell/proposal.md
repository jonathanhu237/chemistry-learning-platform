## Why

The current point-video detail player mixes ArtPlayer's default chrome with custom student-facing controls, which creates duplicate playback surfaces: ArtPlayer's built-in toolbar can control playback, while custom UI pieces such as the time capsule are only partially wired. The product direction is now clear: keep ArtPlayer as the playback engine, but replace the visible point-video chrome with a single mobile YouTube-like custom shell that is touch-safe, visually quiet when inactive, and fully wired to playback.

## What Changes

- Treat ArtPlayer as the media engine for point-video detail pages, not as the final student-facing control UI.
- Hide browser native video controls and ArtPlayer's default player chrome for playable point videos.
- Introduce a custom mobile YouTube-like shell as the only visible playback control layer for playable point videos.
- Keep the inactive playable state video-first: no persistent toolbar or back arrow, only a subtle bottom progress line when progress data exists.
- Reveal the active shell on tap/pointer activation, including player-owned back, centered play/pause, seek/progress, time capsule, and supported fullscreen/settings affordances.
- Require every custom visible playback control to call ArtPlayer or `HTMLVideoElement` playback APIs; display-only controls are not acceptable.
- Preserve the existing empty/no-video state contract: because no playable chrome can be revealed, the empty state keeps a visible shared back affordance.
- Keep ArtPlayer over xgplayer for this change; xgplayer remains a future option only if streaming, clarity switching, or complex buffering requirements justify a playback-engine migration.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `student-h5-mobile-design-system`: Replace the previous ArtPlayer-native-control preference with a custom point-video shell requirement, including inactive/active mobile control composition, touch targets, and visual constraints.
- `student-h5-learning-experience`: Update point video detail behavior so the playable video header owns a single custom playback shell while keeping title/path/content below the player.
- `student-h5-route-stack-navigation`: Preserve source-aware route-stack return behavior while moving the playable point-video back action into the custom active shell only.

## Impact

- Affected frontend code: `apps/web-student/src/features/catalog/PointVideoPlayer.tsx`, point-video detail page wiring, student mobile CSS, route/back callback plumbing, and player-focused tests.
- Affected behavior: playable point-video detail pages, teacher student-preview iframe rendering of those pages, and mobile/touch playback interaction.
- No backend API or catalog data model changes are required.
- No player-engine migration is required; ArtPlayer remains installed and xgplayer is not introduced by this change.
