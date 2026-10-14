"""Garment and fabric records (fit-engine-poc 5.1, 5.2): the garment-model spec scenarios."""

import copy
import json

import pytest
from pydantic import ValidationError

from simiq_fit.cli import check_records, main
from simiq_fit.garment import (
    DATA,
    ChartRow,
    Fabric,
    Garment,
    chart_size,
    grading_warnings,
    load_size_chart,
    template_zones,
)

EXAMPLES = DATA / "examples"


def example(name):
    return json.loads((EXAMPLES / f"{name}.json").read_text())


def errors_of(model, data):
    with pytest.raises(ValidationError) as error:
        model.model_validate(data)
    return str(error.value)


def test_valid_records():
    jersey = Garment.model_validate(example("garment-jersey"))
    assert jersey.panel_category == "jerseys"  # derived from the type
    assert len(jersey.display.colors) == 2 and jersey.display.name.cs == "Ukázkový dres"
    Garment.model_validate(example("garment-bib-shorts"))
    Fabric.model_validate(example("fabric-knit"))


def test_missing_sizes_is_named():
    data = example("garment-jersey")
    del data["sizes"]
    assert "sizes" in errors_of(Garment, data)


def test_missing_point_of_measure_names_size_and_pom():
    data = example("garment-jersey")
    del data["sizes"][2]["pom"]["chest_circumference"]
    message = errors_of(Garment, data)
    assert "size L" in message and "chest_circumference" in message


def test_grading_warning_when_chest_does_not_grow():
    data = example("garment-jersey")
    data["sizes"][2]["pom"]["chest_circumference"] = 84  # L equal to M
    warnings = grading_warnings(Garment.model_validate(data))
    assert warnings == [
        "example-jersey: chest_circumference does not increase from M (84.0) to L (84.0)"
    ]
    assert grading_warnings(Garment.model_validate(example("garment-jersey"))) == []


def test_unknown_body_measurement_names_zone_and_measurement():
    data = example("garment-jersey")
    data["zones"][0]["body"] = "neck_girth"
    message = errors_of(Garment, data)
    assert "zone 'chest'" in message and "neck_girth" in message


def test_profile_zone_needs_a_level():
    data = example("garment-jersey")
    del data["zones"][3]["body_at_cm"]  # sleeve_opening on the upper-arm profile
    assert "body_at_cm is required" in errors_of(Garment, data)


def test_price_is_rejected_with_the_reason():
    data = example("garment-jersey") | {"price": 129.0}
    message = errors_of(Garment, data)
    assert "price" in message and "belong to the shop manifest" in message


def test_untranslated_name_is_rejected():
    data = example("garment-jersey")
    del data["display"]["name"]["cs"]
    assert "cs" in errors_of(Garment, data)


def test_team_measured_size_keeps_its_provenance():
    size = Garment.model_validate(example("garment-jersey")).sizes[1]
    assert (size.provenance.by, str(size.provenance.date)) == ("simiq team", "2026-10-14")
    data = example("garment-jersey")
    del data["sizes"][1]["provenance"]
    assert "provenance" in errors_of(Garment, data)


def test_curve_ending_at_20_percent_fails_for_that_direction():
    data = example("fabric-knit")
    data["curves"]["wale"] = {"strain": [0, 0.05, 0.1, 0.15, 0.2], "force_n": [0, 1, 2, 3, 4]}
    message = errors_of(Fabric, data)
    assert "curves.wale" in message and "must cover 0-40%" in message


def test_curve_whose_force_drops_fails_for_that_direction():
    data = example("fabric-knit")
    data["curves"]["course"]["force_n"][3] = 4.0  # 7.5 N at 30 % becomes 4.0, below 4.5 at 20 %
    message = errors_of(Fabric, data)
    assert "curves.course" in message and "force decreases between strains 20%->30%" in message


def test_fabric_needs_both_directions():
    data = example("fabric-knit")
    del data["curves"]["wale"]
    assert "missing curve for wale" in errors_of(Fabric, data)


def test_jersey_template_zones():
    assert [z.id for z in template_zones("jersey")] == [
        "chest", "waist", "hem", "sleeve_opening", "back_length",
    ]  # fmt: skip


def test_bib_shorts_template_zones():
    assert [z.id for z in template_zones("bib_shorts")] == ["hip", "leg_opening", "vertical_loop"]


def test_validate_data_checks_fabric_references(tmp_path):
    garment = copy.deepcopy(example("garment-jersey"))
    garment["fabrics"]["main"] = "no-such-fabric"
    path = tmp_path / "garment.json"
    path.write_text(json.dumps(garment))
    errors, _ = check_records([path, EXAMPLES / "fabric-knit.json"])
    assert errors == [f"{path}: fabrics.main: no fabric record 'no-such-fabric' among the files"]


def test_validate_data_passes_the_examples(capsys):
    files = [str(p) for p in sorted(EXAMPLES.glob("*.json"))]
    assert main(["validate-data", *files]) == 0
    assert "3 files, 0 errors, 0 warnings" in capsys.readouterr().out


def test_schema_export_validates_the_examples(tmp_path):
    # Spec scenario "Schema export": the written JSON Schemas accept the example records.
    jsonschema = pytest.importorskip("jsonschema")
    assert main(["schema", "--out", str(tmp_path)]) == 0
    garment_schema = json.loads((tmp_path / "garment.schema.json").read_text())
    fabric_schema = json.loads((tmp_path / "fabric.schema.json").read_text())
    jsonschema.validate(example("garment-jersey"), garment_schema)
    jsonschema.validate(example("garment-bib-shorts"), garment_schema)
    jsonschema.validate(example("fabric-knit"), fabric_schema)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({k: v for k, v in example("fabric-knit").items() if k != "curves"},
                            fabric_schema)  # fmt: skip


def test_published_schemas_match_the_models():
    # data/schema is what other components read; `simiq-fit schema` rewrites it after a change.
    for name, model in (("garment", Garment), ("fabric", Fabric)):
        published = json.loads((DATA / "schema" / f"{name}.schema.json").read_text())
        assert published == model.model_json_schema(), name


CHART = [
    ChartRow(label="S", ranges={"chest": (88, 92), "waist": (72, 76)}),
    ChartRow(label="M", ranges={"chest": (92, 96), "waist": (76, 80)}),
    ChartRow(label="L", ranges={"chest": (96, 100), "waist": (80, 84)}),
]


def test_chart_lookup():
    # Spec scenario: chest 95 cm where M covers 92-96 cm.
    result = chart_size(CHART, {"chest": 95})
    assert (result.size, result.rule) == ("M", "single_measure")


def test_measures_disagree_the_larger_size_decides():
    result = chart_size(CHART, {"chest": 94, "waist": 81})  # chest M, waist L
    assert (result.size, result.rule) == ("L", "larger_size")
    assert result.by_measure == {"chest": "M", "waist": "L"}


def test_a_shared_bound_goes_to_the_larger_size_and_the_top_bound_is_kept():
    assert chart_size(CHART, {"chest": 92}).size == "M"
    assert chart_size(CHART, {"chest": 100}).size == "L"
    assert chart_size(CHART, {"chest": 101}).rule == "beyond_chart"


def test_unpublished_measures_are_ignored():
    assert chart_size(CHART, {"chest": 95, "inseam": 80}).by_measure == {"chest": "M"}
    with pytest.raises(ValueError, match="publishes none"):
        chart_size(CHART, {"inseam": 80})


def test_isadore_published_chart():
    # isadore.com size guide, retrieved 2026-10-14: M is chest 97-103, waist 85-91, hip 100-106.
    chart = load_size_chart("isadore-men")
    assert [row.label for row in chart] == ["XXS", "XS", "S", "M", "L", "XL", "XXL", "3XL"]
    assert chart_size(chart, {"chest": 100, "waist": 88, "hip": 103}).size == "M"
    assert chart_size(chart, {"chest": 100, "waist": 92}).size == "L"
