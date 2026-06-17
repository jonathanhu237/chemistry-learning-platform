## Why

The periodic-table chapter entry is currently mixing recommendation and selection visuals: the recommended chapter card looks selected even though tapping it immediately navigates into the chapter. On a phone-first H5 screen, this makes the entry page feel stateful in the wrong place and makes the periodic table's selected-area outline look visually heavy.

## What Changes

- Clarify that the area controls are the only selectable/filtering state on the periodic-table entry page.
- Keep chapter cards as navigation entries with no selected/active styling before navigation.
- Preserve recommendation guidance with labels on the recommended chapter and the recommended area.
- Replace the selected periodic-table area's dark per-cell outline with a softer area highlight and muted non-selected areas.
- Keep the implementation scoped to the student H5 periodic-table entry page.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `student-h5-learning-experience`: Clarify periodic-table entry behavior so recommendations are distinct from selected state and chapter cards remain navigation entries.
- `student-h5-mobile-design-system`: Clarify mobile visual-state treatment for selected areas, recommended areas, and chapter entry cards.

## Impact

- Affected frontend code:
  - `apps/student-web/src/App.tsx`
  - `apps/student-web/src/styles.css`
- No backend API or database changes.
- Verification should cover student-web typecheck, focused E2E, and mobile viewport QA for the chapter entry screen.
