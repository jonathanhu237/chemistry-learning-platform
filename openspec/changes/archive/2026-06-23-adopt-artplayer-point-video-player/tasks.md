## 1. Player Dependency And Wrapper

- [x] 1.1 Add ArtPlayer to the student H5 package dependencies and lockfile.
- [x] 1.2 Create a point-specific ArtPlayer React wrapper that accepts media URLs, poster, title, empty state, and the existing route back callback.
- [x] 1.3 Ensure the wrapper destroys the ArtPlayer instance on unmount and recreates it safely when the media source changes.

## 2. Point Detail Integration

- [x] 2.1 Replace the raw point-detail `<video controls>` stage with the ArtPlayer wrapper.
- [x] 2.2 Remove the standard point-detail `PageBar` title header while preserving loading and error states.
- [x] 2.3 Keep catalog path and full point title below the player and preserve no-video, preview, AI, related-point, and assessment behavior.

## 3. Branded Mobile Controls

- [x] 3.1 Add a player-control-layer return action that appears with ArtPlayer chrome and calls the existing source-aware `onBack`.
- [x] 3.2 Add scoped SYSU-branded player progress styling, including a SYSU-logo progress thumb.
- [x] 3.3 Add mobile-safe CSS for 16:9 player geometry, hidden/inactive controls, no-video fallback, and long-title wrapping.

## 4. Tests And Validation

- [x] 4.1 Update student H5 tests or mocks for point detail playback, long title layout, no-video fallback, and back-control behavior.
- [x] 4.2 Run OpenSpec validation for the new change.
- [x] 4.3 Run relevant student H5 typecheck/tests and record any remaining browser/WebView verification risk.

Verification note: `openspec validate adopt-artplayer-point-video-player --strict`, `npm run typecheck`, `npm run test:e2e`, and `npm run test` pass. Remaining risk is limited to real-device WebView gesture timing and first-frame chrome behavior, which automated jsdom tests approximate through ArtPlayer control/hover events but cannot visually prove.

## 5. Edge-To-Edge Video Header Refinement

- [x] 5.1 Update the point detail page layout so the player is the edge-to-edge top header with no route top padding, side gutters, outer border, radius, shadow, or card background.
- [x] 5.2 Remove grid-paper background and stacked card presentation from the point video detail route while preserving readable flat title and learning sections below the player.
- [x] 5.3 Update no-video fallback to use the same full-width header footprint and keep the return action inside that footprint.
- [x] 5.4 Update tests to assert the Bilibili-style layout constraints and no-card/no-grid styling hooks.
- [x] 5.5 Rerun OpenSpec validation and student H5 typecheck/tests after the refinement.

Refinement verification note: `openspec validate adopt-artplayer-point-video-player --strict`, `npm run typecheck`, `npm run test:e2e`, `npm run test`, and `npm run build` pass. The updated student H5 build was copied into `chemistry-admin-web-student-1`; container health is healthy and `http://222.200.189.249:5173/` serves `index-3tvxwYdV.js` plus `index-CFxYlruA.css`.

## 6. Chemistry Equation Rendering

- [x] 6.1 Add a reusable student H5 chemistry equation renderer using KaTeX and mhchem.
- [x] 6.2 Render point detail `reaction_equations[].canonical_mhchem` as chemical equations instead of a single raw backend text paragraph.
- [x] 6.3 Preserve supplemental annotation text below each rendered equation and render simple inline chemistry tokens where possible.
- [x] 6.4 Update point-detail tests to assert KaTeX/mhchem output and no raw-equation fallback for normalized rows.

Equation rendering verification note: `openspec validate adopt-artplayer-point-video-player --strict`, `npm run typecheck`, `npm run test:e2e`, `npm run test`, and `npm run build` pass. The updated build was copied into `chemistry-admin-web-student-1`; container health is healthy and `http://222.200.189.249:5173/` serves `index-FbHAzCyd.js` plus `index-DPo27zSs.css`.

## 7. Shared Reaction Equation Rendering

- [x] 7.1 Add a shared frontend reaction-equation rendering core that owns canonical source priority, invalid-row filtering, fallback text, and annotation preservation.
- [x] 7.2 Route the teacher catalog equation preview through the shared core while preserving the teacher review presentation profile.
- [x] 7.3 Replace the student point-detail chemistry renderer with the shared core and a student-mobile presentation profile that uses inline KaTeX/mhchem, body-copy sizing, wrapping, and plain fallback for unconfirmed legacy text.
- [x] 7.4 Update tests to cover canonical-only rendering semantics, plain legacy fallback, teacher/student shared source priority, and absence of default student KaTeX display blocks.
- [x] 7.5 Rerun OpenSpec validation, student H5 typecheck/tests/build, teacher typecheck/tests for touched preview behavior, and update the running student container.

Shared reaction-equation rendering verification note: `openspec validate adopt-artplayer-point-video-player --strict`, student `npm run typecheck`, `npm run test:e2e`, `npm run test`, `npm run build`, teacher `npm run typecheck`, `npm run test`, and `npm run build` pass. The updated student H5 build was copied into `chemistry-admin-web-student-1`; container health is healthy and `http://222.200.189.249:5173/` serves `index-DIIDebId.js` plus `index-BfjE2qhc.css`.
