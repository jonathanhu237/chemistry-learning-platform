## 1. Dependency And Contract Setup

- [x] 1.1 Add `@floating-ui/react` to the student web package and lockfile.
- [x] 1.2 Update the periodic-table selection callback contract so triggers pass both `areaId` and the clicked HTMLElement anchor.

## 2. Anchored Popover Implementation

- [x] 2.1 Add a reusable learning area popover component that uses Floating UI fixed positioning, offset, flip, shift, size, dismissal, and role behavior.
- [x] 2.2 Reuse the existing area-to-profile filtering and chapter row rendering inside the popover without changing backend data shape.
- [x] 2.3 Update `LearningEntryPanel` to manage the active area, anchor element, open state, and chapter row selection.
- [x] 2.4 Update `LearnRootPage` so periodic-table selection opens the popover and chapter row selection navigates directly to the chapter route.
- [x] 2.5 Keep the selected-area detail page and `navigateToLearningArea` available for direct route fallback.

## 3. Mobile Styling And Layout Safety

- [x] 3.1 Add popover styling for compact rows, viewport-contained width, fixed overlay layering, safe-area padding, and non-stretching behavior.
- [x] 3.2 Ensure opening and closing the popover does not resize the periodic-table root layout or create horizontal overflow.
- [x] 3.3 Preserve accessible labels, focus-visible states, and touch-friendly row targets.

## 4. Tests And QA Updates

- [x] 4.1 Update student learning tests so tapping `p` area shows an in-place popover instead of navigating to `/learn/area/p`.
- [x] 4.2 Add or update tests that selecting a popover row navigates to the matching chapter detail route.
- [x] 4.3 Update mobile viewport QA expectations for the new anchored popover flow.

## 5. Verification

- [x] 5.1 Run OpenSpec validation for `add-periodic-area-popover`.
- [x] 5.2 Run student-web typecheck and relevant Vitest/e2e checks.
- [x] 5.3 Run or document mobile viewport QA for 360x780, 390x844, and 430x932.
