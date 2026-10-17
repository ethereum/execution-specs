"""Check Hive results retain client teardown diagnostics."""

import json
from typing import Any

import pytest

pytest_plugins = ["pytester"]


@pytest.mark.parametrize("capture", ["fd", "sys", "tee-sys", "no"])
@pytest.mark.parametrize("fail", [False, True], ids=["pass", "fail"])
def test_hive_result_includes_client_teardown_output(
    pytester: Any, capture: str, fail: bool
) -> None:
    """Keep client shutdown output in both Hive and pytest reports."""
    pytester.makeconftest(
        """
import json
import logging
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from hive import testing as hive_testing
from hive.client import ClientType

from execution_testing.cli.pytest_commands.plugins.consume.simulators import (
    single_test_client,
)

from execution_testing.cli.pytest_commands.plugins.pytest_hive import (
    pytest_hive,
)

hive_test = pytest_hive.hive_test
pytest_runtest_makereport = pytest_hive.pytest_runtest_makereport
client = single_test_client.client

class Client:
    def stop(self):
        print('client shutdown stdout')
        print('client shutdown stderr', file=sys.stderr)
        Path('client-stopped').touch()

class Session:
    def post(self, url, **kwargs):
        assert url == 'http://hive.invalid/test/1'
        assert Path('client-stopped').exists()
        Path('hive-result.json').write_text(json.dumps(kwargs['json']))
        return SimpleNamespace(raise_for_status=lambda: None)

class Test(hive_testing.HiveTest):
    def start_client(self, **kwargs):
        print('client setup stdout')
        return Client()

class Suite:
    def start_test(self, **kwargs):
        return Test(url='http://hive.invalid/test/1', id=1, **kwargs)

@pytest.fixture
def test_suite(monkeypatch):
    monkeypatch.setattr(hive_testing, 'get_session', lambda: Session())
    handler = logging.StreamHandler(sys.stdout)
    logger = single_test_client.logger
    previous_level = logger.level
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    try:
        yield Suite()
        assert Path('hive-result.json').exists()
    finally:
        logger.removeHandler(handler)
        logger.setLevel(previous_level)

@pytest.fixture
def test_case_description():
    return 'teardown output regression'

@pytest.fixture
def client_files():
    return {}

@pytest.fixture
def environment():
    return {}

@pytest.fixture
def client_type():
    return ClientType(name='regression-client', version='', meta={})

@pytest.fixture
def total_timing_data():
    return single_test_client.TimingData('regression')
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
    assert set(recorded) == {"pass", "details"}
    assert recorded["pass"] is not fail
    if capture != "no":
        assert recorded["details"].count("client shutdown stdout") == 1
        assert recorded["details"].count("client shutdown stderr") == 1
        assert recorded["details"].count("client setup stdout") == 1
        assert recorded["details"].splitlines().count("test call stdout") == 1
        assert "Stopping client (regression-client)..." in recorded["details"]
        assert "Client (regression-client) stopped!" in recorded["details"]
        result.stdout.fnmatch_lines(
            ["*client shutdown stdout*", "*client shutdown stderr*"]
        )
    else:
        assert "client shutdown stdout" not in recorded["details"]
