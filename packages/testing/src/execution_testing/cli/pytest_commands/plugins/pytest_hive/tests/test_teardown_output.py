"""Check Hive results retain client teardown diagnostics."""

import json
from typing import Any

import pytest

pytest_plugins = ["pytester"]


@pytest.mark.parametrize("capture", ["fd", "sys", "no"])
@pytest.mark.parametrize("fail", [False, True], ids=["pass", "fail"])
def test_hive_result_includes_client_teardown_output(
    pytester: Any, capture: str, fail: bool
) -> None:
    """Keep client shutdown output in both Hive and pytest reports."""
    pytester.makeconftest(
        """
import json
import sys
from pathlib import Path

import pytest

from execution_testing.cli.pytest_commands.plugins.pytest_hive import (
    pytest_hive,
)

hive_test = pytest_hive.hive_test
pytest_runtest_makereport = pytest_hive.pytest_runtest_makereport

class Test:
    def end(self, *, result):
        assert Path('client-stopped').exists()
        Path('hive-result.json').write_text(json.dumps({
            'passed': result.test_pass,
            'details': result.details,
        }))

class Suite:
    def start_test(self, **kwargs):
        return Test()

@pytest.fixture
def test_suite():
    yield Suite()
    assert Path('hive-result.json').exists()

@pytest.fixture
def test_case_description():
    return 'teardown output regression'

@pytest.fixture
def client(hive_test):
    print('client setup stdout')
    yield
    print('client shutdown stdout')
    print('client shutdown stderr', file=sys.stderr)
    Path('client-stopped').touch()
"""
    )
    pytester.makepyfile(
        f"""
def test_client(client):
    print('test call stdout')
    assert {not fail}
"""
    )

    result = pytester.runpytest(f"--capture={capture}", "-rP")
    result.assert_outcomes(passed=0 if fail else 1, failed=1 if fail else 0)
    recorded = json.loads((pytester.path / "hive-result.json").read_text())
    assert recorded["passed"] is not fail
    if capture != "no":
        assert recorded["details"].count("client shutdown stdout") == 1
        assert recorded["details"].count("client shutdown stderr") == 1
        assert recorded["details"].count("client setup stdout") == 1
        assert recorded["details"].splitlines().count("test call stdout") == 1
        result.stdout.fnmatch_lines(
            ["*client shutdown stdout*", "*client shutdown stderr*"]
        )
    else:
        assert "client shutdown stdout" not in recorded["details"]
