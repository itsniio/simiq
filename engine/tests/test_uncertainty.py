import pytest

from simiq_fit.inputs import BodyInputs
from simiq_fit.uncertainty import (
    PREDICTED_SD_CM,
    SELF_MEASURED_SD_SHARE,
    combined_sd,
    measurement_sds_cm,
)

REQUIRED = dict(sex="male", height_cm=180, weight_kg=75, body_type="regular")


def test_combined_sd_of_two_independent_estimates():
    # 1 / sqrt(1/3² + 1/4²) = 1 / sqrt(25/144) = 12/5 = 2.4: never above the smaller SD.
    assert combined_sd(3.0, 4.0) == pytest.approx(2.4)


def test_self_measurement_sd_is_five_percent():
    # Contardo Ayala et al. 2014: SD of self- minus researcher-measured waist 4.82 cm at a mean of
    # 96.6 cm, 4.99 % -> 5 %.
    assert SELF_MEASURED_SD_SHARE == 0.05


def test_every_measurement_has_an_sd():
    sds = measurement_sds_cm(BodyInputs(**REQUIRED))
    assert set(sds) == {
        "chest_girth", "waist_girth", "hip_girth", "upper_arm_girth", "thigh_girth",
        "back_length", "vertical_trunk_girth",
    }  # fmt: skip
    assert sds == PREDICTED_SD_CM["male"]


def test_chest_sd_is_smaller_when_chest_girth_is_given():
    # Spec scenario "Uncertainty shrinks with an input". A 100 cm chest is self-measured to
    # 5 % = 5 cm; combined with the prediction's SD p the result is 1 / sqrt(1/p² + 1/25).
    without = measurement_sds_cm(BodyInputs(**REQUIRED))
    given = measurement_sds_cm(BodyInputs(**REQUIRED, chest_cm=100))
    p = PREDICTED_SD_CM["male"]["chest_girth"]
    assert given["chest_girth"] == pytest.approx((1 / p**2 + 1 / 25) ** -0.5)
    assert given["chest_girth"] < without["chest_girth"]
    assert {k: v for k, v in given.items() if k != "chest_girth"} == {
        k: v for k, v in without.items() if k != "chest_girth"
    }


def test_women_use_womens_sds_and_other_uses_mens():
    female = measurement_sds_cm(BodyInputs(**{**REQUIRED, "sex": "female"}))
    other = measurement_sds_cm(BodyInputs(**{**REQUIRED, "sex": "other"}))
    assert female == PREDICTED_SD_CM["female"]
    assert other == PREDICTED_SD_CM["male"]
