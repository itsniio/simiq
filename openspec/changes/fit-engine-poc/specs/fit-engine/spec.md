# Spec Delta: fit-engine

## Purpose

Computes how a specific garment size fits a specific body in a given pose, zone by zone, and recommends a size with a stated confidence and an explanation.

## ADDED Requirements

### Requirement: Per-zone fit result
For a body profile, garment, size and pose, the engine SHALL return for each zone the strain (girth and loop zones) or the length margin in cm (length zones), and a status.

#### Scenario: Stretched girth
- **WHEN** the body chest girth in the pose is 96 cm and the garment chest circumference is 84 cm
- **THEN** the chest strain is 14.3 %

#### Scenario: Loose girth
- **WHEN** the body girth is 80 cm and the garment circumference is 84 cm
- **THEN** the strain is −4.8 % and an ease of 4.0 cm is reported

### Requirement: Fit status scale
Girth and loop zones SHALL use the statuses `too_loose`, `loose`, `ok`, `tight` and `too_tight`. Length zones SHALL use `too_short`, `short`, `ok` and `long`. Thresholds SHALL come from the fit ranges for the garment's brand and fit block.

#### Scenario: Inside the ok band
- **WHEN** a zone's strain lies inside its ok band
- **THEN** the zone status is `ok`

#### Scenario: No brand ranges
- **WHEN** no fit ranges exist for the garment's brand and fit block
- **THEN** default ranges are used and the result is flagged `default_ranges`

### Requirement: Relative pressure
For girth zones under tension the engine SHALL compute pressure from fabric tension and body radius (Laplace's law), and SHALL expose it only relative to other sizes of the same garment, never as an absolute value.

#### Scenario: Smaller size presses more
- **WHEN** chest pressure is computed for sizes M and L of the same garment on the same body
- **THEN** M's relative pressure is higher than L's

#### Scenario: Strain beyond the measured curve
- **WHEN** a zone's strain exceeds the measured range of its fabric curve
- **THEN** the zone is flagged `out_of_curve` and no extrapolated pressure is reported

### Requirement: Length margin accounts for stretch
For length zones the margin SHALL include how far the garment can stretch along the measurement at its fabric's configured comfort tension.

#### Scenario: Back length covered by stretch
- **WHEN** the garment back length is 60 cm, the fabric reaches comfort tension at 5 % wale strain, and the body back length in the pose is 62 cm
- **THEN** the margin is +1.0 cm and the status is `ok`

### Requirement: Size recommendation with explanation
The engine SHALL recommend the size with the lowest weighted penalty across zones, and SHALL explain the recommendation with the zones whose status decided it.

#### Scenario: Clear case
- **WHEN** size M has all zones `ok` and sizes S and L each have a weighted zone outside `ok`
- **THEN** M is recommended

#### Scenario: Explanation names deciding zone
- **WHEN** M is recommended over L because L's chest is `loose`
- **THEN** the explanation lists zone `chest` with status `loose` for size L

### Requirement: Confidence and alternative size
The engine SHALL report a confidence between 0 and 1 derived from body-measurement uncertainty, and SHALL name an alternative size when confidence is below the configured threshold (default 0.6).

#### Scenario: Borderline body
- **WHEN** the body lies at the boundary between M and L
- **THEN** confidence is below 0.6 and the other of the two sizes is named as alternative

#### Scenario: Clear body
- **WHEN** the body lies well inside M's ok bands for all weighted zones
- **THEN** confidence is at least 0.8 and no alternative is named

### Requirement: Pose used for recommendation
The recommendation SHALL be computed in the garment's configured riding pose (default `hoods`), and results for `standing` SHALL also be available for comparison. The result SHALL state the pose used.

#### Scenario: Default pose
- **WHEN** a recommendation is requested without a pose
- **THEN** it is computed in `hoods` and the result states pose `hoods`

### Requirement: Fast and deterministic
Given precomputed body measurements, the engine SHALL compute results for all sizes of one garment in under 50 ms on a laptop CPU, and repeated runs with the same inputs and versions SHALL return identical results.

#### Scenario: Five sizes
- **WHEN** a recommendation for a garment with 5 sizes is computed from body measurements
- **THEN** it completes in under 50 ms and a repeated run returns an identical result

### Requirement: Command-line use
The engine SHALL produce a recommendation JSON from the command line, given body inputs and a garment file.

#### Scenario: CLI recommendation
- **WHEN** the recommend command runs with height, weight, age, sex and a garment file
- **THEN** it prints JSON containing the recommended size, confidence, alternative, pose and per-size zone results
