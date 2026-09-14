"""PROTOTYPE — throwaway (#280). Not production; lives on a prototype branch, never main.

Question: with the number line on the scene's label placement and bbox viewBox, which
font cap keeps labels on one row at the largest size — capped against every tick gap,
or only against the gap between labelled ticks?

Shortcut: builds on the scene `Ctx` around an empty `Figure`, where the real module
builds on the extracted `Canvas`. Labels are the generators' own strings, captured by
spying on `generate_universal_number_line`, since derivation is not what this checks.

Run: python -m backend.core.scene.numberline_prototype OUT.html
"""

import html
import random
import re
import sys
import uuid

from backend.chapters.ulamki_dziesietne import topic_30_os_liczbowa as t30
from backend.chapters.ulamki_zwykle import topic_50_os_liczbowa as t50
from backend.core.scene.geometry import Figure
from backend.core.scene.render import ACCENT, INK, MUTED, Ctx
from backend.core.utils import generate_universal_number_line as old_render

CARD_PX = 368  # ProblemDisplay: max-w-sm (384 px) minus p-2
L = 100.0
BASE_FONT = 6.0  # the scene's default: 6 pen units
SEEDS = 400
RULES = {"B": "tick", "C": "pair"}


def cap_font(ticks, labeled, rule):
    """Largest font at which the longest label fits the chosen gap, never above the scene default."""
    longest = max(len(t) for t in labeled.values())
    sp = L / ticks
    if rule == "tick":
        gap = sp
    else:
        idx = sorted(labeled)
        gap = min((b - a for a, b in zip(idx, idx[1:])), default=ticks) * sp
    return min(BASE_FONT, 0.9 * gap / (0.6 * longest))


def render_new(ticks, labeled, target, rule):
    """Draw one number line on the scene context; return (svg, label px at card width, staggered)."""
    ctx = Ctx(fig=Figure(kind="polygon"), u=L / 100)
    font = cap_font(ticks, labeled, rule)
    sp = L / ticks

    ctx.line((-4, 0), (L + 4, 0))
    ctx.parts.append(
        f'<polygon points="{L + 7:.3f},0 {L + 3.5:.3f},-1.8 {L + 3.5:.3f},1.8" fill="{INK}"/>'
    )
    ctx.include((L + 7, 0))

    for i in range(ticks + 1):
        x = i * sp
        lab = i in labeled
        h = 2.4 if lab else 1.5
        ctx.line(
            (x, h),
            (x, -h),
            color=INK if lab else MUTED,
            width=ctx.stroke if lab else ctx.thin,
        )
        if lab:
            ctx.text((x, -h), (0, -1), labeled[i], scale=font / ctx.font, gap=1.2)

    fid = f"glow-{uuid.uuid4().hex[:8]}"
    # An feMergeNode with no `in` takes the previous primitive's output: the blur.
    ctx.defs.append(
        f'<filter id="{fid}" x="-100%" y="-50%" width="300%" height="200%">'
        f'<feGaussianBlur stdDeviation="0.45"/>'
        f'<feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
    )
    tx = target * sp
    ctx.parts.append(
        f'<line x1="{tx:.3f}" y1="-10.5" x2="{tx:.3f}" y2="-4.6" stroke="{ACCENT}" '
        f'stroke-width="1.3" stroke-linecap="round" filter="url(#{fid})"/>'
        f'<polygon points="{tx - 1.7:.3f},-5 {tx + 1.7:.3f},-5 {tx:.3f},-2.6" fill="{ACCENT}" filter="url(#{fid})"/>'
    )
    ctx.include((tx - 1.7, 11), (tx + 1.7, 2.6))

    ctx.place_labels()

    ys = {
        round(float(m), 2)
        for m in re.findall(r'<text x="[^"]+" y="([^"]+)"', "".join(ctx.parts))
    }
    xs = [p[0] for p in ctx.extent]
    yy = [p[1] for p in ctx.extent]
    pad = 2.0
    x0, x1, y0, y1 = min(xs) - pad, max(xs) + pad, min(yy) - pad, max(yy) + pad
    w, h = x1 - x0, y1 - y0
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0:.3f} {-y1:.3f} {w:.3f} {h:.3f}" '
        f'width="100%" style="max-width:100%;height:auto;overflow:visible" role="img">'
        f'<defs>{"".join(ctx.defs)}</defs>{"".join(ctx.parts)}</svg>'
    )
    return svg, font * CARD_PX / w, len(ys) > 1


GENERATORS = [("Ułamki zwykłe", t50, f"frac_number_line_{n}") for n in range(1, 5)] + [
    ("Ułamki dziesiętne", t30, f"dec_number_line_{n}") for n in range(1, 7)
]


def capture(mod, name):
    """Every distinct (ticks, labels, target) the generator draws over SEEDS seeds."""
    seen, draws = set(), []
    original = mod.generate_universal_number_line

    def spy(ticks, labeled, target):
        draws.append((ticks, dict(labeled), target))
        return ""

    mod.generate_universal_number_line = spy
    try:
        fn = getattr(mod, name)
        out = []
        for seed in range(SEEDS):
            random.seed(seed)
            draws.clear()
            if fn() and draws:
                d = draws[-1]
                key = (d[0], tuple(sorted(d[1].items())), d[2])
                if key not in seen:
                    seen.add(key)
                    out.append(d)
        return fn.__doc__, out
    finally:
        mod.generate_universal_number_line = original


def main(path):
    """Write the gallery HTML to `path`."""
    rows, summary = [], {v: {"min_px": 99.0, "staggered": 0, "draws": 0} for v in RULES}
    for chapter, mod, name in GENERATORS:
        doc, draws = capture(mod, name)
        for d in draws:
            for v, rule in RULES.items():
                _, px, stag = render_new(*d, rule)
                s = summary[v]
                s["min_px"] = min(s["min_px"], px)
                s["staggered"] += stag
                s["draws"] += 1
        crowded_pair = min(draws, key=lambda d: cap_font(d[0], d[1], "pair"))
        crowded_tick = min(draws, key=lambda d: cap_font(d[0], d[1], "tick"))
        picks = (
            [crowded_pair]
            if crowded_pair == crowded_tick
            else [crowded_pair, crowded_tick]
        )
        for k, d in enumerate(picks):
            ticks, labeled, target = d
            variants = {
                "A": (old_render(ticks, labeled, target), 100 * CARD_PX / 4000, False)
            }
            for v, rule in RULES.items():
                variants[v] = render_new(ticks, labeled, target, rule)
            rows.append((chapter, name, doc, k, len(picks), d, variants))
    open(path, "w").write(page(rows, summary))
    for v, s in summary.items():
        print(v, s)


def page(rows, summary):
    """The gallery document."""
    row_html = []
    for chapter, name, doc, k, n_picks, (ticks, labeled, target), variants in rows:
        labels = " · ".join(
            f"tick {i}: <b>{html.escape(t)}</b>" for i, t in sorted(labeled.items())
        )
        cells = []
        for v, (svg, px, stag) in variants.items():
            flag = (
                '<span class="chip bad">labels stagger</span>'
                if stag
                else '<span class="chip ok">one row</span>'
            )
            cells.append(
                f'<div class="variant" data-v="{v}">'
                f'<div class="cards"><div class="app light"><div class="card">{svg}</div></div>'
                f'<div class="app dark"><div class="card">{svg}</div></div></div>'
                f'<p class="stats"><span class="px">{px:.1f} px</span> labels {flag}</p></div>'
            )
        if n_picks == 1:
            tag = "most crowded draw under both rules"
        else:
            tag = (
                "most crowded draw, labelled-pair rule"
                if k == 0
                else "most crowded draw, tick-gap rule"
            )
        row_html.append(
            f'<section class="row"><header class="meta"><p class="eyebrow">{chapter} · <code>{name}</code></p>'
            f"<h2>{html.escape(doc or '')}</h2>"
            f'<p class="draw">{ticks} gaps · target at tick {target} · {labels}</p>'
            f'<p class="why">{tag}</p></header><div>{"".join(cells)}</div></section>'
        )
    s = summary
    return TEMPLATE.replace("{{ROWS}}", "".join(row_html)).replace(
        "{{SUMMARY}}",
        "".join(
            f'<div class="sum"><span class="k">{label}</span>'
            f'<span class="n">{s[v]["min_px"]:.1f} px</span><span class="d">smallest label over {s[v]["draws"] // 1} distinct draws</span>'
            f'<span class="n">{s[v]["staggered"]}</span><span class="d">draws with staggered labels</span></div>'
            for v, label in (("B", "B · tick-gap cap"), ("C", "C · labelled-pair cap"))
        ),
    )


TEMPLATE = """<title>Number Line Prototype</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>
:root{--ground:#eef1f5;--panel:#f8fafc;--ink:#172033;--muted:#5b6678;--line:#d3dae3;--accent:#0369a1;--ok:#15803d;--bad:#be123c;--bar:#172033;--bar-ink:#f1f5f9}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--ground:#0a0f19;--panel:#111826;--ink:#e3e8ef;--muted:#8b95a6;--line:#253146;--accent:#7dd3fc;--ok:#4ade80;--bad:#fb7185;--bar:#e3e8ef;--bar-ink:#0a0f19}}
:root[data-theme="dark"]{--ground:#0a0f19;--panel:#111826;--ink:#e3e8ef;--muted:#8b95a6;--line:#253146;--accent:#7dd3fc;--ok:#4ade80;--bad:#fb7185;--bar:#e3e8ef;--bar-ink:#0a0f19}
body{background:var(--ground);color:var(--ink);font:15px/1.55 "IBM Plex Sans",system-ui,sans-serif;padding-block:32px 120px;padding-inline:20px}
.wrap{max-width:1180px;margin:0 auto;display:grid;gap:28px}
code,.px,.n,.draw{font-family:"IBM Plex Mono",ui-monospace,monospace}
.top{display:grid;gap:10px;max-width:70ch}
.top h1{font-size:28px;line-height:1.2;margin:0;font-weight:600;text-wrap:balance}
.ruler{height:12px;max-width:420px;background:repeating-linear-gradient(90deg,var(--muted) 0 1px,transparent 1px 21px) bottom/100% 7px no-repeat,repeating-linear-gradient(90deg,var(--ink) 0 2px,transparent 2px 105px) bottom/100% 12px no-repeat;opacity:.55}
.top p{margin:0;color:var(--muted)}
.top b{color:var(--ink);font-weight:600}
.legend{display:flex;flex-wrap:wrap;gap:8px 18px;font-size:13px;color:var(--muted)}
.legend span b{font-family:"IBM Plex Mono",monospace;color:var(--accent)}
.summary{display:flex;flex-wrap:wrap;gap:16px}
.sum{display:grid;grid-template-columns:auto 1fr;gap:2px 12px;align-items:baseline;background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px 18px;min-width:0;flex:1 1 300px}
.sum .k{grid-column:1/-1;font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin-bottom:4px}
.sum .n{font-size:20px;font-weight:600;font-variant-numeric:tabular-nums;text-align:right}
.sum .d{color:var(--muted);font-size:13px}
.row{display:grid;grid-template-columns:minmax(0,260px) minmax(0,1fr);gap:24px;padding-top:24px;border-top:1px solid var(--line)}
.meta{display:grid;gap:4px;align-content:start}
.eyebrow{margin:0;font-size:12px;letter-spacing:.05em;text-transform:uppercase;color:var(--muted)}
.eyebrow code{text-transform:none;letter-spacing:0;color:var(--ink)}
.meta h2{margin:0;font-size:17px;font-weight:600;text-wrap:balance}
.draw{margin:0;font-size:12.5px;color:var(--muted)}
.draw b{color:var(--ink)}
.why{margin:0;font-size:12px;color:var(--accent)}
.cards{display:flex;flex-wrap:wrap;gap:12px}
.app{flex:1 1 300px;max-width:420px;border-radius:14px;padding:18px;display:flex;justify-content:center;box-sizing:border-box}
.app.light{background:linear-gradient(135deg,#f8fafc,#f0f9ff);color:#334155}
.app.dark{background:linear-gradient(135deg,#020617,#0f172a);color:#cbd5e1}
.card{width:100%;max-width:384px;overflow:hidden;border-radius:12px;padding:8px;box-sizing:border-box}
.light .card{background:#fff;border:1px solid #e2e8f0}
.dark .card{background:rgba(2,6,23,.6);border:1px solid #334155}
.stats{margin:8px 0 0;font-size:13px;color:var(--muted);display:flex;gap:10px;align-items:center}
.px{font-weight:600;color:var(--ink);font-variant-numeric:tabular-nums}
.chip{font-size:11.5px;padding:1px 8px;border-radius:99px;border:1px solid currentColor}
.chip.ok{color:var(--ok)}.chip.bad{color:var(--bad)}
.switch{position:fixed;left:50%;bottom:18px;transform:translateX(-50%);display:flex;align-items:center;gap:4px;background:var(--bar);color:var(--bar-ink);border-radius:99px;padding:6px;box-shadow:0 8px 28px rgba(0,0,0,.28);max-width:calc(100% - 32px)}
.switch button{all:unset;cursor:pointer;width:34px;height:34px;display:grid;place-items:center;border-radius:99px;font-size:18px}
.switch button:hover{background:rgba(127,127,127,.25)}
.switch button:focus-visible{outline:2px solid var(--accent);outline-offset:1px}
.switch .label{padding:0 12px;font-size:14px;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
@media (max-width:720px){.row{grid-template-columns:1fr}}
</style>
<div class="wrap">
<header class="top">
<h1>Number line: which font cap keeps labels on one row?</h1>
<div class="ruler" aria-hidden="true"></div>
<p>Prototype for <b>#280</b>. Every number-line Level in <b>Ułamki zwykłe</b> (Topic 50) and <b>Ułamki dziesiętne</b> (Topic 30), drawn from each generator's real arguments. For each Level: its most crowded draw, shown in a light and a dark copy of the arena's image card at 384&nbsp;px. Pixel sizes are at that width.</p>
<div class="legend"><span><b>A</b> today's renderer</span><span><b>B</b> scene layout, font capped against every tick gap</span><span><b>C</b> scene layout, font capped against the nearest labelled pair</span><span>← → keys switch</span></div>
</header>
<div class="summary">{{SUMMARY}}</div>
{{ROWS}}
</div>
<nav class="switch" aria-label="Variant"><button id="prev" aria-label="Previous variant">←</button><span class="label" id="vlabel" aria-live="polite"></span><button id="next" aria-label="Next variant">→</button></nav>
<script>
const V=[["A","Today's renderer"],["B","Tick-gap cap"],["C","Labelled-pair cap"]];
let i=0;try{const q=new URLSearchParams(location.search).get("variant");const f=V.findIndex(v=>v[0]===q);if(f>=0)i=f}catch(e){}
function show(){const k=V[i][0];document.querySelectorAll(".variant").forEach(el=>{el.hidden=el.dataset.v!==k});
document.getElementById("vlabel").textContent=k+" — "+V[i][1];
try{const u=new URL(location.href);u.searchParams.set("variant",k);history.replaceState(null,"",u)}catch(e){}}
function step(d){i=(i+d+V.length)%V.length;show()}
document.getElementById("prev").onclick=()=>step(-1);document.getElementById("next").onclick=()=>step(1);
addEventListener("keydown",e=>{if(e.target.closest&&e.target.closest("input,textarea,[contenteditable]"))return;if(e.key==="ArrowLeft")step(-1);if(e.key==="ArrowRight")step(1)});
show();
</script>
"""

if __name__ == "__main__":
    main(sys.argv[1])
