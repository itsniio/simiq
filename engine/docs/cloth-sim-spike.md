# Cloth-sim spike

Working notes and, at the end of the time box, the go/no-go report for `openspec/changes/cloth-sim-spike`.

## Reference data from CLO (tasks 1.1, 1.2), 16 Oct 2026

The RenderHub demo jersey draped by CLO on four Anny bodies in three poses and three sizes: 36 cases plus the starting drape (178/75 `standing` M, frame 0). Nothing of it is in git; it lives in `$SIMIQ_SPIKE_DIR` (default `~/Documents/SIMIQ/mens cycling jersey-green printed/simiq-anny/spike/`):

- `cases/garment-uv.obj`: the garment mesh with its UV layout (88,369 vertices, 149,894 faces), identical in all nine runs;
- `cases/<pose>-<size>.npz`: garment vertex positions in mm, CLO frame (Y up), one array per body;
- `cases/manifest.json`: per case the pose, body, size, source frame and how much the garment still moved over the 10 frames before it.

How they were made: the three CLO projects of the demo (`simiq-anny-{standing,body,drops}-sequence.zprj`) already hold the M animation. For S and L, `jersey-demo/scripts/clo_spike_export.py` scales every pattern piece's course (width) shrinkage by 68.5/72 or 75.5/72, the animation is recorded again, and the FBX export writes the mesh and a Maya cache of all frames; `engine/scripts/clo_cache_extract.py` keeps the mid-hold frame of each body.

Found on the way:

- CLO's OBJ/GLB export ignores the animation frame (it always writes the garment's base state); only the FBX export with a cloth cache carries the frames. The OBJ it writes alongside is frame 0, in the same vertex order as the cache.
- Course shrinkage is 75 % on one piece and 72 % on the other fourteen, not 72 % everywhere. Sizes scale each piece's own value.
- On a tight jersey the sizes barely change the garment's shape: chest girths of S, M and L on the same body agree within 0.1 cm in most bands, because the fabric lies on the body. The size shows up in strain (same length, shorter rest length), so the comparison has to be made on strain, not on positions.
- Settling: the largest movement over 10 frames before a case is 5–11 mm for every M, standing and hoods run (one vertex; the share above 5 mm was not recorded for those). The first recording of drops S had not settled (up to 81 mm) and was recorded again: now the 99th percentile is 1–3 mm. Drops L moves up to 31 mm at the collar and shoulders on 0.3–3 % of vertices, 99th percentile 3–10 mm; if group 5 shows it affects the shoulder zones, it is recorded again.
- CLO shows a trial-licence notice: the subscription renews on 29 Oct 2026.

## Garment rest state (tasks 2.1, 2.2), 16 Oct 2026

`simiq_fit/garment_mesh.py` reads CLO's OBJ, keeps the fabric pieces (material `FABRIC_13`; zipper, topstitch and trim blocks are left out), welds seams and gives every triangle its unstretched shape in the flat pattern.

- **UV is not mm.** CLO's UV layout is a non-square texture space: 1 unit of u is 538.01 mm and 1 unit of v is 763.79 mm for this export. Fitted per piece from the DXF (outline size across and along the grain line over the UV size): spread 0.016 % and 0.004 % over the 15 pieces. Stored in `cases/manifest.json` (`uv_mm_per_unit`) with how it was found; `scripts/cloth_spike.py calibrate-uv` recomputes it.
- **Grain along v.** CLO lays every piece out with its grain line along v, whatever the DXF orientation (six pieces are turned 90° in UV). So u is the course (where the 72 % width shrinkage acts) and v the wale.
- **Welding.** 80 % of the pieces' outline vertices lie within 0.01 mm of another piece's in CLO's drape; the rest are free edges (hem, cuffs, neckline, zipper). Pairs within 0.5 mm are joined nearest first, and never so that one seam vertex holds two vertices of the same piece: a binding folded over an edge would otherwise collapse onto itself (the first version did that to 113 vertices and left 35 degenerate triangles).
- **Check on the starting drape** (`scripts/cloth_spike.py mesh`): 15 pieces, 38,775 triangles, 20,664 vertices welded to 19,673, one connected garment, no degenerate triangle. The pieces' outlines measured on the UV rest shapes total 1694.5 cm against 1694.6 cm of DXF cut lines; 564 cm of seams are sewn.

## Strain and pressure fields (tasks 3.1–3.3), 16 Oct 2026

`simiq_fit/surface_strain.py` measures any draped garment with a pattern rest state the same way: per-triangle course and wale strain from the deformation gradient, the area-weighted zone mean, and pressure p = T_c·κ_c + T_w·κ_w with κ from the body under the garment (derivations and hand-computed tests in `formulas.md`). `scripts/cloth_spike.py zones | strain | pressure` run it on CLO's 36 cases; every case is welded on the starting drape so all share one mesh, one set of zone triangles and one rest state per size.

**Zones** (`zones`, written to `$SIMIQ_SPIKE_DIR/zones.npz`, outside git since they index the licensed mesh). The body vertex sets of `jersey-demo/scripts/heatmap.py` on 178/75 `standing` (chest and waist: ±25 mm about the fit engine's section planes, square to the torso; hem: ±25 mm about the hip ring's height; sleeve opening: 10–14 cm from each armpit, lateral; back length: a 6 cm strip down the spine from C7 to the back of the hip). A garment triangle is in a zone when the body vertex nearest its centre on the starting drape is in the set and lies within 30 mm. Result: chest 2021 triangles (444 cm²), waist 2921 (647 cm²), hem 619 (150 cm²), sleeve opening 2684 (617 cm²), back length 2441 (537 cm²).

- The hem band sits at the jersey's lower edge and catches mostly the longer back (median z −166 mm, with the back at about −190 mm and the front at +80 mm): it is a back-hem zone, not a full girth.
- The sleeve band is a spherical shell round the armpit: 55 % of it lies above the armpit, on the shoulder cap, not at the sleeve's opening.

**Alignment check.** The point caches that drove CLO give the posed body of every case (`anny-{standing,hoods-body,drops-standing}-sequence.pc2` at the frames of `clo_cache_extract.FRAMES`); the standing 178/75 frame equals the A-pose OBJ to 0.0 mm. Garment vertices sit 3.4 / 4.6 / 9.6 mm (p10 / median / p90) off the body along its normal on the starting drape, with no systematic offset (median offset vector under 1.2 mm): CLO's collision distance plus some loose fabric, as expected.

### Strain on CLO's drapes (task 3.2)

Zone mean course strain (wale for back length), size M; all 36 cases in the run log (`strain`, 5.7 s):

| pose | body | chest | waist | hem | sleeve opening | back length |
|---|---|---|---|---|---|---|
| standing | 178/75 | 8.6 % | 11.8 % | 26.0 % | 6.8 % | −0.8 % |
| standing | 180/64 | 6.2 % | 1.2 % | 20.6 % | 6.2 % | −0.1 % |
| standing | 176/88 | 13.8 % | 26.7 % | 31.8 % | 7.1 % | −0.6 % |
| standing | 192/82 | 11.8 % | 10.7 % | 29.6 % | 10.0 % | 2.1 % |
| hoods | 178/75 | 5.7 % | 15.6 % | 30.2 % | 2.3 % | 0.1 % |
| hoods | 180/64 | 4.6 % | 3.7 % | 23.9 % | 2.9 % | 0.6 % |
| hoods | 176/88 | 16.0 % | 29.7 % | 41.9 % | 1.1 % | 2.4 % |
| hoods | 192/82 | 9.0 % | 13.4 % | 32.3 % | 5.9 % | 3.3 % |
| drops | 178/75 | 5.2 % | 19.3 % | 38.8 % | 1.0 % | −1.3 % |
| drops | 180/64 | 3.1 % | 10.0 % | 35.0 % | 1.6 % | −0.6 % |
| drops | 176/88 | 17.0 % | 32.1 % | 50.2 % | −0.3 % | −0.4 % |
| drops | 192/82 | 7.1 % | 18.6 % | 42.6 % | 3.9 % | −0.5 % |

- **176/88 above 180/64:** holds in chest, waist and hem in every pose and size (27 of 27). It does **not** hold for the sleeve opening in 5 of the 9 posed pose × size runs (hoods S, M, L; drops M, L), e.g. hoods M 1.1 % against 2.9 %. Split at the armpit's height, the band's part on the arm is barely stretched on any body (180/64: 0.4–0.8 %) and compressed on 176/88 (−1.0 % standing, −3.4 % hoods, −3.2 % drops): the sleeve lies in folds under a heavy arm. Its part on the shoulder cap does rank 176/88 above 180/64 standing (12.3 against 10.0 %) but not in the poses. So the videos' claim holds for the torso, not for the sleeve; task 3.2 stays open until the founders decide whether the sleeve zone needs a different band (at the sleeve's own hem) or whether CLO's sleeve is right.
- **Sizes:** chest strain S > M > L on every body and pose except drops 176/88 (S 11.5 %, M 17.0 %, L 7.2 %). The drops-M runs also have the highest hem strain of the three sizes on every body (178/75: S 23.5 %, M 38.8 %, L 12.9 %) and less waist strain than L on 178/75 (19.3 against 20.2 %). Drops M is the demo's original recording, S and L were recorded by `clo_spike_export.py`; it looks like a different garment state rather than a size effect, and should be recorded again by the same script before group 5 uses it as reference.
- Back length strain is within ±3.3 %: the wale hardly stretches on this jersey, so the length zone is decided by how the garment rides, not by strain.

### Relative pressure (task 3.3)

The example knit's curves stand in for CLO's unknown FABRIC_13, so only the ranking of sizes is meaningful, never the Pascals. Chest on 178/75 `standing`: S 282 Pa, **M 196 Pa > L 118 Pa** (relative 1.00 / 0.70 / 0.42). In `standing` every girth zone of every body ranks S > M > L. M presses more than L in every girth zone, body and pose except drops (waist on all four bodies, sleeve opening on 178/75 and 180/64), the same drops-M recording as above. Up to 5 % of chest, waist and sleeve triangles are beyond the example curve's 50 % (no pressure), except the waist of drops 176/88 S (26 %); the hem has up to 23 %, on S and in the poses.

Taking κ from the garment's own surface instead of the body (tried first) let CLO's folds flip the sign of the curvature: hoods L chest came out at −17 Pa and sizes did not rank in the poses. With the body's κ the ranking holds wherever the strain ranking does.

Run times on the Mac: `zones` 16 s, `strain` 6 s for 36 cases, `pressure` 2 min (nearest body triangle by brute force, 38,775 × 27,420 per case).
