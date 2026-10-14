"""Back length and vertical trunk girth on posed Anny bodies (fit-engine-poc 4.4). Slow."""

import numpy as np
import pytest

from simiq_fit.inputs import BodyInputs

BODIES = [  # the 10 bodies of scripts/body_lengths.py, across the supported ranges
    ("female", 158, 50),
    ("female", 165, 60),
    ("female", 170, 85),
    ("female", 175, 58),
    ("female", 182, 70),
    ("male", 168, 72),
    ("male", 175, 64),
    ("male", 178, 75),
    ("male", 185, 100),
    ("male", 195, 88),
]


@pytest.fixture(scope="module")
def measured():
    """{body: {pose: (back length cm, vertical trunk girth cm)}} for the 10 bodies."""
    from simiq_fit.body import fit_body, load_model, pose_body
    from simiq_fit.landmarks import load_landmarks
    from simiq_fit.measure import back_length, vertical_trunk_girth
    from simiq_fit.poses import load_pose

    model = load_model()
    faces, landmarks = np.asarray(model.faces), load_landmarks()["landmarks"]
    result = {}
    for sex, height, weight in BODIES:
        inputs = BodyInputs(sex=sex, height_cm=height, weight_kg=weight, body_type="regular")
        phenotype = fit_body(model, inputs)
        result[(sex, height, weight)] = {}
        for pose in ("standing", "hoods"):
            vertices = pose_body(model, phenotype, load_pose(pose))["vertices"]
            result[(sex, height, weight)][pose] = (
                100 * back_length(vertices, faces, landmarks),
                100 * vertical_trunk_girth(vertices, faces, landmarks),
            )
    return result


def test_back_is_longer_in_hoods_on_ten_bodies(measured):
    shorter = {b: m for b, m in measured.items() if not m["hoods"][0] > m["standing"][0]}
    assert shorter == {}


def test_lengths_are_in_an_adult_range(measured):
    # Rough bounds that catch a path gone astray (down a leg, round an arm): adult back length
    # C7 to the hip line 50-75 cm, vertical trunk girth 130-200 cm.
    for body, poses in measured.items():
        for back, trunk in poses.values():
            assert 50 < back < 75 and 130 < trunk < 200, (body, back, trunk)
