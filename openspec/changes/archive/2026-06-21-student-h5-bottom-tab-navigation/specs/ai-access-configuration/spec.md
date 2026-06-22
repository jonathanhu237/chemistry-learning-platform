## MODIFIED Requirements

### Requirement: H5 feature switch propagation
The system SHALL propagate admin-managed learning feature switches to the student H5 app through a pull-based configuration endpoint and enforce them again at protected action endpoints.

#### Scenario: Admin disables student AI entry
- **WHEN** an admin disables the AI learning assistant entry in system settings
- **THEN** subsequent student app-config responses MUST mark the H5 assistant entry as disabled
- **AND** the authenticated student app shell MUST hide or disable the `问答` bottom-nav entry and move any active assistant route back to a safe tab
- **AND** student assistant request endpoints MUST reject stale requests without invoking the agent.

#### Scenario: Admin disables feedback entry
- **WHEN** an admin disables the feedback entry in system settings
- **THEN** subsequent student app-config responses MUST mark the H5 feedback entry as disabled
- **AND** the `我的` tab MUST hide or disable the feedback section
- **AND** student feedback submission endpoints MUST reject stale requests.

#### Scenario: Admin disables student AI capability
- **WHEN** an admin disables student AI capability in AI feature controls
- **THEN** subsequent student app-config responses MUST mark student AI capability as disabled
- **AND** the H5 assistant tab MUST not be available even if the general learning assistant entry remains enabled.
