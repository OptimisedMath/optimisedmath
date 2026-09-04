"""PROTOTYPE — throwaway. Numeric collision audit for #212: for every adversarial
case, report any label whose final placement still overlaps a stroke or another
label (cost > 0), rather than relying on eyeballing a screenshot.
"""

from backend.core.scene_prototype import adversarial as A
from backend.core.scene_prototype import geometry as G  # noqa: F401
from backend.core.scene_prototype import render as R


def _overlap(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


for title, _note, src in A.CASES:
    env = {"G": G, "R": R}
    exec(src, env)
    scene = env["scene"]
    f = scene.figure
    ctx = R.Ctx(fig=f, u=0)
    if f.kind == "circle":
        gw = gh = 2 * f.radius
    else:
        xs = [p[0] for p in f.points.values()]
        ys = [p[1] for p in f.points.values()]
        gw, gh = max(xs) - min(xs), max(ys) - min(ys)
    import math

    diag = max(math.hypot(gw, gh), 1e-6)
    ctx = R.Ctx(fig=f, u=diag / 100.0)
    for ann in scene.annotations:
        ann.render(ctx)

    placed = []
    for lab in ctx.labels:
        best_box, best_cost = None, None
        for sign in (1.0, -1.0):
            d = (lab.direction[0] * sign, lab.direction[1] * sign)
            for step in range(0, 14):
                off = lab.gap * ctx.u + lab.reach() + step * ctx.u * 1.7
                c = (lab.anchor[0] + d[0] * off, lab.anchor[1] + d[1] * off)
                box = (
                    c[0] - lab.half_w,
                    c[1] - lab.half_h,
                    c[0] + lab.half_w,
                    c[1] + lab.half_h,
                )
                cost = sum(1.0 for q in placed if _overlap(box, q))
                cost += sum(0.75 for seg in ctx.obstacles if R._hits(box, seg))
                cost += step * 0.05 + (0.12 if sign < 0 else 0.0)
                if best_cost is None or cost < best_cost:
                    best_box, best_cost = box, cost
                if cost < 0.5:
                    break
            if best_cost is not None and best_cost < 0.5:
                break
        placed.append(best_box)
        if best_cost >= 0.5:
            print(
                f"[{title}] label {lab.text!r} final cost={best_cost:.2f} (COLLISION)"
            )
