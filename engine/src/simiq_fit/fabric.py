"""Fabric tension from measured stretch curves (design D6)."""

import numpy as np

from simiq_fit.garment import Curve


def tension_n_per_m(curve: Curve, strain: float, specimen_width_mm: float) -> float | None:
    """Tension (N/m) at a strain, interpolated on the curve; None beyond its last point."""
    if strain <= 0:
        return 0.0
    if strain > curve.strain[-1]:
        return None  # out_of_curve: the curve is never extrapolated
    force_n = float(np.interp(strain, curve.strain, curve.force_n))
    return force_n / (specimen_width_mm / 1000)


def comfort_strain(curve: Curve, specimen_width_mm: float, comfort_n_per_m: float) -> float | None:
    """Strain at which the fabric's tension reaches the comfort tension; None if it never does."""
    tensions = [f / (specimen_width_mm / 1000) for f in curve.force_n]
    if tensions[-1] < comfort_n_per_m:
        return None
    return float(np.interp(comfort_n_per_m, tensions, curve.strain))
