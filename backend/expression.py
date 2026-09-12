"""Kolejność wykonywania działań expression module — parses the ASCII grammar
`+ - * : ^ ( )` the twelve generators emit, evaluates it exactly, and renders any
subtree back to LaTeX in the operand notation (`n/d` fraction or decimal-comma) it
was parsed with. Pure: no Session, state, or HTTP imports.
"""

from __future__ import annotations

import dataclasses
import re
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction

from backend.core.utils import fmt_dec

_TOKEN_RE = re.compile(r"\s*(\d+(?:[/,]\d+)?|[()+\-*:^])")


class ExpressionSyntaxError(ValueError):
    """Raised when a string does not match the `+ - * : ^ ( )` grammar."""


@dataclass(frozen=True, slots=True)
class Value:
    """A leaf operand — a fraction (`n/d`), a decimal (`n,d`), or a bare integer."""

    value: Fraction
    notation: str  # "fraction" | "decimal"
    parenthesized: bool = False


@dataclass(frozen=True, slots=True)
class BinOp:
    """A binary operation on two subtrees. `op` is one of `+ - * :`."""

    op: str
    left: "Node"
    right: "Node"
    parenthesized: bool = False


@dataclass(frozen=True, slots=True)
class Power:
    """A subtree raised to an integer exponent, e.g. `(a + b)^2`."""

    base: "Node"
    exponent: int
    parenthesized: bool = False


Node = Value | BinOp | Power


def _tokenize(source: str) -> list[str]:
    """Split an expression string into number and operator tokens."""
    tokens = []
    pos = 0
    source = source.strip()
    while pos < len(source):
        match = _TOKEN_RE.match(source, pos)
        if not match:
            raise ExpressionSyntaxError(f"Unexpected character at {pos} in {source!r}")
        pos = match.end()
        tokens.append(match.group(1))
    return tokens


def _parse_number(token: str) -> Value:
    if "/" in token:
        num, den = token.split("/")
        return Value(Fraction(int(num), int(den)), "fraction")
    if "," in token:
        whole, frac_part = token.split(",")
        return Value(Fraction(f"{whole}.{frac_part}"), "decimal")
    return Value(Fraction(int(token)), "fraction")


def _parenthesized(node: Node) -> Node:
    return dataclasses.replace(node, parenthesized=True)


class _Parser:
    """Recursive-descent parser: `expr := term ((+|-) term)*`, down to atoms."""

    def __init__(self, tokens: list[str]) -> None:
        self._tokens = tokens
        self._pos = 0

    def _peek(self) -> str | None:
        return self._tokens[self._pos] if self._pos < len(self._tokens) else None

    def _consume(self) -> str:
        token = self._peek()
        if token is None:
            raise ExpressionSyntaxError("Unexpected end of expression")
        self._pos += 1
        return token

    def parse(self) -> Node:
        node = self._expr()
        if self._pos != len(self._tokens):
            raise ExpressionSyntaxError(f"Unexpected token {self._peek()!r}")
        return node

    def _expr(self) -> Node:
        node = self._term()
        while self._peek() in ("+", "-"):
            op = self._consume()
            node = BinOp(op, node, self._term())
        return node

    def _term(self) -> Node:
        node = self._power()
        while self._peek() in ("*", ":"):
            op = self._consume()
            node = BinOp(op, node, self._power())
        return node

    def _power(self) -> Node:
        node = self._atom()
        if self._peek() == "^":
            self._consume()
            exponent = self._consume()
            if not exponent.isdigit():
                raise ExpressionSyntaxError(
                    f"Expected an integer exponent, got {exponent!r}"
                )
            node = Power(node, int(exponent))
        return node

    def _atom(self) -> Node:
        token = self._consume()
        if token == "(":
            node = self._expr()
            closing = self._consume()
            if closing != ")":
                raise ExpressionSyntaxError(f"Expected ')', got {closing!r}")
            return _parenthesized(node)
        return _parse_number(token)


def parse(source: str) -> Node:
    """Parse an ASCII infix expression into a tree."""
    return _Parser(_tokenize(source)).parse()


def evaluate(node: Node) -> Fraction:
    """Evaluate an expression tree to its exact value — no intermediate rounding."""
    if isinstance(node, Value):
        return node.value
    if isinstance(node, Power):
        return evaluate(node.base) ** node.exponent
    left, right = evaluate(node.left), evaluate(node.right)
    if node.op == "+":
        return left + right
    if node.op == "-":
        return left - right
    if node.op == "*":
        return left * right
    return left / right  # ":"


_OP_LATEX = {"+": " + ", "-": " - ", "*": " \\cdot ", ":": " : "}


def render(node: Node) -> str:
    """Render an expression (sub)tree back to LaTeX, in its own operand notation."""
    inner = _render_inner(node)
    return f"({inner})" if node.parenthesized else inner


def _render_inner(node: Node) -> str:
    if isinstance(node, Value):
        return _render_value(node.value, node.notation)
    if isinstance(node, Power):
        return f"{render(node.base)}^{node.exponent}"
    return f"{render(node.left)}{_OP_LATEX[node.op]}{render(node.right)}"


def _render_value(value: Fraction, notation: str) -> str:
    if notation == "decimal":
        return fmt_dec(Decimal(value.numerator) / Decimal(value.denominator))
    if value.denominator == 1:
        return str(value.numerator)
    return rf"\frac{{{value.numerator}}}{{{value.denominator}}}"
