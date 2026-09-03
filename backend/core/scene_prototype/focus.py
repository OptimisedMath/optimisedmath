"""PROTOTYPE — throwaway. Render a few named cases big, for close inspection."""

import pathlib
import subprocess
import sys

from backend.core.scene_prototype import gallery
from backend.core.scene_prototype import geometry as G  # noqa: F401
from backend.core.scene_prototype import render as R  # noqa: F401

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
here = pathlib.Path(__file__).parent

wanted = sys.argv[1:] or ["trapezu", "równoległoboku", "Suma", "wysokości"]
picked = [c for c in gallery.CASES if any(w.lower() in c[1].lower() for w in wanted)]

cards = []
for _topic, title, _note, src in picked:
    env: dict = {"G": G, "R": R}
    exec(src, env)
    cards.append(
        f'<figure><figcaption>{title}</figcaption><div class="fig">{env["scene"].to_svg()}</div></figure>'
    )

html = (
    '<!doctype html><meta charset="utf-8">'
    "<style>body{background:#fff;color:#0f172a;font:13px system-ui;margin:0;padding:16px;"
    "display:grid;grid-template-columns:1fr 1fr;gap:16px}"
    "figure{margin:0}figcaption{font-weight:600;margin-bottom:6px}"
    ".fig{border:1px dashed #cbd5e1;border-radius:10px;padding:12px}</style>"
    + "".join(cards)
)
page = here / "_focus.html"
page.write_text(html, encoding="utf-8")
out = here / "focus.png"
subprocess.run(
    [
        CHROME,
        "--headless",
        "--disable-gpu",
        "--hide-scrollbars",
        f"--screenshot={out}",
        "--window-size=900,760",
        "--force-device-scale-factor=2",
        str(page),
    ],
    check=True,
    capture_output=True,
)
page.unlink()
print(out)
