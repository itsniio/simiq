"""Strain, ease, tension and relative pressure (fit-engine-poc 6.1, 6.2), hand-computed."""

import pytest

from simiq_fit.fabric import tension_n_per_m
from simiq_fit.fit import girth_fit, relative_pressures
from simiq_fit.garment import Curve

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
