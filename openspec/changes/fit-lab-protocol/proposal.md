# Proposal

## Why

The product is a 3D fit visualizer for tight technical apparel (cycling jerseys first), sold to brands and embedded on their product pages. Its entire value rests on one claim: that a heatmap and size verdict computed for a shopper's body is more right than the brand's size chart. Nobody has measured whether that claim holds, and a confident wrong heatmap is worse than no widget at all.

The fit lab is the cheapest way to find out. One or two sessions with a cycling club produce ground-truth data (real bodies, real jerseys, real riding posture) that every later software spike is scored against. It costs a few thousand euros instead of a year of building. Riders are available at the start of the cycling season (spring 2027), so the body and garment software spikes run over the winter and the lab becomes the gate on whether to build the shopper-facing widget.

## What Changes

- Define a repeatable fit lab protocol: rider recruitment, stations, measurement procedure, try-on and on-bike photo capture, rider feel charts, and data handling.
- Produce the first ground-truth dataset: per rider, minimal inputs, self-picked silhouettes, full tape measurements, and per rider x garment size x pose, a feel chart, dot-grid photos, and a buy decision.
- Establish the size chart baseline: for every rider, the size the brand's chart would have picked, so the system has a number to beat.
- Define how the body model and the fit simulation are evaluated against the dataset: body measurement error, zone agreement between predicted and reported tightness, and size verdict accuracy versus the chart and versus the rider's own choice.
- Use the existing Figma onboarding flow (gender, height, weight, silhouettes) as the self-report form, so the lab also tests whether riders pick silhouettes that match their tape measurements.

Out of scope: the body model implementation, the garment digitization pipeline, the simulation solver, the shopper widget, and any brand integration. Those are separate changes that consume this dataset.

## Capabilities

### New Capabilities

- `fit-ground-truth-dataset`: the structure and content of the data the system holds about real riders in real garments: rider record (pseudonymous ID, minimal inputs, silhouette picks, tape measurements), garment record (model, sizes, rest-state grid photos, fabric), and observation records (rider x size x pose: feel chart per zone, buy decision, photos with scale reference). Includes consent and pseudonymization rules.
- `fit-accuracy-evaluation`: how a body model and a fit simulation are scored against the dataset: body measurement error from minimal versus full inputs, per-zone agreement between predicted and reported tightness in each pose, and size verdict accuracy compared with the brand size chart baseline and with the rider's chosen size.

### Modified Capabilities

None. The project has no existing specs.

## Impact

- No code is affected yet. The first consumers are the body model spike and the garment simulation spike, which will read this dataset and report the evaluation metrics.
- New external dependencies: a cycling club willing to supply 20 to 30 riders, one race-fit jersey purchased in every size (Isadore as the default, since it is the intended pilot brand), optionally a second jersey, and basic lab equipment (tapes, scale, tripods, fabric markers, borrowed trainers).
- Personal data: body measurements and photographs of identifiable people are collected. GDPR consent, pseudonymous IDs, and separate storage of the ID-to-name mapping are part of the protocol, not an afterthought.
- Budget on the order of 2,000 to 2,500 EUR, dominated by garments.
