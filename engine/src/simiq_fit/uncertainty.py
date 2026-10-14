"""How uncertain each body measurement is, given which inputs the shopper entered (D8, task 4.5)."""

from simiq_fit.inputs import BodyInputs

# SD of a self-taken tape measurement as a share of its value: self- minus researcher-measured waist
# had SD 4.82 cm at a mean of 96.6 cm (Contardo Ayala, Nijpels, Lakerveld, BMC Medicine 2014;12:170,
# n = 617), 5 %. Applied to every step-3 girth; the study rounds (group 8) will check it.
SELF_MEASURED_SD_SHARE = 0.05

# SD (cm) of each measurement predicted from sex, height and weight alone: the residual SD of
# measurement ~ stature + weight + BMI in ANSUR II, 4082 men and 1986 women (scripts/ansur_sds.py,
# run 2026-10-14; caveats in docs/measurements.md, "Uncertainty").
PREDICTED_SD_CM = {
    "male": {
        "chest_girth": 3.19,
        "waist_girth": 4.37,
        "hip_girth": 2.60,
        "upper_arm_girth": 1.88,
        "thigh_girth": 2.25,
        "back_length": 2.07,
        "vertical_trunk_girth": 3.97,
    },
    "female": {
        "chest_girth": 4.24,
        "waist_girth": 4.82,
        "hip_girth": 2.91,
        "upper_arm_girth": 1.39,
        "thigh_girth": 2.26,
        "back_length": 2.08,
        "vertical_trunk_girth": 3.77,
    },
}

# Our measurement -> the step-3 input that measures it directly.
STEP3_INPUT = {
    "chest_girth": "chest_cm",
    "waist_girth": "waist_cm",
    "upper_arm_girth": "biceps_cm",
    "thigh_girth": "thigh_cm",
}


def combined_sd(a: float, b: float) -> float:
    """SD of the inverse-variance weighted mean of two independent estimates."""
    return (1 / a**2 + 1 / b**2) ** -0.5


def measurement_sds_cm(inputs: BodyInputs) -> dict[str, float]:
    """SD of each measurement: the prediction's, narrowed by a self-measurement if one is given."""
    predicted = PREDICTED_SD_CM["female" if inputs.sex == "female" else "male"]
    sds = {}
    for name, sd in predicted.items():
        given = getattr(inputs, STEP3_INPUT[name]) if name in STEP3_INPUT else None
        sds[name] = sd if given is None else combined_sd(sd, SELF_MEASURED_SD_SHARE * given)
    return sds
