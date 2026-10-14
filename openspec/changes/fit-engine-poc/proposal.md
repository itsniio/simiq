# Proposal: fit-engine-poc

## Why

simiq's value is a size recommendation that holds in the riding position, and published studies show that 3D cloth simulation does not predict real pressure on cycling and compression wear. Before building UI or integrations we must prove that a strain-based fit engine on a parametric body predicts the size riders actually choose better than the brand's size chart. Demo day is 20 Nov 2026 and the fit study needs a working engine by early November.

## What Changes

- New Python package (`engine/`) that turns shopper inputs (height, weight, age, sex, optional chest/waist/hip girths) into a 3D body using the Anny body model (Apache-2.0 code, CC0 assets).
- Pose presets (`standing`, `hoods`, `drops`) and pose-dependent body measurements: girths, girth profiles along the upper arm and thigh, back length, vertical trunk girth.
- Garment data contract for cycling jerseys and bib shorts: per-size points of measure, fit zones, fabric stretch curves and the brand's size chart.
- Per-zone fit computation (strain, length margin, relative pressure) and a size recommendation with confidence, an alternative size and an explanation.
- Fit-study tooling: study data format, calibration of fit ranges, accuracy evaluation against the brand size chart.
- First data: one jersey and one pair of bib shorts bought by the team and measured in 3–4 sizes.

Out of scope here: HTTP API and latency work, 3D viewer (both in `tryon-viewer-mvp`), photo input, cloth simulation, absolute pressure values.

## Capabilities

### New Capabilities

- `body-profile`: turning shopper inputs into a posed 3D body and pose-dependent body measurements, with input validation and measurement uncertainty.
- `garment-model`: the data contract for digitized garments: sizes, points of measure, fit zones, fabrics with stretch curves, size charts and provenance.
- `fit-engine`: per-zone fit of a garment size on a body in a pose, and the size recommendation with confidence and explanation.
- `fit-calibration`: fit-study data rules, calibration of fit ranges and evaluation of recommendation accuracy against a baseline.

### Modified Capabilities

None.

## Impact

- New code: `engine/` (Python 3.12, uv), versioned non-personal data in `data/garments/`, `data/fabrics/`, `data/poses/`, `data/fit-ranges/`; `data/private/` is gitignored for study data.
- New dependencies: Anny (PyTorch), numpy, pydantic, mesh utilities. SMPL-family models and assets are excluded because their licenses are non-commercial.
- `tryon-viewer-mvp` builds its API and precompute on this package.
- Fit-study measurements are personal data and possibly health-related; they never enter git.
- Physical items: garments in 3–4 sizes, plus one extra garment or fabric swatch to cut for stretch tests.
