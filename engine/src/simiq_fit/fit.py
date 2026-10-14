"""How a garment size fits a body, zone by zone (design D6)."""

import math

from simiq_fit.fabric import tension_n_per_m
from simiq_fit.garment import Curve


def girth_fit(body_cm: float, garment_cm: float, curve: Curve, specimen_width_mm: float) -> dict:
    """Strain, ease, tension and Laplace pressure of a girth or loop zone.

    ε = C_body / C_garment − 1. Loose (ε ≤ 0): ease = −ε · C_garment. Stretched: tension from the
    curve and pressure P = T / r with r = C_body / 2π, unless ε lies beyond the curve.
    """
    strain = body_cm / garment_cm - 1
    if strain <= 0:
        return dict(strain=strain, ease_cm=-strain * garment_cm, tension_n_per_m=0.0,
                    pressure_pa=0.0, flags=[])  # fmt: skip
    tension = tension_n_per_m(curve, strain, specimen_width_mm)
    if tension is None:
        return dict(strain=strain, ease_cm=None, tension_n_per_m=None, pressure_pa=None,
                    flags=["out_of_curve"])  # fmt: skip
    radius_m = body_cm / 100 / (2 * math.pi)
    return dict(strain=strain, ease_cm=None, tension_n_per_m=tension,
                pressure_pa=tension / radius_m, flags=[])  # fmt: skip


def relative_pressures(pressures: dict[str, float | None]) -> dict[str, float | None]:
    """Each size's pressure over the highest among the sizes; pressures are never shown absolute."""
    known = [p for p in pressures.values() if p is not None]
    top = max(known, default=0.0)
    return {
        size: (None if p is None else (p / top if top > 0 else 0.0))
        for size, p in pressures.items()
    }
