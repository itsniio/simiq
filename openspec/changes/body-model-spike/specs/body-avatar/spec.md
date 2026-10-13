# Spec Delta

## Purpose

Produces a posed, measurable 3D body from what a shopper is willing to tell us, and says how uncertain it is, as the foundation of every fit result.

## ADDED Requirements

### Requirement: Body from minimal inputs
The system SHALL produce a body mesh from gender, height, weight, and a body silhouette pick (slim, regular, athletic) alone. The produced body's virtual height SHALL match the input within 1 cm.

#### Scenario: Minimal inputs given
- **WHEN** gender, height 189 cm, weight 86 kg, and silhouette "slim" are supplied
- **THEN** a body mesh is returned and its measured height is within 1 cm of 189 cm

#### Scenario: Silhouette changes shape
- **WHEN** the same height and weight are supplied with "athletic" instead of "slim"
- **THEN** the returned body has a larger chest and shoulder width than the slim body

### Requirement: Optional measurements refine the body
When optional tape measurements are supplied, the system SHALL produce a body whose virtual measurement of each supplied value is within 1 cm of it, without moving unsupplied measurements outside their reported error bands.

#### Scenario: Chest supplied
- **WHEN** minimal inputs plus chest 96 cm are supplied
- **THEN** the body's virtual chest is within 1 cm of 96 cm

#### Scenario: Torso length supplied
- **WHEN** minimal inputs plus torso length are supplied
- **THEN** the body's virtual torso length is within 1 cm of the supplied value and height remains within 1 cm of the input

### Requirement: Inputs are validated
The system SHALL reject inputs outside plausible adult ranges or inconsistent with each other, with a reason naming the field.

#### Scenario: Height out of range
- **WHEN** height 40 cm is supplied
- **THEN** the request is rejected and the reason names height

#### Scenario: Measurement contradicts others
- **WHEN** chest 60 cm is supplied with weight 110 kg and height 170 cm
- **THEN** the request is rejected or the body is returned with a warning naming chest, and the behaviour is the same on every call

### Requirement: Every body shares one topology
All bodies the system produces SHALL have the same vertex count and vertex order, so that a vertex index means the same anatomical location on every body.

#### Scenario: Two different bodies
- **WHEN** two bodies are produced from different inputs
- **THEN** both have identical vertex counts and the named landmark vertices refer to the same anatomical points on each

### Requirement: Virtual tape follows the lab protocol
The system SHALL measure a body with the same definitions the fit lab uses for riders: circumferences as slice perimeters at defined landmarks, lengths between defined landmarks, in centimetres.

#### Scenario: Measurements requested
- **WHEN** measurements are requested for a body
- **THEN** every item in the lab's measurement list is returned in centimetres

#### Scenario: Chest definition
- **WHEN** chest is measured
- **THEN** it is the perimeter of the horizontal slice through the fullest point of the chest, matching the lab's written definition

### Requirement: Error bands accompany predicted measurements
For each measurement, the system SHALL return an error band that reflects which inputs were supplied, and SHALL name the single optional input that would most reduce uncertainty for a jersey fit.

#### Scenario: Minimal inputs only
- **WHEN** a body is produced from minimal inputs
- **THEN** every measurement carries a non-zero error band and the suggested next input is one of chest, torso length, or shoulder width

#### Scenario: Optional input added
- **WHEN** chest is added to the inputs
- **THEN** the chest error band is smaller than it was from minimal inputs and the suggested next input is no longer chest

### Requirement: Named poses
The system SHALL pose any body into "standing" and into "riding" with an aggressiveness parameter, preserving topology, so garment results can be compared across poses.

#### Scenario: Riding pose requested
- **WHEN** the riding pose is requested with a given aggressiveness
- **THEN** a posed mesh is returned with the same vertex count as the standing mesh, with flexed hips, curved spine, and arms reaching forward

#### Scenario: Aggressiveness increased
- **WHEN** aggressiveness is increased
- **THEN** the torso angle to horizontal decreases and the back length measured along the surface increases

### Requirement: Export in the body contract format
The system SHALL export any posed body as glTF and OBJ in metres, Y up, facing positive Z, with the origin between the feet, together with the shape parameters and landmark indices.

#### Scenario: Export requested
- **WHEN** an export is requested
- **THEN** both files load in a standard viewer at the correct scale and orientation, and the shape parameters and landmarks are included alongside

### Requirement: Same inputs produce the same body
The system SHALL return an identical body for identical inputs, so results can be cached and compared across runs.

#### Scenario: Repeated call
- **WHEN** the same inputs are supplied twice
- **THEN** the two meshes are identical vertex for vertex
