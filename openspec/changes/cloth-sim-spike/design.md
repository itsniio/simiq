# Design: cloth-sim-spike

## Context

See proposal.md for why. What exists (branch `rp-anny`): Anny bodies fitted to height and weight, pose presets, landmarks and zone templates in `engine/`; CLO runs of the RenderHub jersey on four bodies in three poses, driven by point caches generated from the same bodies (`jersey-demo/scripts/clo_*.py`). CLO's Python API exports the draped garment's frames only through the FBX cloth cache (OBJ and GLB exports ignore the animation frame), with the mesh and UV layout alongside; it can change each piece's simulation shrinkage, but does not expose its strain numbers. The jersey's CLO project uses weft shrinkage 72 %, so its sizes can be emulated by changing that one value. The founder's Mac has no CUDA; Warp runs on its CPU.

## Goals / Non-Goals

**Goals:** a drape solver good enough to match CLO's strain within the spec's tolerance on held-out cases; one shared strain metric for our drape and CLO's; a go/no-go report by 23 Oct.

**Non-Goals:** arranging and sewing flat pieces (we start from CLO's draped garment), self-collision quality beyond what a single-layer tight jersey needs, rendering, speed beyond the 60 s budget.

## Decisions

### D1. Start from a draped garment, not from flat pieces
The solver's first state is CLO's drape of the jersey on Anny 178/75 standing; seams are welded where vertices of different pieces coincide (≤ 0.5 mm), and each triangle's rest shape is its UV triangle in mm, scaled by shrinkage (course ×0.72 for the jersey). From there the body follows the same point-cache sequence that drove CLO (morph between bodies, then pose).
*Alternative:* arrange DXF pieces around the body and sew them, as CLO does. Weeks of work and a different source of error; it comes after the spike (founder ruling 4).

### D2. XPBD on triangles in Warp
Extended position-based dynamics with per-triangle constraints: anisotropic stretch measured in the triangle's rest frame (course = pattern u, wale = pattern v, shear separately), dihedral bending with a small fixed stiffness, gravity, and body collision as a signed-distance query against the posed body mesh with a 2 mm thickness and Coulomb friction. Stretch compliance per direction follows the fabric curve's local slope at the current strain (piecewise linear, as in `fabric.py`).
*Alternatives:* mass-spring (isotropic, poor control of course vs wale); implicit FEM (more accurate, slower and much more code); NVIDIA Newton (newer API, same Warp underneath, more to learn in a week). XPBD is the standard for real-time cloth and maps to WebGPU later (founder ruling 2).

### D3. One strain metric for both drapes
For each triangle the deformation gradient F maps its UV rest triangle to 3D; course strain = |F·u| − 1, wale strain = |F·v| − 1, with u and v the pattern axes. Zones are triangle sets chosen on the standing body with the same landmark bands as `jersey-demo/scripts/heatmap.py`; a zone's value is the area-weighted mean course strain (wale for the length zone). The metric runs on any draped mesh with UVs, so CLO's exports are scored exactly like ours, and CLO's colour map is never read.

### D4. Relative pressure from tension and curvature
Per triangle, pressure p = T_c·κ_c + T_w·κ_w (Laplace's law on a surface), with T from the fabric curve at the triangle's strain and κ the body's normal curvature along the garment's course and wale directions at the nearest body point. Reported relative to the highest value among the sizes of the same garment, as the fit engine does.

### D5. Sizes by shrinkage, fitted on one case
S, M, L are the jersey with course shrinkage 68.5 %, 72 % and 75.5 % (≈ ±4 cm chest), set identically in CLO and in our rest state. Two stiffness scales (course, wale) are fitted by least squares on 178/75 `standing` M against CLO; the other 35 cases are held out. CLO's fabric is "FABRIC 13 / Unknown", so its stiffness cannot be copied.

### Program design

Flat modules in `engine/src/simiq_fit/`, named for what they compute:

```
garment_mesh.py   load OBJ with UVs → pieces, welded vertices, rest frames (u, v in mm × shrinkage)
drape.py          XPBD step and run(sequence) on Warp: stretch, shear, bend, collide, gravity → frames
surface_strain.py per-triangle course/wale strain, relative pressure (D4), zone means (D3)
```

```
mesh   = load_garment(garment-uv.obj, shrinkage=per piece course %, wale 100 %)
bodies = body_sequence(start=(178,75,'standing'), to=(h,w,pose))      # reuses clo_* logic
frames = drape(mesh, fabric, bodies, substeps, iterations)            # last frame = settled drape
ours   = zone_strain(mesh, frames[-1], zones)
clo    = zone_strain(mesh, cases[pose-size][body], zones)            # same function, CLO's positions
report(ours vs clo for 36 cases, timing)
```

`engine/scripts/cloth_spike.py` runs the matrix and writes `engine/docs/cloth-sim-spike.md`; the XPBD constraint derivations go in `engine/docs/formulas.md`. CLO-side export scripts stay with the demo scripts.

## Risks / Trade-offs

- [Warp on the Mac's CPU is too slow for 60 s] → coarser garment mesh (CLO particle distance 10 mm → 15 mm) and fewer substeps; report timing honestly; GPU timing is a separate question.
- [Tight jersey penetrates the body or jitters] → collision thickness and more iterations near the body; the no-penetration scenario catches it.
- [CLO's own drape differs from reality] → the spike only proves agreement with CLO; real fabric curves and try-ons decide accuracy later.
- [Fitting stiffness on one case overfits] → 35 held-out cases, including other bodies and poses.
- [Licensed geometry leaks into git] → working folder outside the repository; `.gitignore` guards for garment meshes, CLO projects and point caches.

## Open Questions

- Particle distance for the spike mesh (10 or 15 mm), decided by the first timing run.
