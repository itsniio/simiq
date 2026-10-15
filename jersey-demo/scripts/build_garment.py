"""Demo garment (RenderHub green jersey) graded XS-XXL from its CLO-effective size M, with demo ranges."""
import json
from simiq_fit.garment import DATA, Fabric, Garment, template_zones

OUT = "/tmp/claude-0/demo/data/"
M = {"chest_circumference": 86.4, "waist_circumference": 79.6, "hem_circumference": 70.6,
     "sleeve_opening_circumference": 24.0, "center_back_length": 59.6}
STEP = {"chest_circumference": 4, "waist_circumference": 4, "hem_circumference": 4,
        "sleeve_opening_circumference": 1, "center_back_length": 1.5}
LABELS = ["XS", "S", "M", "L", "XL", "XXL"]
prov = {"by": "simiq demo", "date": "2026-10-15",
        "method": "CLO pattern length x 0.72 weft shrinkage (size M), graded by fixed steps; demo only"}
sizes = [{"label": l, "provenance": prov,
          "pom": {k: round(v + (i - 2) * STEP[k], 1) for k, v in M.items()}} for i, l in enumerate(LABELS)]
zones = [z.model_dump(exclude_none=True) for z in template_zones("jersey")]
for z in zones:
    if z["id"] == "sleeve_opening":
        z["fabric"] = "main"; z["body_at_cm"] = 12
loc = lambda sk, cs, en: {"sk": sk, "cs": cs, "en": en}
garment = {
    "schema_version": 1, "id": "demo-green-jersey", "type": "jersey", "brand": "simiq-demo",
    "model": "Green Printed Jersey (demo)", "fit_block": "race", "source": "brand_cad",
    "display": {
        "name": loc("Ukážkový dres", "Ukázkový dres", "Demo jersey"),
        "subtitle": loc("Pretekársky strih, zelená potlač", "Závodní střih, zelený potisk", "Race fit, green print"),
        "colors": [{"name": loc("Zelená", "Zelená", "Green"), "swatch": "#1f8a4f", "image": "images/demo-green.webp"}],
        "features": [loc("Pružná pletenina", "Pružný úplet", "Stretch knit"),
                     loc("Tri zadné vrecká", "Tři zadní kapsy", "Three rear pockets")],
    },
    "zones": zones, "sizes": sizes, "fabrics": {"main": "demo-knit"},
    "size_chart": [{"label": s["label"], "ranges": {"chest": [round(s["pom"]["chest_circumference"] * 1.0, 1),
                                                              round(s["pom"]["chest_circumference"] * 1.16, 1)]}} for s in sizes],
}
Garment.model_validate(garment)
fabric = json.loads((DATA / "examples" / "fabric-knit.json").read_text()) | {"id": "demo-knit", "name": "Demo stretch knit"}
Fabric.model_validate(fabric)
ranges = {"brand": "simiq-demo", "provenance": "demo values chosen for the demo, not from try-ons",
          "fit_blocks": {"race": {
              "chest": {"kind": "girth", "edges": [-0.06, 0.0, 0.16, 0.26]},
              "waist": {"kind": "girth", "edges": [-0.06, 0.0, 0.16, 0.26]},
              "hem": {"kind": "girth", "edges": [0.0, 0.15, 0.45, 0.6]},
              "sleeve_opening": {"kind": "girth", "edges": [-0.06, 0.0, 0.18, 0.28]},
              "back_length": {"kind": "length", "edges": [-3, 0, 8]}}}}
for name, obj in (("garment", garment), ("fabric", fabric), ("ranges", ranges)):
    json.dump(obj, open(OUT + f"{name}.json", "w"), ensure_ascii=False, indent=1)
for s in sizes: print(s["label"], s["pom"])
