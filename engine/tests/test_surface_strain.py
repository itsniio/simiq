"""Strain and relative pressure over a draped garment: spec scenarios of cloth-sim-spike group 3."""

import json

import numpy as np
import pytest

from simiq_fit.garment import DATA, Fabric
from simiq_fit.surface_strain import (
    deformation_gradients,
    face_areas,
    normal_curvatures,
    pressures,
    strains,
    zone_means,
)

# One triangle in the flat pattern, (course, wale) mm: 10 mm along each pattern axis.
REST = np.array([[[0.0, 0.0], [10.0, 0.0], [0.0, 10.0]]])
FACES = np.array([[0, 1, 2]])


def test_undeformed_triangle_has_no_strain():
    # The pattern triangle laid in 3D unchanged, turned: course along z, wale along y.
    positions = np.array([[5.0, 2.0, 1.0], [5.0, 2.0, 11.0], [5.0, 12.0, 1.0]])
    assert strains(REST, FACES, positions) == pytest.approx(np.array([[0.0, 0.0]]))


def test_uniform_stretch():
    # Course edge 10 -> 12 mm, wale edge 10 -> 11 mm: 12 / 10 - 1 = 0.2, 11 / 10 - 1 = 0.1.
    positions = np.array([[0.0, 0.0, 0.0], [12.0, 0.0, 0.0], [0.0, 0.0, 11.0]])
    assert strains(REST, FACES, positions) == pytest.approx(np.array([[0.2, 0.1]]))


def test_shear_stretches_the_wale_line_only():
    # The wale corner slides 5 mm along the course: F·v = (0.5, 0, 1), |F·v| = √1.25 = 1.118034.
    positions = np.array([[0.0, 0.0, 0.0], [10.0, 0.0, 0.0], [5.0, 0.0, 10.0]])
    assert strains(REST, FACES, positions) == pytest.approx(np.array([[0.0, 0.118034]]), abs=1e-6)


def test_rest_triangle_not_on_the_axes():
    # Rest corners (2, 1), (6, 4), (1, 7): every edge doubled in 3D gives 100 % in both directions.
    rest = np.array([[[2.0, 1.0], [6.0, 4.0], [1.0, 7.0]]])
    positions = np.array([[4.0, 0.0, 2.0], [12.0, 0.0, 8.0], [2.0, 0.0, 14.0]])
    assert strains(rest, FACES, positions) == pytest.approx(np.array([[1.0, 1.0]]))


def test_face_area_in_the_drape():
    # The stretched triangle above: legs 12 and 11 mm, area 12 · 11 / 2 = 66 mm².
    positions = np.array([[0.0, 0.0, 0.0], [12.0, 0.0, 0.0], [0.0, 0.0, 11.0]])
    assert face_areas(FACES, positions) == pytest.approx([66.0])


def test_zone_mean_is_area_weighted():
    # Faces of 50 and 150 mm² at 10 % and 30 %: (50 · 0.1 + 150 · 0.3) / 200 = 0.25.
    values, areas = np.array([0.1, 0.3, 0.9]), np.array([50.0, 150.0, 10.0])
    means = zone_means(values, areas, {"chest": np.array([0, 1]), "hem": np.array([2])})
    assert means == pytest.approx({"chest": 0.25, "hem": 0.9})


def test_zone_mean_leaves_out_faces_without_a_value():
    # A face beyond the fabric curve has no pressure (NaN) and does not count: 0.1 over 50 mm².
    values, areas = np.array([0.1, np.nan]), np.array([50.0, 150.0])
    assert zone_means(values, areas, {"chest": np.array([0, 1])}) == pytest.approx({"chest": 0.1})


def tube(sides, chord_mm, rest_chord_mm, rings=3, spacing_mm=10.0):
    """A closed tube of `sides` equal chords round the z axis, normals outward, and its pattern.

    The pattern is the tube cut open at angle 0: corner (side i, ring k) at (i · rest chord,
    k · spacing) in (course, wale) mm.
    """
    radius = chord_mm / (2 * np.sin(np.pi / sides))
    angles = 2 * np.pi * np.arange(sides) / sides
    positions = np.array(
        [
            (radius * np.cos(a), radius * np.sin(a), k * spacing_mm)
            for k in range(rings)
            for a in angles
        ]
    )
    faces, rest = [], []
    for k in range(rings - 1):
        for i in range(sides):
            a, b = k * sides + i, k * sides + (i + 1) % sides
            faces += [(a, b, b + sides), (a, b + sides, a + sides)]
            corner = {
                "a": (i, k), "b": (i + 1, k), "b+": (i + 1, k + 1), "a+": (i, k + 1)
            }  # fmt: skip
            for names in (("a", "b", "b+"), ("a", "b+", "a+")):
                rest.append(
                    [(corner[n][0] * rest_chord_mm, corner[n][1] * spacing_mm) for n in names]
                )
    return positions, np.array(faces), np.array(rest, float), radius


def test_curvature_of_a_cylinder():
    # 48 chords of 20 mm: radius 20 / (2 sin(π/48)) = 152.8979 mm, so κ = 1/152.8979 round the
    # tube and 0 along it.
    positions, faces, rest, radius = tube(48, 20.0, 20.0)
    assert radius == pytest.approx(152.8979, abs=1e-4)
    f = deformation_gradients(rest, faces, positions)
    course, wale = f[:, :, 0], f[:, :, 1]
    assert normal_curvatures(positions, faces, course) == pytest.approx(1 / radius, rel=1e-9)
    assert normal_curvatures(positions, faces, wale) == pytest.approx(0, abs=1e-12)


def example_knit():
    path = DATA / "examples" / "fabric-knit.json"
    return Fabric.model_validate(json.loads(path.read_text()))


def test_tube_on_a_cylinder_presses_with_tension_over_radius():
    # Spec: a tube of 84 cm course circumference on a cylinder of 96 cm. 48 chords of 17.5 mm
    # stretched to 20 mm: 20 / 17.5 − 1 = 0.142857. Course tension on the example knit:
    # F = 2.0 + 0.42857 · 2.5 = 3.07143 N over 50 mm = 61.4286 N/m; P = T / r with
    # r = 0.1528979 m → 401.76 Pa (402.04 Pa on the round cylinder, r = 0.96 / 2π).
    positions, faces, rest, _ = tube(48, 20.0, 17.5)
    assert strains(rest, faces, positions)[:, 0] == pytest.approx(0.142857, abs=1e-6)
    on_itself = (positions, faces, np.arange(len(faces)))
    assert pressures(rest, faces, positions, example_knit(), on_itself) == pytest.approx(
        401.76, abs=0.01
    )


def test_no_pressure_beyond_the_fabric_curve():
    # 48 chords of 12 mm stretched to 20 mm: 20 / 12 − 1 = 66.7 %, beyond the curve's 50 %.
    positions, faces, rest, _ = tube(48, 20.0, 12.0)
    on_itself = (positions, faces, np.arange(len(faces)))
    assert np.isnan(pressures(rest, faces, positions, example_knit(), on_itself)).all()


def test_pressure_takes_the_curvature_of_the_body_under_the_garment():
    # The same tube on a body meshed with 96 chords of 10 mm: r = 10 / (2 sin(π/96)) = 152.8160 mm
    # (sin(π/96) = 0.0327191); P = 61.4286 / 0.1528160 = 401.98 Pa.
    positions, faces, rest, _ = tube(48, 20.0, 17.5)
    body, body_faces, _, radius = tube(96, 10.0, 10.0, rings=5, spacing_mm=5.0)
    assert radius == pytest.approx(152.8160, abs=1e-4)
    centroids, body_centroids = positions[faces].mean(1), body[body_faces].mean(1)
    nearest = np.linalg.norm(centroids[:, None] - body_centroids[None], axis=2).argmin(1)
    p = pressures(rest, faces, positions, example_knit(), (body, body_faces, nearest))
    assert p == pytest.approx(401.98, abs=0.01)
