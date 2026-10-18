"""The drape solver: spec scenarios of cloth-sim-spike group 4."""

import json

import numpy as np
import pytest

from simiq_fit.drape import COLLISION_MM, body, cloth, positions_mm, run
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
    # (as a force: a 0.46 kg weight on 1 g of fabric would need ~10⁴ Gauss-Seidel iterations).
    # The strip's own 190 g/m² · 50 · 100 mm² · 9.81 = 0.0093 N adds at most 0.2 % at the top.
    positions, faces, rest = grid(11, 21, 5.0)
    top, bottom = np.arange(11), np.arange(20 * 11, 21 * 11)
    load = np.zeros_like(positions)
    load[bottom, 1] = -4.5 / 11
    sheet = cloth(rest, faces, positions, KNIT, pinned=top, force_n=load)
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
        rest, faces, positions, KNIT, pinned=np.arange(11), force_n=load, stiffness_scale=stiff
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


def test_an_outer_layer_keeps_its_own_distance_off_the_body():
    # A pocket lies on the back panel, so it keeps 2.2 mm more off the body; the same 84 cm tube
    # settles at 14.3 % on a body 2.2 mm thinner than before.
    garment, faces, rest = tube(48, 5, 133.79, 10.0, 17.5)
    distance = COLLISION_MM + 2.2
    cylinder, cylinder_faces, _ = tube(720, 9, 152.8979 - distance, 10.0, 1.0)
    cylinder[:, 2] -= 20.0
    sheet = cloth(rest, faces, garment, KNIT, collision_mm=np.full(len(garment), distance))
    run(sheet, seconds=2.0, body=body(cylinder, cylinder_faces))
    assert strains(rest, faces, positions_mm(sheet))[:, 0].mean() == pytest.approx(
        0.142857, abs=0.002
    )
