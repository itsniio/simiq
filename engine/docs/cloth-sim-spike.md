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
