# Spec Delta

## Purpose

Represents a garment as panels, seams, sizes, and fabrics so it can be simulated on any body regardless of whether the brand supplied a pattern, a spec sheet, or nothing at all.

## ADDED Requirements

### Requirement: Three input tiers resolve to one garment form
The system SHALL create a garment from a pattern file, from a spec sheet of points of measure, or from flat measurements of a physical garment, and in every case produce the same form: panels with rest shapes, seams, a size run, and a fabric per panel.

#### Scenario: Created from a pattern file
- **WHEN** a DXF pattern with panel pieces and a bill of materials is supplied
- **THEN** the garment's panels are the file's pieces and each panel is assigned the fabric the bill of materials names

#### Scenario: Created from a spec sheet
- **WHEN** points of measure per size and fabric names are supplied without a pattern
- **THEN** template panels are sized to match the points of measure and the garment is marked as template-derived

#### Scenario: Created from a measured physical garment
- **WHEN** flat measurements taken from a bought garment are supplied
- **THEN** the garment is created exactly as from a spec sheet, with provenance recorded as physical

### Requirement: Template archetypes cover known jersey layouts
The template SHALL support set-in and raglan sleeves, with and without side panels, and SHALL reject a requested layout it cannot represent with a reason.

#### Scenario: Raglan requested
- **WHEN** a spec sheet declares raglan sleeves
- **THEN** the raglan archetype is used and the sleeve panel extends to the collar

#### Scenario: Unsupported layout
- **WHEN** a layout outside the supported archetypes is requested
- **THEN** creation fails with a reason naming the unsupported feature

### Requirement: Size run is graded consistently
Each size SHALL have its own panel dimensions, and key dimensions SHALL not decrease from one size to the next larger size.

#### Scenario: Grading inverted
- **WHEN** size M is supplied with a smaller chest half width than size S
- **THEN** the garment is rejected with a reason naming the sizes and the dimension

### Requirement: Every panel references a fabric with an orientation
Each panel SHALL reference a fabric library entry and state the warp direction on the panel. A garment with any panel lacking a fabric SHALL be marked not simulatable.

#### Scenario: Panel without fabric
- **WHEN** a garment is saved with a side panel that has no fabric
- **THEN** the garment is stored but flagged not simulatable, naming the panel

### Requirement: Designer intent is recorded per garment
Each garment SHALL record the brand's intended fit category (race, fitted, relaxed) and MAY record intended stretch per zone. When neither is supplied the category SHALL default to fitted and be flagged as a default.

#### Scenario: Intent not supplied
- **WHEN** a garment is created without an intended fit
- **THEN** it is stored as fitted with a visible flag that the value is a default

### Requirement: Rest-state dimensions are kept for strain reference
Each size SHALL store the flat, unstretched dimensions of its panels so that stretch can be computed relative to the garment at rest.

#### Scenario: Strain reference requested
- **WHEN** a simulation asks for the rest shape of a panel in size M
- **THEN** the flat panel geometry for size M is returned unchanged by any previous simulation

### Requirement: Provenance is recorded
Each garment SHALL record which input tier created it, the source files or measurement session, and the date, so a result can be traced to its inputs.

#### Scenario: Provenance queried
- **WHEN** a garment's provenance is requested
- **THEN** the tier, source reference, and creation date are returned
