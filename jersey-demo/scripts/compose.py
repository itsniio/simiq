"""Per-pose comparison videos and grids, plus an all-poses video and summary, from CLO exports."""
import subprocess, sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

V = Path(sys.argv[1])
POSES = {"hoods": "jazda, ruky na páčkach (hoods)", "drops": "jazda, ruky v spodnom držaní (drops)", "standing": "stoj"}
BODIES = [("178-75", "178 cm · 75 kg · BMI 23,7"), ("180-64", "180 cm · 64 kg · BMI 19,8 (štíhly)"),
          ("176-88", "176 cm · 88 kg · BMI 28,4 (silnejší)"), ("192-82", "192 cm · 82 kg · BMI 22,2 (vysoký)")]
FRAMES = [7, 82, 172, 262]
CLO = LinearSegmentedColormap.from_list("clo", ["#4f8cff", "#36d6e8", "#34e37a", "#f4ef3a", "#ff9a1f", "#ff2a1a"])
W, H = 1440, 160
def ff(*args):
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *args], check=True)

def caption(pose, text, path):
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
    fig.text(0.015, 0.62, f"Rovnaký dres (veľkosť M), rôzne telá · {POSES[pose]}", fontsize=17, color="#222", weight="bold")
    fig.text(0.015, 0.2, text, fontsize=22, color="#c0392b")
    ax = fig.add_axes([0.62, 0.42, 0.35, 0.2])
    ax.imshow(np.linspace(0, 1, 256)[None, :], aspect="auto", cmap=CLO)
    ax.set_yticks([]); ax.set_xticks([0, 127, 255]); ax.set_xticklabels(["0 %", "20 %", "40 %"], fontsize=13)
    fig.text(0.62, 0.75, "Natiahnutie látky (simulácia CLO)", fontsize=14, color="#222")
    fig.text(0.62, 0.04, "Ukážkový dres, látka neznáma – nie meranie", fontsize=11, color="#666")
    fig.savefig(path, facecolor="white"); plt.close(fig)

def strip(pose, vid):
    out = V / pose / f"strip-{vid}.png"
    sel = "+".join(f"eq(n\\,{f})" for f in FRAMES)
    ff("-i", str(V / pose / f"{vid}.mp4"), "-vf", f"select='{sel}',scale=360:-1,tile=4x1", "-frames:v", "1", "-fps_mode", "passthrough", str(out))
    return plt.imread(out)

def grid(cols, title, path):
    fig, axs = plt.subplots(4, len(cols), figsize=(4 * len(cols), 23), dpi=100)
    for c, (pose, vid, head) in enumerate(cols):
        s = strip(pose, vid); w = s.shape[1] // 4
        for r, (key, text) in enumerate(BODIES):
            a = axs[r, c]; a.imshow(s[:, r * w:(r + 1) * w]); a.set_xticks([]); a.set_yticks([])
            for sp in a.spines.values(): sp.set_visible(False)
            if r == 0: a.set_title(head, fontsize=15)
            if c == 0: a.set_ylabel(text.replace(" · BMI", "\nBMI"), fontsize=14)
    fig.suptitle(title, fontsize=18, y=0.995); fig.tight_layout(); fig.savefig(path); plt.close(fig)

for pose in POSES:
    d = V / pose
    for key, text in BODIES:
        caption(pose, text, d / f"cap-{key}.png")
    views = ["texture-front", "strain-front", "strain-side", "texture-back", "strain-back", "strain-34front"]
    ins = sum([["-i", str(d / f"{v}.mp4")] for v in views], []) + sum([["-loop", "1", "-i", str(d / f"cap-{k}.png")] for k, _ in BODIES], [])
    fc = "".join(f"[{i}]scale=480:720[v{i}];" for i in range(6)) + "[v0][v1][v2]hstack=3[r1];[v3][v4][v5]hstack=3[r2];" \
         "[6][7]overlay=enable='between(t,0.5,3.5)'[c1];[c1][8]overlay=enable='between(t,3.5,6.5)'[c2];[c2][9]overlay=enable='between(t,6.5,9.5)'[cap];" \
         "[r1][r2][cap]vstack=3,format=yuv420p[out]"
    ff(*ins, "-filter_complex", fc, "-map", "[out]", "-t", "12.5", "-r", "30", "-c:v", "libx264", "-crf", "20", "-movflags", "+faststart", str(V / f"simiq-{pose}-sequence.mp4"))
    grid([(pose, "texture-front", "Potlač · spredu"), (pose, "strain-front", "Heatmapa · spredu"), (pose, "texture-back", "Potlač · zozadu"),
          (pose, "strain-back", "Heatmapa · zozadu"), (pose, "strain-side", "Heatmapa · z boku")],
         f"Ukážkový dres M na štyroch telách z Anny · {POSES[pose]} (CLO, natiahnutie 0–40 %)", V / f"simiq-{pose}-comparison.png")
    print(pose, "ok")

lst = V / "concat.txt"
lst.write_text("".join(f"file 'simiq-{p}-sequence.mp4'\n" for p in POSES))
ff("-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(V / "simiq-all-poses.mp4")); lst.unlink()
grid([(p, v, f"{h} · {n}") for p, n in (("hoods", "hoods"), ("drops", "drops"), ("standing", "stoj")) for v, h in (("strain-side", "z boku"), ("strain-back", "zozadu"))],
     "Ukážkový dres M: štyri telá v troch polohách (CLO, natiahnutie 0–40 %)", V / "simiq-poses-summary.png")
print("all ok")
