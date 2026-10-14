"""Anny spike (fit-engine-poc 2.1-2.4): pose 5 bodies, export glTF, measure skinning artifacts.

Run from engine/:  uv run python scripts/anny_spike.py
Writes renders and metrics to docs/anny-spike/ and meshes to out/.
Throwaway: deleted once the go/no-go of task 2.3 is decided.
"""

import importlib.metadata
import platform
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import trimesh  # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # noqa: E402

from simiq_fit.body import ANNY_TOPOLOGY, load_model, pose_body  # noqa: E402
from simiq_fit.poses import POSES, load_pose  # noqa: E402

ENGINE = Path(__file__).resolve().parents[1]
DOCS = ENGINE / "docs" / "anny-spike"
OUT = ENGINE / "out"

# Phenotypes in [0, 1]: gender 0 male, 1 female; age 0.75 is an adult (young 2/3, old 1).
BODIES = {
    "male-average": dict(gender=0.0, age=0.75, muscle=0.5, weight=0.5, height=0.5, proportions=0.5),
    "female-average": dict(
        gender=1.0, age=0.75, muscle=0.5, weight=0.5, height=0.5, proportions=0.5
    ),
    "male-heavy": dict(gender=0.0, age=0.75, muscle=0.5, weight=0.9, height=0.5, proportions=0.5),
    "female-tall-slim": dict(
        gender=1.0, age=0.75, muscle=0.4, weight=0.2, height=0.9, proportions=0.5
    ),
    "male-short-muscular": dict(
        gender=0.0, age=0.75, muscle=0.9, weight=0.6, height=0.2, proportions=0.5
    ),
}

# Vertices are assigned to the region of their heaviest skinning bone.
REGIONS = {
    "hip-crotch": {"root", "spine05", "pelvis.L", "pelvis.R", "upperleg01.L", "upperleg01.R"},
    "shoulder": {
        "clavicle.L",
        "clavicle.R",
        "shoulder01.L",
        "shoulder01.R",
        "upperarm01.L",
        "upperarm01.R",
    },
}
COMPRESSED, STRETCHED = 0.7, 1.4  # edge length ratios flagged as artifacts


def edges(faces, rest):
    e = np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]])
    e = np.unique(np.sort(e, axis=1), axis=0)
    return e[np.linalg.norm(rest[e[:, 0]] - rest[e[:, 1]], axis=1) > 1e-6]


def vertex_regions(model):
    weights = model.vertex_bone_weights.numpy()
    indices = model.vertex_bone_indices.numpy()
    top = indices[np.arange(len(indices)), weights.argmax(axis=1)]
    labels = np.array(model.bone_labels)[top]
    return {name: np.isin(labels, list(bones)) for name, bones in REGIONS.items()}


def signed_volume(vertices, faces):
    a, b, c = vertices[faces[:, 0]], vertices[faces[:, 1]], vertices[faces[:, 2]]
    return np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6.0


def angle_deg(u, v):
    return np.degrees(np.arccos(np.clip(u @ v / np.linalg.norm(u) / np.linalg.norm(v), -1, 1)))


def pose_angles(model, bone_poses):
    head = {
        name: bone_poses[model.bone_labels.index(name), :3, 3]
        for name in (
            "root",
            "spine01",
            "upperleg01.L",
            "lowerleg01.L",
            "upperleg01.R",
            "lowerleg01.R",
        )
    }
    torso = head["spine01"] - head["root"]
    return {
        "torso from horizontal": 90 - angle_deg(torso, np.array([0, 0, 1.0])),
        "hip angle L": angle_deg(torso, head["lowerleg01.L"] - head["upperleg01.L"]),
        "hip angle R": angle_deg(torso, head["lowerleg01.R"] - head["upperleg01.R"]),
    }


def edge_metrics(rest, posed, edge_list, regions):
    ratio = np.linalg.norm(
        posed[edge_list[:, 0]] - posed[edge_list[:, 1]], axis=1
    ) / np.linalg.norm(rest[edge_list[:, 0]] - rest[edge_list[:, 1]], axis=1)
    rows = {}
    for name, mask in regions.items():
        r = ratio[mask[edge_list[:, 0]] | mask[edge_list[:, 1]]]
        rows[name] = dict(
            p1=np.percentile(r, 1),
            p50=np.percentile(r, 50),
            p99=np.percentile(r, 99),
            compressed=100 * np.mean(r < COMPRESSED),
            stretched=100 * np.mean(r > STRETCHED),
        )
    return ratio, rows


def vertex_ratio(ratio, edge_list, n):
    total, count = np.zeros(n), np.zeros(n)
    for col in (0, 1):
        np.add.at(total, edge_list[:, col], ratio)
        np.add.at(count, edge_list[:, col], 1)
    return total / np.maximum(count, 1)


def draw(ax, vertices, faces, values, elev, azim, center=None, half=None, title=""):
    tri = vertices[faces]
    normals = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    normals /= np.maximum(np.linalg.norm(normals, axis=1, keepdims=True), 1e-12)
    e, a = np.radians(elev), np.radians(azim)
    view = np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])
    shade = 0.35 + 0.65 * np.abs(normals @ view)
    if values is None:
        colors = np.tile([0.8, 0.78, 0.75, 1.0], (len(faces), 1))
    else:
        colors = plt.get_cmap("coolwarm")(np.clip((values[faces].mean(axis=1) - 0.6) / 0.8, 0, 1))
    colors[:, :3] *= shade[:, None]
    ax.add_collection3d(Poly3DCollection(tri, facecolors=colors, edgecolors="none"))
    center = vertices.mean(axis=0) if center is None else center
    half = np.ptp(vertices, axis=0).max() / 2 if half is None else half
    for setter, c in zip((ax.set_xlim, ax.set_ylim, ax.set_zlim), center, strict=True):
        setter(c - half, c + half)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    ax.set_title(title, fontsize=8)


# Camera directions: from the left side, from behind and below (crotch), from the front.
VIEWS = {"side": (5, 0), "rear-low": (-35, 60), "front": (5, -90)}


def render_body(name, results, faces):
    fig = plt.figure(figsize=(12, 12))
    for i, pose in enumerate(POSES):
        posed, values, _ = results[pose]
        for j, (view, (elev, azim)) in enumerate(VIEWS.items()):
            ax = fig.add_subplot(len(POSES), len(VIEWS), i * len(VIEWS) + j + 1, projection="3d")
            draw(ax, posed, faces, values, elev, azim, title=f"{pose} · {view}")
    fig.suptitle(f"{name}: colour = edge length ratio posed/rest (blue < 1 < red, range 0.6-1.4)")
    fig.savefig(DOCS / f"{name}.png", dpi=110, bbox_inches="tight")
    plt.close(fig)

    fig = plt.figure(figsize=(12, 8))
    for i, pose in enumerate(("hoods", "drops")):
        posed, _, pelvis = results[pose]
        for j, (view, (elev, azim)) in enumerate(VIEWS.items()):
            ax = fig.add_subplot(2, len(VIEWS), i * len(VIEWS) + j + 1, projection="3d")
            draw(
                ax,
                posed,
                faces,
                None,
                elev,
                azim,
                center=pelvis,
                half=0.25,
                title=f"{pose} · {view} · hips",
            )
    fig.savefig(DOCS / f"{name}-hips.png", dpi=130, bbox_inches="tight")
    plt.close(fig)


def dependency_licenses():
    lines = []
    for dist in sorted(
        importlib.metadata.distributions(), key=lambda d: d.metadata["Name"].lower()
    ):
        meta = dist.metadata
        license_ = meta.get("License-Expression") or (meta.get("License") or "").strip()
        license_ = license_.splitlines()[0][:60] if license_ else ""
        classifiers = [
            c.split(" :: ")[-1]
            for c in meta.get_all("Classifier") or []
            if c.startswith("License ::")
        ]
        lines.append(f"| {meta['Name']} | {dist.version} | {license_} | {', '.join(classifiers)} |")
    return (
        "| Package | Version | License field | License classifiers |\n|---|---|---|---|\n"
        + "\n".join(lines)
    )


def main():
    DOCS.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(exist_ok=True)
    started = time.time()
    model = load_model()
    print(f"model loaded in {time.time() - started:.0f} s, {len(model.bone_labels)} bones")
    regions = vertex_regions(model)
    report = [
        "# Anny spike: metrics",
        "",
        f"Run {time.strftime('%Y-%m-%d %H:%M')} on {platform.platform()}; anny "
        f"{importlib.metadata.version('anny')}, torch {importlib.metadata.version('torch')}, "
        f"topology `{ANNY_TOPOLOGY}`.",
        "",
        f"Edge length ratio posed/rest per region; compressed < {COMPRESSED}, "
        f"stretched > {STRETCHED} (share of edges in %). Volume ratio is the whole mesh. "
        "Angles come from the posed bones.",
        "",
        "| Body | Pose | Region | p1 | p50 | p99 | Compressed % | Stretched % |",
        "|---|---|---|---|---|---|---|---|",
    ]
    extra = [
        "",
        "| Body | Pose | Volume posed/rest | Torso from horizontal | Hip angle L | "
        "Hip angle R | glTF reloads |",
        "|---|---|---|---|---|---|---|",
    ]
    for name, phenotype in BODIES.items():
        results, faces = {}, None
        for pose in POSES:
            body = pose_body(model, phenotype, load_pose(pose))
            faces = body["faces"]
            edge_list = edges(faces, body["rest_vertices"])
            ratio, rows = edge_metrics(body["rest_vertices"], body["vertices"], edge_list, regions)
            values = vertex_ratio(ratio, edge_list, len(body["vertices"]))
            pelvis = body["bone_poses"][model.bone_labels.index("root"), :3, 3]
            results[pose] = (body["vertices"], values, pelvis)
            path = OUT / f"{name}-{pose}.glb"
            trimesh.Trimesh(body["vertices"], faces, process=False).export(path)
            reloaded = trimesh.load(path, force="mesh", process=False)
            for region, r in rows.items():
                report.append(
                    f"| {name} | {pose} | {region} | {r['p1']:.2f} | {r['p50']:.2f} | "
                    f"{r['p99']:.2f} | {r['compressed']:.1f} | {r['stretched']:.1f} |"
                )
            volume = signed_volume(body["vertices"], faces) / signed_volume(
                body["rest_vertices"], faces
            )
            angles = pose_angles(model, body["bone_poses"])
            extra.append(
                f"| {name} | {pose} | {volume:.3f} | {angles['torso from horizontal']:.0f}° | "
                f"{angles['hip angle L']:.0f}° | {angles['hip angle R']:.0f}° | "
                f"{len(reloaded.vertices) == len(body['vertices'])} |"
            )
        render_body(name, results, faces)
        print(f"{name}: done ({time.time() - started:.0f} s)")
    import anny.paths

    noncommercial = (anny.paths.get_anny_cache_path() / "noncommercial").exists()
    extra += ["", f"Non-commercial Anny data (SMPL conversions) in the cache: {noncommercial}"]
    (DOCS / "metrics.md").write_text("\n".join(report + extra) + "\n")
    (DOCS / "dependency-licenses.md").write_text(
        "# Installed packages and their declared licenses\n\n"
        "Generated by scripts/anny_spike.py.\n\n" + dependency_licenses() + "\n"
    )
    print(f"all done in {time.time() - started:.0f} s; see {DOCS}")


if __name__ == "__main__":
    main()
