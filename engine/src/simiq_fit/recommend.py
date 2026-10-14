"""Size recommendation from per-zone fits: penalty, tie-break and explanation (design D8)."""

from collections import Counter

import numpy as np
from pydantic import BaseModel

from simiq_fit.fit import Status, ZoneFit, ZoneRange, size_fits
from simiq_fit.garment import Fabric, Garment
from simiq_fit.measure import Measurements

SAMPLES = 64  # measurement vectors drawn around the body for the confidence (design D8)
CONFIDENCE_THRESHOLD = 0.6  # below it, an alternative size is named
SAMPLE_SEED = 20261014  # fixed, so the same request always gives the same confidence

# Cost of a zone's status (design D8); a size's penalty is the weighted sum over its zones.
BAND_COST = {
    "ok": 0, "loose": 1, "tight": 1, "short": 1, "long": 1,
    "too_loose": 3, "too_tight": 3, "too_short": 3,
}  # fmt: skip


class Reason(BaseModel):
    """A zone whose status differs between the recommended size and a neighbouring size."""

    size: str
    zone: str
    status: Status


def penalty(fits: list[ZoneFit], weights: dict[str, float]) -> float:
    """Σ weight × BAND_COST over a size's zones."""
    return sum(weights[f.zone] * BAND_COST[f.status] for f in fits)


def off_centre(fits: list[ZoneFit], weights: dict[str, float], ranges: dict[str, ZoneRange]):
    """Σ weight × distance from the ok band's centre, in ok-band widths: the tie-break."""
    total = 0.0
    for f in fits:
        lo, hi = ranges[f.zone].edges[1:3]  # the ok band, for both kinds of zone
        value = f.margin_cm if f.kind == "length" else f.strain
        total += weights[f.zone] * abs(value - (lo + hi) / 2) / (hi - lo)
    return total


def choose_size(
    fits: dict[str, list[ZoneFit]], weights: dict[str, float], ranges: dict[str, ZoneRange]
) -> tuple[str, dict[str, float], list[Reason]]:
    """The size with the lowest penalty (ties: nearest the ok-band centres), and why.

    fits lists sizes from smallest to largest. The explanation names, for the sizes next to the
    recommended one, each zone whose status differs from the recommended size's.
    """
    penalties = {size: penalty(zones, weights) for size, zones in fits.items()}
    best = min(fits, key=lambda s: (penalties[s], off_centre(fits[s], weights, ranges)))
    labels = list(fits)
    i = labels.index(best)
    chosen = {f.zone: f.status for f in fits[best]}
    reasons = [
        Reason(size=neighbour, zone=f.zone, status=f.status)
        for neighbour in labels[max(i - 1, 0) : i] + labels[i + 1 : i + 2]
        for f in fits[neighbour]
        if f.status != chosen[f.zone]
    ]
    return best, penalties, reasons


class Recommendation(BaseModel):
    """The engine's answer for one garment, body and pose (design D8)."""

    size: str
    confidence: float  # share of SAMPLES measurement draws whose best size is `size`
    alternative: str | None  # the next most frequent size, when confidence < CONFIDENCE_THRESHOLD
    pose: str
    penalties: dict[str, float]
    sizes: dict[str, list[ZoneFit]]
    explanation: list[Reason]


def sampled(measurements: Measurements, sds_cm: dict[str, float], rng) -> Measurements:
    """One draw of the body's measurements: each moved by a normal deviation with its SD.

    A profile moves as a whole. The deviation is the standing one, unchanged in the pose: the
    Jacobian from standing to pose measurements (design D8) is taken as identity until task 3.5
    makes the step-3 measurements targets of the fit.
    """

    def moved(values: dict) -> dict:
        return {name: value + rng.normal(0, sds_cm[name]) for name, value in values.items()}

    return Measurements(
        pose=measurements.pose,
        girths_cm=moved(measurements.girths_cm),
        lengths_cm=moved(measurements.lengths_cm),
        profiles_cm={
            name: list(np.asarray(profile) + rng.normal(0, sds_cm[name]))
            for name, profile in measurements.profiles_cm.items()
        },
    )


def recommend(
    garment: Garment,
    fabrics: dict[str, Fabric],
    measurements: Measurements,
    sds_cm: dict[str, float],
    ranges: dict[str, ZoneRange],
    range_flags: list[str],
    comfort_n_per_m: float,
) -> Recommendation:
    """The recommended size, its confidence from SAMPLES draws of the body, and why."""
    weights = {zone.id: zone.weight for zone in garment.zones}
    fits = size_fits(garment, fabrics, measurements, ranges, range_flags, comfort_n_per_m)
    size, penalties, reasons = choose_size(fits, weights, ranges)
    rng = np.random.default_rng(SAMPLE_SEED)
    votes = Counter(
        choose_size(
            size_fits(garment, fabrics, sampled(measurements, sds_cm, rng), ranges, [],
                      comfort_n_per_m),
            weights,
            ranges,
        )[0]
        for _ in range(SAMPLES)
    )  # fmt: skip
    confidence = votes[size] / SAMPLES
    others = [(count, s) for s, count in votes.items() if s != size]
    alternative = max(others)[1] if confidence < CONFIDENCE_THRESHOLD and others else None
    return Recommendation(
        size=size, confidence=confidence, alternative=alternative, pose=measurements.pose,
        penalties=penalties, sizes=fits, explanation=reasons,
    )  # fmt: skip
