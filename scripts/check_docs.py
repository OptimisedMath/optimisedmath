"""Enforce the mechanical rules in docs/agents/documentation.md.

Checks what a pattern can decide; everything needing judgment is left to review.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

SECTION_HEADINGS = ("Args:", "Arguments:", "Returns:", "Return:")
ROOTS = ("backend", "tests")


def check(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    failures = []

    for node in ast.walk(tree):
        if not isinstance(
            node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            continue
        doc = ast.get_docstring(node)
        if doc is None:
            continue
        line = 1 if isinstance(node, ast.Module) else node.lineno
        where = f"{path}:{line}"

        for heading in SECTION_HEADINGS:
            if any(l.strip() == heading for l in doc.splitlines()):
                failures.append(
                    f"{where}: `{heading}` section — the signature is typed"
                )

    return failures


def main() -> int:
    failures = []
    for root in ROOTS:
        for path in sorted(Path(root).rglob("*.py")):
            failures.extend(check(path))

    for failure in failures:
        print(failure)
    if failures:
        print(f"\n{len(failures)} documentation-rule violations.")
        print("See docs/agents/documentation.md.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
