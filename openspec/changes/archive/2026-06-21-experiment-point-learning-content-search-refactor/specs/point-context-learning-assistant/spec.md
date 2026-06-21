## ADDED Requirements

### Requirement: Assistant point evidence remains separate from student point content
The learning assistant SHALL keep manual-reviewed point evidence packages as an AI/RAG consumer path that is separate from teacher-authored student point learning content.

#### Scenario: Student point page content exists
- **WHEN** a point-context assistant request is made for a point that also has published student point learning content
- **THEN** the assistant MAY receive compact page context from the frontend
- **AND** it MUST still resolve the fixed point evidence package through the assistant evidence path when available.

#### Scenario: Manual-reviewed evidence exists without student content
- **WHEN** `experiment_video_point_evidence` exists for a point but no published point learning content exists
- **THEN** the assistant MAY use the evidence package for answering point-context questions
- **AND** the student point detail page MUST NOT treat that evidence as published display content.

#### Scenario: Student content exists without manual-reviewed evidence
- **WHEN** published teacher-authored point learning content exists but no manual-reviewed evidence binding exists
- **THEN** the student point detail page MAY display the published content
- **AND** the assistant diagnostics MUST still report that fixed point evidence is missing rather than pretending content fields are evidence chunks.

#### Scenario: Admin diagnostics are shown
- **WHEN** an admin inspects a point-context assistant turn
- **THEN** diagnostics MUST distinguish teacher-authored point learning content context from fixed manual-reviewed evidence and supplemental RAG evidence
- **AND** it MUST not merge their source labels into a single ambiguous source.
