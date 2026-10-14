"""Anny body model: the only module that imports Anny or PyTorch."""

import numpy as np

from simiq_fit.inputs import BodyInputs

ANNY_TOPOLOGY = "anny"
SMPL_DERIVED_TOPOLOGIES = ("smpl", "smplx")

BODY_DENSITY_KG_PER_L = 1.03
DEFAULT_AGE = 35

# Anny's own morphological age calibration (anny/data/shape_calibration/boys.pth and girls.pth,
# identical for both): age in years and the matching value of Anny's age parameter.
AGE_YEARS_ANCHORS = (0, 1, 4, 11, 16, 18, 64, 110)
ANNY_AGE_ANCHORS = (0.0, 0.05, 0.215, 0.415, 0.67, 0.77, 0.83, 1.0)

# Prior on muscle and fixed proportions until body types are mapped (task 3.3). Muscle 0.25 sits
# between Anny's min (0) and average (0.5) muscle anchors, away from their kinks; there the weight
# parameter spans about BMI 15-34, at 0.5 only about BMI 17-22 (scripts/body_ranges.py, 2026-10-14).
DEFAULT_MUSCLE = 0.25
DEFAULT_PROPORTIONS = 0.5

# Weighted Gauss-Newton fit of Anny's height, weight and muscle (docs/formulas.md, "Body fit").
FIT_MAX_STEPS = 30
FIT_MAX_HALVINGS = 8
FIT_MAX_PARAMETER_STEP = 0.25
FIT_STOP_HEIGHT_CM = 0.05
FIT_STOP_MASS_SHARE = 0.002
FIT_MUSCLE_PRIOR_SD = 0.25  # how far muscle may drift from its prior when weight alone saturates
FIT_START_WEIGHTS = (0.0, 0.25, 0.5, 0.75, 1.0)  # the fit starts from the best of these


def check_topology(topology: str) -> None:
    """Refuse a mesh topology derived from the non-commercial SMPL family."""
    if topology.split("-")[0] in SMPL_DERIVED_TOPOLOGIES:
        raise ValueError(f"topology {topology!r} is SMPL-derived and non-commercial")


def anny_age(years: float) -> float:
    """Anny's age parameter for an age in years, interpolated in Anny's calibration."""
    return float(np.interp(years, AGE_YEARS_ANCHORS, ANNY_AGE_ANCHORS))


def height_cm(vertices):
    """Vertical extent of a standing mesh in cm (Anny works in metres, z up)."""
    return (vertices[:, 2].max() - vertices[:, 2].min()) * 100


def mass_kg(vertices, faces):
    """Mesh volume by the divergence theorem, in litres, times the body density."""
    a, b, c = vertices[faces[:, 0]], vertices[faces[:, 1]], vertices[faces[:, 2]]
    cross_x = b[:, 1] * c[:, 2] - b[:, 2] * c[:, 1]
    cross_y = b[:, 2] * c[:, 0] - b[:, 0] * c[:, 2]
    cross_z = b[:, 0] * c[:, 1] - b[:, 1] * c[:, 0]
    volume_m3 = abs((a[:, 0] * cross_x + a[:, 1] * cross_y + a[:, 2] * cross_z).sum() / 6)
    return volume_m3 * 1000 * BODY_DENSITY_KG_PER_L


def load_model(topology: str = ANNY_TOPOLOGY):
    """Anny with its default 104-bone rig and local-ref pose parameterization."""
    check_topology(topology)
    import anny
    import torch

    return anny.Anny(topology=topology).to(dtype=torch.float32)


def fit_body(model, inputs: BodyInputs) -> dict[str, float]:
    """Anny phenotype whose standing mesh has the given height and mass."""
    import torch

    fixed = {
        "gender": 1.0 if inputs.sex == "female" else 0.0,  # `other` is built as male (D2)
        "age": anny_age(inputs.age or DEFAULT_AGE),
        "proportions": DEFAULT_PROPORTIONS,
    }
    fixed_tensors = {k: torch.tensor([v]) for k, v in fixed.items()}
    faces = torch.as_tensor(np.asarray(model.faces))
    target = torch.tensor([inputs.height_cm, inputs.weight_kg])
    scale = torch.tensor([FIT_STOP_HEIGHT_CM, FIT_STOP_MASS_SHARE * inputs.weight_kg])

    def measure(x):
        phenotype = {**fixed_tensors, "height": x[0:1], "weight": x[1:2], "muscle": x[2:3]}
        vertices = model(phenotype_kwargs=phenotype)["rest_vertices"][0]
        return torch.stack([height_cm(vertices), mass_kg(vertices, faces)])

    def residuals(x):
        prior = (x[2:3] - DEFAULT_MUSCLE) / FIT_MUSCLE_PRIOR_SD
        return torch.cat([(measure(x) - target) / scale, prior])

    def cost(x):
        return float((residuals(x).detach() ** 2).sum())

    starts = [torch.tensor([0.5, w, DEFAULT_MUSCLE]) for w in FIT_START_WEIGHTS]
    x = min(starts, key=cost)
    for _ in range(FIT_MAX_STEPS):
        r = residuals(x).detach()
        if abs(r[0]) < 1 and abs(r[1]) < 1:
            return {**fixed, "height": float(x[0]), "weight": float(x[1]), "muscle": float(x[2])}
        jacobian = torch.autograd.functional.jacobian(residuals, x)
        step = torch.linalg.lstsq(jacobian, r.unsqueeze(1)).solution.squeeze(1)
        # Freeze a parameter that sits at its bound and is pushed outward; re-solve the rest.
        stuck = ((x <= 0) & (step > 0)) | ((x >= 1) & (step < 0))
        if stuck.any():
            free = jacobian * ~stuck
            step = torch.linalg.lstsq(free, r.unsqueeze(1)).solution.squeeze(1) * ~stuck
        step = step.clamp(-FIT_MAX_PARAMETER_STEP, FIT_MAX_PARAMETER_STEP)
        # Backtracking: halve the step until it lowers the squared residuals.
        current = float((r**2).sum())
        for _ in range(FIT_MAX_HALVINGS):
            candidate = (x - step).clamp(0.0, 1.0)
            if cost(candidate) < current:
                break
            step = step / 2
        else:
            break  # no step lowers the residuals: the closest body is reached
        x = candidate
    reached = measure(x).detach()
    raise ValueError(
        f"no Anny body reaches {inputs.height_cm} cm and {inputs.weight_kg} kg; "
        f"closest: height {float(reached[0]):.1f} cm, mass {float(reached[1]):.1f} kg "
        f"(height {float(x[0]):.3f}, weight {float(x[1]):.3f}, muscle {float(x[2]):.3f})"
    )


def rest_vertices(model, phenotype: dict[str, float]) -> np.ndarray:
    """Standing (rest pose) vertices of a body, in metres."""
    import torch

    with torch.no_grad():
        return model(phenotype_kwargs=phenotype)["rest_vertices"][0].numpy()


def pose_body(model, phenotype: dict[str, float], pose: dict[str, np.ndarray]) -> dict:
    """Rest and posed vertices of one body; pose maps bone names to 3x3 rotations."""
    import torch

    transforms = torch.eye(4).repeat(1, model.bone_count, 1, 1)
    for bone, r in pose.items():
        transforms[0, model.bone_labels.index(bone), :3, :3] = torch.as_tensor(r)
    with torch.no_grad():
        out = model(pose_parameters=transforms, phenotype_kwargs=phenotype)
    return {
        "rest_vertices": out["rest_vertices"][0].numpy(),
        "vertices": out["vertices"][0].numpy(),
        "bone_poses": out["bone_poses"][0].numpy(),
        "faces": np.asarray(model.faces),
    }
