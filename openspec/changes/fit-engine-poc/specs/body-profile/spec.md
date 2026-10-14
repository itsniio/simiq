# Spec Delta: body-profile

## Purpose

Turns the few inputs a shopper is willing to give into a 3D body in cycling poses, and into the body measurements the fit engine needs, together with how uncertain those measurements are.

## ADDED Requirements

### Requirement: Shopper body inputs
The system SHALL accept height (cm), weight (kg), age (years) and sex (`female` or `male`) as required inputs, and chest, waist and hip girths (cm) as optional inputs.

#### Scenario: Required inputs only
- **WHEN** a body is requested with height 180, weight 75, age 30, sex male and no girths
- **THEN** the system produces a body profile and marks chest, waist and hip girths as estimated

#### Scenario: Optional girths given
- **WHEN** a body is requested with chest 98 and waist 84 in addition to the required inputs
- **THEN** the standing chest and waist girths of the produced body are each within 1.0 cm of the given values

### Requirement: Input validation
The system SHALL reject inputs outside the supported ranges with an error naming each invalid field. Supported ranges: height 140–210 cm, weight 35–160 kg, age 16–90 years, each girth 50–160 cm, BMI 15–45.

#### Scenario: Height out of range
- **WHEN** height 250 is submitted
- **THEN** the system returns a validation error for field `height_cm` and produces no body

#### Scenario: Implausible combination
- **WHEN** height 150 and weight 150 are submitted
- **THEN** the system returns a validation error stating that the height and weight combination is outside the supported range

### Requirement: Height and weight matching
The produced body SHALL match the given height within 0.5 cm and the given weight within 2 %, where weight is derived from body volume and the configured body density.

#### Scenario: Height matched
- **WHEN** a body is produced for height 172 cm
- **THEN** the standing height measured on the mesh is between 171.5 cm and 172.5 cm

#### Scenario: Weight matched
- **WHEN** a body is produced for weight 68 kg
- **THEN** mesh volume times configured density is between 66.64 kg and 69.36 kg

### Requirement: Cycling pose presets
The system SHALL provide the named poses `standing`, `hoods` and `drops`, and SHALL produce the same body profile in any of them.

#### Scenario: Body in hoods pose
- **WHEN** the body is requested in pose `hoods`
- **THEN** the mesh has the torso leaning forward with hands at handlebar position, and measurements are reported for that pose

#### Scenario: Unknown pose
- **WHEN** pose `aero` is requested and no such preset exists
- **THEN** the system returns an error listing the available poses

### Requirement: Pose-dependent measurements
For each pose the system SHALL report, in cm: chest, waist and hip girth; upper-arm and thigh girth profiles in 2 cm steps; back length; and vertical trunk girth. Girths SHALL be measured as a tape measure would, bridging concavities.

#### Scenario: Measurements per pose
- **WHEN** measurements are requested for poses `standing` and `hoods`
- **THEN** every listed measurement is present for both poses and the back length in `hoods` is greater than in `standing`

#### Scenario: Limb profile lookup
- **WHEN** the thigh girth 25 cm below the crotch is requested
- **THEN** the system returns a value interpolated from the thigh girth profile

### Requirement: Measurement uncertainty
The system SHALL report a standard deviation for each measurement. A girth estimated without the matching girth input SHALL have a larger standard deviation than the same girth when the input is given.

#### Scenario: Uncertainty shrinks with a girth input
- **WHEN** the same person is profiled once without and once with a chest girth
- **THEN** the chest girth standard deviation is smaller in the second profile

### Requirement: Commercially usable body assets only
The body pipeline SHALL use only models, assets and code whose licenses allow commercial use; SMPL-family models and assets SHALL NOT be used.

#### Scenario: License review
- **WHEN** the body-model dependencies and assets are reviewed
- **THEN** each is under Apache-2.0, CC0 or another license that allows commercial use, and none is SMPL-derived

### Requirement: Deterministic output
The same inputs, pose and versions of model and data SHALL produce the same measurements.

#### Scenario: Repeatability
- **WHEN** the same body request is run twice
- **THEN** all measurements are identical within 0.1 mm
