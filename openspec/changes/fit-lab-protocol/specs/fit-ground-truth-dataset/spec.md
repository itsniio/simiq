# Spec Delta

## Purpose

Holds what the system knows about real riders wearing real garments in real postures: the ground truth every body model and fit simulation is evaluated against.

## ADDED Requirements

### Requirement: Rider records are pseudonymous
The dataset SHALL identify each rider only by an assigned rider ID. Names and contact details SHALL be stored outside the dataset, in a separate mapping that is never exported with it.

#### Scenario: Rider enrolled
- **WHEN** a rider is enrolled at the lab
- **THEN** a rider ID is assigned and the dataset record contains no name, email, or phone number

#### Scenario: Dataset exported
- **WHEN** the dataset is exported for evaluation
- **THEN** the export contains rider IDs only and no field from the identity mapping

### Requirement: Consent gates every record
The dataset SHALL refuse to store measurements, observations, or photos for a rider without a recorded consent. Optional photo consent for future body capture SHALL be recorded separately from the main consent.

#### Scenario: Measurement without consent
- **WHEN** a measurement is submitted for a rider ID with no consent recorded
- **THEN** the submission is rejected and the reason names the missing consent

#### Scenario: Optional photo consent absent
- **WHEN** a rider has given main consent but not optional photo consent
- **THEN** lab photos of the garment are accepted and body-capture photos are rejected

#### Scenario: Rider withdraws
- **WHEN** a rider withdraws consent
- **THEN** all of that rider's records are excluded from every export and evaluation, and the exclusion is counted

### Requirement: Self-reported inputs are stored apart from measured values
The rider record SHALL store gender, height, weight, and silhouette picks exactly as the rider entered them, separately from tape measurements, so the two can be compared.

#### Scenario: Self-report captured
- **WHEN** a rider completes the onboarding flow at the first station
- **THEN** the record stores the entered gender, height, weight, body silhouette, and any per-limb silhouettes, marked as self-reported

#### Scenario: Measured height differs from self-reported
- **WHEN** a measurer records height for the same rider
- **THEN** both values are retained and neither overwrites the other

### Requirement: Tape measurement set is fixed and includes torso length
Each measured rider record SHALL hold the lab's measurement list: height, weight, neck, chest, waist, hips, shoulder width, back length, torso length, arm length, upper arm, wrist, thigh, inseam, calf. Each value SHALL carry the measurer's ID.

#### Scenario: Torso length missing
- **WHEN** a rider record is saved without torso length
- **THEN** the record is flagged incomplete and excluded from body evaluation until completed

#### Scenario: Measurement entered
- **WHEN** a measurer enters chest for a rider
- **THEN** the value is stored in centimetres with the measurer's ID and a timestamp

### Requirement: Duplicate measurements are retained for noise estimation
When a rider is measured by more than one measurer, the dataset SHALL retain every set and SHALL NOT average or replace them.

#### Scenario: Second measurer records the same rider
- **WHEN** a second measurer submits a full set for a rider already measured
- **THEN** both sets are stored and the rider is marked as a duplicate-measurement rider

### Requirement: Garment records describe the physical garment used
Each garment record SHALL hold the model name, brand, the size run, per-size flat measurements, fabric per panel where known, and a rest-state photo of the gridded garment for each size, taken before any wear.

#### Scenario: Size added without rest-state photo
- **WHEN** a garment size is saved without a rest-state grid photo
- **THEN** the size is flagged as not usable for stretch comparison

### Requirement: Observations are keyed by rider, size, and pose
Each observation SHALL belong to exactly one rider ID, one garment size, and one pose (standing or riding), and SHALL hold a feel chart, photos, and a buy decision for that combination.

#### Scenario: Feel chart submitted
- **WHEN** a feel chart is submitted for a rider, size, and pose
- **THEN** all eight zones (collar, shoulders, chest, upper back, belly, lower back and hem, sleeve hem, armpit) carry a rating on the five-point scale, or the submission is rejected

#### Scenario: Photo stored
- **WHEN** a photo is uploaded
- **THEN** it is linked to a rider ID, size, pose, and view (front, side, back, arms forward, hoods, drops) and the upload is rejected if any of these is missing

#### Scenario: Buy decision recorded
- **WHEN** a rider answers "would you buy this size" for a size
- **THEN** the yes or no is stored on that rider and size, independent of pose

### Requirement: Final rider answers are captured once per rider
The dataset SHALL store, once per rider, the size the rider would actually order and the rider's preferred fit style (race, fitted, relaxed).

#### Scenario: Rider finishes
- **WHEN** a rider completes the final questions
- **THEN** the chosen size and preferred fit style are stored on the rider record

### Requirement: Size chart baseline is recorded per rider
For each rider and garment, the dataset SHALL record the size the brand's size chart selects from the rider's tape measurements, as a set when the chart is ambiguous.

#### Scenario: Chart is unambiguous
- **WHEN** the rider's chest and height fall in one chart cell
- **THEN** that single size is recorded as the baseline

#### Scenario: Chart is ambiguous
- **WHEN** the rider's measurements fall across two chart sizes
- **THEN** both sizes are recorded as the baseline set and the rider is scheduled to try both
