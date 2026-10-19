"""Tests for printing transition tool traces."""

import io

import pytest
from rich.console import Console

from execution_testing.client_clis.cli_types import (
    TraceLine,
    Traces,
    TransactionTraces,
)


def _make_trace_line(**overrides: object) -> TraceLine:
    """Create a TraceLine with sensible defaults."""
    defaults = {
        "pc": 0,
        "op": 0x60,
        "gas": 0x5F5E100,
        "gas_cost": 0x3,
        "mem_size": 0,
        "stack": [],
        "depth": 1,
        "refund": 0,
        "op_name": "PUSH1",
    }
    defaults.update(overrides)
    return TraceLine.model_validate(defaults)


def _render(traces: TransactionTraces) -> list[str]:
    """Render the trace table and return its non-empty lines."""
    console = Console(file=io.StringIO(), width=200)
    console.print(traces.table())
    output = console.file.getvalue()  # type: ignore[attr-defined]
    return [line.rstrip() for line in output.splitlines() if line.strip()]


def test_one_row_per_step() -> None:
    """Each execution step is a single row, after the header."""
    traces = TransactionTraces(
        traces=[
            _make_trace_line(pc=0),
            _make_trace_line(pc=2, stack=["0x1"]),
            _make_trace_line(
                pc=4, op=0x00, op_name="STOP", gas_cost=0, stack=["0x1", "0x2"]
            ),
        ]
    )
    lines = _render(traces)

    assert len(lines) == 2 + 3
    assert lines[0].split() == [
        "Step",
        "PC",
        "Op",
        "Gas",
        "Cost",
        "Depth",
        "Stack",
    ]
    assert lines[-1].split() == [
        "2",
        "4",
        "STOP",
        "100000000",
        "0",
        "1",
        "0x2",
        "0x1",
    ]


def test_stack_shows_top_items_first() -> None:
    """The topmost stack values come first, the rest are elided."""
    stack = [hex(i) for i in range(6)]
    traces = TransactionTraces(traces=[_make_trace_line(stack=stack)])

    row = _render(traces)[-1]

    assert row.endswith("0x5 0x4 0x3 0x2 ...")


def test_long_stack_values_are_shortened() -> None:
    """Long stack values keep their start and end only."""
    value = "0x" + "ab" * 32
    traces = TransactionTraces(traces=[_make_trace_line(stack=[value])])

    row = _render(traces)[-1]

    assert value not in row
    assert row.endswith("0xababa...bababab")


def test_nested_calls_are_indented() -> None:
    """Op names are indented by call depth."""
    traces = TransactionTraces(
        traces=[
            _make_trace_line(op=0xF1, op_name="CALL"),
            _make_trace_line(depth=2),
        ]
    )
    lines = _render(traces)
    op_column = lines[0].index("Op")

    assert lines[-2][op_column:].startswith("CALL")
    assert lines[-1][op_column:].startswith("  PUSH1")


def test_error_column_only_when_needed() -> None:
    """The error column is added only if a step has an error."""
    ok = TransactionTraces(traces=[_make_trace_line()])
    failed = TransactionTraces(traces=[_make_trace_line(error="out of gas")])

    assert "Error" not in _render(ok)[0]
    assert "Error" in _render(failed)[0]
    assert _render(failed)[-1].endswith("out of gas")


def test_print_includes_summary(capsys: pytest.CaptureFixture[str]) -> None:
    """Printing all traces adds the transaction header and gas used."""
    traces = Traces(
        root=[
            TransactionTraces(
                traces=[_make_trace_line()], gas_used=0x5208, output="0x01"
            )
        ]
    )

    traces.print()

    output = capsys.readouterr().out
    assert "Transaction 0:" in output
    assert "PUSH1" in output
    assert "gas used: 21000, output: 0x01" in output


def test_error_is_not_read_as_markup() -> None:
    """Square brackets in an error message are printed as is."""
    traces = TransactionTraces(
        traces=[_make_trace_line(error="bad jump [pc 3]")]
    )

    assert _render(traces)[-1].endswith("bad jump [pc 3]")
