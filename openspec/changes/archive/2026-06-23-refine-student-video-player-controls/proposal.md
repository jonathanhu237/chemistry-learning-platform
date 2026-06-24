## Why

The student H5 point video player already uses Artplayer, but its current chrome does not yet match the intended mobile video behavior: the return arrow can read as persistent page chrome, the inactive player state is not defined as a video-first state, and the progress/time controls are not yet organized like mature mobile video players.

This change specifies a stable mobile player control model before further CSS tuning, so the implementation can use Artplayer deliberately instead of accumulating one-off overrides.

## What Changes

- Define a two-state point-video control model:
  - inactive/default state prioritizes the video frame or poster and shows only a subtle bottom mini progress indicator when a playable video exists;
  - active state reveals the player toolbar, the shared return arrow, centered playback control, interactive progress, time feedback, and fullscreen/settings affordances where supported.
- Require the playable point-video return arrow to appear only with the active player control layer, while preserving the always-visible navigable return affordance in the no-video placeholder state.
- Add a YouTube-like mobile control composition for point videos:
  - persistent faint progress line at the bottom in inactive playback;
  - time feedback in a bottom-left capsule in active chrome;
  - central playback control in the video area;
  - controls contained inside the video footprint rather than in the page header.
- Keep Artplayer as the player implementation and use its native lifecycle, mini-progress, controls, layers, and events before adding custom gesture or progress logic.
- Preserve existing route-stack return behavior, shared back-arrow geometry, preview media access, no-video fallback, point title/path below the player, and SYSU-scoped branding.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `student-h5-learning-experience`: Clarify the point video detail page's player-header behavior, including when the return action appears and how the no-video state remains navigable.
- `student-h5-mobile-design-system`: Refine the branded point-video player control layer into explicit inactive and active mobile states, including mini progress, time capsule, centered playback, scoped branding, and QA expectations.
- `student-h5-route-stack-navigation`: Clarify that playable point-video routes keep route-stack return behavior through a player-owned back affordance that is visible only with active player chrome, while no-video states keep a visible return affordance.

## Impact

- Affected student code is expected to stay within `apps/web-student`, primarily the point video player wrapper, point detail composition, scoped mobile CSS, and related tests.
- Artplayer remains the player dependency; no new player library is introduced by this change.
- No backend API, media binding, catalog data, or teacher-admin authoring behavior is expected to change.
- Teacher student-preview should continue rendering the same student H5 player behavior through the existing iframe/preview path.
