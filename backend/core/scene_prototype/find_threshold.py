"""PROTOTYPE — throwaway. Binary-search-ish scan for the AngleArc collision floor."""

import math

from backend.core.scene_prototype import geometry as G
from backend.core.scene_prototype import render as R


def _overlap(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def collides(angle: float) -> float:
    fig = G.Triangle.angles(angle_a=angle, angle_b=90, scale=10)
    scene = R.Scene(fig, [R.Outline(), R.VertexLabels(), R.AngleArc("A")])
    f = scene.figure
    xs = [p[0] for p in f.points.values()]
    ys = [p[1] for p in f.points.values()]
    diag = max(math.hypot(max(xs) - min(xs), max(ys) - min(ys)), 1e-6)
    ctx = R.Ctx(fig=f, u=diag / 100.0)
    for ann in scene.annotations:
        ann.render(ctx)
    placed = []
    worst = 0.0
    for lab in ctx.labels:
        best_cost = None
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
        worst = max(worst, best_cost)
    return worst


for angle in [0.5, 1, 2, 3, 4, 5, 6, 8, 10, 11, 12, 13, 15, 20]:
    print(f"angle={angle:>6} worst_cost={collides(angle):.2f}")

print("--- wide side (angle_b small, angle_a near 180) ---")


def collides_wide(angle_a: float) -> float:
    fig = G.Triangle.angles(angle_a=angle_a, angle_b=180 - angle_a - 0.5, scale=10)
    scene = R.Scene(fig, [R.Outline(), R.VertexLabels(), R.AngleArc("A")])
    f = scene.figure
    xs = [p[0] for p in f.points.values()]
    ys = [p[1] for p in f.points.values()]
    diag = max(math.hypot(max(xs) - min(xs), max(ys) - min(ys)), 1e-6)
    ctx = R.Ctx(fig=f, u=diag / 100.0)
    for ann in scene.annotations:
        ann.render(ctx)
    placed = []
    worst = 0.0
    for lab in ctx.labels:
        best_cost = None
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
        worst = max(worst, best_cost)
    return worst


for angle_a in [170, 175, 177, 178, 179, 179.4]:
    print(f"angle_a={angle_a:>6} worst_cost={collides_wide(angle_a):.2f}")
