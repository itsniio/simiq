# Spec Delta: fit-calibration

## Purpose

Defines how fit-study data is captured and protected, how fit ranges are calibrated from it, and how recommendation accuracy is measured against the brand's size chart.

## ADDED Requirements

### Requirement: Study record contents
Each participant record SHALL contain:
- a pseudonymous id and consent timestamp;
- shopper inputs (height, weight, age, sex);
- tape-measured chest, waist and hip girths;
- the garment and sizes tried;
- a rating per zone, size and pose on the fit status scale;
- the size the participant would buy, and free-text comments.

#### Scenario: Missing consent
- **WHEN** a record without a consent timestamp is imported
- **THEN** the import rejects it and names the record

#### Scenario: Several sizes and poses
- **WHEN** a record has ratings for sizes M and L in poses `standing` and `hoods`
- **THEN** all four rating sets are imported

### Requirement: Study data protection
Study data SHALL NOT be committed to the repository. Names and contact details SHALL be stored separately from measurements. A participant's data SHALL be deletable by pseudonymous id.

#### Scenario: Commit blocked
- **WHEN** a file from the private data folder is staged for commit
- **THEN** the commit is blocked with a message explaining why

#### Scenario: Deletion
- **WHEN** deletion is requested for participant P07
- **THEN** all P07 records are removed and evaluation outputs are regenerated without them

### Requirement: Fit range calibration
The system SHALL fit per-zone thresholds for a brand and fit block from study ratings, and SHALL store them versioned together with an identifier of the study data they came from.

#### Scenario: Calibration output
- **WHEN** calibration runs on a study dataset
- **THEN** a new fit-range file is written containing a version and the dataset hash

### Requirement: Accuracy evaluation
The evaluation report SHALL contain:
- the number of participants;
- hit rate (recommended size equals the size the participant would buy) and hit-or-alternative rate;
- the brand size chart's baseline hit rate;
- per-zone agreement between predicted status and rating;
- 95 % confidence intervals for each rate.

#### Scenario: Report contents
- **WHEN** evaluation runs on 20 participants
- **THEN** the report shows N = 20, the hit rate, hit-or-alternative rate, baseline hit rate and per-zone agreement, each rate with a 95 % confidence interval

#### Scenario: Two baselines
- **WHEN** the baseline is computed
- **THEN** the size chart is applied once to tape-measured girths and once to girths estimated from height and weight only, and both results are reported

### Requirement: Out-of-sample accuracy
When fit ranges are calibrated on the same study that is evaluated, reported accuracy SHALL be out of sample.

#### Scenario: Leave-one-out
- **WHEN** ranges are calibrated and evaluated on the same 20 participants
- **THEN** each participant's prediction uses ranges fitted without that participant

### Requirement: Body measurement check
The evaluation SHALL report the difference between body-profile girths and tape-measured girths, both for profiles built from height and weight only and for profiles that include girth inputs.

#### Scenario: Girth error report
- **WHEN** evaluation runs
- **THEN** mean absolute error per girth is reported for "height and weight only" and for "with girths"

### Requirement: Aggregate-only results
Evaluation outputs intended for sharing SHALL contain only aggregate figures and SHALL NOT contain any individual's measurements.

#### Scenario: Shared report
- **WHEN** the shareable report is generated
- **THEN** it contains no row-level participant data
