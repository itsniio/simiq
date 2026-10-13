# Spec Delta

## Purpose

Scores a body model and a fit simulation against the ground-truth dataset so the team can decide, with numbers, whether the picture and the size verdict are trustworthy.

## ADDED Requirements

### Requirement: Body measurement error is reported per measurement and per input level
Given predicted measurements for each rider from a candidate body model, the evaluation SHALL report error against tape per measurement, separately for the minimal-input level and the minimal-plus-optional level, alongside the tape noise estimated from duplicate measurements.

#### Scenario: Minimal inputs scored
- **WHEN** predictions made from gender, height, weight, and silhouette are supplied for all complete riders
- **THEN** the report lists mean absolute error and the 90th percentile error for each measurement in the lab list

#### Scenario: Tape noise shown alongside
- **WHEN** duplicate-measurement riders exist
- **THEN** the report shows, next to each measurement's model error, the mean absolute difference between the two measurers

### Requirement: Zone agreement is reported per zone and per pose
Given a predicted tightness class per zone for each rider, size, and pose, the evaluation SHALL report the rate of agreement with the rider's feel chart per zone and per pose, and the direction of disagreement.

#### Scenario: Zone agreement computed
- **WHEN** predictions are supplied for every observation
- **THEN** the report shows, for each of the eight zones and each pose, the agreement rate and a confusion table of predicted versus reported classes

#### Scenario: Direction of error visible
- **WHEN** the simulation predicts "as designed" where riders reported "too tight"
- **THEN** that case is counted as an under-prediction of tightness, distinct from an over-prediction

### Requirement: Simulated stretch is compared with dot-grid stretch
Given simulated stretch ratios per zone and dot-grid stretch measured from photos, the evaluation SHALL report the error per zone and per pose for zones where the grid is readable.

#### Scenario: Grid readable in a zone
- **WHEN** a zone has dot-grid stretch for a rider, size, and pose
- **THEN** the report includes the difference between simulated and measured stretch for that zone

#### Scenario: Grid not readable
- **WHEN** a zone's dots are occluded or outside the camera-facing area
- **THEN** that zone is excluded from the stretch comparison and the exclusion is counted

### Requirement: Size verdict accuracy is reported against the chart baseline
Given a recommended size per rider from a candidate, the evaluation SHALL report the share of riders whose recommendation matches the size they chose, and the same share for the brand's size chart baseline, side by side.

#### Scenario: Verdict scored
- **WHEN** recommendations exist for all riders with a chosen size
- **THEN** the report shows candidate accuracy and chart accuracy on the same riders, with the count of riders

#### Scenario: Ambiguous chart baseline
- **WHEN** the chart baseline is a set of two sizes
- **THEN** the chart is scored correct if the rider's chosen size is in the set, and the report states how many riders were ambiguous

### Requirement: Candidates are scored on identical rider sets
When more than one candidate (for example two body models, or two solvers) is evaluated, the evaluation SHALL score each on exactly the same riders and observations and present them side by side.

#### Scenario: Two body models compared
- **WHEN** predictions from two body models are supplied
- **THEN** riders missing from either set are excluded from both, and the report lists the shared rider count

### Requirement: Incomplete and withdrawn records are excluded and counted
The evaluation SHALL exclude riders flagged incomplete or withdrawn and SHALL state how many were excluded and why.

#### Scenario: Incomplete rider present
- **WHEN** a rider lacks torso length
- **THEN** that rider is excluded from body evaluation and the exclusion appears in the report summary
