## 1. Preserve ArtPlayer Engine Contract

- [x] 1.1 Audit `PointVideoPlayer` current ArtPlayer options, lifecycle cleanup, media URL handling, poster handling, autoplay/muted policy, `playsInline`, and no-video placeholder behavior.
- [x] 1.2 Keep ArtPlayer as the only playback engine for point-video detail pages and confirm no xgplayer or alternate player dependency is introduced.
- [x] 1.3 Ensure browser native video controls are explicitly disabled for playable point videos through ArtPlayer video attributes or equivalent.
- [x] 1.4 Keep the existing source-aware `onBack` route callback available to the player layer without changing route-stack semantics.

## 2. Build Custom Shell Foundation

- [x] 2.1 Add a React-owned custom player shell overlay inside `PointVideoPlayer` above the ArtPlayer mount.
- [x] 2.2 Define the shell state model for readiness, playing, seeking, current time, duration, loading/error state, fullscreen/web-fullscreen state, and active/inactive chrome.
- [x] 2.3 Wire ArtPlayer and video lifecycle events into the shell state, with cleanup on source change and unmount.
- [x] 2.4 Implement shell activation rules for tap/pointer activation, playback pause, seeking, focus inside controls, inactivity timeout, route transition, and source changes.

## 3. Implement Wired Player Controls

- [x] 3.1 Implement the inactive shell with a video-first surface and faint bottom progress indicator only.
- [x] 3.2 Implement the active shell route back button using shared back-arrow geometry and the existing source-aware `onBack` callback.
- [x] 3.3 Implement the active central play/pause control wired to ArtPlayer playback APIs.
- [x] 3.4 Implement time formatting and active time capsule rendering from ArtPlayer/media current time and duration.
- [x] 3.5 Implement active progress/seek interaction with pointer/touch hit-zone handling and ArtPlayer seek updates.
- [x] 3.6 Implement fullscreen or web-fullscreen control only if it can be wired to ArtPlayer/fullscreen APIs in the current runtime.
- [x] 3.7 Implement skip backward/forward and settings controls only if they are fully wired; otherwise omit them from the first implementation.
- [x] 3.8 Handle autoplay rejection by keeping the custom shell usable and exposing a working play action.

## 4. Hide Default Chrome and Style Mobile Shell

- [x] 4.1 Hide ArtPlayer default visible chrome for playable point videos under `.point-art-player` without affecting unrelated future ArtPlayer usage.
- [x] 4.2 Ensure ArtPlayer default bottom toolbar, progress bar, time display, play control, settings/fullscreen controls, and mask/state chrome do not remain visible as product UI.
- [x] 4.3 Style inactive progress as a quiet bottom-pinned line with no thumb or full toolbar.
- [x] 4.4 Style active shell controls so back, central playback, time capsule, progress, and fullscreen affordances do not overlap at 360px, 390px, or 430px widths.
- [x] 4.5 Keep SYSU progress branding scoped to the active progress/seek control, with the inactive progress remaining gray/white and thumb-free.
- [x] 4.6 Preserve edge-to-edge square-corner video header layout and title/content bands below the player.

## 5. Preserve Empty State and Route Behavior

- [x] 5.1 Keep the no-playable-video placeholder as a separate non-playback state, without fake play/progress/time/fullscreen controls.
- [x] 5.2 Keep a visible shared back affordance in the no-video placeholder.
- [x] 5.3 Ensure playable-video back is hidden while inactive and visible/touchable only while the custom shell is active.
- [x] 5.4 Ensure tapping player back stops propagation and does not also toggle playback or seek.
- [x] 5.5 Verify source-aware return from chapter catalog, directory page, unified search, home feed, related point links, and recent-learning contexts where supported by existing routes.

## 6. Regression Coverage

- [x] 6.1 Update component/e2e tests to assert ArtPlayer remains the engine and native browser controls remain disabled.
- [x] 6.2 Add tests that the custom shell renders and ArtPlayer default chrome is not visible as the student-facing UI.
- [x] 6.3 Add tests for active/inactive shell transitions, inactivity hiding, paused/seek/focus active retention, and cleanup on unmount/source change.
- [x] 6.4 Add tests for custom play/pause, time capsule formatting, and progress seek behavior.
- [x] 6.5 Add tests for playable back visibility, shared arrow geometry usage, route callback invocation, and event propagation safety.
- [x] 6.6 Add tests that the no-video placeholder remains visibly navigable and does not render fake playback controls.
- [x] 6.7 Update role-boundary/source-level tests to catch reintroduction of ArtPlayer default toolbar as product UI or migration to an unapproved player dependency.

## 7. Validation and Manual QA

- [x] 7.1 Run `openspec validate replace-point-video-default-chrome-with-custom-youtube-shell --strict`.
- [x] 7.2 Run targeted web-student Vitest tests for point video, route boundaries, and route stack behavior.
- [x] 7.3 Run web-student typecheck/build commands appropriate for the current workspace state.
- [x] 7.4 Manually verify playable point videos at 360px, 390px, and 430px widths.
- [x] 7.5 Manually verify teacher student-preview iframe behavior matches normal student H5 for tap-to-show, inactivity hide, play/pause, and seeking.
- [x] 7.6 Record any browser/WebView-specific native-player takeover issues as follow-up risks rather than silently working around them with preview-only code.
