# Spec Delta: garment-intake

## Purpose

Defines what a brand hands over to have a garment digitized, how that package is validated, and how the garment's status is tracked from submission until it goes live.

## ADDED Requirements

### Requirement: Submission package
A submission SHALL include, per garment:
- the points-of-measure sheet for every size in the template for its garment type;
- the fabric and composition for each zone;
- the brand's body-measurement size chart.

Tech packs, DXF patterns, fabric datasheets, photos and a note about physical samples SHALL be optional.

#### Scenario: Complete package
- **WHEN** a brand submits a jersey with a valid sheet, fabric info for every zone and a size chart
- **THEN** the submission moves to `submitted`

#### Scenario: Incomplete package
- **WHEN** fabric info is missing for zone `chest`
- **THEN** submission is refused with an error naming the zone

### Requirement: Template validation
Uploaded sheets SHALL be validated against the garment-model contract. Errors SHALL be reported per row and column.

#### Scenario: Invalid value
- **WHEN** row "M", column `chest_circumference` contains "eighty"
- **THEN** the error names row M and that column and the sheet is not accepted

### Requirement: Status workflow
Each garment SHALL move through `draft`, `submitted`, `in_digitization`, `in_review`, `live` and `archived`, with `changes_requested` returning it to the brand. Only staff SHALL set `in_digitization` and `in_review`. Every transition SHALL be logged with user and time.

#### Scenario: Staff starts digitization
- **WHEN** a staff member picks up a submitted garment
- **THEN** its status becomes `in_digitization` and the log shows who and when

#### Scenario: Brand cannot skip review
- **WHEN** a brand user tries to set a garment to `live` while it is `in_digitization`
- **THEN** the change is refused

### Requirement: Brand approval before going live
A garment SHALL become `live` only after a brand member approves it from a preview of the viewer.

#### Scenario: Approval
- **WHEN** a brand owner approves a garment in `in_review` after opening its preview
- **THEN** it becomes `live`

### Requirement: Turnaround tracking
The system SHALL show each submission's target date from the turnaround constant and SHALL flag overdue submissions to staff.

#### Scenario: Overdue
- **WHEN** a submission passes its target date without reaching `in_review`
- **THEN** it is flagged overdue in the staff queue

### Requirement: Private files
Uploaded files SHALL be accessible only to members of the owning brand and to staff, through expiring links.

#### Scenario: Other brand
- **WHEN** a user of another brand requests a file link
- **THEN** access is denied

### Requirement: Contract-conformant output
Every garment that reaches `in_review` SHALL be a valid garment-model record.

#### Scenario: Validation gate
- **WHEN** staff move a garment to `in_review`
- **THEN** the garment record is validated and the move is refused if validation fails
