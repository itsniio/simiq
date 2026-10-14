"""Anny body model: the only module that imports Anny or PyTorch."""

import numpy as np

ANNY_TOPOLOGY = "anny"
SMPL_DERIVED_TOPOLOGIES = ("smpl", "smplx")


def check_topology(topology: str) -> None:
    """Refuse a mesh topology derived from the non-commercial SMPL family."""
    if topology.split("-")[0] in SMPL_DERIVED_TOPOLOGIES:
        raise ValueError(f"topology {topology!r} is SMPL-derived and non-commercial")


def load_model(topology: str = ANNY_TOPOLOGY):
    """Anny with its default 104-bone rig and local-ref pose parameterization."""
    check_topology(topology)
    import anny
    import torch

    return anny.Anny(topology=topology).to(dtype=torch.float32)


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
