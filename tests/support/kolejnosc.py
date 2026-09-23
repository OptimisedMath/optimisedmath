"""The twelve Kolejność generators, shared by every sweep that rolls them."""

from backend.problem_generation import FUNCTION_REGISTRY

# Both Chapters name their generators `dec_order_N` / `frac_ord_N`, and nothing else
# in the registry contains "ord" — `test_the_sweep_covers_every_kolejnosc_generator`
# is what keeps that true, for every sweep that imports this.
KOLEJNOSC_GENERATORS = sorted(name for name in FUNCTION_REGISTRY if "ord" in name)
