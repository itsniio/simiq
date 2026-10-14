"""A figure per body measurement, standing and in `hoods`, and a check against ANSUR II (task 4.6).

Run from engine/:  uv run python scripts/measurement_figures.py [ansur2-folder]
Writes docs/measurements/measure-<name>.png for a man 178 cm 75 kg, and, given the ANSUR II folder
(data/external/ansur2), docs/measurements/ansur-check.md: our standing measurements of four bodies
next to what ANSUR II predicts from the same sex, height and weight.
"""

import csv
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # noqa: E402

from simiq_fit.body import body_parts, fit_body, load_model, pose_body  # noqa: E402
from simiq_fit.inputs import BodyInputs  # noqa: E402
from simiq_fit.landmarks import load_landmarks  # noqa: E402
from simiq_fit.measure import (  # noqa: E402
    PROFILE_STEP_CM,
    back_length_path,
    girth_sections,
    limb_axes,
    limb_starts,
    measure,
    vertical_trunk_arcs,
)
from simiq_fit.poses import load_pose  # noqa: E402
from simiq_fit.tape import section_loops, surface_arc  # noqa: E402

DOCS = Path(__file__).resolve().parents[1] / "docs" / "measurements"
DRAWN = BodyInputs(sex="male", height_cm=178, weight_kg=75, body_type="regular")
CHECKED = [("male", 178, 75), ("female", 165, 60), ("male", 185, 100), ("female", 170, 85)]
ANSUR = {  # our measurement -> ANSUR II column (mm), as in scripts/ansur_sds.py
    "chest_girth": "chestcircumference",
    "waist_girth": "waistcircumference",
    "hip_girth": "buttockcircumference",
    "upper_arm_girth": "bicepscircumferenceflexed",
    "thigh_girth": "thighcircumference",
    "vertical_trunk_girth": "verticaltrunkcircumferenceusa",
}


def posed_parts(model, phenotype, pose):
    posed = pose_body(model, phenotype, load_pose(pose))
    joints = {n: posed["bone_poses"][i, :3, 3] for i, n in enumerate(model.bone_labels)}
    return posed["vertices"], posed["faces"], joints


def lines(model, phenotype, parts, data, starts):
    """{measurement: {pose: [polylines]}} of what each measurement measures."""
    out = {}
    for pose in ("standing", "hoods"):
        v, faces, joints = posed_parts(model, phenotype, pose)
        lm = data["landmarks"]
        for name, s in girth_sections(v, faces, parts, lm, data["waist_ring"]).items():
            loops = section_loops(v, s["faces"], s["point"], s["normal"])
            if s["around_point"]:  # only the loop nearest the point, as the tape takes it
                loops = [
                    min(loops, key=lambda loop: np.linalg.norm(loop - s["point"], axis=1).min())
                ]
            out.setdefault(name, {})[pose] = loops
        step = PROFILE_STEP_CM / 100
        limb_faces = {"upper_arm_girth": parts["upper_arm.L"], "thigh_girth": parts["thigh.L"]}
        for name, (start, end) in limb_axes(joints, starts).items():
            axis = (end - start) / np.linalg.norm(end - start)
            rings = []
            for d in np.arange(0, np.linalg.norm(end - start), step):
                rings += section_loops(v, faces[limb_faces[name]], start + d * axis, axis)
            out.setdefault(name, {})[pose] = rings
        out.setdefault("back_length", {})[pose] = [surface_arc(v, faces, **back_length_path(v, lm))]
        out.setdefault("vertical_trunk_girth", {})[pose] = vertical_trunk_arcs(v, faces, lm)
    return out


def draw(ax, vertices, faces, polylines, azim, title):
    tri = vertices[faces]
    normals = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    normals /= np.maximum(np.linalg.norm(normals, axis=1, keepdims=True), 1e-12)
    a = np.radians(azim)
    colors = np.tile([0.8, 0.78, 0.75, 0.25], (len(faces), 1))
    colors[:, :3] *= (0.35 + 0.65 * np.abs(normals @ [np.cos(a), np.sin(a), 0.0]))[:, None]
    ax.add_collection3d(Poly3DCollection(tri, facecolors=colors, edgecolors="none"))
    for points in polylines:
        closed = np.vstack([points, points[:1]]) if len(points) > 2 else points
        ax.plot(closed[:, 0], closed[:, 1], closed[:, 2], color="crimson", linewidth=1.5)
    center, half = vertices.mean(axis=0), np.ptp(vertices, axis=0).max() / 2
    for setter, c in zip((ax.set_xlim, ax.set_ylim, ax.set_zlim), center, strict=True):
        setter(c - half, c + half)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=10, azim=azim)
    ax.set_axis_off()
    ax.set_title(title, fontsize=9)


def ansur_check(model, parts, data, folder):
    def rows(path):
        with open(path, newline="", encoding="latin-1") as f:
            return [{k.lower(): v for k, v in r.items()} for r in csv.DictReader(f)]

    tables = {
        "male": rows(folder / "ANSUR_II_MALE_Public.csv"),
        "female": rows(folder / "ANSUR_II_FEMALE_Public.csv"),
    }

    def predicted(sex, height, weight, column):
        t = tables[sex]
        s = np.array([float(r["stature"]) for r in t]) / 1000
        w = np.array([float(r["weightkg"]) for r in t]) / 10
        y = np.array([float(r[column]) for r in t]) / 10
        x = np.column_stack([np.ones_like(s), s, w, w / s**2])
        c, *_ = np.linalg.lstsq(x, y, rcond=None)
        h = height / 100
        return float(np.array([1, h, weight, weight / h**2]) @ c)

    out = [
        "# Standing measurements against ANSUR II",
        "",
        "Generated by `scripts/measurement_figures.py`. Ours / ANSUR II's prediction for the same",
        "sex, height and weight (regression as in `scripts/ansur_sds.py`), in cm. Limb girths: the",
        "largest of the profile's first 10 cm.",
        "",
        "| Body | " + " | ".join(ANSUR) + " |",
        "|---|" + "---|" * len(ANSUR),
    ]
    for sex, height, weight in CHECKED:
        inputs = BodyInputs(sex=sex, height_cm=height, weight_kg=weight, body_type="regular")
        phenotype = fit_body(model, inputs)
        v, faces, joints = posed_parts(model, phenotype, "standing")
        lm = data["landmarks"]
        m = measure(v, faces, parts, lm, data["waist_ring"], joints, limb_starts(v, lm, joints),
                    "standing")  # fmt: skip
        ours = {**m.girths_cm, **m.lengths_cm}
        ours |= {name: max(p[: 10 // PROFILE_STEP_CM + 1]) for name, p in m.profiles_cm.items()}
        cells = [
            f"{ours[n]:.1f} / {predicted(sex, height, weight, c):.1f}" for n, c in ANSUR.items()
        ]
        out.append(f"| {sex} {height} cm {weight} kg | " + " | ".join(cells) + " |")
        print(out[-1])
    (DOCS / "ansur-check.md").write_text("\n".join(out) + "\n")


def main():
    DOCS.mkdir(parents=True, exist_ok=True)
    model = load_model()
    parts, data = body_parts(model), load_landmarks()
    phenotype = fit_body(model, DRAWN)
    v0, _, j0 = posed_parts(model, phenotype, "standing")
    starts = limb_starts(v0, data["landmarks"], j0)
    drawn = lines(model, phenotype, parts, data, starts)
    meshes = {p: posed_parts(model, phenotype, p)[:2] for p in ("standing", "hoods")}
    for name, by_pose in drawn.items():
        fig = plt.figure(figsize=(12, 5))
        for i, (pose, azim) in enumerate([("standing", -60), ("standing", 0), ("hoods", 0)]):
            v, faces = meshes[pose]
            ax = fig.add_subplot(1, 3, i + 1, projection="3d")
            draw(ax, v, faces, by_pose[pose], azim, pose)
        fig.suptitle(f"{name}: man 178 cm 75 kg")
        fig.savefig(DOCS / f"measure-{name}.png", dpi=110, bbox_inches="tight")
        plt.close(fig)
        print(f"drew {name}")
    if len(sys.argv) > 1:
        ansur_check(model, parts, data, Path(sys.argv[1]))


if __name__ == "__main__":
    main()
