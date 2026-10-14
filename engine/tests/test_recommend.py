"""Size recommendation (fit-engine-poc 7.1): the spec scenarios with hand-made zone fits."""

import pytest

from simiq_fit.fit import ZoneFit, ZoneRange
from simiq_fit.recommend import BAND_COST, Reason, choose_size, penalty, recommend

RANGES = {
    "chest": ZoneRange(kind="girth", edges=[-0.05, 0.0, 0.10, 0.20]),  # ok 0-10 %, centre 5 %
    "back_length": ZoneRange(kind="length", edges=[-3.0, 0.0, 4.0]),  # ok 0-4 cm, centre 2 cm
}
WEIGHTS = {"chest": 2, "back_length": 1}


def zones(chest_strain, chest_status, margin, back_status):
    return [
        ZoneFit(zone="chest", kind="girth", strain=chest_strain, status=chest_status),
        ZoneFit(zone="back_length", kind="length", margin_cm=margin, status=back_status),
    ]


def test_band_costs():
    assert BAND_COST["ok"] == 0 and BAND_COST["loose"] == 1 and BAND_COST["too_tight"] == 3


def test_clear_case_and_its_explanation():
    # Spec: M all ok; S has a tight chest (penalty 2 × 1 = 2), L a loose chest (2 × 1 = 2).
    fits = {
        "S": zones(0.15, "tight", 1.0, "ok"),
        "M": zones(0.05, "ok", 2.0, "ok"),
        "L": zones(-0.02, "loose", 3.0, "ok"),
    }
    size, penalties, reasons = choose_size(fits, WEIGHTS, RANGES)
    assert size == "M" and penalties == {"S": 2, "M": 0, "L": 2}
    # Spec: M is recommended over L because L's chest is loose.
    assert Reason(size="L", zone="chest", status="loose") in reasons
    assert reasons == [
        Reason(size="S", zone="chest", status="tight"),
        Reason(size="L", zone="chest", status="loose"),
    ]


def test_weights_scale_the_penalty():
    # A too_tight chest (3) weighted 2 plus a short back (1) weighted 1: 2 × 3 + 1 × 1 = 7.
    assert penalty(zones(0.25, "too_tight", -1.0, "short"), WEIGHTS) == 7


def test_tie_goes_to_the_size_nearer_the_ok_centres():
    # Both all ok (penalty 0). M: chest 9 % is 4 % from the 5 % centre = 0.4 band widths, × 2 =
    # 0.8; back 2 cm is at the centre, 0. L: chest 5 % -> 0; back 3.8 cm is 1.8 cm / 4 cm = 0.45.
    # L is nearer: 0.45 < 0.8.
    fits = {"M": zones(0.09, "ok", 2.0, "ok"), "L": zones(0.05, "ok", 3.8, "ok")}
    assert choose_size(fits, WEIGHTS, RANGES)[0] == "L"


def test_smallest_size_has_only_one_neighbour():
    fits = {"S": zones(0.05, "ok", 2.0, "ok"), "M": zones(-0.02, "loose", 3.0, "ok")}
    size, _, reasons = choose_size(fits, WEIGHTS, RANGES)
    assert size == "S" and reasons == [Reason(size="M", zone="chest", status="loose")]


def test_penalty_needs_a_weight_for_every_zone():
    with pytest.raises(KeyError):
        penalty(zones(0.05, "ok", 2.0, "ok"), {"chest": 2})


def chest_only_case(chest_cm, sd_cm):
    """The example jersey reduced to its chest zone (S/M/L 80/84/88 cm), ok band 2-6 % strain."""
    import json

    from simiq_fit.garment import DATA, Fabric, Garment
    from simiq_fit.measure import Measurements

    data = json.loads((DATA / "examples" / "garment-jersey.json").read_text())
    data["zones"] = [z for z in data["zones"] if z["id"] == "chest"]
    garment = Garment.model_validate(data)
    fabric = Fabric.model_validate_json((DATA / "examples" / "fabric-knit.json").read_text())
    body = Measurements(
        pose="hoods",
        girths_cm={"chest_girth": chest_cm, "waist_girth": 80, "hip_girth": 90},
        profiles_cm={"upper_arm_girth": [30] * 8, "thigh_girth": [60] * 8},
        lengths_cm={"back_length": 63, "vertical_trunk_girth": 160},
    )
    sds = {n: sd_cm for n in ("chest_girth", "waist_girth", "hip_girth", "upper_arm_girth",
                              "thigh_girth", "back_length", "vertical_trunk_girth")}  # fmt: skip
    ranges = {"chest": ZoneRange(kind="girth", edges=[-0.05, 0.02, 0.06, 0.12])}
    return recommend(garment, {"example-knit": fabric}, body, sds, ranges, [], 65)


def test_clear_body():
    # Spec: chest 87.36 cm = 84 × 1.04 sits mid-way in M's ok band (2-6 %, i.e. 85.68-89.04 cm);
    # S is tight (9.2 %), L loose (-0.7 %). With an SD of 0.5 cm the edges are 3.4 SDs away.
    result = chest_only_case(87.36, 0.5)
    assert result.size == "M" and result.confidence >= 0.8 and result.alternative is None
    assert result.pose == "hoods"


def test_borderline_body():
    # Spec: chest 89.4 cm lies between M's ok band (to 89.04) and L's (from 88 × 1.02 = 89.76): M
    # is tight (6.43 %), L loose (1.59 %), equal penalties, and the tie-break barely prefers L
    # (0.602 vs 0.607 ok-band widths off centre). An SD of 0.5 cm flips it about half the time.
    result = chest_only_case(89.4, 0.5)
    assert result.size in ("M", "L") and result.confidence < 0.6
    assert {result.size, result.alternative} == {"M", "L"}


def test_same_request_same_confidence():
    first, second = chest_only_case(89.4, 0.5), chest_only_case(89.4, 0.5)
    assert first.confidence == second.confidence and first.alternative == second.alternative
