## Context

Student H5 point video detail already renders videos through an Artplayer wrapper (`PointVideoPlayer`) rather than a raw `<video controls>` element. The previous Artplayer adoption established the video-first page structure: the player is the edge-to-edge page header, the generic `PageBar` is removed from playable video pages, and the catalog path/title live below the player.

The current wrapper already has the right foundation:

- Artplayer is installed in `apps/web-student` and is scoped to the point video player.
- The wrapper injects a route-aware back button through Artplayer `layers`.
- The wrapper listens to Artplayer `control` and `hover` events and toggles a `point-player-chrome-active` class.
- The CSS already scopes Artplayer progress and SYSU branding under `.point-art-player`.

The unresolved product issue is the player chrome model. The expected mobile behavior is closer to YouTube/Bilibili-style video chrome:

- the default playback view should prioritize video content;
- only a subtle bottom progress line should remain visible while controls are inactive;
- back, time, fullscreen, and other controls should appear with the playback toolbar;
- the back arrow is a route action, but in playable video state it is visually player chrome, not a persistent page header.

Artplayer exposes native support for this model through `miniProgressBar`, `layers`, `controls`, CSS variables, and events such as `control`, `hover`, `video:timeupdate`, `video:durationchange`, and `setBar`.

## Goals / Non-Goals

**Goals:**

- Define and implement a two-state mobile point-video control model:
  - inactive/default: video/poster first, subtle mini progress only;
  - active: return arrow, centered playback, bottom progress, bottom-left time capsule, and supported secondary controls.
- Use Artplayer's native progress, mini-progress, control, layer, and event systems before adding custom playback logic.
- Keep the playable-video return arrow hidden until player chrome is active.
- Keep the no-video placeholder navigable with a visible shared return arrow because there is no playback chrome to reveal.
- Preserve shared back-arrow glyph geometry and route-stack return behavior.
- Keep all player-specific visual overrides scoped to the point player so other student H5 controls are not restyled.
- Keep teacher student-preview behavior aligned with real student H5 because it renders the same app surface.

**Non-Goals:**

- Do not replace Artplayer or introduce another player library.
- Do not add danmaku, comments, quality switching, subtitles, HLS/DASH conversion, or recommendation feed behavior.
- Do not redesign the point detail content below the player beyond spacing needed to keep the player header stable.
- Do not change backend video binding, media asset, catalog point, or preview-media APIs.
- Do not implement a custom drag/scrub engine unless Artplayer native controls prove insufficient in QA.

## Decisions

### 1. Treat player chrome as a state machine

The point player should expose two explicit visual states:

- `inactive`: Artplayer controls are hidden or de-emphasized. The player shows video/poster content and, when playable media has duration/progress, a faint mini progress line pinned to the bottom edge.
- `active`: Artplayer controls are visible. The point player reveals the shared back arrow layer, central play/pause affordance, full progress control, time feedback, and fullscreen/settings affordances where supported.

The existing `point-player-chrome-active` class remains the state bridge from Artplayer to CSS. It should be driven by Artplayer `control` and mobile interaction signals rather than by separate React state that can drift from Artplayer.

Alternatives considered:

- Always show the back arrow as page chrome. Rejected because the user confirmed playable video pages should not keep a persistent back arrow; it should appear with the player toolbar.
- Build a fully custom overlay outside Artplayer. Rejected because it would duplicate Artplayer's existing control visibility, progress, gesture, and fullscreen state.

### 2. Use Artplayer `miniProgressBar` for the inactive progress line

The inactive bottom progress line should use Artplayer's `miniProgressBar: true` capability. Styling should tune `--art-mini-progress-height`, progress color, loaded color, and opacity under `.point-art-player`.

This keeps the always-visible progress line attached to the player lifecycle and avoids a second progress renderer that could desynchronize during seek, buffering, or duration changes.

Alternatives considered:

- Draw a custom absolute-positioned progress line in React or CSS. Rejected for the first implementation because it would require syncing current time, duration, seek, buffering, and cleanup manually.
- Keep the existing full progress bar visible. Rejected because it visually occupies the player chrome and does not match the quiet default mobile playback state.

### 3. Keep the route back action as an Artplayer layer

The playable-video back affordance should remain an Artplayer `layers` component because it visually belongs to the video surface rather than the page content below. Its button must:

- use the shared `BackArrowIcon`/`createBackArrowSvg` geometry;
- call the existing point-detail `onBack` route callback;
- stop event propagation so tapping back does not also toggle playback chrome;
- be hidden when `point-player-chrome-active` is absent;
- become visible and touchable when `point-player-chrome-active` is present.

The no-video placeholder should keep a visible shared back button because there is no player toolbar to reveal. This is a separate visual state, not an exception to playable video chrome.

Alternatives considered:

- Move the playable-video back button into a normal React `PageBar`. Rejected because point video pages intentionally use the player as the top chrome and render title/path below.
- Use a built-in Artplayer top control. Rejected because the route back action is not a playback control and should remain independently positioned in the player surface.

### 4. Add the time capsule through Artplayer `controls`

The active bottom-left `current / duration` pill should be added as a custom Artplayer `controls` component, preferably in the left controls area. The component should update from Artplayer video events:

- initialize on `ready` and `video:durationchange`;
- update on `video:timeupdate` and `seek`;
- render a stable placeholder while duration is unknown;
- clean up listeners when the player is destroyed.

This makes the time capsule participate in Artplayer's normal control visibility and avoids manual toolbar show/hide code.

Alternatives considered:

- Add the time capsule as an Artplayer `layer`. This gives exact absolute positioning, but it would require duplicate show/hide wiring and careful pointer-event management around the progress bar.
- Use Artplayer's default time display only. Rejected if the default placement/style cannot match the bottom-left capsule composition.

### 5. Preserve Artplayer's central playback and progress behavior

The central play/pause affordance should use Artplayer's native state/mask control where possible, with scoped CSS to adjust size, opacity, and placement. The bottom progress should remain Artplayer's native progress so touch seeking, buffering, and keyboard/hotkey behavior remain consistent.

The existing SYSU progress branding can remain, but it should not overpower the YouTube-like inactive state. If a branded thumb is kept, it should only appear on the active interactive progress, while the inactive mini progress remains faint and unobtrusive.

Alternatives considered:

- Replace Artplayer's central play/pause and progress DOM with custom controls. Rejected because it would increase gesture and accessibility risk without improving the core learning flow.

### 6. Keep student preview and phone behavior on the same path

Teacher student-preview renders the real student app in an iframe/phone frame. Player controls must therefore work without preview-only code paths. Any verification should include:

- normal browser/mobile viewport;
- teacher student-preview phone frame;
- tap-to-show and inactivity-to-hide behavior;
- seeking/dragging behavior with the same touch-emulation bridge that already fixed catalog horizontal swipes.

### 7. Scope selectors and guard against Artplayer upgrade drift

Artplayer customization necessarily touches internal class names such as `.art-video-player`, `.art-bottom`, `.art-progress`, `.art-controls-*`, and `.art-progress-indicator`. The change should keep those selectors under `.point-art-player` and add regression tests that would fail if the wrapper stops enabling mini progress, back chrome state, or the time capsule.

## Risks / Trade-offs

- [Risk] Artplayer internal DOM class names may change in a future dependency update. -> Mitigation: keep overrides scoped, assert expected wrapper/options in tests, and avoid broad global CSS selectors.
- [Risk] `control`/`hover` events may differ across touch devices, desktop browser, and student-preview iframe. -> Mitigation: verify both real student H5 and teacher preview, and keep the source of truth inside Artplayer rather than custom timers.
- [Risk] The time capsule could overlap the progress bar or fullscreen control on narrow widths. -> Mitigation: test 360px, 390px, and 430px widths; keep capsule content compact; allow controls to wrap or hide secondary items before overlapping primary playback controls.
- [Risk] The branded SYSU progress thumb could conflict with the desired quiet YouTube-like default state. -> Mitigation: use the SYSU thumb only for active progress and style inactive mini progress as a faint line.
- [Risk] Fullscreen native controls on some iOS/Android WebViews may suppress custom overlay chrome. -> Mitigation: keep route-stack/browser back as fallback, preserve `playsInline`, and treat in-page playback as the primary target for this change.

## Migration Plan

1. Update `PointVideoPlayer` Artplayer options to enable mini progress and register a custom time-capsule control.
2. Rework scoped point-player CSS so inactive playable videos show only the faint bottom mini progress while active chrome reveals the shared back layer and toolbar controls.
3. Preserve the visible no-video shared back affordance and the existing graceful placeholder.
4. Add or update tests covering:
   - Artplayer option/config expectations;
   - playable back arrow hidden when chrome is inactive and visible when active;
   - no-video state remains visibly navigable;
  - time capsule presence and formatting behavior;
   - route-stack return callback preservation;
   - student-preview/mobile viewport regressions where practical.
5. Run OpenSpec validation, targeted Vitest tests, typecheck/build as appropriate, and a visual/manual pass for 360px, 390px, and 430px phone widths.

Rollback: disable the time-capsule custom control, turn off `miniProgressBar`, and restore the previous scoped Artplayer CSS while keeping the Artplayer wrapper and edge-to-edge player layout.
