"""
Tests that a partial opcode trace is discarded rather than reported.

`debug_traceBlockByHash` returns one entry per transaction. When a single
transaction's trace fails, its entry carries an error instead of a result.
Aggregating what remains yields a well-formed tally that is silently short by
whole transactions -- which then fails a downstream opcode-count assertion that
has nothing to do with tracing.

Observed while filling the compute benchmarks: a 300M block of 18 transactions
executed fully (299.998M gas used, all 18 present) but the tally came back
exactly 94,698 identity calls short, which is precisely one transaction's
worth. The same case passes when re-run.
"""

from execution_testing.base_types import Hash
from execution_testing.client_clis.client_backend import (
    ClientBackend,
    _opcode_count_from_js_tracer,
    _opcode_count_from_struct_logs,
)

BLOCK_HASH = Hash("0x" + "11" * 32)


def _js(counts: dict[str, int]) -> dict:
    """A JS-tracer entry for one successfully traced transaction."""
    return {"result": dict(counts)}


def _js_error() -> dict:
    """An entry for a transaction whose trace failed: no ``result`` key."""
    return {"txHash": "0x" + "ab" * 32, "error": "execution timeout"}


def _struct(ops: list[str]) -> dict:
    """A struct-log entry for one successfully traced transaction."""
    return {"result": {"structLogs": [{"op": op} for op in ops]}}


def test_js_tracer_reports_covered_transactions() -> None:
    """Every usable entry counts toward coverage."""
    opcode_count, covered = _opcode_count_from_js_tracer(
        [_js({"MSTORE": 5}), _js({"MSTORE": 7})]
    )
    assert covered == 2
    assert sum(opcode_count.root.values()) == 12


def test_js_tracer_errored_entry_does_not_count_as_covered() -> None:
    """An entry carrying an error contributes nothing, including coverage."""
    opcode_count, covered = _opcode_count_from_js_tracer(
        [_js({"MSTORE": 5}), _js_error(), _js({"MSTORE": 5})]
    )
    assert covered == 2, "the errored entry must not count as covered"
    assert sum(opcode_count.root.values()) == 10


def test_struct_logs_report_covered_transactions() -> None:
    """The struct-log path reports coverage the same way."""
    opcode_count, covered = _opcode_count_from_struct_logs(
        [_struct(["MSTORE", "MLOAD"]), _struct(["MSTORE"])]
    )
    assert covered == 2
    assert sum(opcode_count.root.values()) == 3


def test_struct_logs_entry_without_logs_is_not_covered() -> None:
    """An entry with no struct logs is a failed trace, not an empty one."""
    _, covered = _opcode_count_from_struct_logs(
        [_struct(["MSTORE"]), {"txHash": "0x00", "error": "boom"}]
    )
    assert covered == 1


def test_complete_coverage_is_returned() -> None:
    """A tally covering every transaction is used as-is."""
    opcode_count, covered = _opcode_count_from_js_tracer(
        [_js({"MSTORE": 5}), _js({"MSTORE": 5})]
    )
    assert (
        ClientBackend._checked_opcode_count(
            opcode_count, covered, 2, BLOCK_HASH
        )
        is opcode_count
    )


def test_partial_coverage_is_discarded() -> None:
    """
    A tally missing a transaction is dropped, not returned.

    Returning it is what turns a tracing hiccup into a bogus count-mismatch
    failure elsewhere. Dropping it leaves the fixture valid but without an
    opcode count, which is recoverable by re-running.
    """
    opcode_count, covered = _opcode_count_from_js_tracer(
        [_js({"MSTORE": 5}), _js_error(), _js({"MSTORE": 5})]
    )
    assert covered == 2
    assert (
        ClientBackend._checked_opcode_count(
            opcode_count, covered, 3, BLOCK_HASH
        )
        is None
    )


def test_missing_transaction_count_keeps_previous_behaviour() -> None:
    """Without a transaction count there is nothing to check against."""
    opcode_count, covered = _opcode_count_from_js_tracer(
        [_js({"MSTORE": 5}), _js_error()]
    )
    assert (
        ClientBackend._checked_opcode_count(
            opcode_count, covered, None, BLOCK_HASH
        )
        is opcode_count
    )


def test_partial_coverage_warns_loudly(caplog) -> None:  # type: ignore[no-untyped-def]
    """The discard must be visible: it is the only signal of the loss."""
    opcode_count, covered = _opcode_count_from_js_tracer(
        [_js({"MSTORE": 5}), _js_error(), _js({"MSTORE": 5})]
    )
    with caplog.at_level("WARNING"):
        ClientBackend._checked_opcode_count(
            opcode_count, covered, 3, BLOCK_HASH
        )
    assert any(
        "covered 2 of 3 transactions" in record.message
        for record in caplog.records
    ), f"expected a warning naming the shortfall, got {caplog.records}"
