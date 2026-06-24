## MODIFIED Requirements

### Requirement: Preview framing and origins are controlled
The platform SHALL allow the teacher app to frame only the expected student preview origin while preventing broad clickjacking exposure.

#### Scenario: Teacher and student apps use different local ports
- **WHEN** the teacher preview page runs on the teacher frontend origin and frames the student frontend origin
- **THEN** configuration MUST allow the expected local, LAN, and deployed student preview origins
- **AND** the default local Compose preview origin MUST resolve to `http://222.200.189.249:5173`
- **AND** it MUST NOT allow arbitrary external origins to be framed.

#### Scenario: Iframe tries to load an unexpected URL
- **WHEN** the teacher preview shell receives or computes a preview URL outside the allowed student origin list
- **THEN** it MUST reject the URL and show a controlled error
- **AND** it MUST NOT render the unexpected origin inside the teacher console.

#### Scenario: Student app is opened without preview bootstrap
- **WHEN** a user opens the normal student frontend without a valid student session or valid preview ticket
- **THEN** normal student authentication rules MUST still apply
- **AND** teacher credentials MUST NOT be treated as student credentials.
