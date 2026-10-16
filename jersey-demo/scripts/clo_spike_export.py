"""Run inside CLO (cloth-sim-spike 1.1): size by course shrinkage, export the recorded drape.

exec() this file in CLO's Python editor, then set_size("S"), record the animation by hand, and
export_run("hoods-S"). The FBX export writes the garment mesh with UVs (frame 0) and a Maya cache
of every frame; engine/scripts/clo_cache_extract.py turns that into the spike's cases.
"""

import json
import os

import ApiTypes
import export_api
import pattern_api
import utility_api

SP = "/Users/rastislav/Documents/SIMIQ/mens cycling jersey-green printed/simiq-anny/spike/"
SIZE_FACTOR = {"S": 68.5 / 72, "M": 1.0, "L": 75.5 / 72}


def set_size(size):
    for b in json.load(open(SP + "base_shrinkage.json")):
        pattern_api.SetWidthShrinkagePercentage(
            b["index"], round(b["width"] * SIZE_FACTOR[size], 3)
        )
    return [
        pattern_api.GetShrinkagePercentage(i)["Width"] for i in range(pattern_api.GetPatternCount())
    ]


def export_run(run):
    out = SP + "runs/" + run + "/"
    os.makedirs(out, exist_ok=True)
    o = ApiTypes.ImportExportOption()
    o.bExportAvatar = False
    o.bExportGarment = True
    o.bSingleObject = True
    o.bThin = True
    o.bCreateClothCacheAnimation = True
    files = export_api.ExportFBX(out + "garment.fbx", o)
    widths = [
        pattern_api.GetShrinkagePercentage(i)["Width"] for i in range(pattern_api.GetPatternCount())
    ]
    json.dump(
        {
            "run": run,
            "project": utility_api.GetProjectFilePath(),
            "end_frame": utility_api.GetEndAnimationFrame(),
            "width_shrinkage": widths,
            "files": files,
        },
        open(out + "export.json", "w"),
        indent=1,
    )
    return files
