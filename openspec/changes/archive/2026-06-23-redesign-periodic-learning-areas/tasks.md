## 1. Domain Taxonomy

- [x] 1.1 Update backend area definitions so the shared order is `hydrogen`, `p`, `s`, `ds`, `d`, `f`, with `general` remaining teacher-only.
- [x] 1.2 Update CH22 grouping so it is reachable from hydrogen context and p context without reintroducing the old combined `氢和稀有气体` area.
- [x] 1.3 Add or enable a CH21 f-block student learning profile with sufficient seed fields to pass existing profile validation.
- [x] 1.4 Add backend tests for area order, CH22 hydrogen/p grouping, teacher-only general resources, and student f availability.

## 2. Student H5 Learning Root

- [x] 2.1 Update student periodic helpers so H maps to hydrogen, noble gases map to p, and f-block cells map to f.
- [x] 2.2 Remove periodic-table recommendation props, yellow area badges, and gold recommendation cell outlines from the student learning root.
- [x] 2.3 Add a lower smart recommendation card to the student learning root with CTA behavior into the recommended chapter or selected area.
- [x] 2.4 Update selected-area chapter filtering so hydrogen, p noble-gas context, and f area show the expected chapter entries.
- [x] 2.5 Update student styles for the new six-area grid, ptable-inspired colors, and phone-safe f-block rendering.

## 3. Teacher Resource Overview

- [x] 3.1 Update teacher resource color metadata to match the accepted shared area tokens while preserving desktop-specific layout.
- [x] 3.2 Update teacher overview element-area mapping so H maps to hydrogen and noble gases map to p.
- [x] 3.3 Fix teacher overview f-block rows to render La-Lu and Ac-Lr with the detached-row spacer structure.
- [x] 3.4 Keep `通识资源` as a teacher-only resource bucket outside periodic element-cell ownership.

## 4. Verification

- [x] 4.1 Add or update frontend tests that lock student area order, removed recommendation chrome, CH22 hydrogen/p behavior, and student f chapter entry.
- [x] 4.2 Add or update teacher tests that lock resource overview colors, f-block layout, and no student UI imports.
- [x] 4.3 Update mobile viewport QA expectations for the redesigned learning root and selected-area navigation.
- [x] 4.4 Run OpenSpec validation plus relevant backend, student, and teacher checks.
