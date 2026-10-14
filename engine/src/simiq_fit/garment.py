"""Garment and fabric records: the contract shared by engine, API and onboarding (design D5)."""

import datetime as dt
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from simiq_fit.measure import GIRTHS, LENGTHS, PROFILES

DATA = Path(__file__).resolve().parents[3] / "data"
BODY_MEASUREMENTS = GIRTHS + PROFILES + LENGTHS
CURVE_MIN_STRAIN = 0.40  # a stretch curve covers at least 0-40 % strain
CURVE_MIN_POINTS = 5
SHOP_FIELDS = ("price", "prices", "currency", "url", "product_url", "link")  # belong to the shop

GarmentType = Literal["jersey", "bib_shorts"]
Direction = Literal["course", "wale"]
PANEL_CATEGORY = {"jersey": "jerseys", "bib_shorts": "bib_shorts"}


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Provenance(Strict):
    """Who measured, when and how."""

    by: str = Field(min_length=1)
    date: dt.date
    method: str = Field(min_length=1)


class Localized(Strict):
    """A user-facing text in every language the viewer ships."""

    sk: str = Field(min_length=1)
    cs: str = Field(min_length=1)
    en: str = Field(min_length=1)


class Color(Strict):
    name: Localized
    swatch: str = Field(pattern=r"^#[0-9a-fA-F]{6}$")
    image: str = Field(min_length=1)


class Display(Strict):
    """What the product panel shows. Prices and product links belong to the shop, not here."""

    name: Localized
    subtitle: Localized
    colors: list[Color] = Field(min_length=1)
    features: list[Localized] = Field(min_length=1)


class Zone(Strict):
    """Where garment and body are compared: a point of measure against a body measurement."""

    id: str = Field(min_length=1)
    kind: Literal["girth", "loop", "length"]
    pom: str = Field(min_length=1)
    body: str
    body_at_cm: float | None = Field(default=None, ge=0)  # level on a limb profile
    fabric: str
    direction: Direction
    weight: float = Field(gt=0)

    @model_validator(mode="after")
    def known_body_measurement(self):
        if self.body not in BODY_MEASUREMENTS:
            raise ValueError(
                f"zone {self.id!r}: unknown body measurement {self.body!r}; "
                f"available: {', '.join(BODY_MEASUREMENTS)}"
            )
        if (self.body in PROFILES) != (self.body_at_cm is not None):
            raise ValueError(
                f"zone {self.id!r}: body_at_cm is required for a limb profile "
                f"({', '.join(PROFILES)}) and only for one"
            )
        return self


class Size(Strict):
    label: str = Field(min_length=1)
    pom: dict[str, float]  # relaxed garment dimensions in cm; flat circumferences stored doubled
    provenance: Provenance

    @field_validator("pom")
    @classmethod
    def positive(cls, pom):
        bad = [name for name, value in pom.items() if not value > 0]
        if bad:
            raise ValueError(f"points of measure must be positive cm: {', '.join(bad)}")
        return pom


class ChartRow(Strict):
    """One size of the brand's published size chart: body-measurement ranges in cm."""

    label: str = Field(min_length=1)
    ranges: dict[str, tuple[float, float]] = Field(min_length=1)


class Garment(Strict):
    schema_version: Literal[1]
    id: str = Field(min_length=1)
    type: GarmentType
    brand: str = Field(min_length=1)
    model: str = Field(min_length=1)
    fit_block: str = Field(min_length=1)
    source: Literal["brand_techpack", "brand_cad", "team_measured"]
    display: Display
    zones: list[Zone] = Field(min_length=1)
    sizes: list[Size] = Field(min_length=1)
    fabrics: dict[str, str] = Field(min_length=1)  # zone fabric key -> fabric record id
    size_chart: list[ChartRow] = Field(min_length=1)

    @model_validator(mode="before")
    @classmethod
    def no_shop_fields(cls, data):
        found = [key for key in SHOP_FIELDS if isinstance(data, dict) and key in data]
        if found:
            raise ValueError(
                f"{', '.join(found)}: prices and product links belong to the shop manifest, "
                "not the garment record"
            )
        return data

    @model_validator(mode="after")
    def consistent(self):
        errors = []
        for name, labels in (("zone", [z.id for z in self.zones]), ("size", self.size_labels)):
            if len(set(labels)) != len(labels):
                errors.append(f"{name} ids repeat: {labels}")
        for zone in self.zones:
            if zone.fabric not in self.fabrics:
                errors.append(f"zone {zone.id!r}: fabric {zone.fabric!r} is not in fabrics")
            for size in self.sizes:
                if zone.pom not in size.pom:
                    errors.append(f"size {size.label}: missing {zone.pom!r} (zone {zone.id!r})")
        if errors:
            raise ValueError("; ".join(errors))
        return self

    @property
    def size_labels(self) -> list[str]:
        return [size.label for size in self.sizes]

    @property
    def panel_category(self) -> str:
        """The product panel's category, from the garment type."""
        return PANEL_CATEGORY[self.type]


def grading_warnings(garment: Garment) -> list[str]:
    """Points of measure that do not grow from one size to the next, sizes in listed order."""
    warnings = []
    labels = garment.size_labels
    for pom in sorted({zone.pom for zone in garment.zones}):
        values = [size.pom[pom] for size in garment.sizes]
        for i in range(1, len(values)):
            if not values[i] > values[i - 1]:
                warnings.append(
                    f"{garment.id}: {pom} does not increase from {labels[i - 1]} "
                    f"({values[i - 1]}) to {labels[i]} ({values[i]})"
                )
    return warnings


class Curve(Strict):
    """Force on a specimen against its strain (0.1 = 10 %), from one stretch test direction."""

    strain: list[float]
    force_n: list[float]

    @model_validator(mode="after")
    def covers_and_rises(self):
        s, f = self.strain, self.force_n
        if len(s) != len(f):
            raise ValueError(f"{len(s)} strains but {len(f)} forces")
        if len(s) < CURVE_MIN_POINTS:
            raise ValueError(f"{len(s)} points; a curve needs at least {CURVE_MIN_POINTS}")
        if s[0] != 0 or s[-1] < CURVE_MIN_STRAIN:
            raise ValueError(
                f"covers {s[0]:.0%}-{s[-1]:.0%} strain; a curve must cover 0-{CURVE_MIN_STRAIN:.0%}"
            )
        if any(b <= a for a, b in zip(s, s[1:], strict=False)):
            raise ValueError("strains must increase")
        drops = [f"{s[i]:.0%}->{s[i + 1]:.0%}" for i in range(len(f) - 1) if f[i + 1] < f[i]]
        if drops:
            raise ValueError(f"force decreases between strains {', '.join(drops)}")
        return self


class Fabric(Strict):
    schema_version: Literal[1]
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    composition: str = Field(min_length=1)  # e.g. "78% polyamide, 22% elastane"
    weight_g_m2: float = Field(gt=0)
    specimen_width_mm: float = Field(gt=0)
    method: Literal["strip_test_weights", "supplier_datasheet", "lab"]
    curves: dict[Direction, Curve]
    provenance: Provenance

    @field_validator("curves")
    @classmethod
    def both_directions(cls, curves):
        missing = [d for d in ("course", "wale") if d not in curves]
        if missing:
            raise ValueError(f"missing curve for {', '.join(missing)}")
        return curves


class ChartLookup(BaseModel):
    """The brand size chart's answer for one body: the evaluation baseline (D9)."""

    size: str | None  # None: a measure lies beyond the chart's largest size
    by_measure: dict[str, str | None]  # the size each published measure points to
    rule: Literal["single_measure", "measures_agree", "larger_size", "beyond_chart"]


def chart_size(chart: list[ChartRow], body_cm: dict[str, float]) -> ChartLookup:
    """Size from the brand's chart: each measure's size, and the larger one when they disagree.

    A range covers lo <= value < hi, so a value on a shared bound goes to the larger size; the
    largest size also includes its upper bound. Measures the chart does not publish are ignored.
    """
    labels = [row.label for row in chart]
    by_measure = {}
    for measure, value in body_cm.items():
        if not any(measure in row.ranges for row in chart):
            continue
        found = None
        for i, row in enumerate(chart):
            lo, hi = row.ranges[measure]
            if lo <= value < hi or (i == len(chart) - 1 and value == hi):
                found = row.label
        by_measure[measure] = found
    if not by_measure:
        raise ValueError(f"the chart publishes none of {', '.join(body_cm)}")
    if None in by_measure.values():
        return ChartLookup(size=None, by_measure=by_measure, rule="beyond_chart")
    sizes = set(by_measure.values())
    size = max(sizes, key=labels.index)
    rule = "single_measure" if len(by_measure) == 1 else "measures_agree"
    return ChartLookup(
        size=size, by_measure=by_measure, rule="larger_size" if len(sizes) > 1 else rule
    )


def load_size_chart(name: str) -> list[ChartRow]:
    """A brand's published body-measurement chart from data/size-charts/<name>.json."""
    data = json.loads((DATA / "size-charts" / f"{name}.json").read_text())
    return [ChartRow.model_validate(row) for row in data["size_chart"]]


def template_zones(garment_type: GarmentType) -> list[Zone]:
    """The default zones of a garment type, from data/templates/<type>.json."""
    data = json.loads((DATA / "templates" / f"{garment_type}.json").read_text())
    return [Zone.model_validate(zone) for zone in data["zones"]]


def write_schemas(folder: Path) -> list[Path]:
    """JSON Schema files of the garment and fabric records, for components in other languages."""
    folder.mkdir(parents=True, exist_ok=True)
    written = []
    for name, model in (("garment", Garment), ("fabric", Fabric)):
        path = folder / f"{name}.schema.json"
        path.write_text(json.dumps(model.model_json_schema(), indent=2) + "\n")
        written.append(path)
    return written
