import numpy as np
import pytest

from simiq_fit.tape import girth, limb_profile, profile_at

UP = np.array([0.0, 0.0, 1.0])
MM = 0.001


def tube(outline, z0=0.0, z1=1.0, rings=11, offset=(0.0, 0.0)):
    """Open tube along z whose cross-section is the closed 2D outline (n x 2), in metres."""
    n = len(outline)
    zs = np.linspace(z0, z1, rings)
    vertices = np.array([[x + offset[0], y + offset[1], z] for z in zs for x, y in outline])
    faces = []
    for i in range(rings - 1):
        for j in range(n):
            a, b = i * n + j, i * n + (j + 1) % n
            faces += [[a, b, a + n], [b, b + n, a + n]]
    return vertices, np.array(faces)


def ellipse(a, b, n=512):
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    return np.column_stack([a * np.cos(t), b * np.sin(t)])


def test_cylinder_girth_is_its_circumference():
    # r = 0.15 m: 2π · 0.15 = 0.94248 m.
    vertices, faces = tube(ellipse(0.15, 0.15))
    assert girth(vertices, faces, point=[0, 0, 0.5], normal=UP) == pytest.approx(0.94248, abs=MM)


def test_ellipse_girth_matches_ramanujan():
    # a = 0.15, b = 0.10: π[3(a+b) − √((3a+b)(a+3b))] = π[0.75 − √(0.55 · 0.45)] = 0.79327 m.
    vertices, faces = tube(ellipse(0.15, 0.10))
    assert girth(vertices, faces, point=[0, 0, 0.5], normal=UP) == pytest.approx(0.79327, abs=MM)


def test_tape_bridges_a_concavity():
    # A 0.2 m square with a 0.05 x 0.05 m notch cut into one side: the outline is
    # 0.8 + 2 × 0.05 = 0.9 m long, but a tape spans the notch and reads the square's 0.8 m.
    notched = np.array(
        [[0, 0], [0.2, 0], [0.2, 0.2], [0.125, 0.2], [0.125, 0.15], [0.075, 0.15],
         [0.075, 0.2], [0, 0.2]]
    )  # fmt: skip
    vertices, faces = tube(notched - 0.1, rings=3)
    assert girth(vertices, faces, point=[0, 0, 0.5], normal=UP) == pytest.approx(0.8, abs=MM)


def test_girth_measures_the_section_around_the_point_only():
    # A torso (r = 0.15) between two arms (r = 0.05), all cut by the same plane.
    torso = tube(ellipse(0.15, 0.15))
    left = tube(ellipse(0.05, 0.05), offset=(0.3, 0))
    right = tube(ellipse(0.05, 0.05), offset=(-0.3, 0))
    vertices = np.concatenate([torso[0], left[0], right[0]])
    faces = np.concatenate(
        [torso[1], left[1] + len(torso[0]), right[1] + len(torso[0]) + len(left[0])]
    )
    assert girth(vertices, faces, point=[0, 0, 0.5], normal=UP) == pytest.approx(0.94248, abs=MM)
    # 2π · 0.05 = 0.31416 m.
    assert girth(vertices, faces, point=[0.3, 0, 0.5], normal=UP) == pytest.approx(0.31416, abs=MM)


def test_tilted_plane_through_a_cylinder_is_an_ellipse():
    # A plane tilted 30° from horizontal cuts r = 0.15 into an ellipse with semi-axes
    # 0.15 and 0.15 / cos 30° = 0.17321: π[3 · 0.32321 − √(0.62321 · 0.66962)] = 1.01669 m.
    vertices, faces = tube(ellipse(0.15, 0.15), z0=-1, z1=2, rings=31)
    tilt = np.radians(30)
    normal = np.array([np.sin(tilt), 0, np.cos(tilt)])
    assert girth(vertices, faces, point=[0, 0, 0.5], normal=normal) == pytest.approx(
        1.01669, abs=MM
    )


def test_plane_missing_the_mesh_is_an_error():
    vertices, faces = tube(ellipse(0.15, 0.15))
    with pytest.raises(ValueError, match="does not cut"):
        girth(vertices, faces, point=[0, 0, 5], normal=UP)


# A tapered limb: radius 0.08 m at z = 0 down to 0.04 m at z = -0.4 (1 cm less per 10 cm).
def tapered_limb():
    rings, n = 41, 256
    zs = np.linspace(0, -0.4, rings)
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    vertices = np.array(
        [[r * np.cos(a), r * np.sin(a), z] for z in zs for r in [0.08 + 0.1 * z] for a in t]
    )
    faces = []
    for i in range(rings - 1):
        for j in range(n):
            a, b = i * n + j, i * n + (j + 1) % n
            faces += [[a, b, a + n], [b, b + n, a + n]]
    return vertices, np.array(faces)


def test_limb_profile_steps_along_the_axis():
    vertices, faces = tapered_limb()
    profile = limb_profile(vertices, faces, start=[0, 0, -0.01], end=[0, 0, -0.39], step=0.02)
    # Levels 0, 0.02, ..., 0.38 m below the start: 20 values; radius at depth d is 0.079 − 0.1 d.
    assert len(profile) == 20
    expected = [2 * np.pi * (0.079 - 0.1 * d) for d in np.arange(20) * 0.02]
    assert profile == pytest.approx(expected, abs=MM)


def test_profile_lookup_interpolates_between_steps():
    # Steps of 0.02: values 0.50 at 0, 0.48 at 0.02, 0.46 at 0.04.
    profile = np.array([0.50, 0.48, 0.46])
    assert profile_at(profile, step=0.02, distance=0.02) == pytest.approx(0.48)
    # 0.025 is a quarter of the way from 0.48 to 0.46: 0.48 − 0.25 × 0.02 = 0.475.
    assert profile_at(profile, step=0.02, distance=0.025) == pytest.approx(0.475)


def test_profile_lookup_outside_the_profile_is_an_error():
    with pytest.raises(ValueError, match="outside"):
        profile_at(np.array([0.50, 0.48]), step=0.02, distance=0.05)
