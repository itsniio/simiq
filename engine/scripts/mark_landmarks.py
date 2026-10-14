"""Mark landmarks on the Anny template and render them on 5 bodies (fit-engine-poc 4.1).

Run from engine/:  uv run python scripts/mark_landmarks.py
Writes data/landmarks.json (vertex indices, valid for every Anny body because the topology is fixed)
and docs/measurements/landmarks-*.png plus docs/measurements/landmarks-check.md.
Each landmark is found by a geometric rule on one template body; the rules are in RULES below and
in docs/measurements.md.
"""

import importlib.metadata
import json
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # noqa: E402

from simiq_fit.body import fit_body, load_model, pose_body, rest_vertices  # noqa: E402
from simiq_fit.inputs import BodyInputs  # noqa: E402
from simiq_fit.poses import load_pose  # noqa: E402
from simiq_fit.tape import hull_perimeter, section_loops  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "engine" / "docs" / "measurements"
UP = np.array([0.0, 0.0, 1.0])
MIDLINE_M = 0.003  # vertices this close to x = 0 lie on the body's sagittal midline
SCAN_STEP_M = 0.002
ARM_SPLIT_DROP_M = 0.03  # a section's width drops by this much where an arm separates

TEMPLATE = BodyInputs(sex="male", height_cm=178, weight_kg=75, body_type="regular")
BODIES = {
    "male-178-75": TEMPLATE,
    "female-165-60": BodyInputs(sex="female", height_cm=165, weight_kg=60, body_type="regular"),
    "male-190-95": BodyInputs(sex="male", height_cm=190, weight_kg=95, body_type="regular"),
    "female-175-58": BodyInputs(sex="female", height_cm=175, weight_kg=58, body_type="regular"),
    "male-168-72": BodyInputs(sex="male", height_cm=168, weight_kg=72, body_type="regular"),
}

RULES = {
    "c7": "back midline vertex closest in height to the neck01 bone head (base of the neck)",
    "acromion.L": "highest vertex within 5 cm (horizontally) of the left shoulder joint",
    "acromion.R": "highest vertex within 5 cm (horizontally) of the right shoulder joint",
    "armpit.L": "torso-side point where a horizontal section, scanned down from the shoulder "
    "joint, first loses the left arm (its width drops by 3 cm)",
    "armpit.R": "as armpit.L, right side",
    "waist_front": "front-most vertex of Anny's own waist ring (anny.anthropometry)",
    "hip_back": "back-most point of the torso section with the largest girth between the crotch "
    "and the waist",
    "crotch": "lowest midline vertex above the knees",
    "elbow.L": "back-most vertex within 5 cm of the left elbow joint",
    "elbow.R": "back-most vertex within 5 cm of the right elbow joint",
    "knee.L": "front-most vertex within 6 cm of the left knee joint",
    "knee.R": "front-most vertex within 6 cm of the right knee joint",
}

# Rough adult landmark heights as a share of stature, only to catch a misplaced landmark.
EXPECTED_SHARE = {
    "c7": (0.82, 0.88),
    "armpit.L": (0.70, 0.78),
    "armpit.R": (0.70, 0.78),
    "waist_front": (0.57, 0.66),
    "hip_back": (0.46, 0.55),
    "crotch": (0.43, 0.50),
}


def nearest_vertex(vertices, point):
    return int(np.argmin(np.linalg.norm(vertices - point, axis=1)))


def torso_section(vertices, faces, z, y_mid):
    """The horizontal section loop at height z that encloses the midline point (0, y_mid)."""
    for loop in section_loops(vertices, faces, (0, y_mid, z), UP):
        xs, ys = loop[:, 0], loop[:, 1]
        crossings = 0
        for i in range(len(loop)):
            x1, y1, x2, y2 = xs[i - 1], ys[i - 1], xs[i], ys[i]
            if (y1 > y_mid) != (y2 > y_mid) and 0 < x1 + (y_mid - y1) * (x2 - x1) / (y2 - y1):
                crossings += 1
        if crossings % 2:
            return loop
    return None


def midline_y(vertices, z):
    near = (np.abs(vertices[:, 0]) < MIDLINE_M) & (np.abs(vertices[:, 2] - z) < 0.02)
    return float(vertices[near, 1].mean())


def find_landmarks(model, vertices, faces, heads):
    found = {}
    midline = np.abs(vertices[:, 0]) < MIDLINE_M

    neck = heads["neck01"]
    back = np.where(midline & (vertices[:, 1] > neck[1]))[0]
    found["c7"] = int(back[np.argmin(np.abs(vertices[back, 2] - neck[2]))])

    for side in ("L", "R"):
        joint = heads[f"upperarm01.{side}"]
        near = np.linalg.norm(vertices[:, :2] - joint[:2], axis=1) < 0.05
        found[f"acromion.{side}"] = int(np.where(near)[0][np.argmax(vertices[near, 2])])
        elbow = heads[f"lowerarm01.{side}"]
        near = np.linalg.norm(vertices - elbow, axis=1) < 0.05
        found[f"elbow.{side}"] = int(np.where(near)[0][np.argmax(vertices[near, 1])])
        knee = heads[f"lowerleg01.{side}"]
        near = np.linalg.norm(vertices - knee, axis=1) < 0.06
        found[f"knee.{side}"] = int(np.where(near)[0][np.argmin(vertices[near, 1])])

    # Armpits: scan down from the shoulder joints until the section narrows by an arm's width.
    top = heads["upperarm01.L"][2]
    previous = None
    for z in np.arange(top, top - 0.30, -SCAN_STEP_M):
        loop = torso_section(vertices, faces, z, midline_y(vertices, z))
        if loop is None:
            continue
        width = (loop[:, 0].max(), loop[:, 0].min())
        if previous is not None:
            for i, side, pick in ((0, "L", np.argmax), (1, "R", np.argmin)):
                key = f"armpit.{side}"
                if key not in found and abs(previous[i] - width[i]) > ARM_SPLIT_DROP_M:
                    found[key] = nearest_vertex(vertices, loop[pick(loop[:, 0])])
        if "armpit.L" in found and "armpit.R" in found:
            break
        previous = width

    import anny.anthropometry

    ring = anny.anthropometry.Anthropometry(model).waist_vertex_indices
    found["waist_front"] = int(ring[np.argmin(vertices[ring, 1])])

    knee_z = heads["lowerleg01.L"][2]
    above_knees = np.where(midline & (vertices[:, 2] > knee_z))[0]
    found["crotch"] = int(above_knees[np.argmin(vertices[above_knees, 2])])

    # Hip: the largest torso girth between just above the crotch and the waist.
    best = (0.0, None)
    for z in np.arange(vertices[found["crotch"], 2] + 0.03, vertices[ring, 2].mean(), 0.005):
        loop = torso_section(vertices, faces, z, midline_y(vertices, z))
        if loop is not None:
            perimeter = hull_perimeter(loop[:, :2])
            if perimeter > best[0]:
                best = (perimeter, loop)
    found["hip_back"] = nearest_vertex(vertices, best[1][np.argmax(best[1][:, 1])])
    return found, [int(i) for i in ring]


def draw(ax, vertices, faces, marks, elev, azim, title):
    tri = vertices[faces]
    normals = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    normals /= np.maximum(np.linalg.norm(normals, axis=1, keepdims=True), 1e-12)
    e, a = np.radians(elev), np.radians(azim)
    view = np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])
    colors = np.tile([0.8, 0.78, 0.75, 0.35], (len(faces), 1))
    colors[:, :3] *= (0.35 + 0.65 * np.abs(normals @ view))[:, None]
    ax.add_collection3d(Poly3DCollection(tri, facecolors=colors, edgecolors="none"))
    for name, index in marks.items():
        x, y, z = vertices[index]
        ax.scatter([x], [y], [z], color="red", s=18, depthshade=False)
        ax.text(x, y, z, f" {name}", fontsize=6, color="darkred")
    center = vertices.mean(axis=0)
    half = np.ptp(vertices, axis=0).max() / 2
    for setter, c in zip((ax.set_xlim, ax.set_ylim, ax.set_zlim), center, strict=True):
        setter(c - half, c + half)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    ax.set_title(title, fontsize=8)


def main():
    DOCS.mkdir(parents=True, exist_ok=True)
    model = load_model()
    faces = np.asarray(model.faces)

    phenotype = fit_body(model, TEMPLATE)
    template = pose_body(model, phenotype, {})
    heads = {n: template["bone_poses"][i, :3, 3] for i, n in enumerate(model.bone_labels)}
    landmarks, ring = find_landmarks(model, template["rest_vertices"], faces, heads)
    missing = set(RULES) - set(landmarks)
    if missing:
        raise SystemExit(f"rules found no vertex for: {sorted(missing)}")

    (ROOT / "data" / "landmarks.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "topology": "anny",
                "vertex_count": len(template["rest_vertices"]),
                "provenance": f"scripts/mark_landmarks.py, {time.strftime('%Y-%m-%d')}, anny "
                f"{importlib.metadata.version('anny')}, template body male 178 cm 75 kg",
                "landmarks": landmarks,
                "waist_ring": ring,
                "rules": RULES,
            },
            indent=2,
        )
        + "\n"
    )

    check = [
        "# Landmark heights as a share of stature",
        "",
        "Generated by `scripts/mark_landmarks.py`. Outside the expected range: **bold**.",
        "",
        "| Body | " + " | ".join(EXPECTED_SHARE) + " |",
        "|---|" + "---|" * len(EXPECTED_SHARE),
        "| expected | "
        + " | ".join(f"{lo:.2f}-{hi:.2f}" for lo, hi in EXPECTED_SHARE.values())
        + " |",
    ]
    for name, inputs in BODIES.items():
        body_phenotype = fit_body(model, inputs)
        vertices = rest_vertices(model, body_phenotype)
        floor, stature = vertices[:, 2].min(), np.ptp(vertices[:, 2])
        cells = []
        for mark, (lo, hi) in EXPECTED_SHARE.items():
            share = (vertices[landmarks[mark], 2] - floor) / stature
            cells.append(f"{share:.2f}" if lo <= share <= hi else f"**{share:.2f}**")
        check.append(f"| {name} | " + " | ".join(cells) + " |")

        posed = pose_body(model, body_phenotype, load_pose("hoods"))["vertices"]
        fig = plt.figure(figsize=(16, 6))
        views = [
            (vertices, 5, -90, "standing · front"),
            (vertices, 5, 0, "standing · side"),
            (vertices, 5, 90, "standing · back"),
            (posed, 5, 0, "hoods · side"),
        ]
        for i, (v, elev, azim, title) in enumerate(views):
            draw(fig.add_subplot(1, 4, i + 1, projection="3d"), v, faces, landmarks, elev, azim,
                 title)  # fmt: skip
        fig.suptitle(f"{name}: landmarks")
        fig.savefig(DOCS / f"landmarks-{name}.png", dpi=120, bbox_inches="tight")
        plt.close(fig)
        print(f"{name}: done")
    (DOCS / "landmarks-check.md").write_text("\n".join(check) + "\n")
    print(f"wrote data/landmarks.json and {DOCS}")


if __name__ == "__main__":
    main()
