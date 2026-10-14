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

### Fitting height, weight and muscle

Sex, age and proportions are fixed by the inputs (proportions at 0.5 until task 3.3 maps the body types). Three Anny parameters are fitted, all in [0, 1]: `height` h, `weight` w and `muscle` m, against the given height H and weight M and a prior on muscle, m₀ = `DEFAULT_MUSCLE` = 0.5 (task 3.3 will set m₀ per body type). The residuals, each divided by the size that counts as "close enough":

    r₁ = (height_cm(mesh) − H) / FIT_STOP_HEIGHT_CM
    r₂ = (mass_kg(mesh) − M) / (FIT_STOP_MASS_SHARE · M)
    r₃ = (m − m₀) / FIT_MUSCLE_PRIOR_SD

Why muscle: the first version fitted only h and w, and a 173.8 cm, 59.3 kg man (BMI 19.6) failed, because at muscle 0.5 Anny's lightest body of that height weighs 64.3 kg. Lowering muscle makes a lighter body of the same height. The prior keeps muscle at m₀ whenever weight alone can match the mass: then all three residuals can be zero, and that is the least-squares minimum. Only when w is at a bound does the mass residual pull m away from m₀; with `FIT_MUSCLE_PRIOR_SD` = 0.25 against a mass scale of 0.2 % of M, the mass wins by orders of magnitude.

Anny is differentiable, so PyTorch gives the 3 × 3 Jacobian J = ∂r/∂(h, w, m). Each step solves J Δ = r in the least-squares sense; a parameter sitting at a bound that Δ would push further out is frozen (its column zeroed) and the rest re-solved. Then

    (h, w, m) ← clamp((h, w, m) − clamp(Δ, ±FIT_MAX_PARAMETER_STEP), 0, 1)

starting from (0.5, 0.5, m₀). The step limit keeps an early, badly linearised step from jumping across the range; the clamp keeps the parameters where Anny interpolates rather than extrapolates. The fit stops when |r₁| < 1 and |r₂| < 1, that is height within 0.05 cm and mass within 0.2 %, ten times tighter than the spec's 0.5 cm and 2 %. After `FIT_MAX_STEPS` = 30 steps without stopping, no Anny body in range reaches the inputs and the fit raises an error with the closest height and mass.

Tests (`test_body_fit.py`): 172 cm and 68 kg land within 171.5–172.5 cm and 66.64–69.36 kg; 20 seeded random valid inputs land within 0.5 cm and 2 %; muscle stays at 0.5 for 180 cm, 75 kg; the 173.8 cm, 59.3 kg case is matched with muscle below 0.5.

## Tape measurements (tasks 4.2, 4.3, `tape.py`)

### Girth

A tape measure laid around a body part in a plane reads the length of the shortest closed loop that encloses the cross-section, which is the perimeter of the cross-section's **convex hull**: the tape spans concavities instead of following them (between the shoulder blades, under the buttocks).

1. **Plane section.** For a plane through point p with unit normal n, each vertex gets s = (v − p) · n. A mesh edge with s of opposite signs at its ends crosses the plane at v_a + t (v_b − v_a), with t = s_a / (s_a − s_b). A triangle with mixed signs has exactly two crossed edges and contributes one segment between them; segments that share a crossed edge chain into closed loops.
2. **The loop around the point.** A plane at chest height in the A-pose also cuts the arms. The loops are projected onto two unit vectors spanning the plane; the loop containing p (even-odd rule) is the one measured. If several contain p, the outermost (largest hull) is taken; if none does, the loop nearest to p.
3. **Convex hull perimeter** by Andrew's monotone chain.

Tests (`test_tape.py`), all within 1 mm:

| Shape | Hand-computed girth |
|---|---|
| Cylinder r = 0.15 m | 2π · 0.15 = 0.94248 m |
| Elliptic cylinder a = 0.15, b = 0.10 m | Ramanujan: π[3(a+b) − √((3a+b)(a+3b))] = π[0.75 − √0.2475] = 0.79327 m |
| 0.2 m square with a 0.05 × 0.05 m notch | outline 0.9 m; tape reads the square, 0.8 m |
| Cylinder r = 0.15 cut by a plane tilted 30° | ellipse with semi-axes 0.15 and 0.15 / cos 30° = 0.17321: 1.01669 m |
| Torso r = 0.15 between two arms r = 0.05, one plane | 0.94248 m around the torso point, 2π · 0.05 = 0.31416 m around an arm point |

A 512-sided polygon underestimates a circle's perimeter by 2πr (π/512)² / 6 ≈ 0.006 mm at r = 0.15 m, far inside the 1 mm tolerance.

### Limb profile

Upper-arm and thigh girths are measured on planes perpendicular to the bone axis from `start` to `end`, every `step` (`PROFILE_STEP_CM` = 2 cm in `measure.py`, task 4.3). A girth between two levels is linearly interpolated (`profile_at`); a distance outside the profile is an error rather than an extrapolation.

Test: a truncated cone whose radius falls linearly from 0.079 m by 0.1 m per metre of depth gives 2π(0.079 − 0.1 d) at each level d = 0, 0.02, …, 0.38 m; the profile 0.50, 0.48, 0.46 at 0.02 m steps gives 0.475 at 0.025 m (a quarter of the way from 0.48 to 0.46).
