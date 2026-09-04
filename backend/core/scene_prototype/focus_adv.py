"""PROTOTYPE — throwaway. Render a few named adversarial cases big, for close inspection."""

import pathlib
import subprocess
import sys

from backend.core.scene_prototype import adversarial
from backend.core.scene_prototype import geometry as G  # noqa: F401
from backend.core.scene_prototype import render as R  # noqa: F401

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
here = pathlib.Path(__file__).parent

wanted = sys.argv[1:] or ["1°", "słowne", "telefonu"]
picked = [
    c for c in adversarial.CASES if any(w.lower() in c[0].lower() for w in wanted)
]

cards = []
for title, _note, src in picked:
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
page = here / "_focus_adv.html"
page.write_text(html, encoding="utf-8")
out = here / "focus_adv.png"
subprocess.run(
    [
        CHROME,
        "--headless",
        "--disable-gpu",
        "--hide-scrollbars",
        f"--screenshot={out}",
        "--window-size=1100,1400",
        "--force-device-scale-factor=2",
        str(page),
    ],
    check=True,
    capture_output=True,
)
page.unlink()
print(out)
