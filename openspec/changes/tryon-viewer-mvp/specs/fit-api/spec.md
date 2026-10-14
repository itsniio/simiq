# Spec Delta: fit-api

## Purpose

Serves size recommendations and public garment information over HTTP, fast enough for interactive use, without storing or logging shoppers' body data.

## ADDED Requirements

### Requirement: Recommendation endpoint
The API SHALL accept `POST /v1/recommendations` with a garment id, body inputs, an optional pose and an optional language. It SHALL return:
- the recommended size, confidence and optional alternative;
- per-size zone results and explanation data;
- the pose used and the URL of a matching body mesh.

#### Scenario: Valid request
- **WHEN** a request with a known garment id and valid body inputs is sent
- **THEN** the API responds 200 with recommended size, confidence, per-size zone results, pose and body mesh URL

#### Scenario: Unknown garment
- **WHEN** the garment id does not exist
- **THEN** the API responds 404 with error code `garment_not_found`

#### Scenario: Invalid body inputs
- **WHEN** height 250 is sent
- **THEN** the API responds 422 listing `height_cm` as invalid, using the same ranges as body-profile

### Requirement: Latency
Server-side processing of a recommendation SHALL take at most 300 ms at the 95th percentile with 20 concurrent requests.

#### Scenario: Load test
- **WHEN** a load test sends recommendations at 20 concurrent requests for 5 minutes
- **THEN** server-side p95 processing time is at most 300 ms

### Requirement: Agreement with the fit engine
Recommendations served by the API SHALL equal the fit engine's direct computation for at least 95 % of a held-out set of bodies. Pose measurements used by the API SHALL have a mean absolute error of at most 0.5 cm against the direct pipeline.

#### Scenario: Held-out comparison
- **WHEN** 1,000 held-out bodies are evaluated through the API path and the direct engine path
- **THEN** recommended sizes match for at least 950 and pose-measurement MAE is at most 0.5 cm

### Requirement: No storage of body data
The API SHALL NOT persist body inputs or derived measurements, and SHALL NOT include them in logs, traces or error reports.

#### Scenario: Logs after requests
- **WHEN** recommendations are served and the logs are inspected
- **THEN** no height, weight, age, sex or girth values appear in them

#### Scenario: Error during a request
- **WHEN** an unexpected error occurs while handling a recommendation
- **THEN** the error report contains no request body

### Requirement: Garment information endpoint
`GET /v1/garments/{id}` SHALL return public garment data: id, type, display name, size labels, zones with display names, and available poses.

#### Scenario: Garment info
- **WHEN** a known garment is requested
- **THEN** the response contains its size labels, zones and poses, and no fabric curves or fit ranges

### Requirement: Versioned contract
All endpoints except health SHALL be under a version prefix. Responses SHALL state the engine, model and data bundle versions used.

#### Scenario: Version fields
- **WHEN** a recommendation is returned
- **THEN** it includes `engine_version`, `model_version` and `bundle_version`

### Requirement: Cross-origin access
The API SHALL allow browser requests only from configured viewer origins.

#### Scenario: Disallowed origin
- **WHEN** a browser request arrives from an origin not in the allowlist
- **THEN** the response carries no CORS permission for that origin

### Requirement: Health endpoint
`GET /healthz` SHALL report readiness, the number of loaded garments and the model version, without authentication.

#### Scenario: Ready
- **WHEN** the service has loaded the bundle and models
- **THEN** `/healthz` responds 200 with garment count and model version

### Requirement: Rate limiting
The API SHALL limit requests per client IP (default 60 per minute) and respond 429 when the limit is exceeded.

#### Scenario: Over the limit
- **WHEN** one client sends 61 requests within a minute
- **THEN** at least the 61st receives 429
