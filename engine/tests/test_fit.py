"""Strain, ease, tension and relative pressure (fit-engine-poc 6.1, 6.2), hand-computed."""

import json

import pytest

from simiq_fit.fabric import comfort_strain, tension_n_per_m
from simiq_fit.fit import (
    ZoneRange,
    girth_fit,
    length_margin_cm,
    load_ranges,
    relative_pressures,
    size_fits,
    zone_status,
)
from simiq_fit.garment import DATA, Curve, Fabric, Garment
from simiq_fit.measure import Measurements

# The example knit's course curve (data/examples/fabric-knit.json), 50 mm specimens.
COURSE = Curve(strain=[0, 0.1, 0.2, 0.3, 0.4, 0.5], force_n=[0, 2.0, 4.5, 7.5, 11.0, 15.0])
WIDTH_MM = 50


def test_stretched_girth():
    # Spec: body 96 cm in a garment of 84 cm: 96 / 84 - 1 = 0.142857 -> 14.3 %.
    result = girth_fit(96, 84, COURSE, WIDTH_MM)
    assert result["strain"] == pytest.approx(0.142857, abs=1e-6)
    assert result["ease_cm"] is None


def test_loose_girth_reports_ease():
    # Spec: 80 / 84 - 1 = -0.047619 -> -4.8 %; ease = 0.047619 * 84 = 4.0 cm (= 84 - 80).
    result = girth_fit(80, 84, COURSE, WIDTH_MM)
    assert result["strain"] == pytest.approx(-0.047619, abs=1e-6)
    assert result["ease_cm"] == pytest.approx(4.0)
    assert result["pressure_pa"] == 0.0


def test_tension_interpolates_the_curve():
    # At 15 % strain: halfway between 2.0 N (10 %) and 4.5 N (20 %) = 3.25 N on a 0.05 m strip
    # -> 3.25 / 0.05 = 65 N/m.
    assert tension_n_per_m(COURSE, 0.15, WIDTH_MM) == pytest.approx(65.0)
    assert tension_n_per_m(COURSE, 0.0, WIDTH_MM) == 0.0


def test_laplace_pressure():
    # A 96 cm body girth at 15 % strain would need a 96 / 1.15 = 83.478 cm garment. T = 65 N/m,
    # r = 0.96 / 2π = 0.152789 m, P = T / r = 425.42 Pa.
    result = girth_fit(96, 96 / 1.15, COURSE, WIDTH_MM)
    assert result["tension_n_per_m"] == pytest.approx(65.0)
    assert result["pressure_pa"] == pytest.approx(425.42, abs=0.01)


def test_smaller_size_presses_more():
    # Spec: chest 96 cm in M (84 cm, strain 14.29 %) and L (88 cm, 9.09 %).
    # M: F = 2.0 + 0.4286 * 2.5 = 3.0714 N -> 61.43 N/m; L: F = 0.9091 * 2.0 = 1.8182 N -> 36.36
    # N/m. Same radius, so M / L = 61.43 / 36.36 = 1.689: relative M 1.0, L 0.592.
    sizes = {
        s: girth_fit(96, c, COURSE, WIDTH_MM)["pressure_pa"] for s, c in (("M", 84), ("L", 88))
    }
    relative = relative_pressures(sizes)
    assert relative == pytest.approx({"M": 1.0, "L": 0.592}, abs=0.001)


def test_strain_beyond_the_curve_is_flagged_and_not_extrapolated():
    # 120 / 75 - 1 = 60 % strain; the curve ends at 50 %.
    result = girth_fit(120, 75, COURSE, WIDTH_MM)
    assert result["flags"] == ["out_of_curve"]
    assert result["tension_n_per_m"] is None and result["pressure_pa"] is None
    assert relative_pressures({"S": result["pressure_pa"], "M": 300.0}) == {"S": None, "M": 1.0}


def test_back_length_covered_by_stretch():
    # Spec: garment 60 cm, comfort tension reached at 5 % wale strain, body 62 cm in the pose:
    # 60 * 1.05 - 62 = +1.0 cm.
    assert length_margin_cm(60, 62, 0.05) == pytest.approx(1.0)


def test_comfort_strain_inverts_the_curve():
    # Tensions on the 50 mm strip: 0, 40, 90, 150, 220, 300 N/m. 65 N/m lies halfway between 40
    # (10 %) and 90 (20 %) -> 15 %. Beyond 300 N/m the curve never reaches it.
    assert comfort_strain(COURSE, WIDTH_MM, 65) == pytest.approx(0.15)
    assert comfort_strain(COURSE, WIDTH_MM, 400) is None


# Test ranges only; real ones come from the team's try-ons (task 6.4) and the study (group 8).
CHEST = ZoneRange(kind="girth", edges=[-0.05, 0.0, 0.10, 0.20])
BACK = ZoneRange(kind="length", edges=[-3.0, 0.0, 4.0])


@pytest.mark.parametrize(
    ("strain", "status"),
    [(-0.06, "too_loose"), (-0.05, "loose"), (0.0, "ok"), (0.05, "ok"), (0.10, "ok"),
     (0.15, "tight"), (0.20, "tight"), (0.21, "too_tight")],
)  # fmt: skip
def test_girth_status_bands(strain, status):
    assert zone_status(CHEST, strain) == status


@pytest.mark.parametrize(
    ("margin", "status"), [(-3.5, "too_short"), (-1.0, "short"), (1.0, "ok"), (4.5, "long")]
)
def test_length_status_bands(margin, status):
    # The spec's back-length case, margin +1.0 cm, is ok.
    assert zone_status(BACK, margin) == status


def test_band_edges_must_increase():
    with pytest.raises(ValueError, match="4 increasing band edges"):
        ZoneRange(kind="girth", edges=[0.0, -0.05, 0.1, 0.2])


def ranges_folder(tmp_path, brand_blocks):
    default = {"brand": "default", "provenance": "test", "fit_blocks": {"default": {
        "chest": {"kind": "girth", "edges": [-0.1, -0.02, 0.08, 0.18]}}}}  # fmt: skip
    (tmp_path / "default.json").write_text(json.dumps(default))
    brand = {"brand": "acme", "provenance": "test", "fit_blocks": brand_blocks}
    (tmp_path / "acme.json").write_text(json.dumps(brand))
    return tmp_path


def test_brand_ranges_are_used_when_present(tmp_path):
    folder = ranges_folder(tmp_path, {"race": {"chest": CHEST.model_dump()}})
    ranges, flags = load_ranges("acme", "race", folder)
    assert ranges["chest"] == CHEST and flags == []


def test_missing_brand_or_block_falls_back_to_default_and_flags_it(tmp_path):
    folder = ranges_folder(tmp_path, {"race": {"chest": CHEST.model_dump()}})
    for brand, block in (("acme", "club"), ("other", "race")):
        ranges, flags = load_ranges(brand, block, folder)
        assert ranges["chest"].edges == [-0.1, -0.02, 0.08, 0.18] and flags == ["default_ranges"]


def example_case():
    examples = DATA / "examples"
    garment = Garment.model_validate_json((examples / "garment-jersey.json").read_text())
    fabric = Fabric.model_validate_json((examples / "fabric-knit.json").read_text())
    body = Measurements(
        pose="hoods",
        girths_cm={"chest_girth": 92, "waist_girth": 80, "hip_girth": 90},
        profiles_cm={"upper_arm_girth": [33, 32, 31, 30, 29, 28, 27, 26], "thigh_girth": [60] * 8},
        lengths_cm={"back_length": 63, "vertical_trunk_girth": 160},
    )
    ranges = {z: CHEST for z in ("chest", "waist", "hem", "sleeve_opening")} | {"back_length": BACK}
    return garment, {"example-knit": fabric}, body, ranges


def test_every_zone_of_every_size():
    # The example jersey (S/M/L chest 80/84/88, waist 72/76/80, hem 78/82/86, sleeve opening
    # 26/27/28, back 60/62/64 cm) on a body with chest 92, waist 80, hip 90, back length 63 and an
    # upper-arm profile reading 27 cm at the sleeve's 12 cm. Comfort tension 65 N/m: the wale
    # curve's 60 N/m at 10 % and 130 at 20 % give 10 + 5/70 · 10 = 10.714 %.
    garment, fabrics, body, ranges = example_case()
    fits = size_fits(garment, fabrics, body, ranges, ["default_ranges"], 65)
    status = {size: {f.zone: f.status for f in zones} for size, zones in fits.items()}
    # S: chest 92/80 - 1 = 15 %, waist 11.1 %, hem 15.4 % tight; sleeve 27/26 - 1 = 3.8 % ok;
    #    back 60 * 1.10714 - 63 = +3.43 cm ok.
    assert status["S"] == {"chest": "tight", "waist": "tight", "hem": "tight",
                           "sleeve_opening": "ok", "back_length": "ok"}  # fmt: skip
    # M: 9.5 %, 5.3 %, 9.8 %, 0 % ok; back 62 * 1.10714 - 63 = +5.64 cm long.
    assert set(status["M"].values()) == {"ok", "long"} and status["M"]["back_length"] == "long"
    # L: sleeve 27/28 - 1 = -3.6 % loose.
    assert status["L"]["sleeve_opening"] == "loose"
    back_s = next(f for f in fits["S"] if f.zone == "back_length")
    assert back_s.margin_cm == pytest.approx(60 * (1 + 0.5 / 7 * 0.1 + 0.1) - 63, abs=1e-9)
    # Chest tension: S 15 % -> 3.25 N -> 65 N/m; M 9.52 % -> 1.9048 N -> 38.10 N/m;
    # L 4.55 % -> 0.9091 N -> 18.18 N/m. Same radius: relative 1, 0.586, 0.280.
    chest = {size: next(f for f in zones if f.zone == "chest") for size, zones in fits.items()}
    assert [round(chest[s].relative_pressure, 3) for s in "SML"] == [1.0, 0.586, 0.280]
    assert all("default_ranges" in f.flags for zones in fits.values() for f in zones)


def test_five_sizes_take_under_50_ms():
    # Spec "Fast and deterministic" (task 6.5): all sizes of one garment from precomputed body
    # measurements in under 50 ms. The example has 3 sizes; two more are added by grading +4 cm.
    import time

    garment, fabrics, body, ranges = example_case()
    sizes = [*garment.sizes]
    for label, step in (("XL", 4), ("XXL", 8)):
        pom = {k: v + step for k, v in garment.sizes[-1].pom.items()}
        sizes.append(garment.sizes[-1].model_copy(update={"label": label, "pom": pom}))
    garment = garment.model_copy(update={"sizes": sizes})
    size_fits(garment, fabrics, body, ranges, [], 65)  # first call imports and warms up
    start = time.perf_counter()
    for _ in range(10):
        fits = size_fits(garment, fabrics, body, ranges, [], 65)
    per_call_ms = (time.perf_counter() - start) / 10 * 1000
    assert len(fits) == 5 and per_call_ms < 50, per_call_ms
