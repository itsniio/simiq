"""The drape solver: spec scenarios of cloth-sim-spike group 4."""

import json

import numpy as np
import pytest

from simiq_fit.drape import (
    COLLISION_MM,
    FRICTION,
    body,
    cloth,
    kes_shear_n_per_m,
    move_body,
    positions_mm,
    run,
)
from simiq_fit.garment import DATA, Fabric
from simiq_fit.surface_strain import strains

KNIT = Fabric.model_validate(json.loads((DATA / "examples" / "fabric-knit.json").read_text()))


def grid(columns, rows, spacing_mm):
    """A flat sheet in the x–y plane (y down the sheet), two triangles per cell, and its pattern.

    The pattern's course runs down the sheet (−y), its wale across (x).
    """
    xs, ys = np.meshgrid(np.arange(columns) * spacing_mm, -np.arange(rows) * spacing_mm)
    positions = np.c_[xs.ravel(), ys.ravel(), np.zeros(xs.size)]
    faces = []
    for r in range(rows - 1):
        for c in range(columns - 1):
            a, b, d, e = (
                r * columns + c,
                r * columns + c + 1,
                (r + 1) * columns + c,
                (r + 1) * columns + c + 1,
            )
            faces += [(a, d, b), (b, d, e)]
    faces = np.array(faces)
    pattern = np.c_[-positions[:, 1], positions[:, 0]]  # (course, wale) mm
    return positions, faces, pattern[faces]


def test_hanging_strip_settles_on_its_curve():
    # Spec: a 50 mm strip whose load lies on the course curve at 20 %. The example knit pulls
    # 4.5 N on a 50 mm strip at 20 %, so the bottom row carries 4.5 N down, 4.5 / 11 per vertex
    # (as a force: a 0.46 kg weight on 1 g of fabric would need ~10⁴ Gauss-Seidel iterations),
    # with the strip's inertia scaled so that the force does not fling 5 µg vertices.
    # The strip's own 190 g/m² · 50 · 100 mm² · 9.81 = 0.0093 N adds at most 0.2 % at the top.
    positions, faces, rest = grid(11, 21, 5.0)
    top, bottom = np.arange(11), np.arange(20 * 11, 21 * 11)
    load = np.zeros_like(positions)
    load[bottom, 1] = -4.5 / 11
    sheet = cloth(rest, faces, positions, KNIT, pinned=top, force_n=load, inertia_scale=1000)
    run(sheet, seconds=4.0)
    course = strains(rest, faces, positions_mm(sheet))[:, 0]
    assert course.mean() == pytest.approx(0.20, abs=0.01)


def test_a_stiffer_triangle_carries_the_load_at_less_strain():
    # Twice the stiffness: 4.5 N on 50 mm is 90 N/m, the curve's own 45 N/m, which lies between
    # 40 N/m at 10 % and 90 N/m at 20 %: 10 % + 5 / 50 · 10 % = 11 %.
    positions, faces, rest = grid(11, 21, 5.0)
    load = np.zeros_like(positions)
    load[np.arange(20 * 11, 21 * 11), 1] = -4.5 / 11
    stiff = np.full(len(faces), 2.0)
    sheet = cloth(
        rest,
        faces,
        positions,
        KNIT,
        pinned=np.arange(11),
        force_n=load,
        stiffness_scale=stiff,
        inertia_scale=1000,
    )
    run(sheet, seconds=4.0)
    assert strains(rest, faces, positions_mm(sheet))[:, 0].mean() == pytest.approx(0.11, abs=0.01)


def tube(sides, rings, radius_mm, spacing_mm, rest_chord_mm):
    """A closed tube round the z axis (normals outward), rings `spacing_mm` apart, and its pattern.

    The pattern is the tube cut open at angle 0: course round it, wale along it.
    """
    angles = 2 * np.pi * np.arange(sides) / sides
    positions = np.array(
        [
            (radius_mm * np.cos(a), radius_mm * np.sin(a), k * spacing_mm)
            for k in range(rings)
            for a in angles
        ]
    )
    faces, rest = [], []
    for k in range(rings - 1):
        for i in range(sides):
            a, b = k * sides + i, k * sides + (i + 1) % sides
            corner = {a: (i, k), b: (i + 1, k), b + sides: (i + 1, k + 1), a + sides: (i, k + 1)}
            for face in ((a, b, b + sides), (a, b + sides, a + sides)):
                faces.append(face)
                rest.append(
                    [(corner[v][0] * rest_chord_mm, corner[v][1] * spacing_mm) for v in face]
                )
    return positions, np.array(faces), np.array(rest, float)


def test_tube_on_a_cylinder_settles_at_its_strain_outside_the_surface():
    # Spec: a tube of 84 cm course circumference on a cylinder of 96 cm: 96 / 84 − 1 = 14.3 %.
    # 48 chords of 17.5 mm (84 cm) in the pattern. The garment rests COLLISION_MM off the body, so
    # the body's radius is that much less than a 48-gon of 20 mm chords (96 cm), whose radius is
    # 20 / (2 sin(π/48)) = 152.8979 mm; meshed with 720 sides (its faces lie
    # 150 · (1 − cos(π/720)) = 0.0014 mm inside the circle). The tube starts at its rest radius
    # 17.5 / (2 sin(π/48)) = 133.79 mm, inside the body, and is pushed out.
    garment, faces, rest = tube(48, 5, 133.79, 10.0, 17.5)
    radius = 152.8979 - COLLISION_MM
    cylinder, cylinder_faces, _ = tube(720, 9, radius, 10.0, 1.0)
    cylinder[:, 2] -= 20.0  # reaches 20 mm past both ends of the garment
    sheet = cloth(rest, faces, garment, KNIT)
    run(sheet, seconds=2.0, body=body(cylinder, cylinder_faces))
    x = positions_mm(sheet)
    assert strains(rest, faces, x)[:, 0].mean() == pytest.approx(0.142857, abs=0.002)
    assert np.hypot(x[:, 0], x[:, 1]).min() >= radius


def test_a_layer_rests_on_the_one_under_it():
    # A free sheet falls onto a pinned sheet 0.5 mm below it and stops 2.2 mm above it, the layer
    # distance; the two sheets are one cloth (as a pocket and the back panel are).
    under, under_faces, under_rest = grid(6, 6, 10.0)
    upper, upper_faces, upper_rest = grid(4, 4, 10.0)
    flat = np.c_[under[:, 0], np.zeros(len(under)), under[:, 1]]
    lifted = np.c_[upper[:, 0] + 10.0, np.full(len(upper), 0.5), upper[:, 1] - 10.0]
    positions = np.r_[flat, lifted]
    faces = np.r_[under_faces, upper_faces + len(under)]
    rest = np.r_[under_rest, upper_rest]
    upper_ids = np.arange(len(under), len(positions))
    sheet = cloth(
        rest,
        faces,
        positions,
        KNIT,
        pinned=np.arange(len(under)),
        layer=(upper_ids, under_faces, 2.2),
    )
    run(sheet, seconds=1.0)
    assert positions_mm(sheet)[upper_ids, 1] == pytest.approx(2.2, abs=0.05)


def test_free_cloth_falls_at_the_rate_of_gravity():
    # A garment must follow a body that sinks. 50 substeps of dt = 2 ms, v ← (v + g dt) · a with
    # a = e^(−2 · 0.002) = 0.996008: x = g dt² · [N + a/(1−a) · (N − (1 − a^N)/(1 − a))]
    # = 9.81 · 4e-6 · [50 + 249.50 · (50 − 45.408)] = 0.046919 m (continuous: 45.94 mm).
    positions, faces, rest = grid(5, 5, 10.0)
    sheet = cloth(rest, faces, positions, KNIT)
    run(sheet, seconds=0.1)
    assert (positions[:, 1] - positions_mm(sheet)[:, 1]).mean() == pytest.approx(46.92, abs=0.05)


def test_cloth_on_a_body_is_carried_when_the_body_moves():
    # The cylinder slides 50 mm along its axis in 0.5 s; the tube lying on it moves with it (slow
    # inertia, so neither gravity nor momentum could have moved it there).
    garment, faces, rest = tube(48, 5, 152.8979, 10.0, 17.5)
    cylinder, cylinder_faces, _ = tube(720, 9, 152.8979 - COLLISION_MM, 10.0, 1.0)
    cylinder[:, 2] -= 20.0
    sheet = cloth(rest, faces, garment, KNIT, inertia_scale=1000)
    moving = body(cylinder, cylinder_faces)
    run(sheet, seconds=0.2, body=moving)
    before = positions_mm(sheet)[:, 2].mean()
    move_body(moving, cylinder + [0.0, 0.0, 50.0])
    run(sheet, seconds=0.5, body=moving)
    assert positions_mm(sheet)[:, 2].mean() - before == pytest.approx(50.0, abs=0.5)


def axial_slide(friction):
    """How far the spec's tube on its cylinder slides along it in 1 s under a 5 N axial load."""
    garment, faces, rest = tube(48, 5, 152.8979, 10.0, 17.5)
    cylinder, cylinder_faces, _ = tube(720, 9, 152.8979 - COLLISION_MM, 10.0, 1.0)
    cylinder[:, 2] -= 20.0
    load = np.zeros_like(garment)
    load[:, 2] = 5.0 / len(garment)
    sheet = cloth(rest, faces, garment, KNIT, force_n=load, inertia_scale=1000, friction=friction)
    run(sheet, seconds=1.0, body=body(cylinder, cylinder_faces))
    return positions_mm(sheet)[:, 2].mean() - garment[:, 2].mean()


def test_a_gripper_holds_where_fabric_slides():
    # The tube presses on the cylinder with P = T/r = 402 Pa (above) over 0.96 m × 40 mm, 15.4 N.
    # A 5 N pull along it beats μ = 0.3 (4.6 N) and not μ = 1.5 (23.2 N).
    assert axial_slide(np.full(240, 0.3)) > 10.0
    assert abs(axial_slide(np.full(240, 1.5))) < 2.0


def box(low, high):
    """A closed box (normals outward) as a body."""
    corners = np.array(
        [[x, y, z] for x in (low[0], high[0]) for y in (low[1], high[1]) for z in (low[2], high[2])]
    )
    quads = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    return corners, np.array([t for a, b, c, d in quads for t in ((a, b, c), (a, c, d))])


def sideways_slide(pull_times_friction, seconds=1.0, kinetic=FRICTION, slip_mm_s=0.0):
    """How far a 40 × 40 mm sheet lying on a box slides under a sideways pull."""
    positions, faces, rest = grid(5, 5, 10.0)
    sheet_xz = np.c_[positions[:, 0], np.full(len(positions), COLLISION_MM), positions[:, 1]]
    weight = KNIT.weight_g_m2 / 1000 * 0.04 * 0.04 * 9.81  # N
    pull = np.zeros_like(sheet_xz)
    pull[:, 0] = pull_times_friction * FRICTION * weight / len(pull)
    kinetic = np.full(25, kinetic)
    sheet = cloth(
        rest, faces, sheet_xz, KNIT, force_n=pull, friction_kinetic=kinetic, slip_mm_s=slip_mm_s
    )
    run(sheet, seconds=seconds, body=body(*box((-50, -20, -90), (90, 0, 50))))
    return positions_mm(sheet)[:, 0].mean() - sheet_xz[:, 0].mean()


def test_cloth_resting_on_a_body_holds_until_the_pull_beats_friction():
    # Weight 190 g/m² · (0.04 m)² · 9.81 = 2.98 mN against friction μW: half of μW holds, twice
    # it slides (a = μW / m = μ · 9.81 m/s², over 1 s far more than 5 mm).
    assert abs(sideways_slide(0.5)) < 0.5
    assert sideways_slide(2.0) > 5.0


def test_once_sliding_the_cloth_feels_only_kinetic_friction():
    # A pull of 1.2 μ_s W beats static friction. Sliding, the net force is (1.2 − μ_k/μ_s) μ_s W:
    # a = 0.2 · 9.81 = 1.96 m/s² at μ_k = μ_s, (1.2 − 0.1) · 9.81 = 10.79 m/s² at μ_k = 0.1 μ_s.
    # Damped at k = 2/s from rest, x = a/k · (t − (1 − e^(−kt))/k); at t = 0.05 s that is
    # a · 0.0012096 s²: 2.37 mm and 13.05 mm.
    assert sideways_slide(1.2, seconds=0.05) == pytest.approx(2.37, rel=0.25)
    assert sideways_slide(1.2, seconds=0.05, kinetic=0.1 * FRICTION) == pytest.approx(
        13.05, rel=0.25
    )
    # Below the static threshold the low kinetic coefficient does not matter: it holds.
    assert abs(sideways_slide(0.5, kinetic=0.1 * FRICTION)) < 0.5


def test_regularized_friction_lets_a_held_sheet_creep_at_a_rate_set_by_the_pull():
    # Friction μN · min(1, v/v₀): under a pull P < μN the sheet creeps at v = v₀ · P/(μN).
    # P = 0.5 μW and v₀ = 10 mm/s: 5 mm/s, so 5 mm in 1 s (the transient lasts m v₀/(μW) = 1 ms).
    assert sideways_slide(0.5, slip_mm_s=10.0) == pytest.approx(5.0, rel=0.15)
    # A pull above μN still slides freely: the same as plain Coulomb friction.
    assert sideways_slide(1.2, seconds=0.05, slip_mm_s=10.0) == pytest.approx(2.37, rel=0.25)


def sheared(shear_n_per_m):
    """How far the top edge of a 100 mm wide, 10 mm high strip moves under a 0.2 N sideways pull.

    Wide and low, so that the strip shears rather than bends like a cantilever (a square sheet
    moved 4–5 mm more than its shear alone, through its soft compression side).
    """
    positions, faces, rest = grid(21, 3, 5.0)
    pull = np.zeros_like(positions)
    pull[np.arange(21), 0] = 0.2 / 21  # the top row
    sheet = cloth(
        rest,
        faces,
        positions,
        KNIT,
        pinned=np.arange(42, 63),  # the bottom row
        force_n=pull,
        inertia_scale=1000,
        shear_n_per_m=shear_n_per_m,
    )
    run(sheet, seconds=4.0)
    return positions_mm(sheet)[np.arange(21), 0].mean() - positions[np.arange(21), 0].mean()


def test_shear_stiffness_is_the_membrane_shear_modulus():
    # 0.2 N along a 100 mm edge is τ = 2 N/m; γ = τ / G and the top edge moves γ · 10 mm:
    # G = 20 N/m → 0.1 rad → 1.0 mm; G = 40 N/m → 0.5 mm.
    assert sheared(20.0) == pytest.approx(1.0, rel=0.1)
    assert sheared(40.0) == pytest.approx(0.5, rel=0.1)


def test_a_kes_shear_rigidity_becomes_the_membrane_shear_modulus():
    # 1 cN/cm per degree = 0.01 N / 0.01 m per degree = 1 N/m per degree = 180/π = 57.2958 N/m
    assert kes_shear_n_per_m(1.0) == pytest.approx(57.2958, abs=1e-4)
    # the weft-knit range 0.28–1.50 cN/cm/deg, its geometric mean √0.42 = 0.648074 → 37.1319 N/m
    assert kes_shear_n_per_m((0.28 * 1.50) ** 0.5) == pytest.approx(37.1319, abs=1e-4)
