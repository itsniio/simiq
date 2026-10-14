"""How a garment size fits a body, zone by zone (design D6)."""

import json
import math
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from simiq_fit.fabric import comfort_strain, tension_n_per_m
from simiq_fit.garment import DATA, Curve, Fabric, Garment
from simiq_fit.measure import PROFILE_STEP_CM, Measurements
from simiq_fit.tape import profile_at

FIT_RANGES = DATA / "fit-ranges"
GIRTH_STATUSES = ("too_loose", "loose", "ok", "tight", "too_tight")
LENGTH_STATUSES = ("too_short", "short", "ok", "long")
Status = Literal["too_loose", "loose", "ok", "tight", "too_tight", "too_short", "short", "long"]


class ZoneRange(BaseModel):
    """Band edges of one zone: strain for girth and loop zones, margin in cm for length zones.

    Girth/loop, 4 edges a<b<c<d: below a too_loose, [a, b) loose, [b, c] ok, (c, d] tight, above
    too_tight. Length, 3 edges a<b<c: below a too_short, [a, b) short, [b, c] ok, above long.
    """

    model_config = ConfigDict(extra="forbid")
    kind: Literal["girth", "loop", "length"]
    edges: list[float]

    @model_validator(mode="after")
    def increasing(self):
        count = 3 if self.kind == "length" else 4
        if len(self.edges) != count or any(
            b <= a for a, b in zip(self.edges, self.edges[1:], strict=False)
        ):
            raise ValueError(f"a {self.kind} zone needs {count} increasing band edges")
        return self


class FitRanges(BaseModel):
    """data/fit-ranges/<brand>.json: band edges per fit block and zone, and their source."""

    model_config = ConfigDict(extra="forbid")
    brand: str
    provenance: str = Field(min_length=1)
    fit_blocks: dict[str, dict[str, ZoneRange]]


def load_ranges(brand: str, fit_block: str, folder: Path = FIT_RANGES):
    """Zone ranges of a brand's fit block, else the defaults; returns (ranges, flags)."""
    path = folder / f"{brand}.json"
    if path.exists():
        ranges = FitRanges.model_validate(json.loads(path.read_text()))
        if fit_block in ranges.fit_blocks:
            return ranges.fit_blocks[fit_block], []
    defaults = FitRanges.model_validate(json.loads((folder / "default.json").read_text()))
    return defaults.fit_blocks["default"], ["default_ranges"]


def zone_status(zone_range: ZoneRange, value: float) -> Status:
    """The band a strain (girth, loop) or margin in cm (length) falls in."""
    e = zone_range.edges
    if zone_range.kind == "length":
        return (
            "too_short"
            if value < e[0]
            else "short"
            if value < e[1]
            else "ok"
            if value <= e[2]
            else "long"
        )
    if value < e[0]:
        return "too_loose"
    if value < e[1]:
        return "loose"
    return "ok" if value <= e[2] else "tight" if value <= e[3] else "too_tight"


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


def length_margin_cm(garment_cm: float, body_cm: float, allowed_strain: float) -> float:
    """Spare length once the garment stretches to the comfort tension: L_g · (1 + ε_allow) − L_b."""
    return garment_cm * (1 + allowed_strain) - body_cm


class ZoneFit(BaseModel):
    """One zone of one size on one body in one pose (design D6)."""

    zone: str
    kind: Literal["girth", "loop", "length"]
    status: Status
    strain: float | None = None  # girth and loop zones
    ease_cm: float | None = None  # loose girth and loop zones
    margin_cm: float | None = None  # length zones
    relative_pressure: float | None = None  # stretched girth zones, against the other sizes
    flags: list[str] = []  # out_of_curve, default_ranges


def body_value_cm(measurements: Measurements, body: str, at_cm: float | None) -> float:
    """The body measurement a zone compares with; a limb profile is read at the zone's level."""
    if at_cm is not None:
        return profile_at(measurements.profiles_cm[body], PROFILE_STEP_CM, at_cm)
    return {**measurements.girths_cm, **measurements.lengths_cm}[body]


def size_fits(
    garment: Garment,
    fabrics: dict[str, Fabric],
    measurements: Measurements,
    ranges: dict[str, ZoneRange],
    range_flags: list[str],
    comfort_n_per_m: float,
) -> dict[str, list[ZoneFit]]:
    """Every zone of every size of a garment on one body in one pose."""
    fits = {size.label: [] for size in garment.sizes}
    for zone in garment.zones:
        fabric = fabrics[garment.fabrics[zone.fabric]]
        curve, width = fabric.curves[zone.direction], fabric.specimen_width_mm
        body = body_value_cm(measurements, zone.body, zone.body_at_cm)
        pressures = {}
        for size in garment.sizes:
            garment_cm = size.pom[zone.pom]
            if zone.kind == "length":
                allowed = comfort_strain(curve, width, comfort_n_per_m)
                flags = [] if allowed is not None else ["out_of_curve"]
                margin = length_margin_cm(
                    garment_cm, body, curve.strain[-1] if allowed is None else allowed
                )
                fit = ZoneFit(zone=zone.id, kind=zone.kind, margin_cm=margin, flags=flags,
                              status=zone_status(ranges[zone.id], margin))  # fmt: skip
            else:
                g = girth_fit(body, garment_cm, curve, width)
                pressures[size.label] = g["pressure_pa"] if g["strain"] > 0 else None
                fit = ZoneFit(zone=zone.id, kind=zone.kind, strain=g["strain"],
                              ease_cm=g["ease_cm"], flags=g["flags"],
                              status=zone_status(ranges[zone.id], g["strain"]))  # fmt: skip
            fit.flags += range_flags
            fits[size.label].append(fit)
        for label, relative in relative_pressures(pressures).items():
            next(f for f in fits[label] if f.zone == zone.id).relative_pressure = relative
    return fits
