"""Cloth-sim spike runner: checks and comparisons on the CLO reference data (kept outside git).

uv run python scripts/cloth_spike.py calibrate-uv  # mm per UV unit from the DXF, to manifest
uv run python scripts/cloth_spike.py mesh          # the starting drape, checked (task 2.2)
uv run python scripts/cloth_spike.py zones         # garment faces of each zone, to zones.npz (3.2)
uv run python scripts/cloth_spike.py strain        # zone strains of every CLO case (task 3.2)
uv run python scripts/cloth_spike.py pressure      # relative zone pressure by size (task 3.3)
uv run python scripts/cloth_spike.py drape         # our drape 178/75 → 176/88 hoods, twice (4.3)
uv run python scripts/cloth_spike.py timing        # one garment on one body on this machine (4.4)
uv run python scripts/cloth_spike.py fit           # course and wale stiffness scales (task 5.1)
uv run python scripts/cloth_spike.py simulate hoods M   # our drape through CLO's sequence (5.2)
uv run python scripts/cloth_spike.py report        # ours against CLO on all 36 cases (task 5.2)
uv run python scripts/cloth_spike.py dev           # ours against CLO on the development body only
SPIKE_TRY="COMPRESSION_SCALE=0.3" uv run python scripts/cloth_spike.py simulate hoods M  # one try
uv run python scripts/cloth_spike.py calibrate     # knit friction and shear on 178/75 M posed
uv run python scripts/cloth_spike.py render hoods M 176-88  # CLO and ours side by side (5.2)
"""

import json
import os
import struct
import sys
from pathlib import Path

import numpy as np
from clo_cache_extract import FRAMES, SPIKE_DIR

from simiq_fit import drape as solver
from simiq_fit.fit import relative_pressures
from simiq_fit.garment import Curve, Fabric
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
LEAD_IN = {  # CLO's hoods and drops runs start where the 178/75 A-pose → hoods animation ended
    "hoods": "anny-m178-75-morph-hoods.pc2",
    "drops": "anny-m178-75-morph-hoods.pc2",
}
ZONES = SPIKE_DIR / "zones.npz"  # face indices of the licensed mesh: outside git like the mesh
ZONE_NAMES = ("chest", "waist", "hem", "sleeve_opening", "back_length")
GIRTH_ZONES = ("chest", "waist", "hem", "sleeve_opening")
TORSO_ZONES = ("chest", "waist", "hem")  # 3.2's claim; CLO leaves the sleeve opening unstretched
NEAREST_MM = 30  # a garment face belongs to a body zone only this close to the body
SLEEVE_BAND_MM = 50  # sleeve opening: the sleeve's faces this close to its hem, as the torso bands
# Stand-in for CLO's unknown FABRIC_13: Teyeme et al., Materials 14 (2021) 4461, CC BY 4.0, Table 3,
# fabric LB (single-face tricot, 74 % nylon / 26 % elastane, 150 g/m², 0.29 mm): stress 46.010,
# 161.954, 263.138 kPa at 11.1, 24.9, 42.9 % strain; tension T = stress × 0.29 mm, here as force on
# a 1 m strip. Three measured points, below the fit engine's five, so it stays out of data/. One
# direction was published; the wale repeats it.
STAND_IN_TENSION = Curve.model_construct(
    strain=[0, 0.111, 0.249, 0.429], force_n=[0, 13.3429, 46.96666, 76.31002]
)
STAND_IN_FABRIC = Fabric.model_construct(
    specimen_width_mm=1000,
    weight_g_m2=150,
    curves={"course": STAND_IN_TENSION, "wale": STAND_IN_TENSION},
)
ZIPPER = ("Fabric628555",)  # the zipper tapes: they close the front; UV is a texture, not a pattern
ZIPPER_STIFFNESS = 100.0  # a woven tape barely stretches: 100 × the knit, a spike guess
POCKET_PIECES = (1, 12)  # the back pockets and their top band lie on the back panel
BACK_PANEL = 14
POCKET_LAYER_MM = 2.2  # CLO's start drape: pocket p5 6.7–6.8 mm off the body, back panel 4.6 mm
GRIPPER = "Material157617"  # the silicone hem grippers, front and back; left out of the cloth
GRIPPER_MM = 3.0  # fabric vertices this close to the silicone carry it
GRIPPER_FRICTION = 1.5  # silicone on skin; a spike guess (the knit has KNIT_FRICTION)
INERTIA_SCALE = 200.0  # without it 500 × 2 passes do not converge on the jersey: every stiffness
# gave the same drape (fit, 18 Oct: 3.46 points rms for all 25 scales); the body carries the cloth.
# 1000 until 19 Oct: weight then pulls cloth back down at ≤ 5 mm/s, and the hoods hem rode up.
OURS = SPIKE_DIR / "ours"  # our drapes, outside git like CLO's
DEV_BODY = "178-75"  # solver changes are judged on this body only; the other three stay held out
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
    out = {name: np.where(close & np.isin(nearest_vertex, sets[name]))[0] for name in sets}
    out["sleeve_opening"] = sleeve_hem_faces(garment)
    np.savez(ZONES, **out)
    area = face_areas(garment.faces, garment.positions)
    print({name: f"{len(ids)} faces, {area[ids].sum() / 100:.0f} cm²" for name, ids in out.items()})


def sleeve_hem_faces(garment):
    """Faces of the sleeve pieces within SLEEVE_BAND_MM of the sleeve hems.

    The hems are the two free-edge loops (edges of one face) farthest out to the sides.
    """
    edges = np.sort(garment.faces[:, [0, 1, 1, 2, 2, 0]].reshape(-1, 2), axis=1)
    unique, count = np.unique(edges, axis=0, return_counts=True)
    free = unique[count == 1]
    parent = {v: v for v in free.ravel()}

    def root(v):
        while parent[v] != v:
            parent[v] = parent[parent[v]]
            v = parent[v]
        return v

    for a, b in free:
        parent[root(a)] = root(b)
    loops = {}
    for v in parent:
        loops.setdefault(root(v), []).append(v)
    centre_x = garment.positions[:, 0].mean()
    side = {k: np.abs(garment.positions[v, 0] - centre_x).mean() for k, v in loops.items()}
    hems = np.concatenate([loops[k] for k in sorted(side, key=side.get)[-2:]])
    centroids = garment.positions[garment.faces].mean(1)
    _, distance = nearest(centroids, garment.positions[hems])
    on_hem = np.isin(garment.faces, hems).any(1)
    sleeve_pieces = np.unique(garment.piece[on_hem])
    return np.where((distance < SLEEVE_BAND_MM) & np.isin(garment.piece, sleeve_pieces))[0]


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


def read_pc2(path):
    """All frames of a Point Cache 2 file, (frames, points, 3) in its units."""
    with open(path, "rb") as f:
        _magic, _version, points, _start, _rate, frames = struct.unpack("<12siiffi", f.read(32))
        return np.frombuffer(f.read(), "<f4").reshape(frames, points, 3)


@solver.wp.kernel
def signed_distance(
    mesh: solver.wp.uint64,
    x: solver.wp.array(dtype=solver.wp.vec3),
    out: solver.wp.array(dtype=float),
):
    i = solver.wp.tid()
    q = solver.wp.mesh_query_point_sign_winding_number(mesh, x[i], 1.0)
    out[i] = 1.0e9
    if q.result:
        p = solver.wp.mesh_eval_position(mesh, q.face, q.u, q.v)
        out[i] = solver.wp.length(x[i] - p) * q.sign


def distances_mm(body, positions):
    """Signed distance of each point from the body surface, mm (negative inside)."""
    out = solver.wp.zeros(len(positions), dtype=float)
    points = solver.wp.array(np.asarray(positions, float) / 1000, dtype=solver.wp.vec3)
    solver.wp.launch(signed_distance, len(positions), [body.mesh.id, points, out])
    return out.numpy() * 1000


def scaled_fabric(course=1.0, wale=1.0):
    """The stand-in fabric with its course and wale tension scaled (task 5.1 fits the scales)."""
    curves = {
        direction: Curve.model_construct(
            strain=STAND_IN_TENSION.strain, force_n=[f * scale for f in STAND_IN_TENSION.force_n]
        )
        for direction, scale in (("course", course), ("wale", wale))
    }
    return Fabric.model_construct(specimen_width_mm=1000, weight_g_m2=150, curves=curves)


def jersey(size="M"):
    """The jersey welded on the starting drape, with its zipper, rest state of a size."""
    start = np.load(CASES / "standing-M.npz")["start-178-75"]
    return load_garment(MESH, uv_mm(), shrinkage(size), FABRIC, start, trims=ZIPPER)


def simulated_garment(size="M", scales=(1.0, 1.0), friction_knit=None, shear=None):
    """The starting drape with its zipper, ready for our solver (knit friction and shear given,
    or the calibrated ones)."""
    friction_knit = KNIT_FRICTION if friction_knit is None else friction_knit
    shear = KNIT_SHEAR_N_PER_M if shear is None else shear
    garment = jersey(size)
    pocket = np.unique(garment.faces[np.isin(garment.piece, POCKET_PIECES)])
    back = garment.faces[garment.piece == BACK_PANEL]
    _, _, blocks = read_obj(MESH)
    silicone = np.unique(np.concatenate([np.ravel(f)[::2] for m, f in blocks if GRIPPER in m]))
    start = np.load(CASES / "standing-M.npz")["start-178-75"]
    low, high = start[silicone].min(0) - GRIPPER_MM, start[silicone].max(0) + GRIPPER_MM
    near = np.where(((garment.positions > low) & (garment.positions < high)).all(1))[0]
    _, gap = nearest(garment.positions[near], start[silicone])
    friction = np.full(len(garment.positions), friction_knit)
    friction[near[gap < GRIPPER_MM]] = GRIPPER_FRICTION
    zipper = np.where(garment.piece >= len(shrinkage(size)), ZIPPER_STIFFNESS, 1.0)
    cloth = solver.cloth(
        garment.rest_mm,
        garment.faces,
        garment.positions,
        scaled_fabric(*scales),
        stiffness_scale=zipper,
        layer=(pocket, back, POCKET_LAYER_MM),
        inertia_scale=INERTIA_SCALE,
        friction=friction,
        shear_n_per_m=shear,
        friction_kinetic=None
        if KNIT_FRICTION_KINETIC is None
        else np.full(len(garment.positions), KNIT_FRICTION_KINETIC),
        slip_mm_s=KNIT_SLIP_MM_S,
        adhesion_pa=KNIT_ADHESION_PA,
    )
    return garment, cloth


def drape_sequence(target="176-88", size="M", record_every=15):
    """Our drape through the point cache that morphs 178/75 into the target and poses it (hoods).

    Returns the garment, its positions at the recorded frames and their distances off the body.
    """
    garment, cloth = simulated_garment(size)
    h, w = target.split("-")
    frames = read_pc2(START_BODY.parent / f"anny-m{h}-{w}-morph-hoods.pc2").astype(float) * 10
    body = solver.body(frames[0], body_faces())
    records = []
    for f in range(1, len(frames)):
        solver.move_body(body, frames[f])
        solver.run(cloth, 1 / 30, body=body)
        if f % record_every == 0 or f == len(frames) - 1:
            positions = solver.positions_mm(cloth)
            records.append((f, positions, distances_mm(body, positions)))
    return garment, records


def drape():
    """Task 4.3: no penetration at any recorded frame, and the same drape twice."""
    import time

    runs = []
    for attempt in range(2):
        t0 = time.time()
        garment, records = drape_sequence()
        runs.append(records)
        print(f"run {attempt + 1}: {len(records)} recorded frames in {time.time() - t0:.0f} s")
    for f, _positions, distance in runs[0]:
        outside = (distance >= 0).mean()
        print(f"frame {f:3}: outside {outside:.2%}, deepest {distance.min():6.2f} mm, "
              f"p1 {np.percentile(distance, 1):5.2f} mm")  # fmt: skip
    worst = max(np.abs(a[1] - b[1]).max() for a, b in zip(*runs, strict=True))
    print(f"two runs differ by at most {worst:.4f} mm")
    OURS.mkdir(exist_ok=True)
    np.savez(OURS / "hoods-M-176-88.npz", positions=runs[0][-1][1], faces=garment.faces)


def timing():
    """Task 4.4: wall time of setting up and simulating one garment through one body sequence."""
    import platform
    import time

    t0 = time.perf_counter()
    _, cloth = simulated_garment()
    frames = read_pc2(START_BODY.parent / "anny-m176-88-morph-hoods.pc2").astype(float) * 10
    body = solver.body(frames[0], body_faces())
    t1 = time.perf_counter()
    for f in range(1, len(frames)):
        solver.move_body(body, frames[f])
        solver.run(cloth, 1 / 30, body=body, substeps_per_s=SUBSTEPS, iterations=ITERATIONS)
    solver.wp.synchronize()
    t2 = time.perf_counter()
    seconds = (len(frames) - 1) / 30
    print(f"{platform.processor() or platform.machine()}, Warp {solver.wp.__version__} on CPU")
    print(f"{cloth.faces.shape[0]} triangles, {cloth.x.shape[0]} vertices, {seconds:.2f} s "
          f"simulated, {SUBSTEPS}/s × {ITERATIONS} passes")  # fmt: skip
    print(f"setup {t1 - t0:.1f} s, simulation {t2 - t1:.1f} s ({(t2 - t1) / seconds:.1f} s per "
          f"simulated second), total {t2 - t0:.1f} s")  # fmt: skip


def zone_strains(garment, positions, sets):
    """Zone mean course strain (wale for back length) of one drape."""
    eps = strains(garment.rest_mm, garment.faces, positions)
    area = face_areas(garment.faces, positions)
    course = zone_means(eps[:, 0], area, {k: sets[k] for k in GIRTH_ZONES})
    return course | zone_means(eps[:, 1], area, {"back_length": sets["back_length"]})


# Task 5.1, `fit` on 19 Oct (friction 1.0, position-level): least squares over the five zones of
# 178/75 standing M on FIT_GRID, 1.35 points rms (×1/×4: 1.37). Chest −1.34, waist +1.52,
# hem −1.81, sleeve opening −1.22, back length +0.41 points against CLO.
FITTED_SCALES = (2.0, 4.0)  # (course, wale) × the stand-in fabric's tension
FIT_GRID = (0.25, 0.5, 1.0, 2.0, 4.0)
# Literature, not fitted (19 Oct; founders: no time to measure). Fabric on skin: static μ of a
# single-jersey knit on the chest, 0.90 ± 0.19 (Temel et al., Tribol. Lett. 70 (2022) 23, CC BY
# 4.0, 10 people; the highest of six sites, dorsal forearm 0.31 ± 0.07, cotton, dry skin).
# Tuned on the development body 178/75 (9 cases, 19 Oct) inside that spread: 0.65 (−1.3 SD).
KNIT_FRICTION = 0.65
# None: sliding keeps the static coefficient. CLO's avatar has static 0.8, kinetic 0.05 (the
# projects' .avt); with them ours rides up even standing (report, "CLO's avatar friction").
KNIT_FRICTION_KINETIC = None
KNIT_SLIP_MM_S = 0.0  # above 0, friction μN·min(1, v/this): a held hem creeps; 0 is Coulomb
KNIT_ADHESION_PA = 0.0  # friction μN + τA: the contact's shear strength τ, independent of pressure
# Shear: a stretch weft knit's KES-FB1 rigidity, 0.28–1.50 cN/cm/deg (US 6,561,230 B1, Asahi
# Kasei 2003), its geometric mean 0.648 → 37.1 N/m per rad; the range is 16.0–85.9 N/m.
KNIT_SHEAR_N_PER_M = solver.kes_shear_n_per_m((0.28 * 1.50) ** 0.5)
# `calibrate` on 19 Oct over CALIBRATION_GRID, hoods and drops 178/75 M: friction 1.0 with shear
# 40 N/m, 2.48 points rms (worst 3.75); 20 N/m 2.61, 80 N/m 3.03; friction 0.7 and 1.4 ≥ 5.90.
# Superseded by the literature values above; kept so the calibration can be repeated.
CALIBRATION = [("hoods", "M", "178-75"), ("drops", "M", "178-75")]  # fitted body and size, posed
CALIBRATION_GRID = {
    "friction": (0.5, 0.7, 1.0, 1.4),
    "shear": (20.0, 40.0, 80.0),
}  # scales tried per direction, a factor 2 apart
SUBSTEPS = solver.SUBSTEPS_PER_S  # per simulated second in `simulate`; a try may raise them
ITERATIONS = solver.ITERATIONS
FIT_SETTLE_S = 3.0  # the fitted case settles this long on the static start body


def fit():
    """Task 5.1: the course and wale scales that bring 178/75 standing M closest to CLO.

    Least squares over the five zones on a grid; the case settles on the start body (static) from
    CLO's starting drape, so each try takes ~15 s.
    """
    sets = dict(np.load(ZONES))
    reference, drapes = case_garments("standing", "M")
    clo = zone_strains(reference, drapes["178-75"], sets)
    body = solver.body(posed_body("standing", "178-75"), body_faces())
    print("CLO " + " ".join(f"{z} {clo[z] * 100:5.2f}" for z in ZONE_NAMES))
    results = []
    for course in FIT_GRID:
        for wale in FIT_GRID:
            garment, cloth = simulated_garment("M", (course, wale))
            solver.run(cloth, FIT_SETTLE_S, body=body)
            ours = zone_strains(garment, solver.positions_mm(cloth), sets)
            error = sum((ours[z] - clo[z]) ** 2 for z in ZONE_NAMES)
            results.append((error, course, wale, ours))
            print(f"course ×{course:<4} wale ×{wale:<4} rms {np.sqrt(error / 5) * 100:5.2f} pt: "
                  + " ".join(f"{z} {ours[z] * 100:5.2f}" for z in ZONE_NAMES))  # fmt: skip
    error, course, wale, ours = min(results, key=lambda r: r[0])
    print(f"best: course ×{course}, wale ×{wale}; per zone ours − CLO, points: "
          + " ".join(f"{z} {(ours[z] - clo[z]) * 100:+.2f}" for z in ZONE_NAMES))  # fmt: skip


def simulate(pose, size, friction=None, shear=None):
    """Task 5.2: our drape through the point cache that drove CLO's run, saved at its frames.

    With friction and shear given (a calibration try) the file is named after them.
    """
    import time

    tried = friction is not None
    friction, shear = (float(friction), float(shear)) if tried else (None, None)
    _, cloth = simulated_garment(size, FITTED_SCALES, friction, shear)
    frames = read_pc2(START_BODY.parent / BODY_SEQUENCES[pose]).astype(float) * 10
    lead = read_pc2(START_BODY.parent / LEAD_IN[pose]) * 10.0 if pose in LEAD_IN else frames[:1]
    wanted = {frame: body for body, frame in FRAMES[pose].items() if body != "start"}
    body = solver.body(lead[0], body_faces())
    saved = {}
    t0 = time.perf_counter()
    for f in range(1, len(lead)):
        solver.move_body(body, lead[f])
        solver.run(cloth, 1 / 30, body=body, substeps_per_s=SUBSTEPS, iterations=ITERATIONS)
    for f in range(1, max(wanted) + 1):
        solver.move_body(body, frames[f])
        solver.run(cloth, 1 / 30, body=body, substeps_per_s=SUBSTEPS, iterations=ITERATIONS)
        if f in wanted:
            saved[wanted[f]] = solver.positions_mm(cloth)
    seconds = time.perf_counter() - t0
    OURS.mkdir(exist_ok=True)
    steps = len(lead) - 1 + max(wanted)
    name = (f"{pose}-{size}-mu{friction}-g{shear}" if tried else f"{pose}-{size}") + TRY
    np.savez(OURS / f"{name}.npz", wall_s=seconds, frames=steps, **saved)
    print(f"{pose} {size}: {steps} frames in {seconds:.0f} s")


def calibrate():
    """Knit friction and shear from the fitted body and size in the two poses (the others held out).

    Scores the tries `simulate <pose> M <friction> <shear>` left on CALIBRATION_GRID.
    """
    sets = dict(np.load(ZONES))
    garment = jersey("M")
    clo = zone_strain_table()
    results = []
    for friction in CALIBRATION_GRID["friction"]:
        for shear in CALIBRATION_GRID["shear"]:
            diffs = []
            for pose, size, b in CALIBRATION:
                data = np.load(OURS / f"{pose}-{size}-mu{friction}-g{shear}.npz")
                ours = zone_strains(garment, data[b], sets)
                diffs += [(ours[z] - clo[pose, size, b][z]) * 100 for z in ZONE_NAMES]
            rms = float(np.sqrt(np.mean(np.square(diffs))))
            results.append((rms, friction, shear, max(abs(d) for d in diffs)))
            print(f"friction {friction:<4} shear {shear:5.0f} N/m: rms {rms:5.2f}, "
                  f"worst {results[-1][3]:5.2f} points")  # fmt: skip
    rms, friction, shear, worst = min(results)
    print(f"best: friction {friction}, shear {shear} N/m (rms {rms:.2f}, worst {worst:.2f} points)")


def report(friction=None, shear=None):
    """Task 5.2: every case's zone strains, ours against CLO, size ranking, depth, timing.

    With friction and shear given, the runs `simulate <pose> <size> <friction> <shear>` left.
    """
    suffix = (f"-mu{float(friction)}-g{float(shear)}" if friction is not None else "") + TRY
    sets = dict(np.load(ZONES))
    clo = zone_strain_table()
    faces = body_faces()
    ours, depth, wall = {}, {}, {}
    for pose in POSES:
        for size in ("S", "M", "L"):
            data = np.load(OURS / f"{pose}-{size}{suffix}.npz")
            wall[pose, size] = (float(data["wall_s"]), int(data["frames"]))
            garment = jersey(size)
            reference, drapes = case_garments(pose, size)
            for b in BODIES:
                ours[pose, size, b] = zone_strains(garment, data[b], sets)
                body = solver.body(posed_body(pose, b), faces)
                fabric = np.unique(reference.faces)
                depth[pose, size, b] = (
                    distances_mm(body, data[b]).min(),
                    distances_mm(body, drapes[b][fabric]).min(),
                )
    print("| pose | size | body | " + " | ".join(ZONE_NAMES) + " | worst | deepest ours / CLO mm |")
    print("|---" * (len(ZONE_NAMES) + 5) + "|")
    failing = []
    for (pose, size, b), row in ours.items():
        diff = {z: (row[z] - clo[pose, size, b][z]) * 100 for z in ZONE_NAMES}
        fitted = b == DEV_BODY  # the stiffness fit and the solver tuning
        worst = max(abs(d) for d in diff.values())
        if worst > 3 and not fitted:
            failing.append((pose, size, b, worst))
        cells = " | ".join(
            f"{row[z] * 100:.1f} / {clo[pose, size, b][z] * 100:.1f} ({diff[z]:+.1f})"  # noqa: E501
            for z in ZONE_NAMES
        )
        mark = " (fitted)" if fitted else ""
        print(f"| {pose} | {size} | {b}{mark} | {cells} | {worst:.1f} | "
              f"{depth[pose, size, b][0]:.1f} / {depth[pose, size, b][1]:.1f} |")  # fmt: skip
    held_out = 27
    print(
        f"\nheld-out cases within ±3 points in every zone: {held_out - len(failing)} of {held_out}"
    )
    print("failing:", [(p, s, b, round(w, 1)) for p, s, b, w in failing])
    order = {}
    for source, table in (("ours", ours), ("CLO", clo)):
        for pose in POSES:
            for b in BODIES:
                ranked = sorted("SML", key=lambda s: -table[pose, s, b]["chest"])
                order.setdefault((pose, b), {})[source] = "".join(ranked)
    same = [k for k, v in order.items() if v["ours"] == v["CLO"]]
    print(f"chest size ranking as CLO's: {len(same)} of 12;",
          {f"{p} {b}": v for (p, b), v in order.items() if v["ours"] != v["CLO"]})  # fmt: skip
    deeper = [k for k, (o, c) in depth.items() if o < c]
    print(f"deepest vertex no deeper than CLO's: {36 - len(deeper)} of 36; deeper: {deeper}")
    for (pose, size), (seconds, frames) in wall.items():
        print(
            f"{pose} {size}: {frames} frames ({frames / 30:.1f} s), {seconds:.0f} s, 9 in parallel"
        )


def dev(*bodies):
    """The development bodies' cases, ours − CLO per zone; never looks at the other bodies."""
    bodies = bodies or (DEV_BODY,)
    sets = dict(np.load(ZONES))
    clo = zone_strain_table()
    diffs, within = [], 0
    for pose in POSES:
        for size in ("S", "M", "L"):
            data = np.load(OURS / f"{pose}-{size}{TRY}.npz")
            for b in bodies:
                ours = zone_strains(jersey(size), data[b], sets)
                diff = {z: (ours[z] - clo[pose, size, b][z]) * 100 for z in ZONE_NAMES}
                diffs += list(diff.values())
                worst = max(abs(d) for d in diff.values())
                within += worst <= 3
                cells = " ".join(f"{z} {diff[z]:+5.1f}" for z in ZONE_NAMES)
                print(f"{pose:8} {size} {b}: {cells} | worst {worst:4.1f}")
    rms = float(np.sqrt(np.mean(np.square(diffs))))
    n = 9 * len(bodies)
    print(f"{'+'.join(bodies)}{TRY}: within ±3 points {within} of {n}, rms {rms:.2f} points")


RENDERS = Path(__file__).parents[1] / "docs" / "cloth-sim-spike"  # renders may be committed


def render(pose="hoods", size="M", body="176-88"):
    """Course strain over CLO's drape and ours, front and back, one PNG for the report."""
    import matplotlib

    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    reference, drapes = case_garments(pose, size)
    garment = jersey(size)
    ours = np.load(OURS / f"{pose}-{size}.npz")[body]
    fabric = len(reference.faces)  # the zipper tapes follow the fabric faces in ours
    shown = [("CLO", reference, drapes[body]), ("ours", garment, ours)]
    corners = np.concatenate([p[:, [0, 2, 1]] * [1, -1, 1] for _, _, p in shown])
    low, high = corners.min(0), corners.max(0)
    fig = plt.figure(figsize=(10, 11), dpi=110)
    for column, (azim, side) in enumerate([(-90, "front"), (90, "back")]):
        for row, (name, mesh, positions) in enumerate(shown):
            faces = mesh.faces[:fabric]
            course = strains(mesh.rest_mm[:fabric], faces, positions)[:, 0]
            xyz = positions[:, [0, 2, 1]] * [1, -1, 1]  # x, depth, up
            ax = fig.add_subplot(2, 2, 2 * row + column + 1, projection="3d")
            colours = plt.cm.RdBu_r(np.clip(course / 0.6 + 0.5, 0, 1))
            ax.add_collection3d(Poly3DCollection(xyz[faces], facecolors=colours, linewidths=0))
            ax.set(xlim=(low[0], high[0]), ylim=(low[1], high[1]), zlim=(low[2], high[2]))
            ax.set_box_aspect(high - low, zoom=1.3)
            ax.view_init(elev=5, azim=azim)
            ax.set_axis_off()
            ax.set_title(f"{name}, {side}", fontsize=10)
    fig.suptitle(f"Course strain, {pose} {size} on {body}: blue −30 %, white 0, red +30 %")
    fig.subplots_adjust(wspace=0, hspace=0.05)
    RENDERS.mkdir(exist_ok=True)
    path = RENDERS / f"{pose}-{size}-{body}.png"
    fig.savefig(path, bbox_inches="tight")
    print(path)


def zone_strain_table():
    """Zone mean course strain (wale for back length) of every CLO case, by (pose, size, body)."""
    sets = dict(np.load(ZONES))
    table = {}
    for pose in POSES:
        for size in ("S", "M", "L"):
            garment, drapes = case_garments(pose, size)
            for body, positions in drapes.items():
                table[pose, size, body] = zone_strains(garment, positions, sets)
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
    torso = [f for f in failures if f[2] in TORSO_ZONES]
    print("176/88 above 180/64 in every torso girth zone, pose and size:", not torso, torso)
    print("not above in the sleeve opening:", [f for f in failures if f[2] not in TORSO_ZONES])
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

    CLO's fabric is unknown (FABRIC_13), so tension comes from a published tricot (STAND_IN_FABRIC):
    only the ranking of sizes means anything. κ is the posed body's under each garment face (D4).
    """
    fabric = STAND_IN_FABRIC
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


def apply_try():
    """SPIKE_TRY="NAME=value,…" overrides solver or script constants; returns the file suffix."""
    spec = os.environ.get("SPIKE_TRY", "")
    for item in filter(None, spec.split(",")):
        name, value = item.split("=")
        here = sys.modules[__name__]
        module = here if hasattr(here, name) else solver
        kind = type(getattr(module, name))
        setattr(module, name, (int if kind is int else float)(float(value)))
    return f"-try-{spec}" if spec else ""


TRY = apply_try()


if __name__ == "__main__":
    commands = {
        "calibrate-uv": calibrate_uv,
        "mesh": mesh,
        "zones": zones,
        "strain": strain,
        "pressure": pressure,
        "drape": drape,
        "timing": timing,
        "fit": fit,
        "simulate": simulate,
        "report": report,
        "dev": dev,
        "calibrate": calibrate,
        "render": render,
    }
    commands[sys.argv[1]](*sys.argv[2:])
