"""Tests for .claude/hooks/glossary_guard.py, invoked as a subprocess like
Claude Code would invoke it as a PreToolUse hook.

No live Claude Code session involved: each test feeds a PreToolUse-shaped
JSON payload to the script's stdin against a throwaway fake repo (its own
CONTEXT.md + backend/frontend tree) and asserts exit code + stderr.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOK_PATH = (
    Path(__file__).resolve().parent.parent / ".claude" / "hooks" / "glossary_guard.py"
)

BASE_CONTEXT_MD = """\
# Fake Project

**Streak**:
Consecutive correct answers.
_Avoid_: Level Streak, passa

**Session**:
One play session.
_Avoid_: GameState (code name)

**Selected**:
The chapter/topic/level currently active.
_Avoid_: current, active, selection

**Student**:
The person practicing.
_Avoid_: player
"""


def make_repo(tmp_path, context_md=BASE_CONTEXT_MD):
    (tmp_path / "CONTEXT.md").write_text(context_md, encoding="utf-8")
    (tmp_path / "backend").mkdir()
    (tmp_path / "backend" / "docs").mkdir()
    (tmp_path / "frontend").mkdir()
    (tmp_path / "tests").mkdir()
    return tmp_path


def run_hook(payload):
    return subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
    )


def write_payload(repo_root, rel_path, content):
    return {
        "tool_name": "Write",
        "cwd": str(repo_root),
        "tool_input": {"file_path": str(repo_root / rel_path), "content": content},
    }


def edit_payload(repo_root, rel_path, old_string, new_string):
    return {
        "tool_name": "Edit",
        "cwd": str(repo_root),
        "tool_input": {
            "file_path": str(repo_root / rel_path),
            "old_string": old_string,
            "new_string": new_string,
        },
    }


def test_blocks_anywhere_match_term_in_new_code(tmp_path):
    repo = make_repo(tmp_path)
    result = run_hook(write_payload(repo, "backend/session_state.py", "passa = 0\n"))
    assert result.returncode == 2
    assert "passa" in result.stderr
    assert "Streak" in result.stderr


def test_blocks_anywhere_match_code_name(tmp_path):
    repo = make_repo(tmp_path)
    result = run_hook(
        write_payload(repo, "frontend/lib/session.ts", "type GameState = {}\n")
    )
    assert result.returncode == 2
    assert "GameState" in result.stderr
    assert "Session" in result.stderr


def test_blocks_generic_word_as_new_identifier(tmp_path):
    repo = make_repo(tmp_path)
    result = run_hook(
        edit_payload(repo, "backend/foo.py", "", "activeTopic = get_topic()\n")
    )
    assert result.returncode == 2
    assert "active" in result.stderr
    assert "Selected" in result.stderr


def test_blocks_generic_word_as_snake_case_identifier(tmp_path):
    repo = make_repo(tmp_path)
    result = run_hook(
        edit_payload(repo, "backend/foo.py", "", "def player_score():\n    pass\n")
    )
    assert result.returncode == 2
    assert "player" in result.stderr
    assert "Student" in result.stderr


def test_blocks_generic_word_in_union_type_annotation(tmp_path):
    repo = make_repo(tmp_path)
    result = run_hook(edit_payload(repo, "backend/foo.py", "", "player: int | None\n"))
    assert result.returncode == 2
    assert "player" in result.stderr
    assert "Student" in result.stderr


def test_allows_generic_word_used_as_keyword(tmp_path):
    repo = make_repo(tmp_path)
    new_string = "for x in y:\n    continue\n\n\ndef foo():\n    pass\n"
    result = run_hook(edit_payload(repo, "backend/foo.py", "", new_string))
    assert result.returncode == 0
    assert result.stderr == ""


def test_allows_generic_word_in_comment(tmp_path):
    repo = make_repo(tmp_path)
    result = run_hook(
        edit_payload(
            repo,
            "backend/foo.py",
            "",
            "# the current implementation is temporary\n",
        )
    )
    assert result.returncode == 0
    assert result.stderr == ""


def test_allows_generic_word_in_preexisting_identifier(tmp_path):
    repo = make_repo(tmp_path)
    old_string = "current_level = 1\nx = 2\n"
    new_string = "current_level = 1\nx = 3\n"
    result = run_hook(edit_payload(repo, "backend/foo.py", old_string, new_string))
    assert result.returncode == 0
    assert result.stderr == ""


def test_stays_silent_outside_backend_frontend(tmp_path):
    repo = make_repo(tmp_path)
    result = run_hook(write_payload(repo, "tests/foo.py", "passa = 1\n"))
    assert result.returncode == 0
    assert result.stderr == ""


def test_stays_silent_on_nested_docs_dir(tmp_path):
    repo = make_repo(tmp_path)
    result = run_hook(write_payload(repo, "backend/docs/notes.md", "passa\n"))
    assert result.returncode == 0
    assert result.stderr == ""


def test_stays_silent_on_context_md_itself(tmp_path):
    repo = make_repo(tmp_path)
    result = run_hook(write_payload(repo, "CONTEXT.md", "passa\n"))
    assert result.returncode == 0
    assert result.stderr == ""


def test_picks_up_new_avoid_term_without_script_change(tmp_path):
    context_md = BASE_CONTEXT_MD + (
        "\n**Custom Thing**:\nA newly modeled concept.\n"
        "_Avoid_: brandnewbannedword\n"
    )
    repo = make_repo(tmp_path, context_md=context_md)
    result = run_hook(write_payload(repo, "backend/foo.py", "brandnewbannedword = 1\n"))
    assert result.returncode == 2
    assert "brandnewbannedword" in result.stderr
    assert "Custom Thing" in result.stderr


def test_block_message_names_term_and_canonical_replacement(tmp_path):
    repo = make_repo(tmp_path)
    result = run_hook(write_payload(repo, "backend/session_state.py", "passa = 0\n"))
    assert result.returncode == 2
    assert "passa" in result.stderr
    assert "Streak" in result.stderr
    assert "CONTEXT.md" in result.stderr


def test_reports_real_file_line_number_for_edit(tmp_path):
    repo = make_repo(tmp_path)
    target = repo / "backend" / "foo.py"
    target.write_text(
        "\n".join(f"# comment line {i}" for i in range(1, 10)) + "\n",
        encoding="utf-8",
    )
    old_string = "# comment line 5\n# comment line 6"
    new_string = "# comment line 5\nplayer = 1\n# comment line 6"
    result = run_hook(edit_payload(repo, "backend/foo.py", old_string, new_string))
    assert result.returncode == 2
    assert "line 6" in result.stderr
    assert "line 1" not in result.stderr


def test_write_on_non_utf8_existing_file_fails_open(tmp_path):
    repo = make_repo(tmp_path)
    target = repo / "backend" / "legacy.py"
    target.write_bytes("# caf\xe9\n".encode("latin-1"))
    result = run_hook(write_payload(repo, "backend/legacy.py", "passa = 1\n"))
    assert result.returncode == 0


@pytest.mark.parametrize("tool_name", ["Read", "Bash", "Grep", "NotebookEdit"])
def test_ignores_non_edit_write_tools(tmp_path, tool_name):
    repo = make_repo(tmp_path)
    payload = {
        "tool_name": tool_name,
        "cwd": str(repo),
        "tool_input": {"file_path": str(repo / "backend/foo.py")},
    }
    result = run_hook(payload)
    assert result.returncode == 0
