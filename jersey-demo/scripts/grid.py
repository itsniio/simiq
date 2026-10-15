"""Demo body grid: engine measurements and recommendations per body and pose, plus posed meshes."""
import json, sys, time
import numpy as np
from simiq_fit.body import fit_body, load_model, pose_body
from simiq_fit.fit import ZoneRange
from simiq_fit.garment import Fabric, Garment
from simiq_fit.inputs import BodyInputs
from simiq_fit.measure import measure_body
from simiq_fit.poses import load_pose
from simiq_fit.recommend import recommend
from simiq_fit.uncertainty import measurement_sds_cm

D = "/tmp/claude-0/demo/data/"
HEIGHTS = range(160, 201, 5)
BMIS = (19, 22, 25, 28, 31)
COMFORT_N_PER_M = 100.0  # demo value
garment = Garment.model_validate(json.load(open(D + "garment.json")))
fabric = Fabric.model_validate(json.load(open(D + "fabric.json")))
ranges = {k: ZoneRange.model_validate(v) for k, v in json.load(open(D + "ranges.json"))["fit_blocks"]["race"].items()}
model = load_model()
bodies = []
for h in HEIGHTS:
    for bmi in BMIS:
        t = time.time()
        w = round(bmi * (h / 100) ** 2, 1)
        inputs = BodyInputs(sex="male", height_cm=h, weight_kg=w, body_type="regular")
        ph = fit_body(model, inputs)
        sds = measurement_sds_cm(inputs)
        key = f"m{h}-{bmi}"
        entry = {"id": key, "height_cm": h, "bmi": bmi, "weight_kg": w, "poses": {}}
        for pose in ("standing", "hoods"):
            m = measure_body(model, ph, pose)
            r = recommend(garment, {fabric.id: fabric}, m, sds, ranges, ["demo_ranges"], COMFORT_N_PER_M)
            entry["poses"][pose] = {"measurements": m.model_dump(), "recommendation": r.model_dump()}
            np.save(D + f"verts-{key}-{pose}.npy", pose_body(model, ph, load_pose(pose))["vertices"].astype(np.float32))
        bodies.append(entry)
        print(key, w, entry["poses"]["standing"]["recommendation"]["size"], entry["poses"]["hoods"]["recommendation"]["size"],
              round(entry["poses"]["hoods"]["recommendation"]["confidence"], 2), f"{time.time()-t:.1f}s", flush=True)
json.dump({"garment": garment.id, "comfort_n_per_m": COMFORT_N_PER_M, "bodies": bodies}, open(D + "grid.json", "w"))
