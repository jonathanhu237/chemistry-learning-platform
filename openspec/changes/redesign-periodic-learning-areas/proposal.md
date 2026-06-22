## Why

The student learning root and teacher resource overview currently encode periodic-table learning areas in several places, causing recommendation cues, chapter mapping, element colors, and f-block layout to drift between products. This change realigns the chemistry learning taxonomy while preserving the intended product boundary: student H5 and teacher console render different UI shapes, but share the same area semantics and color meaning.

## What Changes

- Replace the old `氢和稀有气体` learning area with a dedicated `氢元素` area and return noble-gas elements to the `p区元素` display area.
- Keep `s区元素` as a first-class learning area for alkali and alkaline-earth chapters.
- Open the `f区元素` area in the student H5 learning entry, including the `第 21 章 镧系和锕系元素` chapter when available.
- Move recommendation guidance on the student `/learn` root out of the periodic-table legend/cells and into a separate smart card in the lower half of the page.
- Remove recommendation badges and yellow recommendation element outlines from the periodic table after the learning-root/list split.
- Align teacher resource overview colors and area/chapter semantics with the student learning taxonomy while keeping teacher desktop layout independent from the phone UI.
- Fix the teacher resource overview f-block placement so lanthanide and actinide rows follow the student-aligned structure with the spacer row and La/Ac-starting sequence.
- Keep `通识资源` as a teacher-only extra resource area outside the student H5 periodic-table entry and outside element-cell ownership.

## Capabilities

### New Capabilities
- `periodic-learning-area-taxonomy`: Defines the authoritative area IDs, order, color-token semantics, chapter ownership, and element ownership used by student and teacher products.
- `teacher-learning-resource-overview`: Defines the teacher resource overview periodic selector, including desktop-specific layout, teacher-only general resources, and f-block placement.

### Modified Capabilities
- `student-h5-learning-experience`: Changes the student learning root composition, recommendation placement, area list, hydrogen/noble-gas mapping, and student f-area availability.
- `student-h5-learning-flow`: Changes periodic-table area handoff behavior for hydrogen, p-block noble gases, and f-block chapter entry.
- `student-h5-mobile-design-system`: Changes visual rules for the phone periodic table by removing inline recommendation chrome and aligning colors with the new area taxonomy.
- `student-h5-route-stack-navigation`: Clarifies that the learning root contains a periodic-table entry plus separate recommendation guidance, while area/chapter pages remain detail routes.

## Impact

- Student frontend: `LearningEntryPanel`, `PeriodicTable`, selected-area page/list, learning styles, periodic-table helpers, mobile viewport QA, and route/role tests.
- Teacher frontend: resource overview periodic selector, resource color metadata, f-block grid rendering, and teacher resource overview tests.
- Backend/domain: student learning area order, chapter-to-area metadata, resource overview area grouping, student learning seed/profile availability for CH21, and tests that assert area/chapter consistency.
- OpenSpec: new taxonomy and teacher overview specs plus deltas for student learning, flow, mobile design, and routing contracts.
