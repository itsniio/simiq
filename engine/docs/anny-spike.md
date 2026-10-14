# Anny spike: go / no-go

Task fit-engine-poc 2.3. **Status: draft, waiting for the first run.** The decision below is empty until the renders and metrics from `scripts/anny_spike.py` are in and the team has signed off.

## The question

Anny has no pose-corrective shapes, so its skin follows the bones by plain linear blend skinning. In deep hip flexion that can collapse the crotch, pinch the front of the hip or swell the buttocks, which is exactly where bib shorts sit (design D3). Can we measure bib-short zones on an Anny body in `hoods` and `drops`?

## Setup

- Model: `anny.Anny()` defaults: 104-bone `anny` rig, `anny` topology, `local-ref` poses (`simiq_fit.body.load_model`).
- Poses: `data/poses/standing.json` (rest A-pose), `hoods.json` (torso 45° from horizontal), `drops.json` (torso 30°). The left crank is at the top of the stroke, which closes the hip the most; the right is near the bottom.
- Bodies: male average, female average, male heavy, female tall and slim, male short and muscular (`BODIES` in the script).

## What counts as an artifact

| Check | Where | Flag |
|---|---|---|
| Skin edges compressed below 0.7× or stretched above 1.4× their rest length | hip-crotch and shoulder regions (vertices whose heaviest bone is the pelvis, hips or upper legs; the clavicles, shoulders or upper arms) | more than a few % of edges, or clusters visible in the renders |
| Folds, creases or self-intersection | hip close-ups | visible at the front of the hip, the crotch or under the buttocks |
| Whole-mesh volume change | all | more than a few % |
| Pose sanity | bone angles | torso and hip angles near the intended ones |

## Results

_To be filled from `anny-spike/metrics.md` and the renders `anny-spike/<body>.png`, `anny-spike/<body>-hips.png`._

## Decision

_Go, no-go, or a fallback from design D3:_

- _(a) measure on the standing body and apply pose deltas measured on the team;_
- _(b) add corrective vertex offsets for the hip region._

_Signed off by: …_
