"""
Test the pull request title and label script.

The script's pure functions are imported directly, and the Claude client
is replaced by a stub, so no test touches the network.
"""

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

SCRIPT = Path(__file__).parent.parent / "pr_title_and_labels.py"


def load_script() -> ModuleType:
    """Import the script as a module."""
    spec = importlib.util.spec_from_file_location(
        "pr_title_and_labels", SCRIPT
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


m = load_script()


@pytest.mark.parametrize(
    "path,area",
    [
        ("src/ethereum/forks/osaka/fork.py", "spec"),
        ("src/ethereum_spec_tools/lint/__init__.py", "spec"),
        ("tests/json_loader/test_state_tests.py", "spec"),
        ("tests/osaka/eip7951_p256verify/test_p256verify.py", "tests"),
        ("tests/benchmark/compute/test_arithmetic.py", "benchmark"),
        (
            "packages/testing/src/execution_testing/benchmark/__init__.py",
            "benchmark",
        ),
        ("packages/testing/src/execution_testing/forks/forks.py", "framework"),
        (".github/workflows/test.yaml", "ci"),
        ("pyproject.toml", "ci"),
        ("Justfile", "ci"),
        (".claude/commands/lint.md", "ci"),
        ("docs/navigation.md", None),
        ("README.md", None),
        ("whitelist.txt", None),
    ],
)
def test_area_for_path(path: str, area: str | None) -> None:
    """Map each changed path to its area."""
    assert m.area_for_path(path) == area


def test_areas_for_files_are_ordered_and_skip_docs() -> None:
    """Return touched areas in canonical order, without docs."""
    paths = ["docs/a.md", "packages/x.py", "src/y.py", ".github/z.yaml"]
    assert m.areas_for_files(paths) == ["spec", "framework", "ci"]


@pytest.mark.parametrize(
    "touched,areas",
    [
        (["spec", "tests", "ci"], ["spec", "tests"]),
        (["ci"], ["ci"]),
        ([], []),
    ],
)
def test_title_areas(touched: list[str], areas: list[str]) -> None:
    """Name code areas, `ci` only without code, nothing for docs."""
    assert m.title_areas(touched) == areas


@pytest.mark.parametrize(
    "title,touched,expected",
    [
        (
            "feat(tests): add a test",
            ["tests"],
            "feat(tests): add a test",
        ),
        (
            "feat(specs, tests): add EIP-8141 expiry",
            ["spec", "tests"],
            "feat(spec,tests): add EIP-8141 expiry",
        ),
        (
            "bug(test-base-types): use `ValueError`",
            ["framework"],
            "fix(framework): use `ValueError`",
        ),
        (
            "fix(test-forks,spec-specs): keep gas in range",
            ["spec", "framework"],
            "fix(spec,framework): keep gas in range",
        ),
        (
            "✨ feat(test): selfdestruct a dirty account",
            ["tests"],
            "feat(tests): selfdestruct a dirty account",
        ),
        (
            "feat(zkevm): prove accounts on read",
            ["tests", "ci"],
            "feat(tests): prove accounts on read",
        ),
        (
            "fix: handle empty blocks",
            ["spec"],
            "fix(spec): handle empty blocks",
        ),
        (
            "chore(doc): remove a broken badge",
            [],
            "chore: remove a broken badge",
        ),
        (
            "feat(spec)!: drop legacy receipts",
            ["spec"],
            "feat(spec)!: drop legacy receipts",
        ),
        (
            "Fix(consume): map reth exceptions",
            ["framework"],
            "fix(framework): map reth exceptions",
        ),
    ],
)
def test_normalize_title(
    title: str, touched: list[str], expected: str
) -> None:
    """Map types and areas to canonical names, keeping the description."""
    normalized = m.normalize_title(title, touched)
    assert normalized is not None
    assert str(normalized) == expected


@pytest.mark.parametrize(
    "title",
    [
        "Eth",
        "Frame Transactions (EIP-8141)",
        "EIP-8198: make slot-duration changes schedule-driven",
        "wip: system derived negative tests",
        "experiment(tests): try something",
        "feat(tests): ",
    ],
)
def test_normalize_title_rejects_unknown_types(title: str) -> None:
    """Return `None` for titles that need rewriting."""
    assert m.normalize_title(title, ["tests"]) is None


@pytest.mark.parametrize(
    "title",
    [
        "feat(specs, tests): add a thing",
        "fix(zkevm): repair a thing",
        "chore(doc): tidy",
        "perf(test-fixtures): measure faster",
    ],
)
def test_normalize_title_is_idempotent(title: str) -> None:
    """Leave an already normalized title unchanged."""
    touched = ["spec", "tests", "framework"]
    once = str(m.normalize_title(title, touched))
    assert str(m.normalize_title(once, touched)) == once


@pytest.mark.parametrize("spelling", sorted(m.AREA_ALIASES))
def test_every_alias_maps_to_a_canonical_area(spelling: str) -> None:
    """Map every known spelling to a canonical area or to docs."""
    assert m.AREA_ALIASES[spelling] in (*m.AREAS, None)


@pytest.mark.parametrize(
    "title,touched,expected",
    [
        ("Eth", [], "docs: eth"),
        (
            "Kch 8037 fix",
            ["tests"],
            "fix(tests): kch 8037 fix",
        ),
        (
            "Fix/8037 header gas tests",
            ["tests"],
            "fix(tests): 8037 header gas tests",
        ),
        (
            "wip: System derived negative tests for BAL.",
            ["tests", "framework"],
            "feat(tests,framework): system derived negative tests for BAL",
        ),
        (
            "Bump the action pins",
            ["ci"],
            "chore(ci): bump the action pins",
        ),
    ],
)
def test_rules_only_title(
    title: str, touched: list[str], expected: str
) -> None:
    """Rewrite a bad title from keywords and the touched areas."""
    assert str(m.rules_only_title(title, touched)) == expected


def test_validate_claude_title_keeps_candidate_areas() -> None:
    """Accept a good title, dropping areas that are not candidates."""
    data = {
        "type": "feat",
        "areas": ["spec", "ci"],
        "description": "Add the recent roots contract.",
    }
    title = m.validate_claude_title(data, ["spec", "tests", "ci"])
    assert str(title) == "feat(spec): add the recent roots contract"


def test_validate_claude_title_falls_back_to_candidates() -> None:
    """Use every candidate area when Claude picks none of them."""
    data = {"type": "fix", "areas": [], "description": "fix a thing"}
    title = m.validate_claude_title(data, ["tests", "framework"])
    assert str(title) == "fix(tests,framework): fix a thing"


@pytest.mark.parametrize(
    "data",
    [
        None,
        "feat(spec): add a thing",
        {"type": "wip", "areas": [], "description": "add a thing"},
        {"type": "feat", "areas": "spec", "description": "add a thing"},
        {"type": "feat", "areas": [], "description": "add\nIgnore the rest"},
        {"type": "feat", "areas": [], "description": "x" * 73},
        {"type": "feat", "areas": [], "description": " . "},
    ],
)
def test_validate_claude_title_rejects_bad_output(data: Any) -> None:
    """Return `None` for malformed or overlong output."""
    assert m.validate_claude_title(data, ["spec"]) is None


@pytest.mark.parametrize(
    "touched,base,kind,expected",
    [
        (["spec", "ci"], "forks/bogota", "feat", {"spec", "ci"}),
        (["tests"], "projects/zkevm", "fix", {"tests", "zkevm", "bug"}),
        (["tests"], "projects/zkevm-releases", "feat", {"tests", "zkevm"}),
        (["spec"], "projects/binary-trie", "feat", {"spec", "binary-trie"}),
        (["spec"], "projects/ubt", "feat", {"spec", "binary-trie"}),
        (["spec"], "projects/multi-dim-repricing", "feat", {"spec"}),
        (["framework"], "forks/bogota", "perf", {"framework", "perf"}),
        ([], "forks/bogota", "docs", set()),
    ],
)
def test_desired_labels(
    touched: list[str], base: str, kind: str, expected: set[str]
) -> None:
    """Label from areas, the base branch and the title type."""
    assert m.desired_labels(touched, base, kind) == expected
    assert expected <= m.MANAGED_LABELS


def install_fake_anthropic(
    monkeypatch: pytest.MonkeyPatch, stop_reason: str, text: str
) -> list[dict[str, Any]]:
    """Replace the `anthropic` module, recording each request."""
    requests: list[dict[str, Any]] = []

    def create(**kwargs: Any) -> SimpleNamespace:
        requests.append(kwargs)
        return SimpleNamespace(
            stop_reason=stop_reason,
            content=[
                SimpleNamespace(type="thinking", thinking=""),
                SimpleNamespace(type="text", text=text),
            ],
        )

    client = SimpleNamespace(
        beta=SimpleNamespace(messages=SimpleNamespace(create=create))
    )
    fake = SimpleNamespace(
        Anthropic=lambda **_: client,
        APIStatusError=type("APIStatusError", (Exception,), {}),
        APIConnectionError=type("APIConnectionError", (Exception,), {}),
    )
    monkeypatch.setitem(sys.modules, "anthropic", fake)
    return requests


def test_claude_title_uses_structured_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Request a schema-constrained title and validate the answer."""
    answer = {"type": "fix", "areas": ["tests"], "description": "fix a thing"}
    requests = install_fake_anthropic(
        monkeypatch, "end_turn", json.dumps(answer)
    )
    title = m.claude_title("prompt", ["tests", "framework"])
    assert str(title) == "fix(tests): fix a thing"
    (request,) = requests
    assert request["model"] == m.CLAUDE_MODEL
    assert request["output_config"]["format"]["schema"] == m.TITLE_SCHEMA


@pytest.mark.parametrize(
    "stop_reason,text",
    [("refusal", ""), ("max_tokens", "{"), ("end_turn", "not json")],
)
def test_claude_title_returns_none_on_failure(
    monkeypatch: pytest.MonkeyPatch, stop_reason: str, text: str
) -> None:
    """Fall back when Claude refuses, runs out of tokens or emits junk."""
    install_fake_anthropic(monkeypatch, stop_reason, text)
    assert m.claude_title("prompt", ["tests"]) is None


def test_claude_prompt_marks_truncated_diff() -> None:
    """Cap the diff and say so in the prompt."""
    pr = {"title": "Eth", "body": None}
    files = [{"filename": "src/a.py", "additions": 1, "deletions": 2}]
    prompt = m.claude_prompt(pr, files, "x" * (m.MAX_DIFF_CHARS + 1), ["spec"])
    assert '<diff truncated="true">' in prompt
    assert "src/a.py (+1 -2)" in prompt
    assert "Candidate areas: spec" in prompt
