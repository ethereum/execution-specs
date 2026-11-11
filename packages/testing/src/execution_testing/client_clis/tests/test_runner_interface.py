"""Test the models of client test runner output."""

import pytest
from pydantic import ValidationError

from execution_testing.client_clis.runner_interface import (
    BalExecution,
    BalFallback,
    RunnerResults,
)

BLOCK_HASH = "0x" + "ab" * 32


def test_results_round_trip_keeps_pass_and_client_keys() -> None:
    """`pass` keeps its name on output, and keys a client adds survive."""
    raw = (
        '[{"name": "test_x[fork_Amsterdam-blockchain_test]", "pass": true,'
        ' "rejections": [{"index": 1, "hash": "' + BLOCK_HASH + '",'
        ' "error": "-38003: invalid"}], "fork": "Amsterdam"}]'
    )
    results = RunnerResults.model_validate_json(raw)
    result = results.root[0]
    assert result.passed
    assert result.model_extra == {"fork": "Amsterdam"}
    assert (
        RunnerResults.model_validate_json(
            results.model_dump_json(by_alias=True)
        )
        == results
    )


def test_rejection_hash_is_optional() -> None:
    """A rejection without a hash, as for a block that fails to decode."""
    results = RunnerResults.model_validate_json(
        '[{"name": "t", "pass": true,'
        ' "rejections": [{"index": 0, "error": "rlp: too short"}]}]'
    )
    assert results.root[0].rejections[0].hash is None


@pytest.mark.parametrize(
    "line",
    [
        pytest.param(
            '{"event": "balExecution", "block": 1, "hash": "'
            + BLOCK_HASH
            + '", "path": "serial", "reason": ""}',
            id="unknown_path",
        ),
        pytest.param(
            '{"event": "balFallback", "block": 1, "hash": "'
            + BLOCK_HASH
            + '", "parallelError": "x", "sequentialResult": "ok",'
            ' "sequentialError": ""}',
            id="unknown_sequential_result",
        ),
    ],
)
def test_report_lines_reject_unknown_values(line: str) -> None:
    """Values outside the page's sets fail validation."""
    model = BalExecution if '"balExecution"' in line else BalFallback
    with pytest.raises(ValidationError):
        model.model_validate_json(line)


def test_schemas_use_wire_names() -> None:
    """The generated schemas name fields as runners print them."""
    result_schema = RunnerResults.model_json_schema(by_alias=True)
    fixture_result = result_schema["$defs"]["FixtureResult"]["properties"]
    assert set(fixture_result) == {"name", "pass", "rejections"}
    fallback = BalFallback.model_json_schema(by_alias=True)["properties"]
    assert {"parallelError", "sequentialResult", "sequentialError"} <= set(
        fallback
    )
