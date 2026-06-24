## Why

The home video feed currently renders each card with a three-column toolbar: `查看实验`, `搜索相关`, and `问问Atom`. That reads like a utility menu rather than a video stream action row, and the per-card `搜索相关` action competes with the home header/search-page model that already owns video search.

This change refines the home feed card actions into a familiar compact video action bar: the learning detail CTA remains primary on the left, while lightweight icon actions live on the right, with Atom highlighted as the product-specific learning assistant action.

## What Changes

- Replace the current three-equal-column home video card toolbar with a single-row action bar.
- Keep `查看实验` as the left-aligned primary learning CTA and continue routing it to the existing point video/detail destination.
- Remove the card-level `搜索相关` action from the home feed card footer.
- Add right-aligned icon actions for lightweight video-flow affordances:
  - like
  - favorite/bookmark
  - share
  - Atom
  - more
- Style the Atom action with its own Atom icon and green primary treatment so it reads as the branded learning-assistant affordance rather than a generic social icon.
- Keep non-Atom icon actions lightweight and non-disruptive; they may be visual/local affordances until later backend behavior is specified.
- Preserve the existing home feed preview, title, catalog context, badges, and point-detail routing.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `student-h5-video-discovery`: Refine the home feed card action contract so card actions behave like a video stream action row, remove per-card search, and keep Atom as a highlighted learning action.
- `student-h5-mobile-design-system`: Add mobile layout requirements for the compact icon action row so it remains aligned, touch-safe, and non-overlapping on common phone widths.

## Impact

- Frontend:
  - `apps/web-student/src/routes/home/HomeRootPage.tsx`
  - `apps/web-student/src/styles/app-shell.css`
  - student H5 tests that assert home video card actions
- Routing:
  - Existing point-detail and Atom chat navigation are preserved.
  - The removed card-level search action no longer navigates from individual cards to video-library query results.
- Backend/API:
  - No backend API contract is required for the visual action row.
  - Like, favorite, share, and more do not require persistence unless a future change defines those behaviors.
