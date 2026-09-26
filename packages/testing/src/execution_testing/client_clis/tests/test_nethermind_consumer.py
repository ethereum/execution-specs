"""
Test `NethtestFixtureConsumer.consume_blockchain_test`.

`nethtest --blockTest` always exits 0 regardless of outcome, so the pass/fail
verdict has to come from stdout. Nethermind's output format has changed
across versions (see execution-specs#3609): older builds only print a
human-readable "<name> PASS"/"FAIL" line per test, while newer builds
(>= 2.0.0) emit a JSON array instead. These tests pin both formats against
recorded/representative stdout so a regression to "always pass" is caught
without needing a real `nethtest` binary.
"""

import json
import subprocess
from pathlib import Path
from typing import Optional

import pytest

from execution_testing.client_clis.clis.nethermind import (
    NethtestFixtureConsumer,
)


class MockCompletedProcess:
    """Minimal stand-in for `subprocess.CompletedProcess`."""

    def __init__(self, stdout: str, stderr: str = "", returncode: int = 0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


def _consumer() -> NethtestFixtureConsumer:
    return NethtestFixtureConsumer(binary=Path("nethtest"))


def _run(
    monkeypatch: pytest.MonkeyPatch,
    stdout: str,
    stderr: str = "",
    returncode: int = 0,
    fixture_name: Optional[str] = "some_test",
) -> None:
    def mock_run(command: list, **kwargs: dict) -> MockCompletedProcess:
        del command, kwargs
        return MockCompletedProcess(
            stdout=stdout, stderr=stderr, returncode=returncode
        )

    monkeypatch.setattr(subprocess, "run", mock_run)
    _consumer().consume_blockchain_test(
        command=("nethtest", "--blockTest"),
        fixture_path=Path("fixture.json"),
        fixture_name=fixture_name,
    )


def test_json_pass_does_not_raise(monkeypatch: pytest.MonkeyPatch) -> None:
    """A JSON result array with `pass: true` should not raise."""
    stdout = json.dumps([{"name": "some_test", "pass": True}])
    _run(monkeypatch, stdout)


def test_json_fail_raises_with_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A JSON result array with `pass: false` should raise with the error."""
    stdout = json.dumps(
        [{"name": "some_test", "pass": False, "error": "root mismatch"}]
    )
    with pytest.raises(Exception, match="root mismatch"):
        _run(monkeypatch, stdout)


def test_json_fail_without_error_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Nethermind omits the `error` key entirely when it is null
    (`[JsonIgnore(Condition = WhenWritingNull)]`); this must not KeyError.
    """
    stdout = json.dumps([{"name": "some_test", "pass": False}])
    with pytest.raises(Exception, match="some_test"):
        _run(monkeypatch, stdout)


def test_json_empty_array_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    An empty JSON array (e.g. `--filter` matched nothing) must not be
    treated as a pass.
    """
    with pytest.raises(Exception, match="no block test results"):
        _run(monkeypatch, "[]")


def test_legacy_text_pass_does_not_raise(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A legacy human-readable PASS line should not raise."""
    stdout = f"{'some_test':<120} PASS\n"
    _run(monkeypatch, stdout)


def test_legacy_text_fail_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    A legacy human-readable FAIL line is the exact regression from
    execution-specs#3609: it must be detected and raised.
    """
    stdout = f"{'some_test':<120} FAIL\n"
    with pytest.raises(Exception, match="failed"):
        _run(monkeypatch, stdout)


def test_legacy_text_load_failure_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A load-failure line (no PASS/FAIL) must not be treated as a pass."""
    stdout = f"{'some_test':<120} some loader exception message\n"
    with pytest.raises(Exception, match="no recognizable PASS/FAIL"):
        _run(monkeypatch, stdout)


def test_empty_stdout_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """Empty stdout (no JSON, no recognizable lines) must not be a pass."""
    with pytest.raises(Exception, match="no recognizable PASS/FAIL"):
        _run(monkeypatch, "")


def test_nonzero_returncode_raises_before_parsing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A non-zero exit code is still an unconditional failure."""
    with pytest.raises(Exception, match="non-zero exit code"):
        _run(monkeypatch, stdout="", returncode=1)
