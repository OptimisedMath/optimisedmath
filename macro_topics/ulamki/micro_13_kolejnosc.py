import random
from core.utils import format_answers, format_fraction_question, build_problem_dict

def order_no_brackets(level):
    while True:
        d = random.randint(3, 6)
        n1, n2, n3 = random.randint(1, d-1), random.randint(1, d-1), random.randint(1, d-1)
        
        q_str = rf"\text{{Oblicz: }} {format_fraction_question(n1, d)} + {format_fraction_question(n2, d)} \cdot {format_fraction_question(n3, d)}"
        c_str, i_str, u_str = format_answers(n1 * d + (n2 * n3), d * d)
        t_str, _, _ = format_answers((n1 + n2) * n3, d * d) # Trap: Added first (left to right)
        w_str, _, _ = format_answers(n1 * d + (n2 * n3) + 1, d * d)
        
        if len({c_str, t_str, w_str}) == 3: return build_problem_dict(q_str, c_str, i_str, u_str, t_str, w_str, f"Poziom {level}")

def order_brackets(level):
    while True:
        d = random.randint(3, 6)
        n1, n2, n3 = random.randint(1, d-1), random.randint(1, d-1), random.randint(1, d-1)
        
        q_str = rf"\text{{Oblicz: }} {format_fraction_question(n1, d)} \cdot \left( {format_fraction_question(n2, d)} + {format_fraction_question(n3, d)} \right)"
        c_str, i_str, u_str = format_answers(n1 * (n2 + n3), d * d)
        t_str, _, _ = format_answers((n1 * n2) + n3, d * d) # Trap: Ignored brackets, multiplied first
        w_str, _, _ = format_answers(n1 * (n2 + n3) + 1, d * d)
        
        if len({c_str, t_str, w_str}) == 3: return build_problem_dict(q_str, c_str, i_str, u_str, t_str, w_str, f"Poziom {level}")