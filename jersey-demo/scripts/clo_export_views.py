"""Run inside CLO (Edit > Python Script): export the recorded animation from three cameras, with and without the strain map."""
import ApiTypes, utility_api, export_api

OUT = "/Users/rastislav/Documents/SIMIQ/mens cycling jersey-green printed/simiq-anny/bodies/videos/standing/"
END_FRAME = 374
VIEWS = {"front": 2, "side": 6, "34front": 1}  # SetCamViewPoint values; a straight back view is key 8 in the 3D window

for mode, strain in (("strain", True), ("texture", False)):
    utility_api.SetStrainMapStatus(strain)
    for name, view in VIEWS.items():
        utility_api.SetCamViewPoint(view)
        utility_api.Refresh3DWindow()
        option = ApiTypes.VideoExportOption()
        option.width, option.height, option.fps, option.startFrame, option.endFrame = 720, 1080, 30, 0, END_FRAME
        print(export_api.ExportAnimationVideo(OUT + f"{mode}-{name}.mp4", option))
utility_api.SetStrainMapStatus(True)
