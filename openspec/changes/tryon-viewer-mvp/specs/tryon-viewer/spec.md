# Spec Delta: tryon-viewer

## Purpose

The shopper-facing experience: collecting body inputs with consent, showing the recommended size and why, and showing the garment's fit on a 3D body in the riding pose — standalone or inside an e-shop.

## ADDED Requirements

### Requirement: Body input form
The viewer SHALL ask for height, weight, age and sex, and SHALL offer optional chest, waist and hip girths with how-to-measure help. Validation SHALL use the same ranges as the API. The form SHALL be completable in under 30 seconds without the optional fields.

#### Scenario: Required fields only
- **WHEN** a shopper fills height, weight, age and sex and leaves girths empty
- **THEN** the form can be submitted

#### Scenario: Missing field
- **WHEN** height is empty and the shopper submits
- **THEN** an inline error is shown at the height field and no request is sent

### Requirement: Consent before processing
The viewer SHALL show a short privacy notice with a link to the full policy, and SHALL require explicit consent before any body data leaves the device.

#### Scenario: No consent
- **WHEN** the consent box is not checked
- **THEN** submit is disabled and no network request carrying body data is made

### Requirement: Recommendation display
The viewer SHALL show the recommended size using the shop's size label, the confidence in plain language, and per-zone explanations for the recommended size.

#### Scenario: High confidence
- **WHEN** the API returns M with confidence 0.85 and no alternative
- **THEN** the viewer shows "M" without an alternative

#### Scenario: Low confidence
- **WHEN** the API returns M with confidence 0.52 and alternative L
- **THEN** the viewer shows M and L together and names the zones that separate them

### Requirement: 3D fit view
The viewer SHALL display a body matching the shopper's height and build, in the riding pose, with garment zones colored by fit status. The shopper SHALL be able to rotate the view.

#### Scenario: Default view
- **WHEN** a recommendation is shown
- **THEN** the 3D body appears in pose `hoods` with each zone colored by its status for the recommended size

#### Scenario: Not by color alone
- **WHEN** zones are colored
- **THEN** every zone status is also given as text in a legend or zone list

### Requirement: Size and pose comparison
The shopper SHALL be able to switch between sizes and between standing and riding poses. Colors and explanations SHALL update without submitting the form again.

#### Scenario: Switch size
- **WHEN** the shopper switches from M to L
- **THEN** zone colors and explanations update within 200 ms without a new API request

### Requirement: Graceful degradation
If WebGL is unavailable or the 3D asset fails to load, the viewer SHALL still show the recommendation and zone explanations. If the API fails, it SHALL show an error with a retry and, when configured, a link to the shop's size chart.

#### Scenario: No WebGL
- **WHEN** the browser has no WebGL
- **THEN** the recommendation and zone list are shown without the 3D view

#### Scenario: API error
- **WHEN** the API responds with a server error
- **THEN** the viewer shows an error message, a retry button and the size-chart link when configured

### Requirement: Standalone and embedded modes
The viewer SHALL work at a public URL per garment and inside an iframe. In embedded mode it SHALL exchange versioned messages only with parent origins allowed for the shop.

#### Scenario: Standalone link
- **WHEN** someone opens the standalone URL for a garment
- **THEN** the viewer loads that garment's form

#### Scenario: Disallowed parent
- **WHEN** the viewer is embedded by a page whose origin is not allowed for the shop
- **THEN** it ignores that page's messages and sends it no recommendation

#### Scenario: Size handoff
- **WHEN** an embedded shopper clicks "choose size M"
- **THEN** the viewer posts a `select-size` message with the shop's size label to the allowed parent

### Requirement: Profile kept on the device only
The viewer SHALL store the body profile on the shopper's device only after opt-in, and SHALL offer a control that deletes it. The viewer SHALL keep working when device storage is unavailable.

#### Scenario: Remembered profile
- **WHEN** a shopper opted in and opens the viewer again on the same device and shop
- **THEN** the form is prefilled

#### Scenario: Storage blocked
- **WHEN** device storage throws on access
- **THEN** the viewer works without remembering and shows no error

### Requirement: Languages
The viewer SHALL be available in Slovak, Czech and English, chosen by URL parameter or browser language, defaulting to English.

#### Scenario: Slovak by parameter
- **WHEN** the viewer is opened with `lang=sk`
- **THEN** all texts are in Slovak

### Requirement: Performance budget
Until the form is visible, the viewer SHALL load at most 80 KB of compressed JavaScript. The 3D chunk SHALL be at most 250 KB compressed, and one body mesh at most 300 KB.

#### Scenario: Budget check
- **WHEN** the production build exceeds any budget
- **THEN** the build check fails

### Requirement: Accessibility
The form and results SHALL be operable with a keyboard and a screen reader. All inputs SHALL be labeled and contrast SHALL meet WCAG 2.1 AA.

#### Scenario: Keyboard only
- **WHEN** a user completes the flow using only the keyboard
- **THEN** they can enter data, give consent, submit and read the recommendation
