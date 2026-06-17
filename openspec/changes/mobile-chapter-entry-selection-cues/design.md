## Context

The student H5 periodic-table entry currently uses one page for two different concepts:

- area selection, which filters the visible chapter list and should have selected state
- chapter entry, which navigates into a family/chapter and should not look selected before navigation

The current recommended chapter card uses a green border and light green background. This visually resembles an active/selected card on a phone screen, while the selected periodic-table area uses dark per-cell outlines that read as heavy black borders in the p-block.

## Goals / Non-Goals

**Goals:**

- Keep area selection visually clear as the page's only local selection state.
- Preserve recommendation guidance for both the recommended area and recommended chapter.
- Make recommended chapter cards look like normal tappable navigation rows with a recommendation tag, not selected cards.
- Replace periodic-table selected-area outlines with a softer mobile-friendly highlight.

**Non-Goals:**

- No backend API, seed-data, recommendation algorithm, routing, or assessment-flow changes.
- No redesign of the selected chapter learning page after navigation.
- No new component library or design token migration.

## Decisions

1. Treat recommendation as metadata, not state.

   The recommended profile already resolves to a profile id and area id. The entry page will continue to initialize the selected area to the recommended area on first load, but the UI will not render the recommended chapter as selected. Recommendation appears only as a compact tag.

   Alternative considered: keep the recommended chapter's green-tinted card. Rejected because it looks like the current active choice before the user has entered a chapter.

2. Add recommended-area cue to the periodic-table heading.

   The selected area button remains the primary state indicator. The periodic-table heading shows a compact `推荐学习 · <area>` tag so a student can see the system suggestion without crowding or distorting the area buttons.

   Alternative considered: attach a small tag to the recommended area button. Rejected because the button is narrow on phone widths and the tag either floats awkwardly or crowds the area label.

3. Use fill, opacity, and soft shadow for periodic-table area emphasis.

   Selected area cells will be saturated and lightly lifted; non-selected cells will be muted. The dark per-cell inset outline will be removed.

   Alternative considered: keep outlines but lighten the color. Rejected because a grid of outlines still creates visual noise on dense phone viewports.

## Risks / Trade-offs

- Recommendation may be less prominent after removing the full-card tint. Mitigation: keep the chapter tag and add a heading-level area recommendation tag.
- Muting non-selected periodic-table cells could reduce color category recognition. Mitigation: preserve each area color and only reduce opacity/saturation modestly.
- The recommended-area tag is not embedded inside the area button. Mitigation: include the recommended area name in the tag while keeping area buttons dedicated to selection state.
