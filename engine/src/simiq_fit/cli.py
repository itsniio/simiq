"""The simiq-fit command line (design D10). Commands are added as their tasks land."""

import argparse
import contextlib
import json
import os
import sys
from pathlib import Path

from pydantic import ValidationError

from simiq_fit.garment import DATA, Fabric, Garment, grading_warnings, write_schemas
from simiq_fit.inputs import BodyInputs
from simiq_fit.poses import POSES

DATA_FOLDERS = ("garments", "fabrics", "examples")


def check_records(paths: list[Path]) -> tuple[list[str], list[str]]:
    """Errors and warnings for garment and fabric files; a file with `curves` is a fabric."""
    errors, warnings, garments, fabric_ids = [], [], [], set()
    for path in paths:
        try:
            data = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as error:
            errors.append(f"{path}: {error}")
            continue
        model = Fabric if "curves" in data else Garment
        try:
            record = model.model_validate(data)
        except ValidationError as error:
            for e in error.errors():
                field = ".".join(str(part) for part in e["loc"]) or "record"
                errors.append(f"{path}: {field}: {e['msg']}")
            continue
        if isinstance(record, Fabric):
            fabric_ids.add(record.id)
        else:
            garments.append((path, record))
            warnings += grading_warnings(record)
    for path, garment in garments:
        for key, fabric_id in garment.fabrics.items():
            if fabric_id not in fabric_ids:
                errors.append(
                    f"{path}: fabrics.{key}: no fabric record {fabric_id!r} among the files"
                )
    return errors, warnings


def validate_data(args) -> int:
    paths = [Path(p) for p in args.files] or sorted(
        p for folder in DATA_FOLDERS for p in (DATA / folder).glob("*.json")
    )
    errors, warnings = check_records(paths)
    for line in warnings:
        print(f"warning: {line}")
    for line in errors:
        print(f"error: {line}")
    print(f"{len(paths)} files, {len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors else 0


def schema(args) -> int:
    for path in write_schemas(Path(args.out)):
        print(f"wrote {path}")
    return 0


def body_inputs(args) -> BodyInputs:
    fields = {name: getattr(args, name) for name in BodyInputs.model_fields if hasattr(args, name)}
    return BodyInputs(**{k: v for k, v in fields.items() if v is not None})


@contextlib.contextmanager
def stdout_to_stderr():
    """Send everything written to stdout, by Python or native libraries, to stderr meanwhile.

    Warp, which Anny uses, prints a banner on stdout from native code; the JSON on stdout must stay
    clean for whoever reads it.
    """
    sys.stdout.flush()
    saved = os.dup(1)
    os.dup2(2, 1)
    try:
        yield
    finally:
        sys.stdout.flush()
        os.dup2(saved, 1)
        os.close(saved)


def built_body(args):
    """Anny and the fitted phenotype for the command-line inputs (slow: builds Anny)."""
    from simiq_fit.body import fit_body, load_model

    model = load_model()
    return model, fit_body(model, body_inputs(args))


def measure_command(args) -> int:
    """Measurements in each pose and their SDs, as JSON on stdout (body data is never logged)."""
    from simiq_fit.measure import measure_body
    from simiq_fit.uncertainty import measurement_sds_cm

    inputs = body_inputs(args)
    with stdout_to_stderr():
        model, phenotype = built_body(args)
        poses = {pose: measure_body(model, phenotype, pose).model_dump() for pose in args.pose}
    print(json.dumps({"poses": poses, "sds_cm": measurement_sds_cm(inputs)}, indent=2))
    return 0


def export_mesh(args) -> int:
    """The posed body as a glTF binary file for any viewer."""
    import trimesh

    from simiq_fit.body import pose_body
    from simiq_fit.poses import load_pose

    rotations = load_pose(args.pose[0])
    with stdout_to_stderr():
        model, phenotype = built_body(args)
        posed = pose_body(model, phenotype, rotations)
    trimesh.Trimesh(posed["vertices"], posed["faces"], process=False).export(args.out)
    print(f"wrote {args.out}")
    return 0


def add_body_arguments(parser):
    parser.add_argument("--sex", required=True, choices=["female", "male", "other"])
    parser.add_argument("--height-cm", dest="height_cm", type=float, required=True)
    parser.add_argument("--weight-kg", dest="weight_kg", type=float, required=True)
    parser.add_argument("--body-type", dest="body_type", default="regular",
                        choices=["slim", "regular", "athletic"])  # fmt: skip
    parser.add_argument("--age", type=int)
    for name in ("chest", "waist", "biceps", "thigh", "calf", "inseam", "outseam"):
        parser.add_argument(f"--{name}-cm", dest=f"{name}_cm", type=float)
    parser.add_argument("--pose", action="append", choices=POSES,
                        help="repeat for several; default standing and hoods")  # fmt: skip


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="simiq-fit")
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("validate-data", help="check garment and fabric files")
    check.add_argument("files", nargs="*", help="default: data/garments, fabrics and examples")
    check.set_defaults(run=validate_data)
    export = commands.add_parser("schema", help="write the JSON Schema of garment and fabric")
    export.add_argument("--out", default=str(DATA / "schema"))
    export.set_defaults(run=schema)
    measuring = commands.add_parser("measure", help="body measurements in each pose, as JSON")
    add_body_arguments(measuring)
    measuring.set_defaults(run=measure_command)
    mesh = commands.add_parser("export-mesh", help="the posed body as glTF (.glb)")
    add_body_arguments(mesh)
    mesh.add_argument("--out", required=True)
    mesh.set_defaults(run=export_mesh)
    args = parser.parse_args(argv)
    if hasattr(args, "pose"):
        args.pose = args.pose or ["standing", "hoods"]
    try:
        return args.run(args)
    except ValueError as error:  # invalid inputs, unknown pose, unreachable body
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
