# Proposal

## Why

Every fit result starts from a body. The shopper gives gender, height, weight and a silhouette, maybe a few tape measurements, and the system must turn that into a posed 3D body whose chest, torso length, shoulders and arms are close enough to reality that a jersey simulated on it says something true. Nobody on the team has built one, and the cheapest way to learn whether a free, scan-free body model is good enough is to build the pipeline on it over the winter and score it against the fit lab's tape measurements in spring 2027 (see the `fit-lab-protocol` change).

## What Changes

- Build a body pipeline on Anny (Apache 2.0): minimal inputs to a body mesh, optional tape measurements refining it, a virtual tape that measures the mesh the way the lab measures riders, and posing into standing and riding postures.
- Define the body contract the garment simulation consumes: fixed-topology mesh, units, orientation, named poses, and the shape parameters that identify a body in the precompute grid.
- Produce the body table for the fit lab evaluation: predicted versus tape measurements from minimal inputs, and from minimal plus optional inputs, with tape noise alongside.
- Decide, from that table, whether Anny is sufficient or whether the SMPL commercial license through Meshcapade is required for the shopper-facing product.

Out of scope: photo-based body capture, the shopper-facing input UI, and any browser rendering beyond a check that the mesh loads in three.js.

## Capabilities

### New Capabilities

- `body-avatar`: producing a posed, fixed-topology 3D body from shopper inputs (gender, height, weight, silhouette picks, optional tape measurements), measuring that body with a virtual tape, expressing how uncertain each measurement is given the inputs provided, and exposing the shape parameters and named poses the fit simulation depends on.

### Modified Capabilities

None.

## Impact

- New dependency: Anny (Python package) and its Blender-compatible mesh export. Fallback dependency, if the evaluation demands it: SMPL via a Meshcapade commercial license (published tiers start around 2,000 EUR per year) or their measurements-to-avatar API.
- Consumed by the `garment-sim-spike` change, which needs the body contract before it can dress a body.
- Scored by the `fit-accuracy-evaluation` capability declared in `fit-lab-protocol`.
- Team learning: Python, mesh basics, Anny's parameter space. First milestone of the winter learning path.
