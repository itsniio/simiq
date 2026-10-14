# Proposal: tryon-viewer-mvp

## Why

The fit engine is a Python library; nobody outside the team can use it. Shoppers and brands trust what they can see, and demo day (20 Nov 2026) needs a live product: a fast API and a viewer where a shopper enters a few numbers and sees the recommended size and where the garment is tight or loose in the riding position. The viewer must work both as a shareable link (team-kit path: send it to club members) and inside an e-shop modal (D2C path), so the first-brand decision does not block this work.

## What Changes

- Fit API (FastAPI) that serves recommendations from a precomputed surrogate of the body pipeline, so a request never runs the body model.
- Offline precompute: surrogate measurement models, a grid of body meshes (glTF with pose animations and per-vertex fit-zone masks) and a garment bundle published to the CDN.
- Viewer web app (TypeScript): body inputs with consent, recommendation with confidence and per-zone explanations, 3D body in the riding pose with zones colored by fit, switching sizes and poses.
- Standalone URL mode and embedded (iframe) mode with a versioned postMessage protocol.
- Staging and demo deployments, plus an offline fallback for demo day.

## Capabilities

### New Capabilities

- `fit-api`: the HTTP contract for recommendations and garment information, its latency, privacy and access rules.
- `tryon-viewer`: the shopper-facing experience: inputs and consent, recommendation, 3D fit view, comparison, degradation, standalone and embedded modes.

### Modified Capabilities

None.

## Impact

- New code: `api/` (Python, FastAPI), `web/viewer/` (TypeScript, Preact, Three.js), precompute commands in `engine/`.
- New infrastructure: object storage + CDN for static assets, one container host for the API, staging and production environments.
- Depends on `fit-engine-poc` (body-profile, garment-model, fit-engine). `shop-embed-mvp` embeds this viewer.
- Body data passes through the API but is not stored or logged.
