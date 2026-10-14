"""Body inputs of the Figma onboarding flow, one field per control, with their valid ranges."""

from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator

Sex = Literal["female", "male", "other"]
Build = Literal["slim", "regular", "athletic"]

BMI_RANGE = (15, 45)


def cm(low: float, high: float):
    return Annotated[float | None, Field(ge=low, le=high)]


class BodyInputs(BaseModel):
    """What the shopper enters; ranges from fit-engine-poc design D2 and the body-profile spec."""

    # step 1, required
    sex: Sex
    height_cm: float = Field(ge=140, le=210)
    weight_kg: float = Field(ge=35, le=160)
    body_type: Build
    # step 2, optional
    arms: Build | None = None
    torso: Build | None = None
    legs: Build | None = None
    # step 3, optional; shoulders and arm length are provisional until task 3.1
    chest_cm: cm(60, 160) = None
    waist_cm: cm(50, 160) = None
    shoulders_cm: cm(30, 60) = None
    arm_length_cm: cm(45, 90) = None
    biceps_cm: cm(18, 60) = None
    thigh_cm: cm(35, 90) = None
    calf_cm: cm(25, 60) = None
    inseam_cm: cm(55, 100) = None
    outseam_cm: cm(75, 130) = None
    # not asked in the flow
    age: int | None = Field(default=None, ge=16, le=90)

    @model_validator(mode="after")
    def bmi_in_range(self):
        bmi = round(self.weight_kg / (self.height_cm / 100) ** 2, 6)
        if not BMI_RANGE[0] <= bmi <= BMI_RANGE[1]:
            raise ValueError(
                f"height and weight combination is outside the supported range "
                f"(BMI {bmi:.1f}, supported {BMI_RANGE[0]}-{BMI_RANGE[1]})"
            )
        return self
