## ADDED Requirements

### Requirement: Student AI uses Atom visual identity
The student H5 app SHALL use the Atom pictogram as the student-facing AI assistant visual identity within `apps/web-student`.

#### Scenario: Student sees AI root navigation
- **WHEN** the authenticated student bottom navigation renders the `AI` root destination
- **THEN** the `AI` destination MUST use the Atom pictogram rather than a generic chat or bot pictogram
- **AND** the destination label MUST be `Atom`

#### Scenario: Student sees contextual AI actions
- **WHEN** a student-facing page offers an AI action such as `问问Atom`, `Atom 讲解错题`, or an AI prompt result
- **THEN** the action MUST use the Atom pictogram as the visible AI mark
- **AND** the action MUST preserve its existing enabled, disabled, loading, route, and request behavior

#### Scenario: Student sees assistant product naming
- **WHEN** the student H5 assistant renders student-facing assistant titles, region labels, disabled states, history labels, or composer accessibility labels within `apps/web-student`
- **THEN** the formal student assistant name MUST be `Atom 学习助手` instead of `AI 学习助手`
- **AND** related student-facing assistant labels SHOULD use Atom naming, such as `Atom 对话`, `Atom 历史记录`, and `向 Atom 提问`
- **AND** teacher/admin surfaces outside `apps/web-student` MUST keep their existing AI naming

#### Scenario: Student sees ask-entry copy
- **WHEN** a student-facing contextual ask entry formerly used visible copy `问 AI` or `问AI`
- **THEN** the visible copy MUST be `问问Atom`
- **AND** the action's route, context payload, enabled state, and request behavior MUST remain unchanged

#### Scenario: Student sees assistant identity states
- **WHEN** the student H5 assistant renders AI identity states such as assistant message metadata, disabled AI empty states, or no-history AI empty states
- **THEN** those AI identity states MUST use the Atom pictogram where an AI identity icon is shown
- **AND** status icons such as loading, success, failure, history, delete, reset, or send MAY continue to use their existing status-specific pictograms

#### Scenario: Student sees AI root welcome
- **WHEN** the student H5 AI root renders its empty first-screen welcome
- **THEN** the centered welcome text MUST show the Atom pictogram above the welcome phrase as the AI identity mark
- **AND** the Atom pictogram MUST remain an unframed identity mark rather than a card, button, or status icon

#### Scenario: Teacher and admin AI surfaces render
- **WHEN** a teacher or admin console AI surface renders outside `apps/web-student`
- **THEN** this student H5 Atom identity and naming rule MUST NOT require changing that surface's existing AI iconography or copy
