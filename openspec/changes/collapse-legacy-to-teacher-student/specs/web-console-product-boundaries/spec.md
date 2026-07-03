## ADDED Requirements

### Requirement: Legacy branch exposes teacher and student web products
The legacy branch SHALL expose exactly two canonical browser-facing frontend products: `web-teacher` for global teaching management and `web-student` for student learning.

#### Scenario: Frontend packages are inspected
- **WHEN** a maintainer inspects the `apps/` directory on the legacy branch
- **THEN** the teacher product MUST be available at `apps/web-teacher`
- **AND** the student product MUST be available at `apps/web-student`
- **AND** active frontend packages named `apps/web-backoffice`, `apps/web-admin`, `apps/web-teacher-old`, or `apps/web-student-old` MUST NOT exist.

#### Scenario: Product ownership is inspected
- **WHEN** frontend package names, Compose service names, page titles, README, and operations docs are inspected
- **THEN** the teaching-management product MUST be identified as `web-teacher`
- **AND** the learning product MUST be identified as `web-student`
- **AND** no standalone platform operations product MUST be documented for the legacy branch.

### Requirement: Teacher product is not a multi-teacher tenant console
The teacher product SHALL represent a global teaching-management backend for this legacy version.

#### Scenario: Teacher product copy is inspected
- **WHEN** the teacher product shell, login page, and docs are inspected
- **THEN** they MAY use teaching or teacher wording
- **AND** they MUST NOT claim per-teacher class isolation, teacher tenant isolation, or scoped teacher ownership.

## REMOVED Requirements

### Requirement: Three web consoles have explicit product boundaries
**Reason**: The legacy branch no longer exposes separate `web-admin`, current `web-teacher`, and current `web-student` products.
**Migration**: Use the two canonical legacy products `web-teacher` and `web-student`.

### Requirement: Console access boundaries are separated
**Reason**: Token-based `web-admin` operations access and mixed `admin`/`teacher` console access are replaced by `teacher` and `student`.
**Migration**: Teacher access is authenticated with `role='teacher'`; student access is authenticated with `role='student'`.

### Requirement: Teacher-console role compatibility does not affect feature visibility
**Reason**: `admin` is no longer a canonical compatibility role.
**Migration**: Convert existing `admin` and `platform_admin` users to `teacher`; require `teacher` for all teacher product workflows.

### Requirement: Legacy products have explicit product boundaries
**Reason**: The old products are no longer optional `*-old` products; they are the canonical legacy branch products.
**Migration**: Replace `web-student-old` with `web-student` and `web-teacher-old`/`web-backoffice` with `web-teacher`.

### Requirement: Legacy boundary hides platform and diagnostic ownership
**Reason**: The legacy teacher product remains focused, but its canonical app name is now `web-teacher`, not `web-teacher-old`.
**Migration**: Keep the focused legacy teacher navigation requirements under the canonical `web-teacher` product.
