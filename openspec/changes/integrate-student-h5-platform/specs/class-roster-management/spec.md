## ADDED Requirements

### Requirement: Roster activation for student H5
Roster entries SHALL be the authoritative source for student H5 account activation.

#### Scenario: Pending roster student logs in
- **WHEN** a pending roster student completes first login with valid class login credentials
- **THEN** the system SHALL activate or link the corresponding student account
- **AND** the admin roster status SHALL remain compatible with existing activation displays.

#### Scenario: Duplicate active student identifiers exist
- **WHEN** migration or login detects duplicate active normalized student identifiers that would make account ownership ambiguous
- **THEN** the system SHALL fail safely instead of linking a student to the wrong roster entry.
