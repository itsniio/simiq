# Spec Delta: garment-model

## Purpose

Defines how a digitized garment is described — sizes, points of measure, fit zones, fabrics with stretch curves, the brand's size chart and data provenance — so the fit engine, API and onboarding tools share one contract.

## ADDED Requirements

### Requirement: Garment record
A garment record SHALL contain: schema version, unique id, garment type (`jersey` or `bib_shorts`), brand, model name, fit block, data source (`brand_techpack`, `brand_cad` or `team_measured`), zones, sizes, fabric references and the brand size chart.

#### Scenario: Valid record
- **WHEN** a record containing all required fields is loaded
- **THEN** it validates without errors

#### Scenario: Missing field
- **WHEN** a record without `sizes` is loaded
- **THEN** validation fails and the error names `sizes`

### Requirement: Points of measure per size
Each size SHALL define every point of measure referenced by the garment's zones, as relaxed garment dimensions in cm. Circumferences measured flat SHALL be stored doubled.

#### Scenario: Missing point of measure
- **WHEN** size L lacks `chest_circumference` and zone `chest` references it
- **THEN** validation fails naming size L and `chest_circumference`

#### Scenario: Grading order
- **WHEN** chest circumference does not increase from S to M to L
- **THEN** validation reports a grading warning for that point of measure

### Requirement: Fit zones
Each zone SHALL declare its id, kind (`girth`, `loop` or `length`), the garment point of measure, the body measurement it is compared with, the fabric, the stretch direction along the measurement (`course` or `wale`) and a weight.

#### Scenario: Jersey template zones
- **WHEN** a jersey record is created from the jersey template
- **THEN** it contains zones chest, waist, hem, sleeve_opening and back_length

#### Scenario: Bib shorts template zones
- **WHEN** a bib_shorts record is created from the bib template
- **THEN** it contains zones hip, leg_opening and vertical_loop

#### Scenario: Unknown body measurement
- **WHEN** a zone references a body measurement that body-profile does not provide
- **THEN** validation fails naming the zone and the measurement

### Requirement: Fabric stretch curves
A fabric SHALL have force-versus-strain curves for both course and wale directions. Each curve SHALL cover at least 0–40 % strain with at least 5 points. The fabric SHALL also record specimen width, composition, weight per m² and measurement method.

#### Scenario: Curve too short
- **WHEN** a wale curve ends at 20 % strain
- **THEN** validation fails for that fabric and direction

#### Scenario: Non-monotonic curve
- **WHEN** force decreases between two consecutive strain points
- **THEN** validation fails for that fabric and direction

### Requirement: Brand size chart
The garment record SHALL store the brand's published body-measurement size chart, with ranges per size label for each body measure the brand publishes, as the baseline for evaluation.

#### Scenario: Chart lookup
- **WHEN** a body with chest 95 cm is looked up in a chart where M covers chest 92–96 cm
- **THEN** the chart size is M

#### Scenario: Measures disagree
- **WHEN** chest points to M and waist points to L
- **THEN** the lookup returns L and records that the larger size rule decided

### Requirement: Display data
A garment record SHALL carry what the product panel shows: name and subtitle in Slovak, Czech and English, colors with a name, a swatch and an image each, and key features including material properties. Prices and product links SHALL NOT be in the garment record; they belong to the shop.

#### Scenario: Display data present
- **WHEN** a jersey record with names in three languages, two colors and key features is loaded
- **THEN** it validates and its panel category is Jerseys, derived from its type

#### Scenario: Price rejected
- **WHEN** a garment record contains a `price` field
- **THEN** validation fails naming `price` and stating that prices belong to the shop manifest

### Requirement: Provenance
Every set of size measurements and every fabric curve SHALL record who measured it, when and by which method.

#### Scenario: Team-measured size
- **WHEN** a team-measured size is stored
- **THEN** the record includes measurer, date and method

### Requirement: Machine-readable schema
The garment and fabric contracts SHALL be published as JSON Schema so components in other languages can validate records.

#### Scenario: Schema export
- **WHEN** the schema export runs
- **THEN** JSON Schema files for garment and fabric are written and the example records validate against them
