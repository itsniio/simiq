"""Cloth-sim spike runner: checks and comparisons on the CLO reference data (kept outside git).

uv run python scripts/cloth_spike.py calibrate-uv  # mm per UV unit from the DXF, to manifest
uv run python scripts/cloth_spike.py mesh          # the starting drape, checked (task 2.2)
"""

import json
import sys

import numpy as np
from clo_cache_extract import SPIKE_DIR

from simiq_fit.garment_mesh import load_garment, read_obj

DXF = SPIKE_DIR.parents[1] / "Mens Cycling Jersey-Green Printed.dxf"
CASES = SPIKE_DIR / "cases"
MESH = CASES / "garment-uv.obj"
FABRIC = "FABRIC_13"
SIZE_FACTOR = {
    "S": 68.5 / 72,
    "M": 1.0,
    "L": 75.5 / 72,
}  # as jersey-demo/scripts/clo_spike_export.py


def dxf_pieces(path):
    """Cut outline (layer 1) and grain line (layer 7) of every AAMA block, in mm."""
    lines = [line.strip() for line in path.read_text(errors="ignore").splitlines()]
    pieces, block, entity = [], None, None
    for code, value in zip(lines[0::2], lines[1::2], strict=False):
        if code == "0":
            if entity is not None and block is not None:
                block["entities"].append(entity)
            entity = None
            if value == "BLOCK":
                block = {"entities": []}
            elif value == "ENDBLK":
                pieces.append(block)
                block = None
            elif block is not None:
                entity = {"type": value, "layer": None, "points": [], "x": None}
        elif entity is not None:
            if code == "8":
                entity["layer"] = value
            elif code in ("10", "11"):
                entity["x"] = float(value)
            elif code in ("20", "21") and entity["x"] is not None:
                entity["points"].append((entity["x"], float(value)))
                entity["x"] = None
    out = []
    for block in pieces:
        outline = np.array(
            [
                e["points"][0]
                for e in block["entities"]
                if e["type"] == "VERTEX" and e["layer"] == "1"
            ]
        )
        grain = [
            e["points"] for e in block["entities"] if e["type"] == "LINE" and e["layer"] == "7"
        ]
        out.append({"outline": outline, "grain": np.array(grain[0])})
    return out


def polygon_area(p):
    return 0.5 * abs(p[:, 0] @ np.roll(p[:, 1], 1) - p[:, 1] @ np.roll(p[:, 0], 1))


def calibrate_uv():
    """mm per UV unit along u and v: each piece's DXF size against its UV size, grain along v."""
    _, uvs, blocks = read_obj(MESH)
    rows = []
    for _material, corners in (b for b in blocks if FABRIC in b[0]):
        uv = uvs[np.unique(np.array(corners)[:, :, 1])]
        tri = uvs[np.array(corners)[:, :, 1]]
        e1, e2 = tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]
        rows.append((np.abs(e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0]).sum() / 2, np.ptp(uv, 0)))
    fits = []
    for piece in dxf_pieces(DXF):
        area, size = polygon_area(piece["outline"]), np.ptp(piece["outline"], 0)
        grain = piece["grain"][1] - piece["grain"][0]
        across, along = (size[1], size[0]) if abs(grain[0]) > abs(grain[1]) else (size[0], size[1])
        uv_area, uv_size = min(
            rows, key=lambda r: abs(r[0] * across * along / (r[1][0] * r[1][1]) - area)
        )
        fits.append((across / uv_size[0], along / uv_size[1]))
    fits = np.array(fits)
    uv_mm = fits.mean(0).round(2).tolist()
    spread = (fits.std(0) / fits.mean(0) * 100).round(3).tolist()
    manifest = json.loads((CASES / "manifest.json").read_text())
    manifest["uv_mm_per_unit"] = {
        "course_u": uv_mm[0],
        "wale_v": uv_mm[1],
        "spread_percent": spread,
        "how": "per piece, DXF outline size across and along its grain line over the UV size "
        "(CLO lays every piece out with the grain along v); mean of the 15 pieces",
    }
    (CASES / "manifest.json").write_text(json.dumps(manifest, indent=1))
    print("mm per UV unit (course u, wale v):", uv_mm, "spread %", spread)


def shrinkage(size):
    """Per piece (course, wale) simulation shrinkage of a size, as fractions."""
    base = json.loads((SPIKE_DIR / "base_shrinkage.json").read_text())
    return [(b["width"] / 100 * SIZE_FACTOR[size], b["height"] / 100) for b in base]


def uv_mm():
    u = json.loads((CASES / "manifest.json").read_text())["uv_mm_per_unit"]
    return u["course_u"], u["wale_v"]


def mesh():
    """Task 2.2: the starting drape as one welded garment, with piece and seam figures."""
    start = np.load(CASES / "standing-M.npz")["start-178-75"]
    garment = load_garment(MESH, uv_mm(), shrinkage("M"), fabric=FABRIC, positions=start)
    flat = load_garment(MESH, uv_mm(), [(1.0, 1.0)] * 15, fabric=FABRIC, positions=start)
    n = len(garment.positions)
    parent = np.arange(n)

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for a, b, c in garment.faces:
        parent[root(b)] = root(a)
        parent[root(c)] = root(a)
    components = len({root(i) for i in range(n)})
    # Edges used by one face of a piece are that piece's outline; welded ones lie on two pieces.
    outline_mm, seam_edges = 0.0, set()
    for k in range(garment.piece.max() + 1):
        faces, rest = flat.faces[flat.piece == k], flat.rest_mm[flat.piece == k]
        sides = [
            ((f[i], f[(i + 1) % 3]), r[(i + 1) % 3] - r[i])
            for f, r in zip(faces, rest, strict=True)
            for i in range(3)
        ]
        count = {}
        for (a, b), _ in sides:
            count[tuple(sorted((a, b)))] = count.get(tuple(sorted((a, b))), 0) + 1
        for (a, b), d in sides:
            if count[tuple(sorted((a, b)))] == 1:
                outline_mm += np.linalg.norm(d)
                seam_edges.add((k, tuple(sorted((a, b)))))
    by_edge = {}
    for k, e in seam_edges:
        by_edge.setdefault(e, set()).add(k)
    seam_mm = sum(np.linalg.norm(garment.positions[a] - garment.positions[b])
                  for (a, b), ks in by_edge.items() if len(ks) > 1)  # fmt: skip
    dxf_mm = sum(np.linalg.norm(np.roll(p["outline"], -1, 0) - p["outline"], axis=1).sum()
                 for p in dxf_pieces(DXF))  # fmt: skip
    print(f"pieces {garment.piece.max() + 1}, faces {len(garment.faces)}, welded vertices {n}, "
          f"connected parts {components}")  # fmt: skip
    print(f"piece outlines from UV {outline_mm / 10:.1f} cm, DXF cut lines {dxf_mm / 10:.1f} cm; "
          f"sewn seams {seam_mm / 10:.0f} cm in the drape")  # fmt: skip


if __name__ == "__main__":
    {"calibrate-uv": calibrate_uv, "mesh": mesh}[sys.argv[1]]()
