## ADDED Requirements

### Requirement: Periodic learning area taxonomy
The platform SHALL define a stable periodic learning taxonomy for chemistry semantics while allowing each frontend product to render its own UI shape.

#### Scenario: Shared learning areas are ordered
- **WHEN** student or teacher code needs the shared learning-area order
- **THEN** the shared semantic order MUST be `hydrogen`, `p`, `s`, `ds`, `d`, and `f`
- **AND** the displayed labels MUST be `氢元素`, `p区元素`, `s区元素`, `ds区元素`, `d区元素`, and `f区元素`
- **AND** the old student learning area `氢和稀有气体` MUST NOT be used as an area id or area selector label.

#### Scenario: Teacher-only general resources are represented
- **WHEN** teacher resource overview includes cross-chapter or general learning resources
- **THEN** those resources MAY use a teacher-only `general` area
- **AND** `general` MUST NOT be exposed as a student H5 periodic-table learning area
- **AND** `general` MUST NOT claim ownership of any periodic-table element cell.

#### Scenario: Area color tokens are used consistently
- **WHEN** the student H5 learning entry and teacher resource overview render shared periodic learning areas
- **THEN** each shared area id MUST use the same color-token meaning across products
- **AND** the implementation MUST keep the six shared token values synchronized through a shared token source or a contract test
- **AND** the colors SHOULD follow ptable-inspired chemistry semantics without requiring ptable's full fine-grained element-series taxonomy.

### Requirement: Element ownership by learning area
The platform SHALL map elements to learning areas according to the accepted student learning taxonomy rather than the old combined hydrogen/noble-gas area.

#### Scenario: Hydrogen is standalone
- **WHEN** an element cell represents hydrogen
- **THEN** the element MUST map to the `hydrogen` learning area
- **AND** selecting hydrogen from the student learning root MUST open the hydrogen selected-area route.

#### Scenario: Noble gases belong to p area
- **WHEN** an element cell represents He, Ne, Ar, Kr, Xe, Rn, or Og
- **THEN** the element MUST map to the `p` learning area
- **AND** these noble-gas cells MUST NOT map to `hydrogen` or to a removed `integrated` area.

#### Scenario: Main block ownership is stable
- **WHEN** element cells are rendered in student or teacher periodic selectors
- **THEN** alkali and alkaline-earth elements except hydrogen MUST map to `s`
- **AND** group 11 and group 12 ds elements MUST map to `ds`
- **AND** transition d-block elements MUST map to `d`
- **AND** La-Lu and Ac-Lr MUST map to `f`.

### Requirement: Chapter ownership by learning area
The platform SHALL keep textbook chapter grouping consistent with the accepted area taxonomy while allowing special chapters to appear in more than one learning context when chemically necessary.

#### Scenario: Standard chapters map to areas
- **WHEN** textbook chapters are grouped for student learning or teacher resources
- **THEN** CH13, CH14, CH15, CH16, and CH17 MUST be available under `p`
- **AND** CH18 MUST be available under `s`
- **AND** CH19 MUST be available under `ds`
- **AND** CH20 MUST be available under `d`
- **AND** CH21 MUST be available under `f`.

#### Scenario: Hydrogen and noble gas chapter maps to two contexts
- **WHEN** CH22 `氢和稀有气体` is grouped for learning selection
- **THEN** it MUST be available from the `hydrogen` context because it contains hydrogen
- **AND** it MUST be available from the `p` context because noble gases are displayed as p-area elements
- **AND** the implementation MUST NOT reintroduce a combined `氢和稀有气体` area selector to represent this chapter.

#### Scenario: Student f chapter is available
- **WHEN** the student H5 learning entry or selected-area page includes available student profiles
- **THEN** the `f区元素` area MUST be enabled when the CH21 f-block profile is present
- **AND** opening the f selected-area route MUST show the CH21 chapter entry rather than an empty disabled state.
