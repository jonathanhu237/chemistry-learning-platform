## 1. Home Feed Markup

- [x] 1.1 Inventory the current `HomeVideoFeedCard` footer props, handlers, labels, and test selectors for `查看实验`, `搜索相关`, and `问问Atom`.
- [x] 1.2 Replace the three-column footer markup with a single action row containing a left `查看实验` primary CTA and a right icon action group.
- [x] 1.3 Remove the visible per-card `搜索相关` footer action and delete the now-unused `onSearch` feed-card prop path if no longer needed.
- [x] 1.4 Add right-side icon buttons for like, favorite/bookmark, share, Atom, and more using the existing icon system.
- [x] 1.5 Keep the Atom action wired to the existing `askItem` flow with the feed item assistant context.
- [x] 1.6 Preserve disabled Atom behavior when assistant access is unavailable without changing the row geometry.

## 2. Visual Design

- [x] 2.1 Replace the `.home-video-actions` three-column grid and divider treatment with a compact flex row.
- [x] 2.2 Style `查看实验` as the left primary learning CTA using the existing green theme and current visual language.
- [x] 2.3 Style ordinary icon actions as secondary icon-only controls without counters or heavy labels.
- [x] 2.4 Style Atom with its own Atom icon and green highlighted treatment distinct from ordinary icon controls.
- [x] 2.5 Ensure the action row stays visually balanced with the existing video card body spacing, badges, and bottom navigation safe area.

## 3. Accessibility and Interaction

- [x] 3.1 Add or preserve accessible names for every action button: open experiment, like, favorite/bookmark, share, Atom, and more.
- [x] 3.2 Ensure tapping media, title, or `查看实验` still navigates to point video detail with home source context.
- [x] 3.3 Ensure tapping Atom still opens Atom chat with item title, catalog path, point identity, and summary context.
- [x] 3.4 Keep like, favorite/bookmark, share, and more lightweight and non-blocking; do not introduce persistence, counters, ranking, or creator/channel behavior in this change.

## 4. Tests

- [x] 4.1 Update student H5 tests that currently expect the `搜索相关` footer action on home feed cards.
- [x] 4.2 Add assertions that the home feed card renders `查看实验`, the right icon controls, and highlighted Atom action.
- [x] 4.3 Add or update tests proving `查看实验` and Atom retain their existing navigation/context behavior.
- [x] 4.4 Add style-contract coverage where existing tests inspect student mobile CSS for home feed action layout and non-overlap constraints.

## 5. Verification

- [x] 5.1 Run targeted student H5 tests covering home feed, route boundaries, and shell behavior.
- [x] 5.2 Run `npm run build` for `apps/web-student`.
- [x] 5.3 Hot-update the student Docker container with the new build output for phone-frame review.
- [x] 5.4 Manually verify common phone widths around 360px, 390px, and 430px: no overflow, no action overlap, Atom remains green-highlighted, and `搜索相关` is absent from card footers.
