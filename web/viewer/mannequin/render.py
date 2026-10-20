# /// script
# requires-python = ">=3.12"
# dependencies = ["playwright==1.58.0", "pillow"]
# ///
"""Render the preview from the front, side and back next to the Figma frame, for review.

uv run render.py mannequin.glb figma.png out.png [chromium executable] [extra query string]
"""

import functools
import http.server
import sys
import threading
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
VIEWS = (("front", 0), ("side", 90), ("back", 180))
SIZE = (420, 760)
FIGMA_BOX = (465, 105, 845, 795)  # the figure in the 1312×840 "Widget / Body" screenshot


def serve(glb: Path):
    """Serve this folder, with /model.glb mapped to the file under review."""
    class Handler(http.server.SimpleHTTPRequestHandler):
        def translate_path(self, path):
            return str(glb) if path.startswith("/model.glb") else super().translate_path(path)

        def log_message(self, *args):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0),
                                             functools.partial(Handler, directory=str(HERE)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def main():
    glb, figma, out = (Path(a).resolve() for a in sys.argv[1:4])
    chromium = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] else None
    extra = sys.argv[5] if len(sys.argv) > 5 else ""
    server = serve(glb)
    shots = []
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chromium, args=["--use-angle=metal"])
        page = browser.new_page(viewport={"width": SIZE[0], "height": SIZE[1]},
                                device_scale_factor=2)
        for name, az in VIEWS:
            page.goto(f"http://127.0.0.1:{server.server_port}/index.html?m=model.glb&az={az}&{extra}")
            page.wait_for_function("window.__ready === true", timeout=60_000)
            page.wait_for_timeout(500)
            path = out.with_name(f"{out.stem}-{name}.png")
            page.screenshot(path=path)
            shots.append(Image.open(path).convert("RGB"))
        browser.close()
    server.shutdown()
    ref = Image.open(figma).convert("RGB").crop(FIGMA_BOX)
    h = shots[0].height
    ref = ref.resize((round(ref.width * h / ref.height), h), Image.LANCZOS)
    sheet = Image.new("RGB", (ref.width + sum(s.width for s in shots), h), (243, 242, 239))
    x = 0
    for im in (ref, *shots):
        sheet.paste(im, (x, 0))
        x += im.width
    sheet.save(out)
    print(out)


if __name__ == "__main__":
    main()
