"""Fitting Anny to height and mass (fit-engine-poc 3.4). The model tests build Anny once (slow)."""

import numpy as np
import pytest

from simiq_fit.body import BODY_DENSITY_KG_PER_L, anny_age, height_cm, mass_kg
from simiq_fit.inputs import BodyInputs

# A unit cube, outward-facing triangles: 1 m tall, 1 m³.
CUBE_VERTICES = np.array(
    [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0], [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]],
    dtype=float,
)
CUBE_FACES = np.array(
    [[0, 2, 1], [0, 3, 2], [4, 5, 6], [4, 6, 7], [0, 1, 5], [0, 5, 4],
     [1, 2, 6], [1, 6, 5], [2, 3, 7], [2, 7, 6], [3, 0, 4], [3, 4, 7]]
)  # fmt: skip


def test_height_is_the_vertical_extent_in_cm():
    assert height_cm(CUBE_VERTICES) == pytest.approx(100.0)


def test_mass_is_volume_times_density():
    # 1 m³ = 1000 L; 1000 L × 1.03 kg/L = 1030 kg.
    assert BODY_DENSITY_KG_PER_L == 1.03
    assert mass_kg(CUBE_VERTICES, CUBE_FACES) == pytest.approx(1030.0)


def test_mass_does_not_depend_on_face_orientation():
    assert mass_kg(CUBE_VERTICES, CUBE_FACES[:, ::-1]) == pytest.approx(1030.0)


@pytest.mark.parametrize(
    ("years", "expected"),
    [
        (18, 0.77),  # anchor
        (64, 0.83),  # anchor
        (35, 0.77 + (35 - 18) / (64 - 18) * 0.06),  # 0.79217
        (16, 0.67),  # anchor
        (90, 0.83 + (90 - 64) / (110 - 64) * 0.17),  # 0.92609
    ],
)
def test_anny_age_interpolates_annys_calibration(years, expected):
    assert anny_age(years) == pytest.approx(expected)


# --- with the Anny model -----------------------------------------------------------------------


@pytest.fixture(scope="module")
def model():
    from simiq_fit.body import load_model

    return load_model()


def built(model, **inputs):
    from simiq_fit.body import fit_body, rest_vertices

    body_inputs = BodyInputs(**{"sex": "male", "body_type": "regular", **inputs})
    phenotype = fit_body(model, body_inputs)
    vertices = rest_vertices(model, phenotype)
    return phenotype, height_cm(vertices), mass_kg(vertices, np.asarray(model.faces))


def test_height_matched(model):
    _, height, _ = built(model, height_cm=172, weight_kg=68)
    assert 171.5 <= height <= 172.5


def test_weight_matched(model):
    _, _, mass = built(model, height_cm=172, weight_kg=68)
    assert 66.64 <= mass <= 69.36


def test_twenty_random_valid_inputs_are_matched(model):
    rng = np.random.default_rng(20261014)
    misses = []
    for _ in range(20):
        sex = str(rng.choice(["female", "male"]))
        height = float(rng.uniform(150, 200))
        weight = round(float(rng.uniform(18, 32)) * (height / 100) ** 2, 1)
        age = int(rng.integers(18, 70))
        try:
            _, got_height, got_mass = built(
                model, sex=sex, height_cm=height, weight_kg=weight, age=age
            )
        except ValueError as error:
            misses.append((sex, age, round(height, 1), weight, str(error)))
            continue
        if abs(got_height - height) > 0.5 or abs(got_mass - weight) > 0.02 * weight:
            misses.append((sex, age, round(height, 1), weight, round(got_height, 1), got_mass))
    assert misses == []


def test_no_age_is_built_for_35(model):
    without, _, _ = built(model, height_cm=180, weight_kg=75)
    with_35, _, _ = built(model, height_cm=180, weight_kg=75, age=35)
    assert without == with_35


def test_sex_other_is_built_as_male(model):
    other, _, _ = built(model, sex="other", height_cm=180, weight_kg=75)
    male, _, _ = built(model, sex="male", height_cm=180, weight_kg=75)
    assert other == male


def test_muscle_stays_at_its_prior_when_weight_suffices(model):
    phenotype, _, _ = built(model, height_cm=180, weight_kg=75)
    assert phenotype["muscle"] == pytest.approx(0.5, abs=0.02)


def test_thin_body_lowers_muscle_once_weight_is_at_its_minimum(model):
    # The first miss of the two-parameter fit: 173.8 cm, 59.3 kg (BMI 19.6), male, 58 years.
    phenotype, height, mass = built(model, height_cm=173.8, weight_kg=59.3, age=58)
    assert abs(height - 173.8) <= 0.5 and abs(mass - 59.3) <= 0.02 * 59.3
    assert phenotype["muscle"] < 0.5
