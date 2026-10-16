"""Pull the settled frame of every body out of one CLO run's Maya cache (cloth-sim-spike task 1.1).

    uv run python scripts/clo_cache_extract.py hoods-M

Reads $SIMIQ_SPIKE_DIR/runs/<pose>-<size>/garment.{obj,mcx}, written by
jersey-demo/scripts/clo_spike_export.py. Writes cases/<pose>-<size>.npz (garment vertices in mm per
body), cases/garment-uv.obj (mesh and UVs, once) and cases/manifest.json, then deletes the cache.
Everything stays outside the repository: CLO's geometry is a licensed garment.
"""

import json
import os
import shutil
import struct
import sys
from pathlib import Path

import numpy as np

SPIKE_DIR = Path(
    os.environ.get(
        "SIMIQ_SPIKE_DIR", "~/Documents/SIMIQ/mens cycling jersey-green printed/simiq-anny/spike"
    )
).expanduser()
TICKS_PER_FRAME = 200  # Maya cache time units per frame at 30 fps, as CLO writes them
FRAMES = {  # mid-hold frame of each body, from jersey-demo/bodies/anny-*-sequence.json
    "standing": {"start": 0, "178-75": 352, "180-64": 82, "176-88": 172, "192-82": 262},
    "hoods": {"178-75": 352, "180-64": 82, "176-88": 172, "192-82": 262},
    "drops": {"178-75": 442, "180-64": 172, "176-88": 262, "192-82": 352},
}
SETTLE_FRAMES = 10  # the case frame is compared with this many frames earlier


def chunks(buf, start, end):
    """IFF chunks of a Maya FOR8 cache as (tag, body offset, size); data is padded to 8 bytes."""
    i = start
    while i < end:
        tag, size = buf[i : i + 4], struct.unpack(">Q", buf[i + 8 : i + 16])[0]
        yield tag, i + 16, size
        i += 16 + size + (0 if tag == b"FOR8" else -size % 8)


def read_cache(path, times):
    """Vertex positions at the given cache times, {time: (n, 3) float32}."""
    buf = Path(path).read_bytes()
    frames = {}
    for tag, body, size in chunks(buf, 0, len(buf)):
        if tag != b"FOR8" or buf[body : body + 4] != b"MYCH":
            continue
        time, data = None, []
        for ctag, cbody, csize in chunks(buf, body + 4, body + size):
            if ctag == b"TIME":
                time = struct.unpack(">i", buf[cbody : cbody + 4])[0]
                if time not in times:
                    break
            elif ctag == b"FVCA":
                data.append(np.frombuffer(buf, ">f4", csize // 4, cbody).reshape(-1, 3))
        else:
            frames[time] = np.concatenate(data).astype(np.float32)
    return frames


def settle(now, before):
    """How much the garment still moves over SETTLE_FRAMES before the case frame."""
    d = np.linalg.norm(now - before, axis=1)
    return {
        "settle_max_mm": round(float(d.max()), 1),
        "settle_p99_mm": round(float(np.percentile(d, 99)), 1),
        "settle_share_over_5mm": round(float((d > 5).mean()), 4),
    }


def main(run):
    pose, size = run.split("-")
    run_dir, cases_dir = SPIKE_DIR / "runs" / run, SPIKE_DIR / "cases"
    wanted = {f for f in FRAMES[pose].values()} | {
        max(f - SETTLE_FRAMES, 0) for f in FRAMES[pose].values()
    }
    frames = read_cache(run_dir / "garment.mcx", {f * TICKS_PER_FRAME for f in wanted})
    cases, rows = {}, []
    for body, frame in FRAMES[pose].items():
        if body == "start" and size != "M":
            continue  # the starting drape is the M project's frame 0
        now = frames[frame * TICKS_PER_FRAME]
        before = frames[max(frame - SETTLE_FRAMES, 0) * TICKS_PER_FRAME]
        key = "start-178-75" if body == "start" else body
        cases[key] = now
        rows.append(
            {
                "case": f"{pose}/{key}/{size}",
                "pose": pose,
                "body": key.removeprefix("start-"),
                "size": size,
                "frame": frame,
                **settle(now, before),
            }
        )
    cases_dir.mkdir(exist_ok=True)
    np.savez_compressed(cases_dir / f"{run}.npz", **cases)
    if not (cases_dir / "garment-uv.obj").exists():
        shutil.copy(run_dir / "garment.obj", cases_dir / "garment-uv.obj")
    manifest_path = cases_dir / "manifest.json"
    manifest = (
        json.loads(manifest_path.read_text())
        if manifest_path.exists()
        else {"units": "mm, CLO frame (Y up)", "garment_mesh": "garment-uv.obj", "cases": []}
    )
    manifest["cases"] = [
        c for c in manifest["cases"] if (c["pose"], c["size"]) != (pose, size)
    ] + rows
    manifest_path.write_text(json.dumps(manifest, indent=1))
    (run_dir / "garment.mcx").unlink()
    for row in rows:
        print(row)


if __name__ == "__main__":
    main(sys.argv[1])
