## Context

Student point detail is currently rendered by `CatalogPointDetailPanel`. The component places a shared `PageBar` with the point title above the 16:9 video stage, then repeats the path and full title below the video. This works for ordinary detail pages, but video point titles can be long enough to stretch the top navigation area and push the video down.

The student H5 app already treats experiment video as a first-class learning entry. Point detail should therefore use a video-player composition rather than a generic detail-header composition. The project is React + Vite and currently has no player dependency.

## Goals / Non-Goals

**Goals:**

- Make the point detail page video-first: the player is the page header, touches the top of the detail viewport, spans the full mobile width, and the title is rendered below it.
- Use ArtPlayer as the mature playback layer for point detail videos.
- Add a return control inside the player control layer, visible with player controls rather than always visible as page chrome.
- Remove the card-like treatment and grid-paper background from this specific point video detail page so the layout reads as a direct split between video header and content sections.
- Customize the progress control with SYSU branding, including a SYSU-logo style thumb.
- Preserve existing route-stack back behavior, preview media URL resolution, no-video state, AI context, related points, and assessment handoff.
- Keep the first implementation scoped to point detail while leaving room for danmaku, HLS control, quality switching, and subtitle plugins.

**Non-Goals:**

- Do not redesign the home video feed.
- Do not add danmaku, HLS conversion, quality switching, or comments in this change.
- Do not change backend point detail API payloads or media access routes.
- Do not replace all student videos globally with ArtPlayer until point detail behavior is stable.

## Decisions

### 1. Use ArtPlayer for point detail playback

ArtPlayer is a better fit than a pure headless player for this page because the product direction is close to a mature mobile video-site player. It has a complete player shell, built-in control behavior, custom controls, plugin hooks, danmaku ecosystem support, and HLS/DASH control plugin paths.

Alternatives considered:

- Vidstack: strong React/headless composition, but future danmaku and full video-site feature coverage would require more custom assembly.
- xgplayer: strong domestic mobile and WeChat-oriented player, but core control customization appears less direct for a custom branded progress treatment.
- Video.js: mature and extensible, but heavier and less aligned with a highly custom student H5 visual identity.

### 2. Wrap ArtPlayer in a route-aware React component

Create a point-specific wrapper component, for example `PointVideoPlayer`, that owns ArtPlayer lifecycle with `useEffect`, receives `src`, `poster`, `title`, `onBack`, and optional `emptyReason`, and destroys the ArtPlayer instance on unmount.

The wrapper should be the only component that imports ArtPlayer. `CatalogPointDetailPanel` should stay focused on data loading and learning content composition.

### 3. Treat back as player chrome, not page chrome

Remove the generic `PageBar` from the point detail panel. The ArtPlayer wrapper should add a back button through an ArtPlayer layer or control element so it appears as part of the active player controls. It must call the existing `onBack` callback from the route, preserving source-aware return.

The control should be hidden when the player chrome is inactive, matching the Bilibili-style behavior: default video frame first, tap to reveal player controls and back action.

### 4. Keep title and path below the player without a card shell

The catalog path and full point title remain the authoritative visible title block, but they should not look like a separate floating card under the player. They should sit in a flat content section with normal wrapping and a light divider. This keeps long chemistry titles below the video while avoiding the "player card plus title card" stack seen in the rejected preview.

### 5. Make the video player the detail page header

The point detail page should opt out of the generic `student-route-content` horizontal padding and detail-route top padding for this route. The player should span from the left edge to the right edge of the phone content area and sit flush at the top of the detail viewport. The player itself should not render an outer border, radius, or drop shadow in the normal detail page state. If a no-video fallback is shown, it uses the same edge-to-edge header footprint.

### 6. Brand progress without coupling learning content to player internals

The first branded treatment should use CSS overrides scoped to the point player wrapper, not global ArtPlayer CSS. The SYSU logo asset can be used as a thumb image or as a styled knob background. This keeps the customization reversible and avoids changing unrelated player instances later.

### 7. Share chemistry-equation semantics while separating presentation profiles

Chemistry equation rendering should not be implemented independently in teacher and student surfaces. The shared frontend core should own the business semantics:

- filter invalid rows where the consuming student view requires it;
- prefer `canonical_mhchem` as the only trusted renderable chemistry source;
- fall back to `canonical_display`, then `equation_core`, then `raw_text` as plain text;
- preserve `annotation_text` as the row explanation; and
- avoid frontend guessing of unconfirmed raw equations when normalized rows are absent.

Teacher catalog review and student H5 point detail can use different presentation profiles on top of that same core:

- `teacherReview`: preserves the review-workbench style that can show a complete teacher-confirmed equation and tolerate horizontal overflow as an authoring/review affordance.
- `studentMobile`: uses KaTeX/mhchem inline text rendering inside a block row, keeps the size at body-copy scale, left-aligns equations, allows natural line wrapping on phone widths, and keeps horizontal scrolling only as an extreme fallback.

This matches observed mature mobile chemistry software behavior: mobile reaction pages usually present equations as readable scientific text that wraps across lines instead of as large display equations that force the student to pan horizontally.

## Risks / Trade-offs

- [Risk] ArtPlayer is imperative and not idiomatic React. -> Mitigation: isolate it in a single wrapper, keep props small, and cleanly destroy/recreate on source changes.
- [Risk] ArtPlayer controls may differ between mobile browsers and WebViews. -> Mitigation: use `playsInline`, preserve the no-video fallback, and verify 360, 390, and 430 px phone widths.
- [Risk] Scoped CSS may break after ArtPlayer version changes. -> Mitigation: keep overrides narrow and test for the specific progress/back-control DOM behavior.
- [Risk] Custom back control could conflict with fullscreen native controls on some iOS states. -> Mitigation: require the in-page player state for this change and preserve browser/back-stack navigation as fallback.
- [Risk] Adding the dependency increases bundle size. -> Mitigation: scope import to point detail and avoid broad player adoption until needed.
- [Risk] Sharing a full React component across the two independently packaged Vite apps could require broader package/workspace changes. -> Mitigation: share a dependency-light rendering core first, keep KaTeX adapters local to each app, and make presentation differences explicit through named profiles.

## Migration Plan

1. Add ArtPlayer dependency to `apps/web-student`.
2. Add a point video player wrapper and scoped styles.
3. Replace the raw `<video controls>` point detail stage with the wrapper.
4. Remove the point detail `PageBar` title header and keep the title below the player.
5. Update tests for long-title point detail, no-video fallback, and route-stack back control presence.
6. Replace the student-only chemistry renderer with the shared reaction-equation core plus a student mobile presentation adapter.
7. Route teacher catalog equation preview through the same shared core while preserving its review-oriented display.
8. Run OpenSpec validation, package install/build or typecheck, and student/teacher tests.

Rollback: remove the wrapper usage and dependency, restore the `PageBar`, and return to the raw `<video controls>` rendering.
