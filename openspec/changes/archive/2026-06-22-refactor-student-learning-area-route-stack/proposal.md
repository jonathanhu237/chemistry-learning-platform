## Why

The student learning tab currently mixes the periodic-table entry and the selected-area chapter list on the same root page. This conflicts with the intended H5 route-stack model where the learning tab is an entry surface and each drilldown, including area selection, opens as a second-level page.

## What Changes

- Keep `/learn` as the first-level learning tab page and render only the periodic-table chapter entry there.
- Move selected-area chapter lists into a new second-level area route opened from area controls or periodic-table cells.
- Keep area pages, chapter pages, catalog directory pages, and point/video pages in the same detail-route stack with bottom navigation hidden.
- Preserve chapter-entry navigation from the area page into the existing chapter route, then catalog and point routes.
- Update existing tests and mobile QA expectations so selected-area chapter cards are no longer asserted on `/learn`.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `student-h5-learning-flow`: Area selection becomes a second-level route before chapter selection.
- `student-h5-learning-experience`: The periodic-table root no longer filters and displays the chapter list inline; that list belongs to the area page.
- `student-h5-route-stack-navigation`: Adds the learning area page to the authenticated second-level route stack.

## Impact

- Affected student frontend routes under `apps/web-student/src/app/router`.
- Affected learning entry and periodic-table components under `apps/web-student/src/features/learning` and `apps/web-student/src/features/periodic-table`.
- Affected route pages under `apps/web-student/src/routes/learn`.
- Affected student E2E/mobile viewport tests that currently expect area filtering on `/learn`.
- No backend API or database changes are expected; the existing learning-page payload can power both the root and area detail page.
