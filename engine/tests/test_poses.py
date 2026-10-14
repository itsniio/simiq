import numpy as np
import pytest

from simiq_fit.poses import POSES, load_pose, rotation

# Anny's world axes: +X is the body's left, -Y is forward, +Z is up.


def test_positive_x_rotation_leans_forward():
    # Rx(90°) takes "up" (0, 0, 1) to y = -sin 90° = -1, z = cos 90° = 0: forward.
    assert np.allclose(rotation(90, 0, 0) @ [0, 0, 1], [0, -1, 0])


def test_z_rotation_turns_left_toward_back():
    # Rz(90°) takes (1, 0, 0) to x = cos 90° = 0, y = sin 90° = 1.
    assert np.allclose(rotation(0, 0, 90) @ [1, 0, 0], [0, 1, 0])


def test_x_is_applied_before_z():
    # Rx(90°) first: (0, 0, 1) -> (0, -1, 0); then Rz(90°): x = 0·0 - (-1)·1 = 1, y = 0.
    assert np.allclose(rotation(90, 0, 90) @ [0, 0, 1], [1, 0, 0])


@pytest.mark.parametrize("name", POSES)
def test_every_preset_loads_as_rotation_matrices(name):
    pose = load_pose(name)
    for bone, r in pose.items():
        assert r.shape == (3, 3), bone
        assert np.allclose(r @ r.T, np.eye(3)), bone
        assert np.isclose(np.linalg.det(r), 1.0), bone


def test_standing_is_the_rest_pose():
    assert load_pose("standing") == {}


def test_unknown_pose_lists_the_available_ones():
    with pytest.raises(ValueError, match="standing, hoods, drops"):
        load_pose("aero")


@pytest.mark.parametrize("name", POSES)
def test_no_preset_rotates_the_root(name):
    # Anny's local-ref parameterization ignores the root bone (spike run 1).
    assert "root" not in load_pose(name)
