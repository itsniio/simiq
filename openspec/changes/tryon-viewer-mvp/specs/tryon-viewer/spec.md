# Spec Delta: tryon-viewer

## Purpose

The shopper-facing try-on studio designed in Figma: building a body through the onboarding flow with consent, browsing the brand's digitized garments, seeing the recommended size and why, and seeing the fit on a 3D body standing and on the bike — standalone or inside an e-shop.

## ADDED Requirements

### Requirement: Studio layout
The viewer SHALL follow the Figma desktop design: the onboarding in a left panel, the 3D body in the middle with reset-view, fullscreen and bike controls and a "Buy the fit" button, and the product panel on the right. Both side panels SHALL fold away. Until mobile frames exist, narrow screens SHALL stack the panels in that order.

#### Scenario: Desktop
- **WHEN** the viewer opens at 1440 px width
- **THEN** the three areas sit side by side as in the Figma desktop frame, and the designer has signed off the comparison screenshot

#### Scenario: Folded panel
- **WHEN** the shopper folds the left panel
- **THEN** the 3D view widens and the panel can be reopened from its edge

### Requirement: Onboarding steps follow the Figma flow
The left panel SHALL run the three steps of the Figma flow: (1) sex, weight, height and body type; (2) arm, torso and leg types; (3) measurements grouped as upper and lower body. Steps 2 and 3 SHALL be skippable. The required step SHALL be completable in under 30 seconds. Validation SHALL use the API's ranges.

#### Scenario: Required step only
- **WHEN** a shopper completes step 1 and skips steps 2 and 3
- **THEN** a body is built and the steps indicator shows step 1 done and the others skippable

#### Scenario: Matches the design
- **WHEN** each step is compared with its Figma frame
- **THEN** fields, options, order and copy match the frame

#### Scenario: Invalid value
- **WHEN** weight is set below the supported range
- **THEN** an inline error appears at the weight field and no request is sent

### Requirement: Measurement help on the model
Clicking a measurement's info icon or its field SHALL highlight the matching body part on the 3D model and show how to measure it.

#### Scenario: Chest help
- **WHEN** the shopper clicks the info icon next to chest
- **THEN** the chest band on the model is highlighted and the measuring instructions are shown

### Requirement: Consent before processing
The viewer SHALL show a short privacy notice with a link to the full policy, and SHALL require explicit consent before any body data leaves the device.

#### Scenario: No consent
- **WHEN** the consent box is not checked
- **THEN** continuing is disabled and no network request carrying body data is made

### Requirement: Product panel
The right panel SHALL list the shop's digitized garments with search and the category filters of the Figma design. A card SHALL show the image, name, number of colors and, when a shop is known, the price. Opening a card SHALL show its detail: name, subtitle, price, image, colors, sizes, a "Try on" button and key features with material properties.

#### Scenario: Filter
- **WHEN** the shopper picks the Bibs filter
- **THEN** only bib shorts are listed

#### Scenario: Try on
- **WHEN** the shopper presses "Try on" on a jersey's detail
- **THEN** the jersey's fit is shown on the body and its recommended size is marked among the sizes

### Requirement: Recommendation display
For a tried-on garment the viewer SHALL mark the recommended size using the shop's size label, state the confidence in plain language, and list per-zone explanations for the recommended size.

#### Scenario: High confidence
- **WHEN** the API returns M with confidence 0.85 and no alternative
- **THEN** M is marked without an alternative

#### Scenario: Low confidence
- **WHEN** the API returns M with confidence 0.52 and alternative L
- **THEN** M and L are both marked and the zones that separate them are named

### Requirement: 3D fit view
The middle area SHALL show a body matching the shopper's height and build, standing by default, with the bike control switching to the riding pose. Tried-on garments' zones SHALL be colored by fit status. The shopper SHALL be able to rotate the view and reset it.

#### Scenario: Bike control
- **WHEN** the shopper presses the bike control
- **THEN** the body changes to pose `hoods` and zone colors show the fit in that pose

#### Scenario: Not by color alone
- **WHEN** zones are colored
- **THEN** every zone status is also given as text in a legend or zone list

### Requirement: Size and pose comparison
The shopper SHALL be able to switch sizes and poses, and colors and explanations SHALL update without a new request.

#### Scenario: Switch size
- **WHEN** the shopper switches from M to L
- **THEN** zone colors and explanations update within 200 ms without a new API request

### Requirement: Buy the fit
"Buy the fit" SHALL hand the tried-on garments with their chosen sizes to the shop: embedded, as `select-size` messages to the allowed parent; standalone, as links to the products' shop pages when a shop is known.

#### Scenario: Embedded
- **WHEN** an embedded shopper has tried on a jersey in M and presses "Buy the fit"
- **THEN** the viewer posts a `select-size` message with the jersey and the shop's label for M

### Requirement: Graceful degradation
If WebGL is unavailable or the 3D asset fails to load, the viewer SHALL still show the recommendation and zone explanations. If the API fails, it SHALL show an error with a retry and, when the shop provides one, a link to its size chart.

#### Scenario: No WebGL
- **WHEN** the browser has no WebGL
- **THEN** the onboarding, product panel, recommendation and zone list work without the 3D view

#### Scenario: API error
- **WHEN** the API responds with a server error
- **THEN** the viewer shows an error message, a retry button and the size-chart link when the shop provides one

### Requirement: Standalone and embedded modes
The viewer SHALL work at a public URL and inside an iframe. Embedded, it SHALL open with the shop's product already tried on, and SHALL exchange versioned messages only with parent origins allowed for the shop.

#### Scenario: Standalone link
- **WHEN** someone opens the standalone URL with a garment id
- **THEN** the studio opens with that garment selected in the product panel

#### Scenario: Disallowed parent
- **WHEN** the viewer is embedded by a page whose origin is not allowed for the shop
- **THEN** it ignores that page's messages and sends it nothing

### Requirement: Profile kept on the device only
The viewer SHALL store the body profile on the shopper's device only after opt-in, and SHALL offer a control that deletes it. The viewer SHALL keep working when device storage is unavailable.

#### Scenario: Remembered profile
- **WHEN** a shopper opted in and opens the viewer again on the same device and shop
- **THEN** the onboarding is prefilled

#### Scenario: Storage blocked
- **WHEN** device storage throws on access
- **THEN** the viewer works without remembering and shows no error

### Requirement: Languages
The viewer SHALL be available in Slovak, Czech and English, chosen by URL parameter or browser language, defaulting to English.

#### Scenario: Slovak by parameter
- **WHEN** the viewer is opened with `lang=sk`
- **THEN** all texts are in Slovak and match the Figma copy

### Requirement: Performance budget
Until the onboarding is visible, the viewer SHALL load at most 80 KB of compressed JavaScript. The 3D chunk SHALL be at most 250 KB compressed, and one body mesh at most 300 KB.

#### Scenario: Budget check
- **WHEN** the production build exceeds any budget
- **THEN** the build check fails

### Requirement: Accessibility
The onboarding, product panel and results SHALL be operable with a keyboard and a screen reader. All inputs SHALL be labeled and contrast SHALL meet WCAG 2.1 AA.

#### Scenario: Keyboard only
- **WHEN** a user completes the flow using only the keyboard
- **THEN** they can build a body, give consent, try on a garment and read the recommendation
