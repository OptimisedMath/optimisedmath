import pytest

from backend.problem_generation import FUNCTION_REGISTRY


def get_all_math_functions():
    return list(FUNCTION_REGISTRY.items())


@pytest.mark.parametrize("func_name, math_func", get_all_math_functions())
def test_universal_math_structure(func_name, math_func):
    successful_runs = 0
    attempts = 0

    # Try up to 100 times to get 10 perfect math problems
    while successful_runs < 10 and attempts < 100:
        attempts += 1
        try:
            problem = math_func()
        except Exception as e:
            pytest.fail(f"CRASH in function '{func_name}': {str(e)}")

        # If the math function destroyed a bad question, skip and try again!
        if problem is None:
            continue

        assert isinstance(problem, dict), f"'{func_name}' did not return a dictionary!"
        assert "question" in problem, f"'{func_name}' is missing a question!"
        assert "correct" in problem, f"'{func_name}' is missing a correct answer!"
        assert len(problem["options"]) == len(
            set(problem["options"])
        ), f"'{func_name}' generated duplicate answer options."

        successful_runs += 1

    assert (
        successful_runs == 10
    ), f"'{func_name}' generated too many duplicates and couldn't make 10 valid problems."
