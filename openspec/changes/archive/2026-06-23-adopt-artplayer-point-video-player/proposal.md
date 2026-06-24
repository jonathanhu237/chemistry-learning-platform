## Why

Student point detail pages currently render the point title in the standard detail page bar before the video. Long chemistry experiment titles can push the video down or stretch the navigation area, which is a poor fit for a video-first point page.

The point detail page should behave like a mature mobile video page: the 16:9 player owns the top of the screen, player controls appear only when the player is active, and the full point title lives below the video with the learning context.

## What Changes

- Replace the point detail page's standard `PageBar` video header pattern with an edge-to-edge video page header: the player touches the top of the detail viewport and spans the full available mobile width.
- Adopt ArtPlayer for the student point detail video player so the H5 app has a mature base for custom controls, future danmaku, HLS/control plugins, and branded player skin work.
- Add a player-control-layer return action that appears with the video controls rather than as an always-visible page header.
- Move the point title and catalog path below the player in a flat content section so long titles can wrap without changing the video stage height.
- Remove the point detail page's grid-paper background and card-like player/title presentation; the page should read as direct video-header plus separated content sections, closer to Bilibili's mobile video detail layout.
- Customize the point video progress control with SYSU branding, including a SYSU-logo style progress thumb.
- Render normalized chemistry equations through a shared reaction-equation rendering contract so teacher review and student H5 use the same data priority, fallback, and annotation behavior while choosing viewport-appropriate presentation.
- Preserve the existing graceful no-video state and teacher preview behavior.
- Keep the existing route-stack `onBack` behavior; the player return control should call the same navigation behavior as the removed page bar.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `student-h5-learning-experience`: Point detail pages must use an edge-to-edge player header with title below the player and player-owned return controls.
- `student-h5-learning-experience`: Point principle equations must render from teacher-confirmed normalized chemistry data through shared rendering semantics.
- `student-h5-mobile-design-system`: The mobile H5 design system must support branded, touch-safe point video player controls, flat segmented content, and readable wrapped chemistry equations on phone viewports.

## Impact

- Shared frontend rendering core, teacher catalog equation preview, student H5 point detail component, point video player component, student styles, and route/detail tests.
- Dependencies: add ArtPlayer to `apps/web-student`.
- Assets: reuse the existing SYSU logo asset for player progress branding.
- Backend/API: no API contract change; point detail continues to use existing video stream and thumbnail paths.
