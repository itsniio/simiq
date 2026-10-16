# Proposal: cloth-sim-spike

## Why

The fit engine compares body girths with garment points of measure (README R1) and needs CLO only for pictures. With real fabric data from brands, a cloth simulation of our own could give strain and relative pressure over the whole garment surface, not just five girths, and could later run without a CLO licence and, eventually, in the browser. Before building on it we need evidence: a one-week spike (to Fri 23 Oct 2026) that shows whether our simulation reproduces CLO on the same bodies and garment. Demo day (20 Nov) stays on the CLO videos and the current engine.

## What Changes

- A cloth simulation in `engine/` that drapes a sewn garment on an Anny body and follows the body through shape and pose changes (standing, hoods, drops), offline in Python on NVIDIA Warp.
- The garment's rest state comes from the 3D garment mesh and its UV layout in millimetres (the flat pattern), with seams welded from the draped geometry. DXF patterns and sewing come later, after the spike.
- Anisotropic fabric behaviour: course and wale follow the fabric's measured stretch curves (`garment-model`), including CLO's weft shrinkage for the comparison.
- A surface strain field (course and wale strain per triangle), relative pressure per triangle, and per-zone summaries in the fit engine's zones.
- A comparison against CLO on 4 bodies × 3 poses × 3 sizes of the RenderHub demo jersey, with a go/no-go report.
- If the spike passes, revising R1 and feeding the fit engine from the simulation is a separate change with its own grill; nothing in this change alters the recommendation.

Out of scope: WebGPU port, DXF import and automatic sewing, multi-layer garments, absolute pressure values, using the simulation in the recommendation or the viewer.

## Capabilities

### New Capabilities

- `cloth-simulation`: draping a garment with a measured fabric on a posed body, and the strain and relative-pressure fields and zone summaries derived from it.

### Modified Capabilities

None. `fit-engine` (in `fit-engine-poc`) is unchanged until a follow-up change revises R1.

## Impact

- New modules in `engine/` (garment mesh and rest state, drape solver, surface strain) and a spike script; `warp-lang` (Apache-2.0, already installed as Anny's dependency) becomes a direct dependency.
- Builds on `fit-engine-poc` body fitting and poses, which today live on branch `rp-anny`, not yet in `master`.
- Garment geometry exported from CLO is a licensed asset: it stays on the founder's machine (outside the repository, like `data/private/`); only renders and aggregate numbers are committed.
- Needs CLO (founder's licence) for the reference exports; no CLO code or binaries are used or inspected.
