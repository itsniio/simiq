# Spec Delta

## Purpose

Stores the measured stretch behaviour of fabrics so that a fabric measured once serves every garment that uses it, and so solver stiffness is tied to a physical measurement rather than a guess.

## ADDED Requirements

### Requirement: A fabric entry holds measured stretch curves
Each entry SHALL hold a name, optional mill and composition, an elongation-versus-load curve with at least three load points in warp and in weft, recovery after unloading, the measurement method, and the measurement date.

#### Scenario: Entry created from the strip rig
- **WHEN** warp and weft elongation at three or more loads are supplied with recovery
- **THEN** the entry is stored with method "strip" and is usable by garments

#### Scenario: Too few load points
- **WHEN** a curve with fewer than three load points is supplied
- **THEN** the entry is rejected with a reason naming the direction

### Requirement: Curves are physically plausible
Elongation SHALL not decrease as load increases within a curve. Entries violating this SHALL be rejected.

#### Scenario: Non-monotonic curve
- **WHEN** a curve shows less elongation at a higher load
- **THEN** the entry is rejected and the reason names the two load points

### Requirement: Comfortable stretch range per direction
Each entry SHALL carry a comfortable stretch range in warp and weft, the elongation band within which a garment made from it is considered "as designed". The range SHALL be set explicitly or derived from the curve, and the source SHALL be recorded.

#### Scenario: Range derived
- **WHEN** no range is supplied
- **THEN** a range is derived from the curve and the entry records that the range is derived

### Requirement: Fidelity is recorded and filterable
An entry measured in place on a whole garment rather than on a cut strip SHALL be marked lower fidelity, and consumers SHALL be able to filter or warn on it.

#### Scenario: In-place measurement
- **WHEN** an entry is created with method "in place"
- **THEN** it is marked lower fidelity and simulations using it carry that mark in their results

### Requirement: Entries are shared and versioned
A garment panel SHALL reference an entry by identity. Changing an entry SHALL create a new version, and results SHALL record which version they used.

#### Scenario: Entry updated after use
- **WHEN** a fabric's curve is re-measured and updated
- **THEN** existing results still reference the earlier version and new simulations use the new one
