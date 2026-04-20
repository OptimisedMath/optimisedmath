import sys
from pathlib import Path

# Tell Python where to find your app's code
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Import the specific math function you want to test
from macro_topics.ulamki_dziesietne.micro_11_kolejnosc import dec_order_1

def test_dec_order_1_structure():
    """Test that Level 1 generates valid problems without crashing."""
    
    # Run the function 100 times to catch rare random number bugs
    for _ in range(100):
        problem = dec_order_1()
        
        # 1. Does it return a dictionary?
        assert isinstance(problem, dict), "Function did not return a dictionary!"
        
        # 2. Did the utils file inject the UUID correctly?
        assert "problem_id" in problem, "Missing problem_id!"
        
        # 3. Does it have a question and a correct answer?
        assert "question" in problem, "Missing question!"
        assert "correct" in problem, "Missing correct answer!"
        
        # 4. Did it generate at least one trap?
        assert len(problem["options"]) >= 2, "Not enough multiple choice options generated!"