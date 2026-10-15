"""Compact demo assets: shared base geometry, int16 body positions, slim recommendations JSON."""
import json, shutil
import numpy as np

D = "/tmp/claude-0/demo/data/"; S = "/tmp/claude-0/demo/site/"; W = "/tmp/claude-0/jersey/work/"
F = np.load(W + "anny_f.npy"); UV = np.load(W + "anny_uv.npy"); FUV = np.load(W + "anny_fuv.npy")
zones = np.load("/tmp/claude-0/jersey/fit/zones.npz")
ZONE_IDS = {"chest": 1, "waist": 2, "hem": 3, "sleeve_opening": 4, "back_length": 5}
pairs = np.stack([F.ravel(), FUV.ravel()], 1)
uniq, inv = np.unique(pairs, axis=0, return_inverse=True)
vmap = uniq[:, 0].astype(np.uint16); uv = UV[uniq[:, 1]].astype(np.float32); idx = inv.reshape(-1).astype(np.uint32)
zone_v = np.zeros(int(F.max()) + 1, np.uint8)
zone_v[np.load(W + "covered.npy")] = 128  # bit 7: under the jersey
for name, zid in ZONE_IDS.items():
    zone_v[zones[name]] = 128 | zid
with open(S + "base.bin", "wb") as f:
    for a in (idx, uv, vmap, zone_v[vmap]):
        f.write(a.tobytes())
base = {"indexCount": len(idx), "cornerCount": len(vmap), "vertexCount": int(F.max()) + 1,
        "zones": ZONE_IDS}
grid = json.load(open(D + "grid.json"))
garment = json.load(open(D + "garment.json")); ranges = json.load(open(D + "ranges.json"))
bodies = []
for b in grid["bodies"]:
    q = {}
    with open(S + f"bodies/{b['id']}.bin", "wb") as f:
        for pose in ("standing", "hoods"):
            v = np.load(D + f"verts-{b['id']}-{pose}.npy").astype(np.float64)
            v = np.c_[v[:, 0], v[:, 2], -v[:, 1]]  # Y up, facing +Z
            lo, hi = v.min(0), v.max(0)
            qv = np.round((v - lo) / (hi - lo) * 65535 - 32768).astype(np.int16)
            f.write(qv.tobytes()); q[pose] = {"lo": lo.round(6).tolist(), "hi": hi.round(6).tolist()}
    slim = {}
    for pose, p in b["poses"].items():
        r = p["recommendation"]
        slim[pose] = {
            "size": r["size"], "confidence": round(r["confidence"], 2), "alternative": r["alternative"],
            "explanation": r["explanation"],
            "sizes": {s: [{k: (round(z[k], 3) if isinstance(z[k], float) else z[k]) for k in ("zone", "kind", "status", "strain", "margin_cm", "ease_cm")} for z in zs]
                      for s, zs in r["sizes"].items()},
            "body": {**{k: round(v, 1) for k, v in p["measurements"]["girths_cm"].items()},
                     **{k: round(v, 1) for k, v in p["measurements"]["lengths_cm"].items()}},
        }
    bodies.append({"id": b["id"], "height": b["height_cm"], "bmi": b["bmi"], "weight": b["weight_kg"], "q": q, "poses": slim})
json.dump({"base": base, "garment": {"name": garment["display"]["name"], "subtitle": garment["display"]["subtitle"],
           "sizes": {s["label"]: s["pom"] for s in garment["sizes"]}},
           "ranges": ranges["fit_blocks"]["race"], "bodies": bodies},
          open(S + "demo.json", "w"), ensure_ascii=False, separators=(",", ":"))
shutil.copy(W + "anny_jersey_texture.png", S + "jersey.png")
import os
print({f: os.path.getsize(S + f) for f in ("base.bin", "demo.json", "jersey.png")}, os.path.getsize(S + "bodies/m180-22.bin"))
