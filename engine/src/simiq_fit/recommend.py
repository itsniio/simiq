"""Size recommendation from per-zone fits: penalty, tie-break and explanation (design D8)."""

from pydantic import BaseModel

from simiq_fit.fit import Status, ZoneFit, ZoneRange

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
