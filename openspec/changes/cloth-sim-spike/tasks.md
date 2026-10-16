# Tasks

Time box: Fri 16 – Fri 23 Oct 2026, then go/no-go. Builds on the engine on branch `rp-anny`. Every formula lands with its derivation in `engine/docs/formulas.md` and a test with hand-computed numbers. Issue numbers are added when the issues are created.

## 1. Reference data from CLO

- [x] 1.1 Export from CLO, by script, the jersey draped on all 4 bodies × 3 poses × 3 sizes (course shrinkage scaled by 68.5 / 72 / 75.5 % of 72 %), plus the starting drape on 178/75 `standing`, outside the repository: the garment mesh with UVs once and every case's vertex positions (CLO writes frames only into the FBX cloth cache); verify 37 cases with one mesh and a manifest listing body, pose, size, frame and settling for each
- [x] 1.2 Add `.gitignore` guards for the spike's garment meshes, CLO projects and point caches; verify `git status` shows none of the exported files

## 2. Garment rest state

- [ ] 2.1 Implement `garment_mesh.py`: load a GLB/OBJ with UVs, split pattern pieces, weld coinciding vertices (≤ 0.5 mm), build per-triangle rest frames from UV in mm × shrinkage; verify the rest-length, seam and missing-UV scenarios with hand-made meshes
- [ ] 2.2 Load the CLO starting drape; verify the welded mesh is one connected garment and print piece count, vertex count and seam length against the DXF

## 3. Strain and pressure fields

- [ ] 3.1 Implement per-triangle course and wale strain from the deformation gradient, with the derivation in `formulas.md`; verify the undeformed and uniform-stretch scenarios by hand-computed triangles
- [ ] 3.2 Implement zone means on the landmark bands and score the CLO exports from 1.1; verify that on CLO's drapes 176/88 has a higher strain than 180/64 in every girth zone in every pose, as the CLO videos show
- [ ] 3.3 Implement relative pressure from tension and curvature (D4); verify the cylinder scenario (P = T / r) and that M presses more than L on 178/75 `standing`

## 4. Drape solver

- [ ] 4.1 Implement XPBD stretch (course, wale, shear) with compliance from the fabric curve, and gravity; verify the hanging-strip scenario at 20 % strain within 1 percentage point
- [ ] 4.2 Add bending and body collision with thickness and friction; verify a garment tube on a cylinder settles at 14.3 % course strain with no vertex inside the surface
- [ ] 4.3 Drive the body through the point-cache sequence (shared with `jersey-demo/scripts/clo_*.py`); verify the no-penetration and determinism scenarios on 178/75 → 176/88 `hoods`
- [ ] 4.4 Time one garment on one body on the Mac and choose the particle distance (design open question); verify and record the timing in the report

## 5. Comparison and decision

- [ ] 5.1 Fit the course and wale stiffness scales on 178/75 `standing` M against CLO; verify the fitted case agrees within 1 percentage point per zone
- [ ] 5.2 Run all 35 held-out cases with `engine/scripts/cloth_spike.py` and write `engine/docs/cloth-sim-spike.md` (per-zone table, size ranking, timing, renders side by side); verify the report states pass or fail per the acceptance scenarios
- [ ] 5.3 Founders read the report and sign go or no-go in it; on go, open the follow-up change that revises R1

## Workflow follow-up

- Create GitHub issues for these tasks (text 1:1) and add their numbers here; label `part:7`, `spike`.
- One PR per group (1–5); group 3 can merge before group 4.
