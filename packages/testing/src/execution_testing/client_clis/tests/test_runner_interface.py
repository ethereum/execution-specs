"""Test the models of client test runner output."""

import pytest
from pydantic import ValidationError

from execution_testing.client_clis.runner_interface import (
    BalExecution,
    BalFallback,
    BuildFixtureResult,
    BuildRunnerResults,
    Mismatch,
    RunnerResults,
)

BLOCK_HASH = "0x" + "ab" * 32
OTHER_HASH = "0x" + "cd" * 32


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


def test_build_results_round_trip_keeps_mismatch_values() -> None:
    """A mismatch keeps any JSON value, and the results round-trip."""
    raw = (
        '[{"name": "test_x[fork_Prague-blockchain_test_engine]",'
        ' "pass": false, "rejections": [], "built": 2, "mismatches": ['
        '{"index": 1, "field": "stateRoot", "expected": "' + BLOCK_HASH + '",'
        ' "got": "' + OTHER_HASH + '"},'
        ' {"index": 1, "field": "executionRequests", "expected": ["0x01"],'
        ' "got": []}]}]'
    )
    results = BuildRunnerResults.model_validate_json(raw)
    result = results.root[0]
    assert not result.passed
    assert result.built == 2
    assert [mismatch.field for mismatch in result.mismatches] == [
        "stateRoot",
        "executionRequests",
    ]
    assert result.mismatches[1].expected == ["0x01"]
    assert (
        BuildRunnerResults.model_validate_json(
            results.model_dump_json(by_alias=True)
        )
        == results
    )


@pytest.mark.parametrize("missing", ["built", "mismatches"])
def test_build_results_require_build_keys(missing: str) -> None:
    """`buildtest` results without `built` or `mismatches` fail validation."""
    result = {
        "name": "t",
        "pass": True,
        "rejections": [],
        "built": 0,
        "mismatches": [],
    }
    del result[missing]
    with pytest.raises(ValidationError):
        BuildFixtureResult.model_validate(result)


def test_build_results_reject_negative_numbers() -> None:
    """A negative `built` count or mismatch index fails validation."""
    with pytest.raises(ValidationError):
        BuildFixtureResult.model_validate(
            {
                "name": "t",
                "pass": True,
                "rejections": [],
                "built": -1,
                "mismatches": [],
            }
        )
    with pytest.raises(ValidationError):
        Mismatch.model_validate(
            {"index": -1, "field": "gasUsed", "expected": "0x1", "got": "0x2"}
        )


def test_shared_results_read_build_output() -> None:
    """A harness that reads only `pass` can parse `buildtest` output too."""
    results = RunnerResults.model_validate_json(
        '[{"name": "t", "pass": true, "rejections": [], "built": 1,'
        ' "mismatches": []}]'
    )
    assert results.root[0].passed
    assert results.root[0].model_extra == {"built": 1, "mismatches": []}


def test_build_schema_uses_wire_names() -> None:
    """The `buildtest` schema adds its two keys to the shared ones."""
    schema = BuildRunnerResults.model_json_schema(by_alias=True)
    fixture_result = schema["$defs"]["BuildFixtureResult"]["properties"]
    assert set(fixture_result) == {
        "name",
        "pass",
        "rejections",
        "built",
        "mismatches",
    }
    mismatch = schema["$defs"]["Mismatch"]["properties"]
    assert set(mismatch) == {"index", "field", "expected", "got"}
