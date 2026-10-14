# Spec Delta: shop-embed

## Purpose

Lets any e-shop add simiq to product pages with one script: a fit button appears only for supported products, opens the viewer on demand, hands the chosen size back to the shop and never harms the host page.

## ADDED Requirements

### Requirement: One-script installation
A shop SHALL be able to enable simiq by adding one script tag carrying its shop key, plus a placement element on product pages.

#### Scenario: Installed and mapped
- **WHEN** a product page contains the script tag and a placement element for a product in the shop's manifest
- **THEN** a fit button is rendered inside the placement element

### Requirement: Shop manifest
Each shop SHALL have a manifest that maps product identifiers to garment ids and shop size labels to garment sizes, with each product's price, currency and product page link. The manifest SHALL also list allowed page origins and display settings.

#### Scenario: Size label mapping
- **WHEN** the manifest maps shop label "Medium" to garment size M and the viewer recommends M
- **THEN** the shopper sees "Medium"

#### Scenario: Origin not allowed
- **WHEN** the script runs on a page whose origin is not in the manifest's allowed origins
- **THEN** nothing is rendered

### Requirement: Button only for mapped products
The loader SHALL render the button only when the placement's product identifier is in the shop's manifest, and SHALL re-evaluate when the page replaces placement elements.

#### Scenario: Unmapped product
- **WHEN** the placement's product identifier is not in the manifest
- **THEN** nothing is rendered and no error is logged without debug mode

#### Scenario: Theme re-render
- **WHEN** the theme replaces the placement element after a variant change
- **THEN** the button is rendered again in the new element

### Requirement: Lightweight, non-blocking loading
The loader SHALL be at most 10 KB compressed, SHALL load asynchronously, and SHALL NOT fetch the viewer or 3D assets before the shopper interacts with the button.

#### Scenario: Page load
- **WHEN** a mapped product page loads and the shopper does not interact
- **THEN** only the loader and the manifest are requested from simiq

#### Scenario: Size budget
- **WHEN** a build produces a loader larger than 10 KB compressed
- **THEN** the build check fails

### Requirement: No layout shift
Rendering the button SHALL NOT shift page content when the shop uses the documented placeholder style.

#### Scenario: Demo page
- **WHEN** the demo product page is measured with Lighthouse
- **THEN** the simiq button contributes no layout shift

### Requirement: Failure isolation
No failure SHALL break the host page. The loader SHALL NOT throw uncaught errors. It SHALL give up on the manifest after 3 seconds and then render nothing, or the configured size-chart link.

#### Scenario: CDN unreachable
- **WHEN** the manifest cannot be loaded within 3 seconds
- **THEN** no button is rendered (or the fallback link if configured) and no uncaught error occurs

#### Scenario: Viewer fails inside the modal
- **WHEN** the viewer does not become ready after the modal opens
- **THEN** the modal shows an error with a close button and, if configured, the size-chart link

### Requirement: Style isolation and theming
The button SHALL be unaffected by host-page styles, and SHALL expose documented variables for accent color, text color, font and corner radius.

#### Scenario: Hostile host CSS
- **WHEN** the host page has a global rule hiding all buttons
- **THEN** the simiq button stays visible

#### Scenario: Theming
- **WHEN** the shop sets `--simiq-accent`
- **THEN** the button uses that color

### Requirement: Accessible modal with the viewer
Clicking the button SHALL open an accessible modal containing the viewer for the mapped garment, in the shop's language. Closing it SHALL return focus to the button.

#### Scenario: Open and close
- **WHEN** the shopper opens the modal and presses Escape
- **THEN** the modal closes and focus returns to the button

### Requirement: Size selection handoff
When the shopper chooses a size in the viewer, the loader SHALL emit a host-page event with the product identifier and the shop's size label, and SHALL call the configured callback if one exists.

#### Scenario: Shop preselects variant
- **WHEN** the shopper chooses "Medium" in the viewer on the demo shop
- **THEN** a `simiq:select-size` event with product and "Medium" is dispatched and the demo shop selects Medium

### Requirement: Trusted messaging only
The loader SHALL accept messages only from the viewer origin with the expected protocol version, and SHALL ignore all others.

#### Scenario: Forged message
- **WHEN** another frame posts a `select-size` message
- **THEN** the loader ignores it and emits no event

### Requirement: Versioned releases
The loader SHALL be published at a moving major-version URL and at immutable exact-version URLs with published integrity hashes.

#### Scenario: Pinned release
- **WHEN** a shop includes an exact-version URL with its published integrity hash
- **THEN** the loader loads, and a modified file would be refused by the browser

### Requirement: Integration guide
The project SHALL publish an integration guide covering the snippet, placeholder style, product identifiers, the size-selection event and the required CSP entries. The guide SHALL be verified on the demo shop.

#### Scenario: Guide on a blank page
- **WHEN** a developer follows the guide on a blank HTML page with a mapped product
- **THEN** a working fit button appears
