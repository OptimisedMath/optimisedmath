"""PROTOTYPE — throwaway. Why did a label land where it landed?"""

from backend.core.scene_prototype import geometry as G
from backend.core.scene_prototype import render as R

fig = G.trapezoid(a=12, b=6, height=4)
scene = R.Scene(
    fig,
    [
        R.Outline(),
        R.VertexLabels(),
        R.EdgeLabel("AB", unit_label="cm"),
        R.EdgeLabel("CD", unit_label="cm"),
        R.ParallelMarks(["AB", "CD"]),
        R.Altitude(apex="D", base="AB", unit_label="cm"),
    ],
)
print("vertices", {k: (round(x, 2), round(y, 2)) for k, (x, y) in fig.points.items()})

scene.to_svg()  # populates nothing we can see; re-run the passes by hand instead

ctx = R.Ctx(fig=fig, u=G.norm((12, 4)) / 100.0)
for a in scene.annotations:
    a.render(ctx)
print("obstacles:", len(ctx.obstacles))
for lab in ctx.labels:
    print(
        f"  {lab.text!r:12} anchor={tuple(round(v,2) for v in lab.anchor)} "
        f"dir={tuple(round(v,2) for v in lab.direction)} half_w={lab.half_w:.2f}"
    )

lab = [x for x in ctx.labels if x.text == "4 cm"][0]
for sign in (1.0, -1.0):
    d = G.mul(lab.direction, sign)
    for step in (0, 1, 2, 3):
        c = G.add(
            lab.anchor, G.mul(d, lab.gap * ctx.u + lab.reach() + step * ctx.u * 1.7)
        )
        box = (
            c[0] - lab.half_w,
            c[1] - lab.half_h,
            c[0] + lab.half_w,
            c[1] + lab.half_h,
        )
        hits = [s for s in ctx.obstacles if R._hits(box, s)]
        print(
            f"sign={sign:+.0f} step={step} box=({box[0]:.2f},{box[1]:.2f})-({box[2]:.2f},{box[3]:.2f}) "
            f"hits={len(hits)} {[tuple(round(v,1) for v in p) for s in hits[:3] for p in s]}"
        )
