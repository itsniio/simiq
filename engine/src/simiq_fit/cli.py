"""The simiq-fit command line (design D10). Commands are added as their tasks land."""

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from simiq_fit.garment import DATA, Fabric, Garment, grading_warnings, write_schemas

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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="simiq-fit")
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("validate-data", help="check garment and fabric files")
    check.add_argument("files", nargs="*", help="default: data/garments, fabrics and examples")
    check.set_defaults(run=validate_data)
    export = commands.add_parser("schema", help="write the JSON Schema of garment and fabric")
    export.add_argument("--out", default=str(DATA / "schema"))
    export.set_defaults(run=schema)
    args = parser.parse_args(argv)
    return args.run(args)


if __name__ == "__main__":
    sys.exit(main())
