## 1. Player State And Artplayer Configuration

- [x] 1.1 Audit the current `PointVideoPlayer` wrapper and scoped player CSS to map existing Artplayer options, event listeners, layer injection, and progress overrides against this spec.
- [x] 1.2 Enable Artplayer `miniProgressBar` for playable point videos and keep the setting scoped to the point player wrapper.
- [x] 1.3 Keep `point-player-chrome-active` as the single CSS state bridge from Artplayer control visibility to the React/CSS player shell.
- [x] 1.4 Verify Artplayer cleanup still destroys the instance and leaves no active control/time listeners after source changes or unmount.

## 2. Playable Video Chrome

- [x] 2.1 Update playable-video back-layer styling so the shared back arrow is hidden and non-interactive when player chrome is inactive.
- [x] 2.2 Update active playable-video styling so the shared back arrow becomes visible and touchable only while player chrome is active.
- [x] 2.3 Preserve route-stack `onBack` behavior and stop back-button events from also toggling playback or control visibility.
- [x] 2.4 Keep the no-video placeholder's visible shared back affordance unchanged and explicitly separate from playable inactive chrome.

## 3. Progress And Time Feedback

- [x] 3.1 Tune the inactive mini progress line so it is subtle, bottom-pinned, and visually quieter than active interactive progress.
- [x] 3.2 Add a custom Artplayer control for compact current-time/duration feedback in the active bottom-left toolbar area.
- [x] 3.3 Update the time control from Artplayer video lifecycle events, including ready, duration changes, time updates, and seeking.
- [x] 3.4 Ensure the active interactive progress remains Artplayer-owned and keeps existing SYSU-scoped branding without affecting the inactive mini progress line.

## 4. Mobile Layout Polish

- [x] 4.1 Adjust scoped `.point-art-player` CSS variables/selectors for centered playback, bottom controls, progress, and time capsule spacing on 360px, 390px, and 430px widths.
- [x] 4.2 Ensure active controls do not overlap the shared return arrow, center playback affordance, bottom progress hit area, or fullscreen/settings controls.
- [x] 4.3 Confirm the point title/path and flat learning sections below the player remain unaffected by player chrome changes.
- [x] 4.4 Confirm teacher student-preview renders the same playable active/inactive player behavior as normal student H5.

## 5. Tests And Validation

- [x] 5.1 Add or update unit/component tests for Artplayer option expectations, including `miniProgressBar`, playable back layer, and custom time control registration.
- [x] 5.2 Add or update tests that assert playable back chrome is inactive by default and active only through the player chrome state class.
- [x] 5.3 Add or update tests that assert the no-video placeholder still renders a visible shared return affordance.
- [x] 5.4 Add or update route/back behavior coverage so tapping the playable player-owned back affordance still calls the existing source-aware return callback.
- [x] 5.5 Run OpenSpec validation for `refine-student-video-player-controls`.
- [x] 5.6 Run targeted student H5 tests and typecheck/build commands needed to verify the change.
- [x] 5.7 Capture or manually verify mobile visual behavior at 360px, 390px, and 430px, including teacher student-preview where practical.
