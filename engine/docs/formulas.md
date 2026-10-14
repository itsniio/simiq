# Formulas

Every formula in `engine/` with its derivation and the test that checks it with hand-computed numbers (CLAUDE.md, "Understanding is the bar").

## Body fit (task 3.4, `body.py`)

### Standing height

Anny works in metres with z up. In the rest pose the body stands upright, so its height is the vertical extent of the mesh:

    height_cm = (max z − min z) × 100

The top of the head is the highest vertex and the sole the lowest; the A-pose arms stay below the head.

Test: a unit cube is 1 m tall → 100 cm (`test_height_is_the_vertical_extent_in_cm`).

### Mass from volume

For a closed triangle mesh, the divergence theorem turns the volume integral into a sum over faces. Each face (a, b, c) and the origin span a tetrahedron with signed volume

    V_face = a · (b × c) / 6

Faces pointing away from the origin add volume, faces pointing towards it subtract, so the sum is the enclosed volume whatever the origin. The sign depends on whether the faces are wound outward or inward, so we take the absolute value. Then

    mass_kg = |Σ V_face| [m³] × 1000 [L/m³] × BODY_DENSITY_KG_PER_L

`BODY_DENSITY_KG_PER_L` = 1.03, the starting value of design D2; it is retuned against study participants only by its own PR with before/after numbers.

Tests: a unit cube is 1 m³ = 1000 L → 1000 × 1.03 = 1030 kg, with either face winding (`test_mass_is_volume_times_density`, `test_mass_does_not_depend_on_face_orientation`).

Anny's eyes are closed meshes inside the head and are counted too; they add about 15 mL, under 0.03 % of an adult's volume.

### Age

Anny's age parameter is not linear in years. Anny ships its own calibration (`anny/data/shape_calibration/boys.pth` and `girls.pth`, the same anchors in both):

| Years | 0 | 1 | 4 | 11 | 16 | 18 | 64 | 110 |
|---|---|---|---|---|---|---|---|---|
| Anny age | 0 | 0.05 | 0.215 | 0.415 | 0.67 | 0.77 | 0.83 | 1 |

`anny_age(years)` interpolates linearly between the anchors. Without an age the body is built for `DEFAULT_AGE` = 35:

    anny_age(35) = 0.77 + (35 − 18) / (64 − 18) × (0.83 − 0.77) = 0.79217

Tests: the anchors 16, 18 and 64, and 35 and 90 by the formula above (`test_anny_age_interpolates_annys_calibration`).

### Fitting height and weight

Sex, age, muscle and proportions are fixed by the inputs (muscle and proportions at 0.5 until task 3.3 maps the body types). Two Anny parameters remain, `height` h and `weight` w, both in [0, 1], and two targets, the given height H and weight M:

    r(h, w) = [height_cm(mesh(h, w)) − H,  mass_kg(mesh(h, w)) − M]

Anny is differentiable, so PyTorch gives the 2 × 2 Jacobian J = ∂r/∂(h, w). With as many unknowns as targets, a Gauss-Newton step is the Newton step

    (h, w) ← clamp((h, w) − clamp(J⁻¹ r, ±FIT_MAX_PARAMETER_STEP), 0, 1)

starting from (0.5, 0.5). The step limit keeps an early, badly linearised step from jumping across the parameter range; the clamp keeps the parameters where Anny interpolates instead of extrapolating. The fit stops when the height is within `FIT_STOP_HEIGHT_CM` = 0.05 cm and the mass within `FIT_STOP_MASS_SHARE` = 0.2 % of the target, ten times tighter than the spec's 0.5 cm and 2 %. If it has not stopped after `FIT_MAX_STEPS` = 25 steps, no Anny body in range reaches the inputs and the fit raises an error with the closest height and mass it found.

Tests: height 172 cm and weight 68 kg land within 171.5–172.5 cm and 66.64–69.36 kg; 20 random valid inputs (seeded) land within 0.5 cm and 2 % (`test_body_fit.py`).
