## ADDED Requirements

### Requirement: Student report AI text renders chemistry Markdown
Student-facing AI or fallback text in posttest reports SHALL use the math-capable Markdown rendering path when displayed in the H5 app.

#### Scenario: Posttest summary contains chemistry notation
- **WHEN** a student views a posttest summary containing Markdown, math, or chemistry notation
- **THEN** the H5 app MUST render the content through the chemistry/math-capable Markdown renderer
- **AND** the visible report MUST avoid exposing raw supported LaTeX commands as ordinary text.

#### Scenario: Mistake explanation contains chemistry notation
- **WHEN** a student views an AI-generated or fallback mistake explanation containing chemistry notation
- **THEN** the H5 app MUST render the content through the same renderer used for assistant chemistry answers
- **AND** rendering failures MUST fall back to readable sanitized text rather than breaking the report.
