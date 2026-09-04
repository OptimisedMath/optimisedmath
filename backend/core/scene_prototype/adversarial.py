"""PROTOTYPE — throwaway. Adversarial gallery for wayfinder ticket #212.

Same harness as `gallery.py`, but every case here is chosen to be hostile:
extreme aspect ratios, extreme angles, colliding labels, long Polish words,
and phone width. The point is to find what breaks, not to look nice.

Run:  python -m backend.core.scene_prototype.adversarial   # writes adversarial.html
"""

from __future__ import annotations

import html
import pathlib

from backend.core.scene_prototype import geometry as G
from backend.core.scene_prototype import render as R

# (title, what this case is stress-testing, generator-side source)
CASES: list[tuple[str, str, str]] = [
    (
        "Prostokąt 1×40",
        "Extreme aspect ratio, long side. Does a thin sliver rectangle still "
        "read as a rectangle, and do both edge labels stay off the strokes?",
        """
fig = G.rectangle(width=40, height=1)
scene = R.Scene(fig, [
    R.Outline(),
    R.EdgeLabel("AB", unit_label="cm"),
    R.EdgeLabel("BC", unit_label="cm"),
])
""",
    ),
    (
        "Prostokąt 40×1",
        "Same ratio, rotated. The pen unit is derived from the diagonal, so "
        "this should look identical to 1×40 turned on its side — check that.",
        """
fig = G.rectangle(width=1, height=40)
scene = R.Scene(fig, [
    R.Outline(),
    R.EdgeLabel("AB", unit_label="cm"),
    R.EdgeLabel("BC", unit_label="cm"),
])
""",
    ),
    (
        "Kąt 179°",
        "A near-straight angle. The arc radius rule shrinks for narrow angles "
        "but this is the opposite extreme — does the arc still read as an arc "
        "rather than a straight line, and does the label sit on the vertex?",
        """
fig = G.Triangle.angles(angle_a=179, angle_b=0.5, scale=10)
scene = R.Scene(fig, [
    R.Outline(),
    R.VertexLabels(),
    R.AngleArc("A"),
])
""",
    ),
    (
        "Kąt 1° — poza dopuszczalnym zakresem",
        "The narrow-angle extreme the squeeze factor exists for. A 1° arc's own "
        "label cannot clear the vertex (found by scanning: the placement cost "
        "crosses its collision threshold between 12° and 13°), so `AngleArc` "
        "now REFUSES below 15° — the same shape of refusal `RightAngle` already "
        "has for a non-90° vertex. This card shows the refusal, not a bad diagram.",
        """
fig = G.Triangle.angles(angle_a=1, angle_b=90, scale=10)
try:
    scene = R.Scene(fig, [
        R.Outline(),
        R.VertexLabels(),
        R.AngleArc("A"),
    ])
    scene.to_svg()
    raised = None
except ValueError as e:
    raised = str(e)
    scene = R.Scene(fig, [R.Outline(), R.VertexLabels()])
""",
    ),
    (
        "Trójkąt równoboczny — etykiety",
        "Near-equal sides put all three vertex labels, edge labels and tick "
        "marks within a tight, symmetric budget — the collision case where "
        "nothing has an obviously freer side to slide toward.",
        """
fig = G.Triangle.sss(a=8, b=8.1, c=7.9)
scene = R.Scene(fig, [
    R.Outline(),
    R.VertexLabels(),
    R.EdgeLabel("AB", unit_label="cm"),
    R.EdgeLabel("BC", unit_label="cm"),
    R.EdgeLabel("CA", unit_label="cm"),
    R.Ticks("AB"), R.Ticks("BC"), R.Ticks("CA"),
])
""",
    ),
    (
        "Trójkąt bardzo rozwarty",
        "A 178° apex angle: the triangle is nearly a flat sliver, so the "
        "altitude's foot lands far outside the base and the dotted extension "
        "has to travel a long way without crossing any label.",
        """
fig = G.Triangle.base_height(base=20, height=1, apex_frac=8.0)
scene = R.Scene(fig, [
    R.Outline(),
    R.VertexLabels(),
    R.EdgeLabel("AB", unit_label="cm"),
    R.Altitude(apex="C", base="AB", unit_label="cm"),
])
""",
    ),
    (
        "Trapez 20:1",
        "Parallel sides differing by a factor of 20 — the upper base is "
        "barely a sliver against the lower one. Does `ParallelMarks` still "
        "make sense at that ratio, and does the short base's label collide "
        "with the vertex labels either side of it?",
        """
fig = G.trapezoid(a=20, b=1, height=4)
scene = R.Scene(fig, [
    R.Outline(),
    R.VertexLabels(),
    R.EdgeLabel("AB", unit_label="cm"),
    R.EdgeLabel("CD", unit_label="cm"),
    R.ParallelMarks(["AB", "CD"]),
    R.Altitude(apex="D", base="AB", unit_label="cm"),
])
""",
    ),
    (
        "Promień nie mieści się w kole",
        "A small circle with a long decimal radius label. `Radius` places its "
        "label along the radius itself — does the label spill outside the "
        "circle rather than sitting on the radius line?",
        """
fig = G.circle(radius=1.5)
scene = R.Scene(fig, [
    R.Outline(),
    R.Centre("O"),
    R.Radius(at=35, unit_label="cm"),
])
""",
    ),
    (
        "Etykiety wielocyfrowe i dziesiętne",
        "`12,5 cm`-style labels on every edge of a shape sized so the "
        "half-width character estimate (`0.30 * size * len(text)`) is put "
        "under real pressure by four long labels at once.",
        """
fig = G.trapezoid(a=12.5, b=6.25, height=4.75)
scene = R.Scene(fig, [
    R.Outline(),
    R.VertexLabels(),
    R.EdgeLabel("AB", unit_label="cm"),
    R.EdgeLabel("CD", unit_label="cm"),
    R.Altitude(apex="D", base="AB", unit_label="cm"),
])
""",
    ),
    (
        "Etykiety słowne — wysokość/podstawa/przekątna",
        "The finding from #211's prototype: the label box is estimated from "
        "character COUNT, not measured width or ascender/descender height. "
        "Polish words are both longer and, with ą/ę descenders, taller than "
        "the digit-and-unit case the estimate was tuned against.",
        """
fig = G.Triangle.base_height(base=10, height=6, apex_frac=0.4)
scene = R.Scene(fig, [
    R.Outline(),
    R.VertexLabels(),
    R.EdgeLabel("AB", unknown=True, unknown_text="podstawa"),
    R.Altitude(apex="C", base="AB", unknown=True),
    R.EdgeLabel("CA", unknown=True, unknown_text="przekątna"),
])
""",
    ),
    (
        "Prostokąt szerokości telefonu",
        "A wide, short rectangle rendered in a card capped to phone width "
        "(~340px). Long labels on the extension-line annotation are the ones "
        "most likely to clip a narrow viewport.",
        """
fig = G.rectangle(width=16, height=3)
scene = R.Scene(fig, [
    R.Outline(),
    R.RightAngle("A"),
    R.DimensionLine("AB", unit_label="cm"),
    R.DimensionLine("BC", unit_label="cm"),
])
""",
    ),
    (
        "Etykiety słowne przy szerokości telefonu",
        "The word-label case again, in the same phone-width card as above — "
        "the combination the report flagged as untested: a long word label "
        "that is a large fraction of the figure's own extent, on a narrow "
        "screen.",
        """
fig = G.Triangle.base_height(base=10, height=6, apex_frac=0.4)
scene = R.Scene(fig, [
    R.Outline(),
    R.VertexLabels(),
    R.EdgeLabel("AB", unknown=True, unknown_text="podstawa"),
    R.Altitude(apex="C", base="AB", unknown=True),
    R.EdgeLabel("CA", unknown=True, unknown_text="przekątna trójkąta"),
])
""",
    ),
    (
        "Etykiety słowne — mały trójkąt, gęsto",
        "The word-label box is estimated from character COUNT (#211's known "
        "gap). This shrinks the figure until the estimate is under real "
        "pressure: three long words plus vertex letters on a small triangle, "
        "the density #211's report predicted would expose it.",
        """
fig = G.Triangle.sss(a=4, b=4.2, c=3.8)
scene = R.Scene(fig, [
    R.Outline(),
    R.VertexLabels(),
    R.EdgeLabel("AB", unknown=True, unknown_text="podstawa"),
    R.EdgeLabel("BC", unknown=True, unknown_text="wysokość"),
    R.EdgeLabel("CA", unknown=True, unknown_text="przekątna"),
])
""",
    ),
]

PHONE_TITLES = {
    "Prostokąt szerokości telefonu",
    "Etykiety słowne przy szerokości telefonu",
}

PAGE = """<!doctype html>
<html lang="pl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Geometria adversarial gallery</title>
<style>
:root {{ --bg:#f8fafc; --card:#ffffff; --ink:#0f172a; --dim:#64748b; --line:#e2e8f0; --code:#f1f5f9; }}
[data-theme="dark"] {{ --bg:#020617; --card:#0f172a; --ink:#e2e8f0; --dim:#94a3b8; --line:#1e293b; --code:#020617; }}
* {{ box-sizing:border-box; }}
body {{ background:var(--bg); color:var(--ink); font:14px/1.55 system-ui,-apple-system,sans-serif;
       margin:0; padding:28px 20px 64px; }}
header {{ max-width:1100px; margin:0 auto 26px; }}
h1 {{ font-size:24px; margin:0 0 6px; letter-spacing:-.02em; }}
header p {{ color:var(--dim); margin:0 0 14px; max-width:66ch; }}
button {{ font:inherit; font-weight:600; padding:7px 14px; border-radius:8px; cursor:pointer;
          border:1px solid var(--line); background:var(--card); color:var(--ink); }}
.grid {{ max-width:1100px; margin:0 auto; display:grid; gap:18px;
         grid-template-columns:repeat(auto-fill,minmax(330px,1fr)); }}
.card {{ background:var(--card); border:1px solid var(--line); border-radius:14px; padding:16px; }}
h2 {{ font-size:15px; margin:0 0 4px; letter-spacing:-.01em; }}
.note {{ color:var(--dim); font-size:12.5px; margin:0 0 12px; }}
.fig {{ border:1px dashed var(--line); border-radius:10px; padding:14px;
        max-width:320px; margin:0 auto 12px; }}
.fig.phone {{ max-width:340px; }}
pre {{ background:var(--code); border:1px solid var(--line); border-radius:9px; margin:0;
       padding:11px 12px; overflow-x:auto; font:11.5px/1.5 ui-monospace,SFMono-Regular,monospace;
       color:var(--dim); }}
</style></head><body>
<header>
  <h1>Geometria adversarial gallery — prototype</h1>
  <p>Ticket #212. Every card here is chosen to be hostile — extreme aspect
     ratios, extreme angles, colliding labels, long Polish words, and phone
     width — rather than representative. The question each card answers is
     "does this break," not "does this look nice."</p>
  <button onclick="document.documentElement.dataset.theme =
     document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark'">Toggle theme</button>
</header>
<div class="grid">{cards}</div>
"""


def build() -> str:
    cards = []
    for title, note, src in CASES:
        env: dict = {"G": G, "R": R}
        exec(src, env)  # noqa: S102 - prototype: the shown code IS the run code
        svg = env["scene"].to_svg()
        assert svg.strip().lower().startswith("<svg") and svg.strip().lower().endswith(
            "</svg>"
        )
        fig_class = "fig phone" if title in PHONE_TITLES else "fig"
        raised = env.get("raised")
        raised_html = (
            f"<p class=note><strong>Raised:</strong> {html.escape(raised)}</p>"
            if raised
            else ""
        )
        cards.append(
            f'<div class="card"><h2>{html.escape(title)}</h2>'
            f"<p class=note>{html.escape(note)}</p>"
            f"{raised_html}"
            f'<div class="{fig_class}">{svg}</div>'
            f"<pre>{html.escape(src.strip())}</pre></div>"
        )
    return PAGE.format(cards="".join(cards))


if __name__ == "__main__":
    out = pathlib.Path(__file__).with_name("adversarial.html")
    out.write_text(build(), encoding="utf-8")
    print(out)
