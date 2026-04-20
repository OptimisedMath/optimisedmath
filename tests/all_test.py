import sys
import importlib
import pytest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

def get_all_math_functions():
    functions_to_test = []
    macro_path = BASE_DIR / "macro_topics"
    
    for file_path in macro_path.rglob("*.py"):
        if file_path.name.startswith("__"): continue
        
        module_path = ".".join(file_path.relative_to(BASE_DIR).parts)[:-3]
        module = importlib.import_module(module_path)
        
        for name, func in module.__dict__.items():
            # FIX 1: Only test actual math functions, ignore imported helpers!
            if callable(func) and (name.startswith("dec_") or name.startswith("frac_")):
                functions_to_test.append((name, func))
                
    return functions_to_test

@pytest.mark.parametrize("func_name, math_func", get_all_math_functions())
def test_universal_math_structure(func_name, math_func):
    successful_runs = 0
    attempts = 0
    
    # FIX 2: Try up to 100 times to get 10 perfect math problems
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
        
        successful_runs += 1
        
    assert successful_runs == 10, f"'{func_name}' generated too many duplicates and couldn't make 10 valid problems."