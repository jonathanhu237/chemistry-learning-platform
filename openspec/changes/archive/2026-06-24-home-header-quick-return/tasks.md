## 1. Header Structure

- [x] 1.1 Ensure `StudentAppHeader` supports a main row plus a header-attached `below` slot without forcing non-home root tabs to change.
- [x] 1.2 Render the home SYSU logo/search row and horizontal recommendation topic rail through the authenticated shell header.
- [x] 1.3 Set `推荐` as the default active home topic and allow topic taps to update only visible active state for this change.

## 2. Quick-Return Behavior

- [x] 2.1 Remove CSS Scroll-Driven Animation, title-height progress state, active `touchmove` or wheel interception, synthetic scroll replay, and per-gesture header offset logic from the home header implementation.
- [x] 2.2 Reuse the existing root `navCompressed` direction/threshold state to compress and restore the `.root-home` header unit.
- [x] 2.3 Scope header compression to the home root so detail routes, video-library search, point video pages, and other root tabs keep their existing chrome behavior.

## 3. Home Feed Layout

- [x] 3.1 Keep the recommendation rail visually attached to the home title/header style with only the configured header/feed spacing.
- [x] 3.2 Remove old home hero, explanatory cards, or background bands between the recommendation rail and the first feed item.
- [x] 3.3 Preserve the flattened YouTube-like video feed layout and bottom navigation spacing while the header compresses or restores.

## 4. Regression Coverage

- [x] 4.1 Update `apps/web-student` tests to assert the home header topic rail, default `推荐` active state, and video-library search navigation.
- [x] 4.2 Add or keep regression coverage that the old home title/explanation card is absent from the home feed.
- [x] 4.3 Add a source-level guard or equivalent test check that home header quick-return does not use active `touchmove`/wheel `preventDefault`, CSS Scroll-Driven Animation dependency, or synthetic scroll replay.

## 5. Verification

- [x] 5.1 Run `npm run build` in `apps/web-student`.
- [x] 5.2 Hot-update the `chemistry-admin-web-student-1` container with the new `dist` output and reload nginx.
- [x] 5.3 Manually check the home root at phone preview widths for downward compression, upward restoration, smooth feed scrolling, attached topic rail spacing, and no control overlap.
