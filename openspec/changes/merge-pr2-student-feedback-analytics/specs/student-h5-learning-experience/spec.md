## ADDED Requirements

### Requirement: H5 feedback supports screenshot attachments
The student H5 feedback capability SHALL support one optional image screenshot attachment from the authenticated mobile feedback entry while preserving feature-flag and identity controls.

#### Scenario: Student submits feedback with screenshot
- **WHEN** an authenticated student submits H5 feedback with a png, jpg, jpeg, or webp screenshot no larger than 5 MB
- **THEN** the backend MUST create the feedback record using the authenticated student's identity
- **AND** it MUST store attachment metadata linked to that feedback record
- **AND** the response MUST indicate that one attachment was accepted
- **AND** the feedback MUST remain visible in the existing admin feedback workflow.

#### Scenario: Student submits feedback without screenshot
- **WHEN** an authenticated student submits H5 feedback without an attachment
- **THEN** the backend MUST create the feedback record through the same authoritative student feedback endpoint
- **AND** the response MUST indicate zero attachments.

#### Scenario: Student submits unsupported attachment
- **WHEN** a student submits feedback with an empty file, a file over 5 MB, or a file that is not png, jpg, jpeg, or webp
- **THEN** the backend MUST reject the request
- **AND** it MUST NOT create an orphaned attachment record.

#### Scenario: Feedback metadata includes spoofed identity
- **WHEN** a feedback request includes client-supplied student id, class id, or student snapshot data in metadata
- **THEN** the backend MUST derive authoritative student and class identity from the authenticated token
- **AND** it MUST remove or quarantine the client-supplied identity fields before storing metadata.

### Requirement: Single student feedback route ownership
The platform SHALL expose only one authoritative student feedback submission behavior for `POST /api/student/feedback`.

#### Scenario: Student feedback endpoint is registered
- **WHEN** backend routes are loaded
- **THEN** there MUST NOT be competing route handlers with different authentication, feature-flag, or payload semantics for `POST /api/student/feedback`
- **AND** the route MUST enforce the student feedback feature switch before creating feedback.

#### Scenario: Feedback switch is disabled
- **WHEN** the student feedback feature switch is disabled and a stale client submits feedback
- **THEN** the authoritative endpoint MUST reject the submission
- **AND** it MUST NOT create a feedback record or attachment.
