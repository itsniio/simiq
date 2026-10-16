"""Cloth-sim spike runner: checks and comparisons on the CLO reference data (kept outside git).

uv run python scripts/cloth_spike.py calibrate-uv  # mm per UV unit from the DXF, to manifest
uv run python scripts/cloth_spike.py mesh          # the starting drape, checked (task 2.2)
uv run python scripts/cloth_spike.py zones         # garment faces of each zone, to zones.npz (3.2)
uv run python scripts/cloth_spike.py strain        # zone strains of every CLO case (task 3.2)
uv run python scripts/cloth_spike.py pressure      # relative zone pressure by size (task 3.3)
"""

import json
import struct
import sys

import numpy as np
from clo_cache_extract import FRAMES, SPIKE_DIR

from simiq_fit.fit import relative_pressures
from simiq_fit.garment import DATA, Fabric
from simiq_fit.garment_mesh import load_garment, read_obj
from simiq_fit.surface_strain import face_areas, pressures, strains, zone_means

DXF = SPIKE_DIR.parents[1] / "Mens Cycling Jersey-Green Printed.dxf"
CASES = SPIKE_DIR / "cases"
MESH = CASES / "garment-uv.obj"
FABRIC = "FABRIC_13"
START_BODY = SPIKE_DIR.parent / "bodies" / "anny-m178-75-apose.obj"  # CLO frame, cm, Anny's order
BODY_SEQUENCES = {  # the point caches that drove CLO, CLO frame in cm, Anny's vertex order
    "standing": "anny-standing-sequence.pc2",
    "hoods": "anny-hoods-body-sequence.pc2",
    "drops": "anny-drops-standing-sequence.pc2",
}
ZONES = SPIKE_DIR / "zones.npz"  # face indices of the licensed mesh: outside git like the mesh
ZONE_NAMES = ("chest", "waist", "hem", "sleeve_opening", "back_length")
GIRTH_ZONES = ("chest", "waist", "hem", "sleeve_opening")
NEAREST_MM = 30  # a garment face belongs to a body zone only this close to the body
BODIES = ("178-75", "180-64", "176-88", "192-82")
POSES = ("standing", "hoods", "drops")
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


def to_anny_axes(points_cm):
    """CLO frame (Y up, facing +Z) to Anny's axes (Z up, facing −Y), in metres; offset kept."""
    return np.c_[points_cm[:, 0], -points_cm[:, 2], points_cm[:, 1]] / 100


def body_zones(vertices, faces, parts, data):
    """Body vertices of each zone: the landmark bands of jersey-demo/scripts/heatmap.py."""
    from simiq_fit.measure import girth_sections

    lm = data["landmarks"]
    sections = girth_sections(vertices, faces, parts, lm, data["waist_ring"])
    torso = np.unique(faces[parts["torso"]])

    def band(point, normal, half=0.025):
        return torso[np.abs((vertices[torso] - point) @ normal) < half]

    sets = {
        "chest": band(sections["chest_girth"]["point"], sections["chest_girth"]["normal"]),
        "waist": band(sections["waist_girth"]["point"], sections["waist_girth"]["normal"]),
        "hem": band(vertices[data["hip_ring"]].mean(0), np.array([0, 0, 1.0])),
    }
    arm = []
    for side in ("L", "R"):
        a = vertices[lm[f"armpit.{side}"]]
        d = np.linalg.norm(vertices - a, axis=1)
        lateral = np.abs(vertices[:, 0] - vertices[lm["c7"], 0]) > abs(a[0] - vertices[lm["c7"], 0])
        arm.append(np.where((d > 0.10) & (d < 0.14) & lateral & (vertices[:, 2] > a[2] - 0.25))[0])
    sets["sleeve_opening"] = np.concatenate(arm)
    c7, hip_back = vertices[lm["c7"]], vertices[lm["hip_back"]]
    sets["back_length"] = np.where(
        (np.abs(vertices[:, 0] - c7[0]) < 0.03)
        & (vertices[:, 1] > c7[1] - 0.02)
        & (vertices[:, 2] < c7[2])
        & (vertices[:, 2] > hip_back[2])
    )[0]
    return sets


def nearest(points, targets, chunk=1000):
    """Index of and distance to the nearest target of each point."""
    index, distance = np.empty(len(points), int), np.empty(len(points))
    squared = (targets**2).sum(1)
    for i in range(0, len(points), chunk):
        p = points[i : i + chunk]
        d2 = (p**2).sum(1)[:, None] + squared[None] - 2 * p @ targets.T
        index[i : i + chunk] = d2.argmin(1)
        distance[i : i + chunk] = np.sqrt(np.maximum(d2.min(1), 0))
    return index, distance


def body_faces():
    lines = [line.split()[1:4] for line in START_BODY.open() if line.startswith("f ")]
    return np.array(lines, int) - 1


def posed_body(pose, body):
    """Body vertices (mm, CLO frame) at the frame of a case, from the point cache that drove CLO."""
    path = START_BODY.parent / BODY_SEQUENCES[pose]
    with path.open("rb") as f:
        _magic, _version, points, _start, _rate, _samples = struct.unpack("<12siiffi", f.read(32))
        f.seek(32 + FRAMES[pose][body] * points * 12)
        return np.frombuffer(f.read(points * 12), "<f4").reshape(-1, 3).astype(float) * 10


def zones():
    """Garment faces of each zone, chosen on the starting drape by the nearest body vertex."""
    from simiq_fit.body import body_parts, load_model
    from simiq_fit.landmarks import load_landmarks

    model = load_model()
    body_cm = np.loadtxt([l for l in START_BODY.open() if l.startswith("v ")], usecols=(1, 2, 3))  # noqa: E741
    body = to_anny_axes(body_cm)
    sets = body_zones(body, np.asarray(model.faces), body_parts(model), load_landmarks())
    garment = start_garment()
    centroids = to_anny_axes(garment.positions[garment.faces].mean(1) / 10)
    nearest_vertex, distance = nearest(centroids, body)
    close = distance < NEAREST_MM / 1000
    out = {name: np.where(close & np.isin(nearest_vertex, sets[name]))[0] for name in ZONE_NAMES}
    np.savez(ZONES, **out)
    area = face_areas(garment.faces, garment.positions)
    print({name: f"{len(ids)} faces, {area[ids].sum() / 100:.0f} cm²" for name, ids in out.items()})


def start_garment(size="M"):
    start = np.load(CASES / "standing-M.npz")["start-178-75"]
    return load_garment(MESH, uv_mm(), shrinkage(size), fabric=FABRIC, positions=start)


def case_garments(pose, size):
    """The garment welded on the starting drape with a size's rest state, and each body's drape."""
    drapes = np.load(CASES / f"{pose}-{size}.npz")
    garment = start_garment(size)
    welded = {}
    for body in BODIES:
        raw = drapes[body]
        used = garment.weld >= 0
        positions = np.zeros((len(garment.positions), 3))
        np.add.at(positions, garment.weld[used], raw[used])
        welded[body] = positions / np.bincount(garment.weld[used])[:, None]
    return garment, welded


def zone_strain_table():
    """Zone mean course strain (wale for back length) of every CLO case, by (pose, size, body)."""
    sets = dict(np.load(ZONES))
    table = {}
    for pose in POSES:
        for size in ("S", "M", "L"):
            garment, drapes = case_garments(pose, size)
            for body, positions in drapes.items():
                eps = strains(garment.rest_mm, garment.faces, positions)
                area = face_areas(garment.faces, positions)
                course = zone_means(eps[:, 0], area, {k: sets[k] for k in GIRTH_ZONES})
                wale = zone_means(eps[:, 1], area, {"back_length": sets["back_length"]})
                table[pose, size, body] = course | wale
    return table


def strain():
    """Task 3.2: zone strains of the CLO drapes; 176/88 above 180/64 in every girth zone, pose."""
    table = zone_strain_table()
    print("pose     size body    " + " ".join(f"{z:>14}" for z in ZONE_NAMES))
    for (pose, size, body), row in table.items():
        print(
            f"{pose:8} {size:4} {body:7} " + " ".join(f"{row[z] * 100:13.1f}%" for z in ZONE_NAMES)
        )
    failures = [
        (pose, size, zone)
        for pose in POSES
        for size in ("S", "M", "L")
        for zone in GIRTH_ZONES
        if table[pose, size, "176-88"][zone] <= table[pose, size, "180-64"][zone]
    ]
    print("176/88 above 180/64 in every girth zone, pose and size:", not failures, failures)
    ranked = [
        (pose, body)
        for pose in POSES
        for body in BODIES
        if not table[pose, "S", body]["chest"]
        > table[pose, "M", body]["chest"]
        > table[pose, "L", body]["chest"]
    ]
    print("chest strain S > M > L on every body and pose:", not ranked, ranked)


def pressure():
    """Task 3.3: zone pressure of S, M, L relative to the highest, on every body and pose.

    CLO's fabric is unknown (FABRIC_13), so tension comes from the example knit: only the ranking
    of sizes means anything. κ is the posed body's under each garment face (D4).
    """
    fabric = Fabric.model_validate_json((DATA / "examples" / "fabric-knit.json").read_text())
    sets = {k: v for k, v in np.load(ZONES).items() if k in GIRTH_ZONES}
    faces = body_faces()
    mean_pa, gap_mm = {}, []
    for pose in POSES:
        drapes = {size: case_garments(pose, size) for size in "SML"}
        for body in BODIES:
            under = posed_body(pose, body)
            body_centroids = under[faces].mean(1)
            for size, (garment, positions) in drapes.items():
                drape = positions[body]
                face_under, gap = nearest(drape[garment.faces].mean(1), body_centroids)
                gap_mm.append(np.median(gap))
                p = pressures(
                    garment.rest_mm, garment.faces, drape, fabric, (under, faces, face_under)
                )
                area = face_areas(garment.faces, drape)
                mean_pa[pose, body, size] = zone_means(p, area, sets) | {
                    f"{z} out_of_curve": float(np.isnan(p[ids]).mean()) for z, ids in sets.items()
                }
    print(f"median garment face to body face centroid: {min(gap_mm):.1f}–{max(gap_mm):.1f} mm")
    print("pose     body    size " + " ".join(f"{z:>27}" for z in GIRTH_ZONES))
    for pose in POSES:
        for body in BODIES:
            rel = {z: relative_pressures({s: mean_pa[pose, body, s][z] for s in "SML"})
                   for z in GIRTH_ZONES}  # fmt: skip
            for size in "SML":
                row = mean_pa[pose, body, size]
                print(f"{pose:8} {body:7} {size:4} " + " ".join(
                    f"{rel[z][size]:5.2f} ({row[z]:5.0f} Pa, {row[z + ' out_of_curve']:4.0%} out)"
                    for z in GIRTH_ZONES))  # fmt: skip
    ranked = [
        (pose, body, zone)
        for pose in POSES
        for body in BODIES
        for zone in GIRTH_ZONES
        if not mean_pa[pose, body, "M"][zone] > mean_pa[pose, body, "L"][zone]
    ]
    print("M presses more than L in every girth zone, body and pose:", not ranked, ranked)
    m, large = mean_pa["standing", "178-75", "M"], mean_pa["standing", "178-75", "L"]
    print(f"178/75 standing chest: M {m['chest']:.0f} Pa > L {large['chest']:.0f} Pa:",
          m["chest"] > large["chest"])  # fmt: skip


if __name__ == "__main__":
    commands = {
        "calibrate-uv": calibrate_uv,
        "mesh": mesh,
        "zones": zones,
        "strain": strain,
        "pressure": pressure,
    }
    commands[sys.argv[1]]()
