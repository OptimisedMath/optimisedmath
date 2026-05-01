# tests/test_core_logic.py
import pytest
from core.utils import clean_mobile_input, clean_latex, check_text_answer, fmt_dec
# import engine # Uncomment when ready to test engine.evaluate_answer

class TestMobileSanitizer:
    """Tests the middleware that cleans messy mobile keyboard inputs."""
    
    @pytest.mark.parametrize("user_input, expected", [
        ("1,5", "1,5"),          # Standard Polish decimal
        ("1.5", "1,5"),          # English dot to Polish comma conversion
        ("0.52", "0,52"),        # Leading zero handling
        ("1-1/2", "1 1/2"),      # Lazy mobile fraction (dash)
        ("1.1/2", "1 1/2"),      # Lazy mobile fraction (dot)
        ("  3/4  ", "3/4"),      # Trailing/leading whitespace
        ("1   1/2", "1 1/2"),    # Aggressive mobile autocorrect spaces
        ("", ""),                # Empty string safety
        (None, ""),              # Null safety
    ])
    def test_clean_mobile_input(self, user_input, expected):
        assert clean_mobile_input(user_input) == expected


class TestLatexCleaner:
    """Tests the engine's LaTeX formatting string builder."""
    
    @pytest.mark.parametrize("latex_in, expected", [
        ("$\\displaystyle 1\\frac{1}{2}$", "1 1/2"),           # Mathjax + space injection + fraction conversion
        ("\\frac{3}{4}", "3/4"),                               # Basic fraction conversion
        ("$\\displaystyle \\frac{10}{20}$", "10/20"),          # Combined stripping and conversion
        ("2\\frac{1}{3}", "2 1/3"),                             # Injects space between whole and frac
    ])
    def test_clean_latex(self, latex_in, expected):
        assert clean_latex(latex_in) == expected


class TestEvaluationLogic:
    """Tests the strict comparison engine for equality."""
    
    @pytest.mark.parametrize("correct_latex, user_text, is_match", [
        ("3/4", "3/4", True),                 # Perfect match
        ("3/4", "3 / 4", True),               # Tolerates spaces around slashes
        ("1 \\frac{1}{2}", "1 1/2", True),    # Matches processed LaTeX to user input
        ("0,5", "0,5", True),                 # Decimal match
        ("0,52", "0,52", True),               # Two decimal match
        ("3/4", "1/2", False),                # Mathematical failure
        ("1 \\frac{1}{2}", "11/2", False),    # Space deletion failure (ensures space preservation)
    ])
    def test_check_text_answer(self, correct_latex, user_text, is_match):
        assert check_text_answer(correct_latex, user_text) is is_match


class TestFormatters:
    """Tests data formatting outputs."""
    
    @pytest.mark.parametrize("val, expected", [
        (1.5, "1,5"),
        (2.0, "2"),          # Strips trailing zeros and decimal
        (0.5200, "0,52"),    # Strips trailing zeros but keeps actual value
        (0.0, "0"),          # Zero bounds
    ])
    def test_fmt_dec(self, val, expected):
        assert fmt_dec(val) == expected

# --- MOCKING THE ENGINE (Example for future implementation) ---
# class TestEngineEvaluator:
#     def test_evaluate_answer_correct(self):
#         mock_problem = {"correct": "0,5"}
#         result = engine.evaluate_answer("0,5", mock_problem, is_text_mode=True)
#         assert result["is_correct"] is True