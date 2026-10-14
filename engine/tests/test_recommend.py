"""Size recommendation (fit-engine-poc 7.1): the spec scenarios with hand-made zone fits."""

import pytest

from simiq_fit.fit import ZoneFit, ZoneRange
from simiq_fit.recommend import BAND_COST, Reason, choose_size, penalty

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
