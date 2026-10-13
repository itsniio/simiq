# Spec Delta

## Purpose

Computes where a garment is tighter or looser than its designer intended on a given body in a given pose, and serves that for any shopper body fast enough for a product page.

## ADDED Requirements

### Requirement: Fit result for a body, size, and pose
Given a body, a garment size, and a pose, the system SHALL produce the draped garment mesh, a stretch ratio in warp and weft per triangle, and a class per vertex of tight, as designed, or loose.

#### Scenario: Result produced
- **WHEN** a body, size M, and the riding pose are supplied
- **THEN** a draped mesh with per-vertex class and per-triangle stretch ratios is returned

### Requirement: Class is relative to designer intent
A vertex SHALL be classed "as designed" when its stretch lies within the panel fabric's comfortable range, "tight" above it, and "loose" below it. Zero stretch SHALL NOT be the reference.

#### Scenario: Race jersey correctly tight
- **WHEN** chest stretch lies inside the fabric's comfortable range on a race-fit garment
- **THEN** the chest is classed as designed, not tight

#### Scenario: Over-stretched
- **WHEN** stretch exceeds the top of the comfortable range
- **THEN** the vertex is classed tight and the ratio is retained for display

### Requirement: Solver reproduces measured fabric behaviour
A simulated strip of a library fabric SHALL elongate within 10 percent of the measured elongation at each of the library's load points, in both directions, before that fabric is used in garment results.

#### Scenario: Calibration check
- **WHEN** a strip of a fabric is simulated under the library's load points
- **THEN** each simulated elongation is within 10 percent of the measured value, or the fabric is marked uncalibrated and garment results using it are withheld

### Requirement: Dressing failures are explicit
When a garment cannot be settled on a body without interpenetration beyond tolerance or without converging, the result SHALL be marked failed with a reason, never stored as a valid result.

#### Scenario: Garment does not converge
- **WHEN** the solve does not reach equilibrium within its limits
- **THEN** the result is marked failed with the reason and the body, size, and pose are logged

### Requirement: Zone summary and hem positions
Each result SHALL summarise class and stretch per feel-chart zone (collar, shoulders, chest, upper back, belly, lower back and hem, sleeve hem, armpit) and SHALL report hem positions relative to body landmarks: back hem versus waist and sleeve hem versus elbow, in centimetres.

#### Scenario: Back hem short in riding pose
- **WHEN** the riding-pose result places the back hem above the rider's waist landmark
- **THEN** the summary reports the back hem as short by the measured distance in centimetres

### Requirement: Both poses are available for comparison
For a body and size the system SHALL produce results for standing and riding, and SHALL report per zone how class and hem positions change between them.

#### Scenario: Pose comparison
- **WHEN** both pose results exist for a body and size
- **THEN** the comparison lists each zone whose class differs between poses and the change in back hem position

### Requirement: Size verdict across the size run
Given results for every size on a body and the shopper's fit preference, the system SHALL recommend one size and give a per-zone reason, and SHALL state when two sizes are equally acceptable.

#### Scenario: Clear verdict
- **WHEN** size M is as designed in all zones and size L is loose in chest and shoulders
- **THEN** M is recommended and the reason names the zones where L is loose

#### Scenario: Preference changes the verdict
- **WHEN** the shopper prefers a relaxed fit and M is as designed while L is loose only in the belly
- **THEN** L is recommended and the reason names the preference

### Requirement: Results are precomputed over a body grid
When a garment is published, the system SHALL compute results for every sampled body in the grid, every size, and both poses, and SHALL exclude failed cases from serving while recording them.

#### Scenario: Grid computed
- **WHEN** a garment with six sizes is published against a grid of N bodies
- **THEN** N times six times two results exist or are recorded as failed, and the count of each is reported

### Requirement: Any shopper body is served by blending
For a body not in the grid, the system SHALL return a result blended from its nearest sampled bodies, with a confidence derived from their distance, within 500 milliseconds of server time.

#### Scenario: Shopper body between grid points
- **WHEN** a shopper body is supplied that is not a grid body
- **THEN** a blended result is returned within 500 milliseconds with a confidence value and the IDs of the bodies blended

#### Scenario: Shopper body far from the grid
- **WHEN** the nearest grid bodies are beyond the configured distance
- **THEN** the result carries a low-confidence flag that the result screen must surface

### Requirement: Results are versioned
Every result SHALL record the solver version, the garment version, and the fabric library versions used, so a result can be reproduced or invalidated.

#### Scenario: Fabric re-measured
- **WHEN** a fabric entry gets a new version
- **THEN** existing results still name the old version and are flagged stale for recomputation
