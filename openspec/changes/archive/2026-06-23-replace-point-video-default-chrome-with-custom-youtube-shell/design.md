## Context

The point-video detail page already uses ArtPlayer through `PointVideoPlayer`, and previous work established the correct page composition: the playable video is the edge-to-edge page header, the generic `PageBar` is absent, and catalog path/title/learning content render below the player. The remaining problem is the control model.

Recent QA exposed that the current implementation can show two control layers at once:

- ArtPlayer's built-in chrome: bottom progress, built-in play/volume/time/settings/fullscreen controls, and mask/state controls. These can control playback.
- Student custom pieces: player-owned back and custom time capsule. These are styled for the product, but the time capsule is display-only and does not replace the built-in toolbar.

Local ArtPlayer inspection confirmed the root cause: `option.controls` appends custom controls after ArtPlayer creates its default controls; it does not replace the default chrome. Therefore adding a custom `point-time` control cannot produce a true YouTube-like mobile player by itself.

The product decision is now:

- Keep ArtPlayer as the media engine.
- Do not migrate to xgplayer for this UI change.
- Hide browser native controls and ArtPlayer's default chrome for playable point videos.
- Build a single student-owned custom mobile player shell and wire every visible control to ArtPlayer/`HTMLVideoElement` APIs.

Relevant implementation constraints:

- Student H5 is phone-first and must work at `360px`, `390px`, and `430px` CSS widths.
- Teacher student-preview renders the same student app inside a phone iframe, so it must share the same interaction path.
- The playable-video back affordance is route navigation, not a media control, but it visually belongs inside the active player shell.
- The no-video state cannot reveal playback chrome, so it must keep a visible shared back affordance.
- Existing shared back-arrow geometry and placement standards still apply.

## Goals / Non-Goals

**Goals:**

- Replace the visible ArtPlayer default chrome on playable point videos with one custom mobile shell.
- Keep ArtPlayer responsible for media lifecycle, playback, source loading, autoplay/muted policy, `playsInline`, time/duration, seek, and fullscreen/web-fullscreen APIs.
- Make the inactive playable state quiet: video or poster first, no persistent back arrow, no persistent toolbar, only a faint bottom progress indicator when progress is known.
- Make the active playable state YouTube-like: player-owned back, central play/pause, optional skip controls, bottom time capsule, bottom seek/progress, and supported fullscreen/settings affordances.
- Ensure every custom visible control is interactive and wired; no display-only playback controls.
- Keep the player shell stable in the student preview iframe and on real mobile browsers.
- Provide regression coverage that fails if ArtPlayer default chrome leaks back into the product UI.

**Non-Goals:**

- Do not replace ArtPlayer with xgplayer, Vidstack, Video.js, Plyr, or Media Chrome for this change.
- Do not introduce HLS/DASH/transcoding/quality-switching work unless already supported by current media URLs.
- Do not build comments, recommendations, danmaku, captions, casting, picture-in-picture, or social video features.
- Do not change backend catalog, media binding, preview-media, or point-detail APIs.
- Do not redesign the point-detail content below the player beyond spacing needed to preserve the video header.
- Do not expose a settings or gear button unless the visible control opens a working settings surface.

## Decisions

### 1. Keep ArtPlayer, do not migrate to xgplayer

ArtPlayer remains the best fit for the current problem because it is already integrated and exposes the required engine APIs: `play()`, `pause()`, `toggle()`, `seek`, `forward`, `backward`, `currentTime`, `duration`, `playing`, `muted`, `volume`, `fullscreen`, `fullscreenWeb`, and video lifecycle events.

xgplayer has a stronger streaming-oriented ecosystem and a more componentized player UI, but adopting it would be a playback-engine migration. That is unnecessary for a UI-shell replacement and would increase risk in route cleanup, tests, student preview, and media URL handling.

Alternatives considered:

- **Migrate to xgplayer now.** Rejected because the current bug is duplicate/incorrect chrome, not insufficient media playback capability.
- **Adopt Media Chrome or Vidstack.** Rejected for this change because they introduce another control framework while ArtPlayer already supplies the playback engine we need.
- **Keep styling ArtPlayer default controls.** Rejected because default controls remain ArtPlayer-owned and cannot match the desired one-shell mobile composition without persistent leakage.

### 2. Treat ArtPlayer as a media engine only

The playable point-video implementation should configure ArtPlayer for playback, not for final student-facing controls. ArtPlayer should still own:

- video element creation and source loading;
- poster and preload behavior;
- autoplay/muted startup policy;
- `playsInline` mobile behavior;
- playback, pause, time, duration, seek, volume, mute, fullscreen/web-fullscreen APIs;
- lifecycle cleanup through `art.destroy(false)`;
- event emission for `ready`, `video:loadedmetadata`, `video:durationchange`, `video:timeupdate`, `video:play`, `video:pause`, `video:waiting`, `video:playing`, `video:error`, `seek`, and fullscreen events.

ArtPlayer should not own the visible product chrome for playable point videos. Its built-in `.art-bottom`, `.art-mask`, default progress, default controls, default time, default play button, and default settings/fullscreen buttons must not be visible as the final UI.

Alternatives considered:

- **Use `option.controls` for all custom UI.** Rejected because ArtPlayer first creates default controls and then appends custom controls.
- **Use ArtPlayer `layers` for the entire shell.** Possible, but less ergonomic for React state and tests. Use only if React overlay proves impossible.

### 3. Render the custom shell as a React overlay above the ArtPlayer mount

The preferred structure is:

```text
.point-art-player
  .point-art-player-mount
    ArtPlayer internal video root
  .point-youtube-shell
    inactive progress
    active overlay controls
```

The shell should be a React-owned overlay inside `PointVideoPlayer`, backed by the current ArtPlayer instance ref. This keeps DOM/state/test ownership in React while ArtPlayer continues to manage playback.

The overlay should:

- cover the player footprint with `position: absolute; inset: 0`;
- sit above ArtPlayer internal chrome;
- allow taps on controls while preserving video tap-to-toggle behavior;
- avoid blocking media gestures unless the shell intentionally handles them;
- clean up timers/listeners when the player unmounts or source changes.

ArtPlayer default chrome can be hidden with scoped CSS under `.point-art-player` and/or by disabling ArtPlayer options that add optional controls. The implementation must remain scoped to point-video pages and must not restyle global ArtPlayer usage if future pages add it.

Alternatives considered:

- **Portal the shell outside the player.** Rejected because the controls must remain inside the video footprint and clip with the player frame.
- **Inject shell HTML through ArtPlayer layers.** Rejected as the primary approach because it makes React event/state wiring harder and risks reproducing the previous split-brain model.

### 4. Define a small player state model

The shell should derive a minimal state snapshot from ArtPlayer/video events:

```text
isReady
isPlaying
isSeeking
currentTime
duration
buffered/loaded ratio if available
error/empty state
isFullscreen or isFullscreenWeb
isChromeActive
```

`isChromeActive` should be student-shell owned, not ArtPlayer-control owned. Recommended rules:

- initial playable state: inactive after the first frame/poster is ready;
- tap on the player surface: activate shell;
- tap central play while inactive: activate and toggle playback;
- playing + no recent interaction: hide active shell after a short timeout;
- paused, seeking, error, settings open, or focus within shell: keep active shell visible;
- route transition/source change/unmount: clear timers and listeners.

This replaces the old reliance on ArtPlayer's `control` event as the source of truth for visible product chrome.

Alternatives considered:

- **Keep using ArtPlayer `control`/`hover` events.** Rejected because default ArtPlayer chrome will be hidden; the custom shell needs its own activity model.
- **Always keep active chrome visible.** Rejected because the requested mobile behavior is video-first with only a quiet persistent progress line.

### 5. Implement custom controls only when they are wired

Every visible control must perform an action:

- Back: call the existing source-aware `onBack` callback and stop propagation.
- Play/pause: call `art.toggle()` or explicit `art.play()`/`art.pause()`.
- Seek/progress: compute target seconds from pointer/touch position and set `art.seek = seconds` or `art.currentTime = seconds` according to ArtPlayer API compatibility.
- Skip backward/forward, if shown: set `art.backward = 10` and `art.forward = 10` or equivalent.
- Time capsule: render formatted `currentTime / duration` from tracked state.
- Fullscreen, if shown: call `art.fullscreenWeb = !art.fullscreenWeb` or supported fullscreen API.
- Mute/settings, if shown: call a real mute/settings action. If no settings surface is implemented, do not show a gear.

Display-only playback controls are explicitly disallowed. The previous time capsule is acceptable only if it is part of a complete custom shell and not visually competing with ArtPlayer's default time control.

### 6. Custom progress replaces ArtPlayer visible progress

The visible product progress should be custom shell progress, not ArtPlayer's default `.art-progress`.

Inactive state:

- render a faint, bottom-pinned progress line;
- no thumb;
- no toolbar;
- no back arrow;
- no full-width gradient that visually turns into a control bar.

Active state:

- render an interactive progress/seek control near the bottom edge;
- use the branded active-progress treatment: a colored SYSU-aligned played track (green/red treatment is acceptable) and a small circular SYSU progress thumb;
- use a phone-safe hit target larger than the visual line;
- keep the time capsule and primary controls clear of the progress hit area;
- update immediately during drag and commit seek on pointer/touch release;
- preserve readable video content by avoiding heavy persistent overlays.

The SYSU progress thumb belongs to the active shell only. The inactive shell must stay quiet with a gray/white line and no thumb, while the active shell may show the colored track and SYSU thumb as the branded seek affordance.

### 7. Preserve mobile inline playback constraints

The player must continue to avoid native fullscreen/player takeover where practical:

- keep `playsInline: true`;
- explicitly keep browser native controls disabled (`moreVideoAttr.controls = false`);
- retain compatible inline video attributes for mobile WebViews where supported;
- use muted autoplay for initial permissive autoplay if autoplay remains enabled;
- handle autoplay rejection gracefully by showing the custom play affordance.

Some iOS or Android browsers/WebViews may still force native playback in specific modes. The primary target for this change is in-page H5 playback and teacher student-preview behavior.

### 8. Empty state remains separate

No-video point detail state is not a playable shell. It must:

- keep the edge-to-edge video header footprint;
- show the existing graceful no-video placeholder;
- keep a visible shared back affordance immediately available;
- not wait for tap-to-reveal playback chrome;
- not show fake play/progress controls.

### 9. Verification must protect against default chrome leakage

Tests and QA should verify that playable point videos:

- do not render ArtPlayer default controls as visible product UI;
- do render the custom shell overlay;
- can play/pause through the custom central control;
- can update and seek through custom progress;
- keep the route back affordance hidden while inactive and visible while active;
- keep no-video state navigable;
- behave the same in teacher student-preview and normal student H5.

CSS/source tests should guard against broad global selectors and against reintroducing a second visible ArtPlayer toolbar.

## Risks / Trade-offs

- [Risk] Custom shell work is larger than styling ArtPlayer controls. -> Mitigation: keep ArtPlayer as the engine and implement the shell in focused layers: first hide default chrome and wire play/time/progress/back, then add optional secondary controls.
- [Risk] The custom progress scrubber could conflict with tap-to-toggle on mobile. -> Mitigation: reserve a dedicated progress hit zone and treat pointer/touch movement beyond a small threshold as seeking, not tapping.
- [Risk] Autoplay may still fail on some browsers. -> Mitigation: use muted autoplay where required, catch play promise rejection, and show the custom play affordance as the recovery path.
- [Risk] Hiding ArtPlayer internal chrome could hide useful error/loading states. -> Mitigation: keep or recreate loading/error affordances in the custom shell before suppressing defaults completely.
- [Risk] Fullscreen behavior differs on iOS, Android WebView, desktop Chrome, and teacher preview iframe. -> Mitigation: use `fullscreenWeb` as the first target, keep route/browser back compatible, and test supported phone preview widths.
- [Risk] Future ArtPlayer updates could change APIs or internal DOM. -> Mitigation: rely on public playback APIs for behavior, keep DOM-hiding selectors scoped, and add source-level regression tests.
- [Risk] Duplicate controls may reappear during incremental implementation. -> Mitigation: make "only one visible product chrome" a spec and test requirement, and treat default ArtPlayer toolbar visibility as a failure.

## Migration Plan

1. Preserve current `PointVideoPlayer` source loading, poster, autoplay/muted policy, `playsInline`, destroy behavior, no-video placeholder, and route-aware `onBack`.
2. Introduce a React custom shell overlay inside `PointVideoPlayer` and connect it to the ArtPlayer instance ref.
3. Subscribe the shell to ArtPlayer/video lifecycle events and maintain the minimal state snapshot.
4. Hide ArtPlayer default visible chrome for playable point videos using scoped CSS and/or option changes.
5. Implement inactive shell: video-first frame plus faint bottom progress line.
6. Implement active shell: route back, central play/pause, time capsule, and interactive progress.
7. Add optional skip/fullscreen/settings controls only when fully wired.
8. Update tests for shell state, wired controls, hidden default chrome, route back behavior, no-video state, and student-preview parity.
9. Run OpenSpec validation, targeted Vitest tests, typecheck/build as appropriate, and manual/visual QA at `360px`, `390px`, and `430px` widths.

Rollback: restore the previous ArtPlayer default chrome configuration and remove the custom shell overlay, while keeping the edge-to-edge player header and no-video placeholder. If rollback is needed after partial implementation, prioritize re-enabling a working play/pause/progress surface over preserving custom visuals.

## Open Questions

- Should the first implementation include skip backward/forward buttons, or should it ship with play/pause, progress, time, back, and fullscreen only?
- Should the active shell include a settings button immediately, or should settings wait until there is a real settings surface such as playback speed?
- Should muted autoplay be a temporary implementation strategy or become a user-configurable preference later?
