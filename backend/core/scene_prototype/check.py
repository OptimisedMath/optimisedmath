"""PROTOTYPE — throwaway. Does the picture actually agree with the numbers?

The to-scale invariant is the point of the whole schema, so it gets checked
numerically rather than by eye.
"""

from backend.core.scene_prototype import geometry as G


def show(name, fig, wanted):
    got = {v: round(fig.interior_angle(v), 2) for v in fig.outline}
    sides = {e: round(fig.edge_length(e), 3) for e in ("AB", "BC", "CA")}
    print(f"{name}\n  angles {got}\n  sides  {sides}\n  wanted {wanted}\n")


show(
    "Triangle.angles(25, 110)",
    G.Triangle.angles(25, 110, 10),
    "one 25, one 110, one 45",
)
show("Triangle.sas(b=9, A=55, c=10)", G.Triangle.sas(9, 55, 10), "angle at A = 55")
show("Triangle.sss(3,4,5)", G.Triangle.sss(3, 4, 5), "a right angle, sides 3/4/5")
show("Triangle.base_height(8, 5, .3)", G.Triangle.base_height(8, 5, 0.3), "AB = 8")

p = G.parallelogram(10, 7, 38)
print(
    "parallelogram(10,7,38): derived height",
    round(p.quantities["height"], 3),
    "vs side 7",
)
t = G.trapezoid(12, 6, 4)
print(
    "trapezoid(12,6,4): AB",
    round(t.edge_length("AB"), 3),
    "CD",
    round(t.edge_length("CD"), 3),
)
print(
    "area of hexagon(6, side 5):",
    round(G.regular_polygon(6, 5).area(), 3),
    "expect 64.952",
)
L = G.rectilinear([(6, 0), (0, 3), (-2.5, 0), (0, 4), (-3.5, 0), (0, -7)])
print("L-shape reflex corners:", [v for v in L.outline if not L.is_convex_at(v)])
print("L-shape angles:", [round(L.interior_angle(v)) for v in L.outline])
