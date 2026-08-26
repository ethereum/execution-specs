"""Tests for general state test execution."""

import argparse
import json
from io import StringIO
from types import SimpleNamespace
from typing import Any

import pytest

from execution_testing.base_types import EmptyTrieRoot, Hash
from execution_testing.evm_tools import statetest
from execution_testing.evm_tools.statetest import (
    StateTest,
    run_test_case,
)
from execution_testing.evm_tools.statetest import (
    TestCase as StateTestCase,
)
from execution_testing.evm_tools.t8n import ForkCache
from execution_testing.test_types import Environment

pytestmark = pytest.mark.evm_tools


def _test_case(
    *,
    env: dict[str, Any],
    post_hash: str,
    transaction_value: str = "0x0",
) -> StateTestCase:
    """Create a minimal state test case."""
    return StateTestCase(
        path="test.json",
        key="test_case",
        index=0,
        fork_name="Shanghai",
        post={
            "hash": post_hash,
            "indexes": {"data": 0, "gas": 0, "value": 0},
        },
        pre={},
        env=env,
        transaction={
            "data": ["0x"],
            "gasLimit": ["0x5208"],
            "value": [transaction_value],
        },
    )


def test_run_test_case_translates_previous_hash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Translate legacy `previousHash` without passing it to t8n."""
    previous_hash = Hash(1).hex()
    test_case = _test_case(env={"previousHash": previous_hash}, post_hash="0x")
    captured_input: dict[str, Any] = {}
    expected_result = object()

    def fake_build_t8n(
        options: argparse.Namespace,
        in_file: StringIO,
        fork_cache: ForkCache,
    ) -> SimpleNamespace:
        captured_input.update(json.load(in_file))
        Environment.model_validate(captured_input["env"])
        return SimpleNamespace(
            run_state_test=lambda: None,
            result=expected_result,
        )

    monkeypatch.setattr(
        statetest,
        "build_t8n_from_cli_options",
        fake_build_t8n,
    )

    with ForkCache() as fork_cache:
        result = run_test_case(test_case, fork_cache)

    assert result is expected_result
    assert captured_input["env"] == {
        "blockHashes": {"0": previous_hash},
        "withdrawals": [],
    }


def test_run_test_case_accepts_empty_hex_value() -> None:
    """Treat the legacy empty hexadecimal transaction value as zero."""
    test_case = _test_case(
        env={
            "currentBaseFee": "0x7",
            "currentRandom": "0x" + "00" * 32,
        },
        post_hash="0x",
        transaction_value="0x",
    )

    with ForkCache() as fork_cache:
        result = run_test_case(test_case, fork_cache)

    assert result.state_root == Hash(EmptyTrieRoot)


def test_run_one_formats_state_root_once(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Emit one `0x` prefix while keeping mismatch hashes unprefixed."""
    state_root = Hash("0x" + "11" * 32)
    expected_root = "0x" + "00" * 32
    test_case = _test_case(env={}, post_hash=expected_root)
    out_file = StringIO()
    state_test = StateTest(
        argparse.Namespace(
            file=None,
            json=False,
            memory=True,
            stack=True,
            return_data=True,
        ),
        out_file,
        StringIO(),
    )
    state_test.supported_forks = ("shanghai",)

    def fake_read_test_cases(_path: str) -> list[StateTestCase]:
        return [test_case]

    def fake_run_test_case(*_args: Any, **_kwargs: Any) -> SimpleNamespace:
        return SimpleNamespace(state_root=state_root)

    monkeypatch.setattr(
        statetest,
        "read_test_cases",
        fake_read_test_cases,
    )
    monkeypatch.setattr(
        statetest,
        "run_test_case",
        fake_run_test_case,
    )

    assert state_test.run_one(test_case.path, ForkCache()) == 0

    assert json.loads(capsys.readouterr().err) == {
        "stateRoot": state_root.hex()
    }
    assert json.loads(out_file.getvalue()) == [
        {
            "stateRoot": state_root.hex(),
            "fork": "Shanghai",
            "name": "test_case",
            "pass": False,
            "error": (
                f"post state root mismatch: got {'11' * 32}, want {'00' * 32}"
            ),
        }
    ]
