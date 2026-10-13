# Design

## Context

See proposal.md for motivation. Constraints:

- Team is two Rails developers and a designer, learning Python and 3D over the winter of 2026/27. No simulation or graphics background yet.
- Minimal shopper inputs were fixed earlier: gender, height, weight, a body silhouette pick (slim / regular / athletic), with per-limb silhouettes and tape measurements optional. Torso length is the most valuable optional field for jerseys.
- Anny is a parametric model driven by gender, age, height, weight and shape sliders, built from MakeHuman anthropometric knowledge rather than body scans, calibrated to WHO population statistics. Its SMPL-X-compatible topology is non-commercial; its native topology is Apache 2.0.
- The garment simulation (see `garment-sim-spike`) runs offline in Blender first, so the body must be exportable as a mesh Blender can collide against, and must have identical topology for every shopper so strain arrays can be blended across bodies.
- The fit lab in spring 2027 produces tape measurements for 20 to 30 riders plus their self-picked silhouettes; that is the only ground truth this spike is scored against.

## Goals / Non-Goals

**Goals:**

- Minimal inputs to a plausible body in under a second, optional inputs refining it.
- A virtual tape that reproduces the lab's measurement definitions on the mesh (circumferences by slicing, lengths between landmarks).
- Standing and riding poses as named, reproducible joint configurations.
- A body contract stable enough that the garment spike can build against it from December.
- An evaluation script that, given the lab's body table, prints error per measurement for each input level.

**Non-Goals:**

- Photo or video body capture.
- Face, hands, hair, or any rendering fidelity. The body is a collider and a measuring dummy.
- A final decision on Anny versus SMPL before the lab data exists.

## Decisions

### Anny first, SMPL as the scored fallback

Anny costs nothing, installs as a package, and is driven by exactly the inputs the shopper gives. SMPL is trained on real scans and models pose deformation better, which matters for the riding posture, but costs a yearly license. The lab's body table decides: if Anny's error on chest, torso length and shoulders from minimal inputs is within the tape noise floor plus what the fit verdict can tolerate, it stays. The evaluation script is written so a second model can be dropped in and scored on the same riders.

Alternative considered: Meshcapade's measurements-to-avatar API from day one. Rejected for the spike because it hides the parameter space the precompute grid is sampled in, and because learning the model is the point of the spike. Kept as the fastest fallback.

### Measurements drive shape parameters through a small optimisation

Given target measurements, find the shape parameters whose mesh, measured with the virtual tape, matches them. Height and weight set the prior; the silhouette pick biases the shape sliders; each optional tape measurement adds a term. This is a few-parameter least-squares fit and runs in milliseconds.

Alternative: a lookup table from inputs to parameters. Rejected; it cannot absorb optional inputs gracefully.

### Virtual tape mirrors the lab protocol exactly

Circumferences are the perimeter of the mesh sliced by a plane at a landmark height (chest at the fullest point, waist at the narrowest, upper arm at the fullest point). Lengths are geodesic or straight distances between landmark vertices (C7 to waist, C7 to hem line, acromion to acromion, acromion to wrist). Because topology is fixed, landmarks are vertex indices chosen once. The definitions are copied from the lab's measurement protocol so the two numbers are comparable.

### Uncertainty is reported per measurement, per input level

For each predicted measurement the pipeline reports an expected error band that depends on which inputs were given. Initially this is estimated by sampling: generate many bodies consistent with the given inputs and look at the spread of each measurement. After the lab it is replaced by the measured error. The shopper-facing result screen later uses this to nudge for the one optional field that most narrows the fit.

### Two named poses, defined as joint angles

`standing` (neutral, arms slightly forward as in the lab's arms-forward photo) and `riding` (hip flexion, spine curvature, shoulders protracted, arms reaching to a hoods position). Riding is parameterised by a single "aggressiveness" value in the spike, so a bike-fit-driven pose can replace it later without changing the contract.

### The body contract

Owned by this spike, consumed by the garment spike:

```
  body id            shape parameter vector (what the precompute grid samples)
  mesh               fixed topology, native Anny topology, triangles, metres,
                     Y up, facing +Z, origin between the feet, exported as glTF
                     and OBJ for Blender
  poses              standing, riding(aggressiveness), as posed mesh exports
  landmarks          named vertex indices used by the virtual tape
  measurements       the lab's list, predicted, with error bands
```

### Deliverables of the spike

1. Script: inputs to posed mesh files, with measurements and error bands printed.
2. A three.js page that loads the glTF and rotates it, to confirm the export path end to end.
3. Evaluation script that takes the lab's body table (rider id, inputs, silhouettes, tape measurements) and prints error per measurement for minimal and for minimal plus optional inputs, next to tape noise from the duplicate measurements.

## Risks / Trade-offs

- [Anny's artist-derived shapes misplace chest or torso length for athletic or very thin builds] → the lab over-represents those builds; the evaluation script scores SMPL on the same riders if the error is unacceptable.
- [Riding-pose deformation is wrong in ways standing measurements never reveal] → the garment spike's dot-grid photos on a bike are the check; if back lengthening is off, SMPL's learned pose correctives are the fix.
- [Silhouette picks do not predict shape well enough to deserve their place in the minimal inputs] → the lab stores picks next to tape; if picks add nothing, they become a decoration and chest becomes the first nudge.
- [Landmark vertex indices drift if the Anny version changes] → pin the version; store landmark definitions as named vertices in the repo with a test that checks their positions on a reference body.
- [Learning Python and meshes takes longer than the spike] → this spike is deliberately the smallest one and runs first; Blender work in the garment spike can start on a hand-exported body before this pipeline is finished.

## Open Questions

- Whether gender should be exposed as a shopper choice or inferred as a shape prior with a neutral option. Does not change the pipeline; changes the input screen.
- How many sampled bodies the precompute grid needs. Settled jointly with the garment spike once blending across neighbours can be tested.
