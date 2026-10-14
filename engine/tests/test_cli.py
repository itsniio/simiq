"""The simiq-fit commands measure and export-mesh (fit-engine-poc 7.3), as in engine/README.md."""

import json

BODY = ["--sex", "female", "--height-cm", "165", "--weight-kg", "60"]


def test_measure_prints_each_pose_and_the_sds(capfd):
    # capfd, not capsys: it also catches what native libraries write to stdout, which would break
    # the JSON (warp's banner did).
    from simiq_fit.cli import main

    assert main(["measure", *BODY, "--chest-cm", "88"]) == 0
    result = json.loads(capfd.readouterr().out)
    assert set(result["poses"]) == {"standing", "hoods"}  # the default poses
    assert result["poses"]["hoods"]["pose"] == "hoods"
    assert set(result["poses"]["standing"]["girths_cm"]) == {
        "chest_girth",
        "waist_girth",
        "hip_girth",
    }
    # A chest measurement was given, so its SD is the combined one, below the women's 4.24 cm.
    assert result["sds_cm"]["chest_girth"] < 4.24 and result["sds_cm"]["hip_girth"] == 2.91


def test_export_mesh_writes_a_gltf_file(tmp_path, capsys):
    import trimesh

    from simiq_fit.cli import main

    out = tmp_path / "body.glb"
    assert main(["export-mesh", *BODY, "--pose", "hoods", "--out", str(out)]) == 0
    mesh = trimesh.load(out, force="mesh", process=False)
    assert len(mesh.vertices) == 13718  # Anny's topology


def test_invalid_inputs_exit_with_the_reason(capsys):
    from simiq_fit.cli import main

    assert main(["measure", "--sex", "male", "--height-cm", "150", "--weight-kg", "150"]) == 2
    assert "height and weight combination" in capsys.readouterr().err
