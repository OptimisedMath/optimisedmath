"""PROTOTYPE — throwaway. Builds the gallery page for wayfinder ticket #211.

Run:  python -m backend.core.scene_prototype.gallery
Then open the path it prints.

Each card renders a figure AND shows the exact generator-side code that produced
it — the schema is judged by reading that code as much as by looking at the SVG.
The code shown is the code executed; there is no second copy to drift.
"""

from __future__ import annotations

import html
import pathlib

from backend.core.scene_prototype import geometry as G
from backend.core.scene_prototype import render as R

# (Topic, title, what this card is proving, generator-side source)
CASES: list[tuple[str, str, str, str]] = [
    (
        "130",
        "Pole trójkąta — wysokość wewnątrz",
        "The recommended vertical slice. Base and height are the constructor's own "
        "arguments, so the label and the drawing cannot disagree.",
        """
fig = G.Triangle.base_height(base=8, height=5, apex_frac=0.3)
scene = R.Scene(fig, [
    R.Outline(),
    R.VertexLabels(),
    R.EdgeLabel("AB", unit_label="cm"),
    R.Altitude(apex="C", base="AB", unit_label="cm"),
])
""",
    ),
    (
        "130",
        "Pole trójkąta — wysokość poza trójkątem",
        "The rozwartokątny case. apex_frac > 1 puts the foot off the base; the "
        "renderer detects that and adds the dotted base extension unasked.",
        """
fig = G.Triangle.base_height(base=8, height=4, apex_frac=1.45)
scene = R.Scene(fig, [
    R.Outline(),
    R.VertexLabels(),
    R.EdgeLabel("AB", unit_label="cm"),
    R.Altitude(apex="C", base="AB", unit_label="cm"),
])
""",
    ),
    (
        "130",
        "Pole trójkąta — dwie wysokości",
        "The hostile case behind `confuses_base_with_height`: two bases, two "
        "heights, both correct, in one figure.",
        """
fig = G.Triangle.sss(a=7, b=6, c=9)
scene = R.Scene(fig, [
    R.Outline(),
    R.VertexLabels(),
    R.EdgeLabel("AB", unit_label="cm"),
    R.EdgeLabel("BC", unit_label="cm"),
    R.Altitude(apex="C", base="AB", unit_label="cm"),
    R.Altitude(apex="A", base="BC", unit_label="cm"),
])
""",
    ),
    (
        "150",
        "Pole trapezu",
        "The tightest label budget on the list: four labels, parallel marks and a "
        "dashed height in a wide, short shape.",
        """
fig = G.trapezoid(a=12, b=6, height=4)
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
        "140",
        "Pole równoległoboku",
        "The height is DERIVED from side·sinθ, so it is visibly shorter than the "
        "slant side — the misconception survives only if that is obvious.",
        """
fig = G.parallelogram(base=10, side=7, angle=38)
scene = R.Scene(fig, [
    R.Outline(),
    R.VertexLabels(),
    R.EdgeLabel("AB", unit_label="cm"),
    R.EdgeLabel("BC", unit_label="cm"),
    R.Altitude(apex="D", base="AB", unit_label="cm"),
])
""",
    ),
    (
        "110",
        "Pole prostokąta — linie wymiarowe",
        "The practical-measurement look: extension lines and arrowheads offset "
        "clear of the figure, rather than labels sitting on the edges.",
        """
fig = G.rectangle(width=9, height=5)
scene = R.Scene(fig, [
    R.Outline(),
    R.RightAngle("A"),
    R.DimensionLine("AB", unit_label="cm"),
    R.DimensionLine("BC", unit_label="cm"),
])
""",
    ),
    (
        "50",
        "Rodzaje trójkątów — równoramienny",
        "Equal-side ticks and equal-angle arcs together. The arcs are sized from "
        "the shorter adjacent edge, so neither swallows its vertex label.",
        """
fig = G.Triangle.sss(a=6, b=6, c=8)
scene = R.Scene(fig, [
    R.Outline(),
    R.VertexLabels(),
    R.Ticks("CA", count=1),
    R.Ticks("BC", count=1),
    R.AngleArc("A"),
    R.AngleArc("B"),
])
""",
    ),
    (
        "70",
        "Suma kątów w trójkącie",
        "Three arcs, one unknown, and a deliberately narrow 25° vertex — the arc "
        "shrinks so it stays inside the corner.",
        """
fig = G.Triangle.angles(angle_a=25, angle_b=110, scale=10)
scene = R.Scene(fig, [
    R.Outline(),
    R.VertexLabels(),
    R.AngleArc("A"),
    R.AngleArc("B"),
    R.AngleArc("C", unknown=True),
])
""",
    ),
    (
        "30/40",
        "Kąty przyległe — łuki zagnieżdżone",
        "Two arcs at one vertex. The scene allocates the radii; the generator "
        "never mentions a radius at all.",
        """
fig = G.Triangle.sas(b=9, angle_a=55, c=10)
scene = R.Scene(fig, [
    R.Outline(),
    R.VertexLabels(),
    R.AngleArc("A"),
    R.AngleArc("A", show_label=False),
])
""",
    ),
    (
        "100",
        "Obwód wielokąta — figura niewypukła",
        "The concave-corner test. Labels sit outside the outline on every edge, "
        "including the two the centroid rule would push inside.",
        """
fig = G.rectilinear([(6, 0), (0, 3), (-2.5, 0), (0, 4), (-3.5, 0), (0, -7)])
scene = R.Scene(fig, [
    R.Outline(),
    *[R.EdgeLabel(e, unit_label="cm")
      for e in ["AB", "BC", "CD", "DE", "EF", "FA"]],
])
""",
    ),
    (
        "160",
        "Pola figur złożonych",
        "Hatched region plus a dashed decomposition line splitting the L into two "
        "rectangles.",
        """
fig = G.rectilinear([(7, 0), (0, 3), (-3, 0), (0, 4), (-4, 0), (0, -7)])
scene = R.Scene(fig, [
    R.Outline(),
    R.Hatch(),
    R.Segment("C", "F", dash=True),
    R.VertexLabels(),
    R.EdgeLabel("AB", unit_label="cm"),
    R.EdgeLabel("FA", unit_label="cm"),
])
""",
    ),
    (
        "80",
        "Czworokąty — przekątne rombu",
        "Diagonals as dashed interior segments with their perpendicular "
        "intersection marked, for the d₁·d₂/2 formula.",
        """
fig = G.rhombus_diagonals(d1=10, d2=6)
scene = R.Scene(fig, [
    R.Outline(),
    R.VertexLabels(),
    R.Segment("A", "C", label="10 cm"),
    R.Segment("B", "D", label="6 cm"),
    R.Ticks("AB"), R.Ticks("BC"), R.Ticks("CD"), R.Ticks("DA"),
])
""",
    ),
    (
        "90",
        "Kąty w wielokącie foremnym",
        "Regular hexagon with construction diagonals partitioning it, plus one "
        "interior angle arc.",
        """
fig = G.regular_polygon(n=6, side=5)
scene = R.Scene(fig, [
    R.Outline(),
    R.VertexLabels(),
    R.Segment("A", "C"), R.Segment("A", "D"), R.Segment("A", "E"),
    R.AngleArc("B"),
])
""",
    ),
    (
        "170",
        "Koło i okrąg",
        "One fill toggle carries the whole okrąg/koło distinction. Radius and "
        "diameter are the same primitive at two angles.",
        """
fig = G.circle(radius=5)
scene = R.Scene(fig, [
    R.Outline(fill=True),
    R.Centre("O"),
    R.Radius(at=52, unit_label="cm"),
    R.Radius(at=-15, unit_label="cm", diameter=True),
])
""",
    ),
    (
        "190",
        "Pole koła — wycinek",
        "Where the arc primitive and the region-fill primitive have to co-operate.",
        """
fig = G.circle(radius=5)
scene = R.Scene(fig, [
    R.Outline(),
    R.Sector(start=15, end=95),
    R.Centre("O"),
    R.Radius(at=15, unit_label="cm"),
])
""",
    ),
    (
        "120",
        "Jednostki pola",
        "Grid at a density that has to stay legible — 100 unit squares inside "
        "1 dm².",
        """
fig = G.square(side=10)
scene = R.Scene(fig, [
    R.Grid(spacing=1),
    R.Outline(),
    R.EdgeLabel("AB", unknown=True, unknown_text="10 cm"),
    R.Caption("1 dm² = 100 cm²"),
])
""",
    ),
    (
        "200",
        "Twierdzenie Pitagorasa",
        "The right-angle marker is mandatory here — and the renderer refuses to "
        "draw one on a vertex that is not 90°.",
        """
fig = G.Triangle.sss(a=4, b=3, c=5)
scene = R.Scene(fig, [
    R.Outline(),
    R.VertexLabels(),
    R.RightAngle("C"),
    R.EdgeLabel("CA", unit_label="cm"),
    R.EdgeLabel("BC", unit_label="cm"),
    R.EdgeLabel("AB", unknown=True),
])
""",
    ),
    (
        "220",
        "Skala",
        "Weakest drawing demand on the list: a plan plus a caption.",
        """
fig = G.rectangle(width=8, height=5)
scene = R.Scene(fig, [
    R.Grid(spacing=1),
    R.Outline(),
    R.EdgeLabel("AB", unit_label="cm"),
    R.EdgeLabel("BC", unit_label="cm"),
    R.Caption("skala 1 : 200"),
])
""",
    ),
]


PAGE = """<title>Geometria scene schema</title>
<style>
:root {{ --bg:#f8fafc; --card:#ffffff; --ink:#0f172a; --dim:#64748b; --line:#e2e8f0; --code:#f1f5f9; }}
[data-theme="dark"] {{ --bg:#020617; --card:#0f172a; --ink:#e2e8f0; --dim:#94a3b8; --line:#1e293b; --code:#020617; }}
* {{ box-sizing:border-box; }}
body {{ background:var(--bg); color:var(--ink); font:14px/1.55 system-ui,-apple-system,sans-serif;
       margin:0; padding:28px 20px 64px; }}
header {{ max-width:1100px; margin:0 auto 26px; }}
h1 {{ font-size:24px; margin:0 0 6px; letter-spacing:-.02em; }}
header p {{ color:var(--dim); margin:0 0 14px; max-width:62ch; }}
button {{ font:inherit; font-weight:600; padding:7px 14px; border-radius:8px; cursor:pointer;
          border:1px solid var(--line); background:var(--card); color:var(--ink); }}
.grid {{ max-width:1100px; margin:0 auto; display:grid; gap:18px;
         grid-template-columns:repeat(auto-fill,minmax(330px,1fr)); }}
.card {{ background:var(--card); border:1px solid var(--line); border-radius:14px; padding:16px; }}
.topic {{ font:600 11px/1 ui-monospace,monospace; color:var(--dim); letter-spacing:.09em; }}
h2 {{ font-size:15px; margin:7px 0 4px; letter-spacing:-.01em; }}
.note {{ color:var(--dim); font-size:12.5px; margin:0 0 12px; }}
.fig {{ border:1px dashed var(--line); border-radius:10px; padding:14px;
        max-width:320px; margin:0 auto 12px; }}
pre {{ background:var(--code); border:1px solid var(--line); border-radius:9px; margin:0;
       padding:11px 12px; overflow-x:auto; font:11.5px/1.5 ui-monospace,SFMono-Regular,monospace;
       color:var(--dim); }}
</style>
<header>
  <h1>Geometria scene schema — prototype gallery</h1>
  <p>Ticket #211. Every figure below is produced by the code shown under it: the
     generator states maths, the constructor derives the geometry, and the label
     text is read back off the constructed figure. The figure strokes are
     <code>currentColor</code>, so dark mode costs nothing.</p>
  <button onclick="document.documentElement.dataset.theme =
     document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark'">Toggle theme</button>
</header>
<div class="grid">{cards}</div>
"""


def build() -> str:
    cards = []
    for topic, title, note, src in CASES:
        env: dict = {"G": G, "R": R}
        exec(src, env)  # noqa: S102 - prototype: the shown code IS the run code
        svg = env["scene"].to_svg()
        assert svg.strip().lower().startswith("<svg") and svg.strip().lower().endswith(
            "</svg>"
        )
        cards.append(
            f'<div class="card"><div class="topic">TOPIC {topic}</div>'
            f"<h2>{html.escape(title)}</h2><p class=note>{html.escape(note)}</p>"
            f'<div class="fig">{svg}</div>'
            f"<pre>{html.escape(src.strip())}</pre></div>"
        )
    return PAGE.format(cards="".join(cards))


if __name__ == "__main__":
    out = pathlib.Path(__file__).with_name("gallery.html")
    out.write_text(build(), encoding="utf-8")
    print(out)
