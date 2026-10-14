import pytest
from pydantic import ValidationError

from simiq_fit.inputs import BodyInputs

REQUIRED = dict(sex="male", height_cm=180, weight_kg=75, body_type="regular")


def invalid_fields(**changes):
    with pytest.raises(ValidationError) as error:
        BodyInputs(**{**REQUIRED, **changes})
    return {e["loc"][0] if e["loc"] else "" for e in error.value.errors()}


def test_required_inputs_only():
    body = BodyInputs(**REQUIRED)
    assert body.age is None
    assert body.arms is None and body.torso is None and body.legs is None
    assert body.chest_cm is None and body.outseam_cm is None


def test_height_out_of_range_names_the_field():
    assert invalid_fields(height_cm=250) == {"height_cm"}


def test_height_edges_are_inclusive():
    # At 75 kg the BMI stays inside 16-40: 75 / 1.40² = 38.3 and 75 / 2.10² = 17.0.
    BodyInputs(**{**REQUIRED, "height_cm": 140})
    BodyInputs(**{**REQUIRED, "height_cm": 210})
    assert invalid_fields(height_cm=139.9) == {"height_cm"}
    assert invalid_fields(height_cm=210.1) == {"height_cm"}


def test_weight_edges_are_inclusive():
    # 35 kg at 140 cm is BMI 17.9; 160 kg at 210 cm is BMI 36.3.
    BodyInputs(**{**REQUIRED, "height_cm": 140, "weight_kg": 35})
    BodyInputs(**{**REQUIRED, "height_cm": 210, "weight_kg": 160})
    assert invalid_fields(height_cm=140, weight_kg=34.9) == {"weight_kg"}
    assert invalid_fields(height_cm=210, weight_kg=160.1) == {"weight_kg"}


def test_implausible_height_and_weight_combination():
    # BMI = 150 / 1.5² = 66.7, above 40.
    with pytest.raises(ValidationError, match="height and weight combination"):
        BodyInputs(**{**REQUIRED, "height_cm": 150, "weight_kg": 150})


def too_thin_or_heavy(**changes):
    with pytest.raises(ValidationError, match="height and weight combination"):
        BodyInputs(**{**REQUIRED, **changes})


def test_bmi_edges_for_men():
    # At 180 cm, BMI 16 is 16 × 1.8² = 51.84 kg and BMI 40 is 40 × 1.8² = 129.6 kg.
    BodyInputs(**{**REQUIRED, "weight_kg": 51.84})
    BodyInputs(**{**REQUIRED, "weight_kg": 129.6})
    too_thin_or_heavy(weight_kg=51.8)  # BMI 15.99
    too_thin_or_heavy(weight_kg=129.7)  # BMI 40.03


def test_bmi_edges_for_women():
    # At 180 cm, BMI 14 is 14 × 1.8² = 45.36 kg; the upper edge is the men's, 129.6 kg.
    BodyInputs(**{**REQUIRED, "sex": "female", "weight_kg": 45.36})
    BodyInputs(**{**REQUIRED, "sex": "female", "weight_kg": 129.6})
    too_thin_or_heavy(sex="female", weight_kg=45.3)  # BMI 13.98
    too_thin_or_heavy(sex="female", weight_kg=129.7)


def test_bmi_range_depends_on_sex():
    # Spec scenario: 48 / 1.8² = 14.8, inside the women's 14-40, below the men's 16.
    BodyInputs(**{**REQUIRED, "sex": "female", "weight_kg": 48})
    too_thin_or_heavy(sex="male", weight_kg=48)


def test_sex_other_has_the_mens_bmi_range():
    # Built as a male body, so held to the male lower edge: 51.8 kg at 180 cm is BMI 15.99.
    BodyInputs(**{**REQUIRED, "sex": "other", "weight_kg": 51.84})
    too_thin_or_heavy(sex="other", weight_kg=51.8)


def test_unknown_type_names_the_field():
    assert invalid_fields(body_type="stocky") == {"body_type"}
    assert invalid_fields(arms="stocky") == {"arms"}


def test_unknown_sex_names_the_field():
    assert invalid_fields(sex="robot") == {"sex"}


def test_age_range():
    BodyInputs(**REQUIRED, age=16)
    BodyInputs(**REQUIRED, age=90)
    assert invalid_fields(age=15) == {"age"}
    assert invalid_fields(age=91) == {"age"}


@pytest.mark.parametrize(
    ("field", "low", "high"),
    [
        ("chest_cm", 60, 160),
        ("waist_cm", 50, 160),
        ("biceps_cm", 18, 60),
        ("thigh_cm", 35, 90),
        ("calf_cm", 25, 60),
        ("inseam_cm", 55, 100),
        ("outseam_cm", 75, 130),
    ],
)
def test_step_three_ranges(field, low, high):
    BodyInputs(**REQUIRED, **{field: low})
    BodyInputs(**REQUIRED, **{field: high})
    assert invalid_fields(**{field: low - 0.1}) == {field}
    assert invalid_fields(**{field: high + 0.1}) == {field}


def test_every_invalid_field_is_named():
    assert invalid_fields(height_cm=300, body_type="stocky", chest_cm=10) == {
        "height_cm",
        "body_type",
        "chest_cm",
    }
