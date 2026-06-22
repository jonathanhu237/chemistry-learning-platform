## 1. Route And Navigation Contract

- [x] 1.1 Add typed area route search/params handling and a navigation helper for `/learn/area/$areaId`.
- [x] 1.2 Register the selected-area route in the student TanStack route tree as an authenticated detail page.
- [x] 1.3 Ensure unsupported area ids render a controlled empty or unavailable state instead of crashing.

## 2. Learning Root And Area Pages

- [x] 2.1 Refactor the learning root so `/learn` renders only the periodic-table entry and recommendation cues, not the selected-area chapter list.
- [x] 2.2 Create a selected-area route page that fetches the existing learning-page payload and filters chapter entries by the route area id.
- [x] 2.3 Extract or create reusable chapter-entry list rendering for the area page, preserving recommendation labels and empty states.
- [x] 2.4 Wire area controls and periodic-table element cells to navigate to the selected-area route.
- [x] 2.5 Wire chapter entry cards on the area route to the existing chapter route.

## 3. Tests And QA Updates

- [x] 3.1 Update student E2E tests to assert `/learn` shows the periodic table without inline selected-area chapter cards.
- [x] 3.2 Add or update tests for `/learn/area/$areaId` showing filtered chapter cards and navigating onward to `/chapter/$profileId`.
- [x] 3.3 Update mobile viewport QA route coverage and scripted interactions for `/learn -> /learn/area/:areaId -> /chapter/:profileId`.

## 4. Validation

- [x] 4.1 Run focused student frontend tests covering the learning route stack.
- [x] 4.2 Run student frontend typecheck or build validation.
- [x] 4.3 Run `openspec validate refactor-student-learning-area-route-stack --strict`.
- [x] 4.4 Run `git diff --check`.
