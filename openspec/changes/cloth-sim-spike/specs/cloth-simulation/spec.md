# Spec Delta: cloth-simulation

## Purpose

Drapes a garment made of a measured fabric on a posed body and derives the strain and relative-pressure fields over the garment surface, with per-zone summaries comparable to the fit engine's zones.

## ADDED Requirements

### Requirement: Garment rest state from the flat pattern
The simulation SHALL take a sewn garment mesh whose UV coordinates are the flat pattern with the grain along v, SHALL convert them to millimetres with the export's scale per UV axis, and SHALL use them, scaled by the fabric's simulation shrinkage per direction, as the unstretched shape of every triangle. Vertices of different pattern pieces that coincide in the draped garment SHALL be joined as seams, never joining two vertices of the same piece.

#### Scenario: Rest lengths come from the pattern
- **WHEN** a triangle's UV edge is 10.0 mm long along the course direction and the course shrinkage is 72 %
- **THEN** its rest length along the course is 7.2 mm

#### Scenario: Seams are joined
- **WHEN** two pattern pieces share a sewn edge whose vertices coincide within 1 mm in the draped garment
- **THEN** those vertices move as one in the simulation

#### Scenario: A folded binding keeps its shape
- **WHEN** both edges of a binding folded over another piece's edge lie within 1 mm of the same vertex
- **THEN** only the nearer one is joined to it and no triangle collapses

#### Scenario: Missing pattern coordinates
- **WHEN** a garment mesh has no UV coordinates or a triangle with zero UV area
- **THEN** the simulation refuses the garment and names the pattern piece at fault

### Requirement: Anisotropic fabric from measured curves
The fabric SHALL resist stretch along the course and the wale separately, each following its measured stretch curve from the garment model.

#### Scenario: Hanging strip settles on its curve
- **WHEN** a 50 mm wide strip hangs under a load whose tension lies on the fabric's course curve at 20 % strain
- **THEN** the settled course strain is 20 % within 1 percentage point

#### Scenario: Strain beyond the curve
- **WHEN** a triangle's strain exceeds the measured range of its fabric curve
- **THEN** that triangle is flagged `out_of_curve` and no pressure is reported for it

### Requirement: Draping on a moving body
The simulation SHALL start from a garment already draped on a body and follow that body through a sequence of shapes and poses (`standing`, `hoods`, `drops`), keeping the garment outside the body surface.

#### Scenario: No penetration
- **WHEN** a garment is simulated through a change of body and pose
- **THEN** at every recorded frame at least 99 % of garment vertices lie outside the body surface, and in the case's settled frame no vertex lies deeper inside it than the deepest vertex of CLO's drape of the same case (grill ruling 7)

#### Scenario: Same input, same output
- **WHEN** the same garment, fabric and body sequence are simulated twice
- **THEN** every vertex position agrees within 0.1 mm

### Requirement: Strain and relative pressure fields
For a draped garment the simulation SHALL report per triangle the course strain, the wale strain and a relative pressure from fabric tension and surface curvature (Laplace's law), and SHALL express pressure only relative to other sizes of the same garment, never as an absolute value.

#### Scenario: Undeformed garment
- **WHEN** every triangle has its rest shape
- **THEN** course and wale strain are 0 everywhere

#### Scenario: Uniform stretch on a cylinder
- **WHEN** a garment tube with a course circumference of 84 cm is fitted on a cylinder of circumference 96 cm
- **THEN** the course strain is 14.3 % and the pressure equals the course tension divided by the cylinder radius before normalisation

#### Scenario: Smaller size presses more
- **WHEN** sizes M and L of the same garment are draped on the same body and pose
- **THEN** M's relative chest pressure is higher than L's

### Requirement: Zone summaries
The simulation SHALL summarise the strain field in the fit engine's garment zones as the area-weighted mean course strain of the triangles in each zone, so that the same numbers can be computed from any draped garment, ours or CLO's.

#### Scenario: Same metric for both drapes
- **WHEN** a draped garment exported from CLO with its UV layout is passed to the zone summary
- **THEN** it returns per-zone strains computed exactly as for our own drape

### Requirement: Spike acceptance against CLO
The spike SHALL be judged on the RenderHub demo jersey in three sizes on four Anny bodies (178/75, 180/64, 176/88, 192/82) in `standing`, `hoods` and `drops`. Fabric stiffness MAY be fitted on one case (178/75, `standing`, size M); every other case is held out.

#### Scenario: Pass
- **WHEN** on every held-out case each zone's strain is within ±3 percentage points of CLO's, the sizes rank in the same order of chest strain as in CLO, and one garment on one body takes under 60 s on the founder's Mac
- **THEN** the report recommends go

#### Scenario: Fail
- **WHEN** any of those conditions fails
- **THEN** the report recommends no-go and lists the failing cases with their numbers

### Requirement: Licensed garments stay private
Garment geometry exported from CLO or received from brands SHALL stay outside the repository; only renders and aggregate numbers SHALL be committed. Body inputs SHALL NOT be logged.

#### Scenario: Garment files are refused by git
- **WHEN** a garment mesh, CLO project or point cache under the spike's working folder is staged
- **THEN** it is ignored and never committed
