"""How thin or heavy can an Anny body get and still look human? Diagnostic for the BMI range.

Run from engine/:  uv run python scripts/thin_bodies.py [heavy]
Builds a 25-year-old man and woman at 190 and 175 cm with Anny's weight parameter at and below 0,
or with `heavy` at and above 1 (beyond [0, 1] is extrapolation), prints mass and BMI and renders
them to docs/measurements/thin-*.png or heavy-*.png.
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import torch  # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # noqa: E402

from simiq_fit.body import anny_age, height_cm, mass_kg  # noqa: E402

DOCS = Path(__file__).resolve().parents[1] / "docs" / "measurements"
CASES = [("male", 190.0), ("female", 175.0)]
HEAVY = sys.argv[1:] == ["heavy"]
WEIGHTS = (1.0, 1.25, 1.5, 1.75) if HEAVY else (0.0, -0.25, -0.5, -0.75)
NAME = "heavy" if HEAVY else "thin"
MUSCLES = (0.0, 0.25)
PROPORTIONS = (0.0, 0.5, 1.0)


def build(model, sex, height, weight, muscle, proportions):
    phenotype = dict(
        gender=1.0 if sex == "female" else 0.0,
        age=anny_age(25),
        height=height,
        weight=weight,
        muscle=muscle,
        proportions=proportions,
    )
    with torch.no_grad():
        return model(phenotype_kwargs=phenotype)["rest_vertices"][0].numpy()


def height_parameter(model, sex, target_cm):
    """Bisect Anny's height parameter for a standing height at weight 0, muscle 0."""
    lo, hi = 0.0, 1.5
    for _ in range(25):
        mid = (lo + hi) / 2
        if height_cm(build(model, sex, mid, 0.0, 0.0, 0.5)) < target_cm:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def draw(ax, vertices, faces, azim, title):
    tri = vertices[faces]
    normals = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    normals /= np.maximum(np.linalg.norm(normals, axis=1, keepdims=True), 1e-12)
    a = np.radians(azim)
    colors = np.tile([0.8, 0.78, 0.75, 1.0], (len(faces), 1))
    colors[:, :3] *= (0.35 + 0.65 * np.abs(normals @ [np.cos(a), np.sin(a), 0.0]))[:, None]
    ax.add_collection3d(Poly3DCollection(tri, facecolors=colors, edgecolors="none"))
    center, half = vertices.mean(axis=0), np.ptp(vertices, axis=0).max() / 2
    for setter, c in zip((ax.set_xlim, ax.set_ylim, ax.set_zlim), center, strict=True):
        setter(c - half, c + half)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=5, azim=azim)
    ax.set_axis_off()
    ax.set_title(title, fontsize=8)


def main():
    import anny

    DOCS.mkdir(parents=True, exist_ok=True)
    model = anny.Anny(extrapolate_phenotypes=True).to(dtype=torch.float32)
    faces = np.asarray(model.faces)
    for sex, target in CASES:
        h = height_parameter(model, sex, target)
        print(f"\n## {sex}, 25 years, {target:.0f} cm (height parameter {h:.3f})")
        print("weight | " + " | ".join(f"m={m} p={p}" for m in MUSCLES for p in PROPORTIONS))
        for weight in WEIGHTS:
            cells = []
            for muscle in MUSCLES:
                for proportions in PROPORTIONS:
                    v = build(model, sex, h, weight, muscle, proportions)
                    cm, kg = height_cm(v), mass_kg(v, faces)
                    cells.append(f"{kg:.1f} kg / BMI {kg / (cm / 100) ** 2:.1f}")
            print(f"{weight} | " + " | ".join(cells))

        fig = plt.figure(figsize=(4 * len(WEIGHTS), 9))
        for i, weight in enumerate(WEIGHTS):
            v = build(model, sex, h, weight, 0.0, 0.5)
            cm, kg = height_cm(v), mass_kg(v, faces)
            title = f"weight {weight}: {kg:.0f} kg, BMI {kg / (cm / 100) ** 2:.1f}"
            draw(fig.add_subplot(2, len(WEIGHTS), i + 1, projection="3d"), v, faces, -90, title)
            draw(fig.add_subplot(2, len(WEIGHTS), len(WEIGHTS) + i + 1, projection="3d"), v,
                 faces, 0, "side")  # fmt: skip
        fig.suptitle(f"{sex} 25 y {target:.0f} cm, muscle 0, proportions 0.5")
        fig.savefig(DOCS / f"{NAME}-{sex}.png", dpi=110, bbox_inches="tight")
        plt.close(fig)
    print(f"\nwrote {DOCS}/{NAME}-male.png and {NAME}-female.png")


if __name__ == "__main__":
    main()
