# Spec Delta: analytics

## Purpose

Measures whether simiq changes shopper behavior — usage, conversion, multi-size ordering and size-related returns — against a holdout group, without collecting body data.

## ADDED Requirements

### Requirement: Usage events
The loader and viewer SHALL record these events: `eligible`, `button_view`, `open`, `form_submit`, `recommendation_shown`, `size_selected` and `error`. Each event SHALL carry the shop, product, garment, visitor, session, variant, versions and timestamp.

#### Scenario: Treatment visit
- **WHEN** a treatment visitor sees the button, opens it and gets a recommendation
- **THEN** `eligible`, `button_view`, `open`, `form_submit` and `recommendation_shown` are stored for that session

### Requirement: No body data in analytics
Analytics events SHALL NOT contain height, weight, age, sex or girths. The server SHALL drop any field not on the event allowlist.

#### Scenario: Unexpected field
- **WHEN** an event arrives with a field `height_cm`
- **THEN** the stored event does not contain that field

### Requirement: Deterministic holdout
When a shop has an active experiment, the loader SHALL assign each consenting visitor to treatment or control deterministically from the visitor id and experiment id. Control visitors SHALL NOT see the button and SHALL be recorded as eligible.

#### Scenario: Stable assignment
- **WHEN** the same visitor returns on another day during the experiment
- **THEN** they are in the same variant as before

#### Scenario: Control visitor
- **WHEN** a control visitor opens a mapped product page
- **THEN** no button is shown and an `eligible` event with variant `control` is stored

### Requirement: Consent respected
Without analytics consent, the system SHALL NOT store a visitor id or send events. The visitor SHALL still get the button and SHALL be excluded from experiment analysis.

#### Scenario: Consent declined
- **WHEN** the shop reports analytics consent as declined
- **THEN** the button is shown and no events or identifiers are stored

### Requirement: Order and return linkage
The system SHALL ingest orders and returns from adapters or CSV, link them to sessions through the simiq session id when present, and map return reasons to a common set: `size_too_small`, `size_too_large`, `other_fit`, `not_fit_related`, `unknown`.

#### Scenario: CSV import
- **WHEN** a CSV of returns with order ids and reasons is uploaded
- **THEN** returns are linked to stored orders and reasons are mapped to the common set

### Requirement: Pilot report
For each shop and experiment, the system SHALL produce a report comparing treatment and control on conversion, multi-size ordering and size-related return rate. Each difference SHALL have a 95 % confidence interval. The report SHALL also include sample sizes, the session-to-order linkage rate and a sample-size estimate.

#### Scenario: Weekly report
- **WHEN** the weekly report runs for an active pilot
- **THEN** it shows the three metrics per variant with differences, 95 % intervals, sample sizes, linkage rate and a sample-size estimate

#### Scenario: CSV export
- **WHEN** the brand requests the data behind the report
- **THEN** an aggregate CSV is provided without visitor-level rows

### Requirement: Retention and deletion
Raw events SHALL be deleted after 13 months. All shop data SHALL be deletable on request or on uninstall, and customer-linked records SHALL be deleted when a platform privacy request arrives.

#### Scenario: Retention job
- **WHEN** the retention job runs
- **THEN** raw events older than 13 months no longer exist
