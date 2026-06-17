## 1. Entry Semantics

- [x] 1.1 Pass the recommended area into the periodic-table entry controls.
- [x] 1.2 Render a compact recommended-area cue without changing selected-area behavior.
- [x] 1.3 Keep recommended chapter cards visually neutral except for the recommendation label.

## 2. Periodic Table Visual State

- [x] 2.1 Replace dark selected-area cell outlines with a softer selected-area treatment.
- [x] 2.2 De-emphasize non-selected element cells while preserving their area colors.

## 3. Verification

- [x] 3.1 Run student-web typecheck and focused E2E.
- [x] 3.2 Run mobile viewport QA for the student H5 entry page.
- [x] 3.3 Validate the OpenSpec change strictly.

## 4. Tag Refinement

- [x] 4.1 Rename recommendation labels to `推荐学习`.
- [x] 4.2 Restore recommended-area guidance to the area button without resizing its label.
- [x] 4.3 Keep the chapter recommendation label on the title row so it does not push the card content down.

## 5. Learnable Element Symbols

- [x] 5.1 Pass current selected-area profile element symbols into the periodic table.
- [x] 5.2 Render symbols only in selected-area cells that map to available learning profiles.
- [x] 5.3 Keep symbol styling legible inside mobile-sized element cells without changing the grid footprint.

## 6. Recommended Family Badge Polish

- [x] 6.1 Pass the recommended profile family number into the area recommendation cue.
- [x] 6.2 Isolate the gold recommendation cue from the selected-area border so the green line does not read through it.
- [x] 6.3 Render the recommended chapter family number as a gold numeric badge.

## 7. Resource Overview Periodic Layout

- [x] 7.1 Add a `氢和稀有气体` learning area and map H plus group 18 elements to it.
- [x] 7.2 Render six student learning areas as a two-row, three-column legend without `通识资源`.
- [x] 7.3 Add left-side period labels to the student periodic table.
- [x] 7.4 Reduce element-symbol cue size for tighter mobile cells.

## 8. Noble Gas Column Classification

- [x] 8.1 Classify `氢和稀有气体` by element symbol rather than by display-layout group number.
- [x] 8.2 Keep Lu/Lr and other f-block cells in the f area even when their layout metadata reaches the right side of the table.
- [x] 8.3 Shift detached f-block display rows away from the group 18 display column so the rightmost column reads as noble gases only.

## 9. Recommendation Profile Cue Copy

- [x] 9.1 Render recommended area cues as `17族` for valid IUPAC family recommendations instead of bare `17`.
- [x] 9.2 Use compact profile/category cue labels such as `过渡金属` for non-family recommendations.
- [x] 9.3 Preserve or restore full recommended chapter titles such as `17族（卤素）`.
- [x] 9.4 Keep recommended chapter cards free of separate family-number badges.
- [x] 9.5 Show recommended profile elements with subtle gold borders instead of highlighting IUPAC group numbers.

## 10. Mobile Title Length Protection

- [x] 10.1 Render area-level chapter cards with learning-object labels such as `碱金属和碱土金属` instead of repeating selected-area prefixes such as `s区`.
- [x] 10.2 Constrain long recommendation cue labels such as `氢和稀有气体` and `碱金属和碱土金属` so they do not overflow mobile area controls.

## 11. Recommended Element Cue Polish

- [x] 11.1 Replace the recommended-element gold dot with a subtle gold border that does not add extra content inside the element cell.
