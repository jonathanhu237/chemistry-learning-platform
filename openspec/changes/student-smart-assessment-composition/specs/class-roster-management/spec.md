## ADDED Requirements

### Requirement: Class smart assessment strategy override
The selected-class management workflow SHALL allow class-level smart assessment strategy overrides that inherit from system defaults when no override is configured.

#### Scenario: Teacher reviews inherited smart assessment strategy
- **GIVEN** a selected class has no smart assessment strategy override
- **WHEN** an authorized teacher or admin opens class settings
- **THEN** the UI MUST show that the class inherits the global smart assessment defaults
- **AND** it MUST display the effective total question count, untested point ratio, weak tendency, and max questions per experiment.

#### Scenario: Teacher saves class override
- **GIVEN** a teacher is authorized to manage the selected class
- **WHEN** they save a class smart assessment strategy override
- **THEN** the backend MUST persist the override for that class only
- **AND** students in that class MUST use the class override instead of the global default.

#### Scenario: Admin manages any class override
- **WHEN** an administrator updates smart assessment strategy for any class
- **THEN** the backend MUST permit the change
- **AND** it MUST preserve a clear distinction between inherited values and overridden values.

#### Scenario: Teacher attempts unauthorized override
- **WHEN** a teacher attempts to update a class they are not authorized to manage
- **THEN** the backend MUST reject the request
- **AND** the UI MUST avoid presenting editable override controls for that class.

#### Scenario: Override is cleared
- **WHEN** an authorized teacher or admin clears a class smart assessment override
- **THEN** the class MUST return to inheriting global smart assessment defaults.

### Requirement: Class custom assessment settings override
The selected-class management workflow SHALL allow class-level custom assessment settings overrides that inherit from system defaults when no override is configured.

#### Scenario: Teacher reviews inherited custom assessment settings
- **GIVEN** a selected class has no custom assessment settings override
- **WHEN** an authorized teacher or admin opens class settings
- **THEN** the UI MUST show that the class inherits the global custom assessment defaults
- **AND** it MUST display the effective enabled state, default question count, maximum question count, and max questions per experiment.

#### Scenario: Teacher saves custom assessment override
- **GIVEN** a teacher is authorized to manage the selected class
- **WHEN** they save a class custom assessment settings override
- **THEN** the backend MUST persist the override for that class only
- **AND** students in that class MUST use the class override instead of the global default.

#### Scenario: Admin manages any custom assessment override
- **WHEN** an administrator updates custom assessment settings for any class
- **THEN** the backend MUST permit the change
- **AND** it MUST preserve a clear distinction between inherited values and overridden values.

#### Scenario: Custom assessment override is cleared
- **WHEN** an authorized teacher or admin clears a class custom assessment override
- **THEN** the class MUST return to inheriting global custom assessment defaults.
