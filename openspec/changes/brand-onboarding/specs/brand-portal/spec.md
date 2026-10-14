# Spec Delta: brand-portal

## Purpose

The brand's self-service workspace: signing in, configuring shops, submitting and following products, approving digitized garments, installing simiq and seeing results.

## ADDED Requirements

### Requirement: Passwordless sign-in
Users SHALL sign in with a single-use email link that expires after 15 minutes. No passwords SHALL be stored.

#### Scenario: Expired link
- **WHEN** a user opens a sign-in link 20 minutes after it was sent
- **THEN** sign-in is refused and a new link can be requested

### Requirement: Brand workspace and roles
Each brand SHALL have a workspace with `owner` and `member` roles. Owners SHALL be able to invite and remove members. Users SHALL see only their own brands' data.

#### Scenario: Invitation
- **WHEN** an owner invites a colleague by email
- **THEN** the colleague can sign in and access the brand as `member`

#### Scenario: Isolation
- **WHEN** a member of brand A requests a product of brand B
- **THEN** access is denied

### Requirement: Shop settings
Owners SHALL be able to manage each shop's platform, allowed page origins, language, fallback size-chart URL and button theme. Changes SHALL take effect through manifest publishing.

#### Scenario: Theme change
- **WHEN** an owner changes the button accent color
- **THEN** the next published manifest carries the new color

### Requirement: Product overview
The portal SHALL list the brand's products with mapping state and garment status, and SHALL let users filter by status.

#### Scenario: Filter
- **WHEN** a user filters by `in_review`
- **THEN** only products whose garment is in review are listed

### Requirement: Preview and approval
For garments in review the portal SHALL offer a preview of the viewer and SHALL let brand members approve or request changes with a comment.

#### Scenario: Request changes
- **WHEN** a member requests changes with a comment
- **THEN** the garment moves to `changes_requested` and staff see the comment

### Requirement: Installation instructions
The portal SHALL show installation steps for the shop's platform with the shop key filled in, linking to the matching adapter or the snippet guide.

#### Scenario: Custom shop
- **WHEN** a shop's platform is `custom`
- **THEN** the portal shows the snippet with the shop key and a link to the integration guide

### Requirement: Results dashboard
The portal SHALL show each shop's usage and, during experiments, the pilot report metrics with confidence intervals, using aggregates from analytics.

#### Scenario: Active pilot
- **WHEN** a shop has an active experiment
- **THEN** the dashboard shows treatment versus control for conversion, multi-size ordering and size-related returns with intervals
