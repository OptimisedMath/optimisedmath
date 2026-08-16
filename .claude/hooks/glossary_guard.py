#!/usr/bin/env python3
"""PreToolUse hook: block reintroduction of CONTEXT.md's banned glossary synonyms.

Reads a Claude Code PreToolUse payload from stdin (Edit or Write). If the
pending content newly introduces a term listed on a CONTEXT.md `_Avoid_`
line, blocks the write (exit 2, message on stderr) naming the offending
term and the canonical replacement. Stdlib only, no venv/npm dependency.
"""

import difflib
import json
import pathlib
import re
import sys

SCOPE_ROOTS = ("backend", "frontend")
EXCLUDED_DIR_NAMES = {
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".next",
    "dist",
    "build",
    ".git",
    "docs",
}

# Single generic-English words that collide with keywords, prose, or
# unrelated identifiers. These only block when newly introduced as the
# name (or a name-component) of a declared identifier, never on bare
# text/keyword/prose usage. Everything else in a glossary `_Avoid_` line
# is matched anywhere in newly added text (word/phrase boundary).
IDENTIFIER_ONLY_TERMS = {
    "pass",
    "continue",
    "module",
    "current",
    "active",
    "item",
    "content",
    "domain",
    "player",
    "track",
    "accessible",
    "proceed",
    "complete",
    "advance",
}

HEADING_RE = re.compile(r"^\*\*(.+?)\*\*:\s*$")
AVOID_RE = re.compile(r"^_Avoid_:\s*(.+)$")
TRAILING_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")

STRING_RE = re.compile(
    r"""('([^'\\]|\\.)*'|"([^"\\]|\\.)*"|`([^`\\]|\\.)*`)""", re.DOTALL
)

PY_DECL_PATTERNS = [
    re.compile(r"^\s*(?:async\s+)?def\s+([A-Za-z_]\w*)"),
    re.compile(r"^\s*class\s+([A-Za-z_]\w*)"),
]
PY_ASSIGN_RE = re.compile(
    r"^\s*([A-Za-z_]\w*(?:\s*,\s*[A-Za-z_]\w*)*)\s*(?::\s*[^=]+)?(?<![=!<>])=(?!=)"
)
PY_ANNOTATION_ONLY_RE = re.compile(
    r"^\s*([A-Za-z_]\w*)\s*:\s*[A-Za-z_][\w\[\],.'\"| ]*$"
)
PY_FOR_RE = re.compile(r"^\s*for\s+([A-Za-z_][\w,\s]*?)\s+in\s+")
PY_DEF_PARAMS_RE = re.compile(r"^\s*(?:async\s+)?def\s+[A-Za-z_]\w*\s*\(([^)]*)\)")

JS_DECL_PATTERNS = [
    re.compile(r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)"),
    re.compile(r"\bfunction\s*\*?\s*([A-Za-z_$][\w$]*)\s*\("),
    re.compile(r"\bclass\s+([A-Za-z_$][\w$]*)"),
    re.compile(r"\binterface\s+([A-Za-z_$][\w$]*)"),
    re.compile(r"\btype\s+([A-Za-z_$][\w$]*)\s*="),
    re.compile(r"\benum\s+([A-Za-z_$][\w$]*)"),
]
JS_DESTRUCTURE_RE = re.compile(r"\b(?:const|let|var)\s*\{([^}]*)\}\s*=")
JS_ARROW_PARAMS_RE = re.compile(r"\(([^)]*)\)\s*(?::\s*[^=>{]+)?\s*=>")
JS_FUNC_PARAMS_RE = re.compile(r"\bfunction\s*\*?\s*[A-Za-z_$][\w$]*\s*\(([^)]*)\)")
JS_FIELD_RE = re.compile(r"^\s*(?:readonly\s+)?([A-Za-z_$][\w$]*)\??\s*:\s*\S")

CAMEL_SPLIT_RE = re.compile(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|\d+")


def find_repo_root(start_path: pathlib.Path):
    for parent in [start_path] + list(start_path.parents):
        if (parent / "CONTEXT.md").is_file():
            return parent
    return None


def parse_glossary(context_md_text: str):
    """Return list of (avoid_term_text, canonical_heading) from CONTEXT.md."""
    entries = []
    current_term = None
    for line in context_md_text.splitlines():
        stripped = line.strip()
        heading_match = HEADING_RE.match(stripped)
        if heading_match:
            current_term = heading_match.group(1).strip()
            continue
        avoid_match = AVOID_RE.match(stripped)
        if avoid_match and current_term:
            for raw_term in split_top_level(avoid_match.group(1), ","):
                term = TRAILING_PAREN_RE.sub("", raw_term).strip()
                if term:
                    entries.append((term, current_term))
    return entries


def split_top_level(s: str, sep: str):
    parts = []
    depth = 0
    current = []
    for ch in s:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth = max(0, depth - 1)
        if ch == sep and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
    parts.append("".join(current))
    return [p.strip() for p in parts if p.strip()]


def in_scope(rel_path: pathlib.PurePosixPath):
    parts = rel_path.parts
    if not parts or parts[0] not in SCOPE_ROOTS:
        return False
    if any(p in EXCLUDED_DIR_NAMES for p in parts[:-1]):
        return False
    if parts[-1] == "CONTEXT.md":
        return False
    return True


def detect_lang(rel_path: pathlib.PurePosixPath):
    ext = rel_path.suffix.lower()
    if ext == ".py":
        return "python"
    if ext in (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"):
        return "js"
    return None


def added_lines_with_numbers(old_text: str, new_text: str):
    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()
    matcher = difflib.SequenceMatcher(None, old_lines, new_lines, autojunk=False)
    result = []
    for tag, _i1, _i2, j1, j2 in matcher.get_opcodes():
        if tag in ("replace", "insert"):
            for offset, line in enumerate(new_lines[j1:j2]):
                result.append((j1 + offset + 1, line))
    return result


def strip_strings_and_comments(line: str, lang: str):
    stripped = STRING_RE.sub('""', line)
    if lang == "python":
        idx = stripped.find("#")
        if idx != -1:
            stripped = stripped[:idx]
    else:
        idx = stripped.find("//")
        if idx != -1:
            stripped = stripped[:idx]
        stripped = re.sub(r"/\*.*?\*/", "", stripped)
    return stripped


def split_top_level_params(s: str):
    return split_top_level(s, ",")


def param_name(param: str):
    param = param.strip().lstrip("*")
    if param.startswith("{") or param.startswith("["):
        return None
    match = re.match(r"^([A-Za-z_$][\w$]*)", param)
    return match.group(1) if match else None


def extract_declared_identifiers(stripped_line: str, lang: str):
    names = []
    if lang == "python":
        for pattern in PY_DECL_PATTERNS:
            match = pattern.match(stripped_line)
            if match:
                names.append(match.group(1))
        assign_match = PY_ASSIGN_RE.match(stripped_line)
        if assign_match:
            names.extend(name.strip() for name in assign_match.group(1).split(","))
        annotation_match = PY_ANNOTATION_ONLY_RE.match(stripped_line)
        if annotation_match:
            names.append(annotation_match.group(1))
        for_match = PY_FOR_RE.match(stripped_line)
        if for_match:
            names.extend(name.strip() for name in for_match.group(1).split(","))
        params_match = PY_DEF_PARAMS_RE.match(stripped_line)
        if params_match:
            for param in split_top_level_params(params_match.group(1)):
                name = param_name(param)
                if name and name not in ("self", "cls"):
                    names.append(name)
    elif lang == "js":
        for pattern in JS_DECL_PATTERNS:
            for match in pattern.finditer(stripped_line):
                names.append(match.group(1))
        destructure_match = JS_DESTRUCTURE_RE.search(stripped_line)
        if destructure_match:
            for item in split_top_level_params(destructure_match.group(1)):
                item = re.sub(r"=.*$", "", item).strip()
                if ":" in item:
                    item = item.split(":")[-1].strip()
                name = param_name(item)
                if name:
                    names.append(name)
        for pattern in (JS_ARROW_PARAMS_RE, JS_FUNC_PARAMS_RE):
            for match in pattern.finditer(stripped_line):
                for param in split_top_level_params(match.group(1)):
                    name = param_name(param)
                    if name:
                        names.append(name)
        field_match = JS_FIELD_RE.match(stripped_line)
        if field_match:
            names.append(field_match.group(1))
    return names


def split_identifier_components(name: str):
    components = []
    for part in name.split("_"):
        if not part:
            continue
        sub = CAMEL_SPLIT_RE.findall(part)
        components.extend(sub if sub else [part])
    return [c.lower() for c in components if c]


def find_violations(repo_root: pathlib.Path, lang, lines):
    glossary_text = (repo_root / "CONTEXT.md").read_text(encoding="utf-8")
    entries = parse_glossary(glossary_text)

    anywhere_patterns = [
        (
            re.compile(r"(?<!\w)" + re.escape(term) + r"(?!\w)", re.IGNORECASE),
            term,
            canonical,
        )
        for term, canonical in entries
        if term.lower() not in IDENTIFIER_ONLY_TERMS
    ]

    violations = []
    seen = set()

    for line_no, raw_line in lines:
        stripped = strip_strings_and_comments(raw_line, lang or "python")

        # Anywhere-match terms: unambiguous phrase/word match in raw added text.
        for pattern, term, canonical in anywhere_patterns:
            if pattern.search(raw_line):
                key = (term.lower(), line_no)
                if key not in seen:
                    seen.add(key)
                    violations.append((term, canonical, line_no, raw_line.strip()))

        # Identifier-only terms: only when newly introduced as a declared name.
        if lang:
            declared = extract_declared_identifiers(stripped, lang)
            for name in declared:
                components = split_identifier_components(name)
                whole = name.lower()
                candidates = set(components) | {whole}
                for term, canonical in entries:
                    if term.lower() not in IDENTIFIER_ONLY_TERMS:
                        continue
                    if term.lower() in candidates:
                        key = (term.lower(), line_no)
                        if key not in seen:
                            seen.add(key)
                            violations.append(
                                (
                                    term,
                                    canonical,
                                    line_no,
                                    f"`{name}` in: {raw_line.strip()}",
                                )
                            )
    return violations


def main():
    payload = json.load(sys.stdin)
    tool_name = payload.get("tool_name")
    if tool_name not in ("Edit", "Write"):
        return 0

    tool_input = payload.get("tool_input") or {}
    file_path = tool_input.get("file_path")
    if not file_path:
        return 0

    target = pathlib.Path(file_path)
    if not target.is_absolute():
        cwd = payload.get("cwd")
        if cwd:
            target = pathlib.Path(cwd) / target
    target = target.resolve()

    repo_root = find_repo_root(target.parent)
    if repo_root is None:
        return 0

    try:
        rel_path = pathlib.PurePosixPath(target.relative_to(repo_root).as_posix())
    except ValueError:
        return 0

    if not in_scope(rel_path):
        return 0

    lang = detect_lang(rel_path)

    try:
        on_disk = target.read_text(encoding="utf-8") if target.is_file() else ""
    except (UnicodeDecodeError, OSError):
        return 0

    if tool_name == "Write":
        old_content = on_disk
        new_content = tool_input.get("content", "")
    else:
        old_string = tool_input.get("old_string", "")
        new_string = tool_input.get("new_string", "")
        replace_all = bool(tool_input.get("replace_all", False))
        if old_string and old_string in on_disk:
            # Reconstruct the resulting file so added-line numbers are real
            # file positions, not positions within the old/new snippets.
            old_content = on_disk
            if replace_all:
                new_content = on_disk.replace(old_string, new_string)
            else:
                idx = on_disk.find(old_string)
                new_content = (
                    on_disk[:idx] + new_string + on_disk[idx + len(old_string) :]
                )
        else:
            old_content = old_string
            new_content = new_string

    lines = added_lines_with_numbers(old_content, new_content)
    if not lines:
        return 0

    violations = find_violations(repo_root, lang, lines)
    if not violations:
        return 0

    messages = [
        f"BLOCKED: {rel_path} line {line_no} reintroduces banned term "
        f'"{term}" — use the canonical glossary term "{canonical}" instead '
        f"(see CONTEXT.md). Offending text: {snippet}"
        for term, canonical, line_no, snippet in violations
    ]
    sys.stderr.write("\n".join(messages) + "\n")
    return 2


if __name__ == "__main__":
    sys.exit(main())
