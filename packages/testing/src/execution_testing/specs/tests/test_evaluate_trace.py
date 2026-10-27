"""Test the traces of evaluation runs."""

from typing import List, Sequence

import pytest

from execution_testing.base_types import Address
from execution_testing.client_clis.cli_types import (
    TraceLine,
    TransactionTraces,
)
from execution_testing.vm import Op

from ..evaluate_trace import Trace, TraceError

A = Address(0xA)
B = Address(0xB)
LIBRARY = Address(0x11B)
CREATED = Address(0xC4EA7ED)


def line(
    op: Op | int,
    depth: int,
    stack: Sequence[int] = (),
    error: str | None = None,
) -> TraceLine:
    """Return a trace line that runs `op` at `depth`."""
    value = op if isinstance(op, int) else op.int()
    return TraceLine(
        pc=0,
        op=value,
        gas=0,
        mem_size=0,
        stack=list(stack),
        depth=depth,
        refund=0,
        op_name=str(op),
        error=error,
    )


def call(op: Op, address: Address, depth: int) -> TraceLine:
    """Return a call line to `address` (stack: ..., address, gas)."""
    return line(op, depth, stack=[int.from_bytes(address), 100_000])


def trace_of(
    lines: List[TraceLine], error: str | None = None, address: Address = A
) -> Trace:
    """Return the trace of a transaction to `address` with `lines`."""
    return Trace.from_transaction(
        TransactionTraces(traces=lines, error=error), address=address
    )


@pytest.fixture
def reentry_trace() -> Trace:
    """
    Return the trace of A -> B -> B (re-entry) -> back to B -> back to A,
    then A -> B again, where the second call to B reverts.
    """
    return trace_of(
        [
            line(Op.PUSH1, 1),
            call(Op.CALL, B, 1),
            line(Op.PUSH1, 2),
            call(Op.CALL, B, 2),
            line(Op.SSTORE, 3),
            line(Op.STOP, 3),
            line(Op.POP, 2),
            line(Op.STOP, 2),
            line(Op.POP, 1),
            call(Op.CALL, B, 1),
            line(Op.REVERT, 2, error="Revert"),
            line(Op.POP, 1),
            line(Op.STOP, 1),
        ]
    )


def test_frames_split_by_call(reentry_trace: Trace) -> None:
    """Test that each call is a frame, holding only its own lines."""
    frames = reentry_trace.frames
    assert [(f.depth, f.address) for f in frames] == [
        (1, A),
        (2, B),
        (3, B),
        (2, B),
    ]
    first_b = frames[1]
    # The frame continues after the call it made returns, without the
    # lines of that call.
    assert first_b.ops == [Op.PUSH1, Op.CALL, Op.POP, Op.STOP]
    assert len(frames[0]) == 6


def test_at_depth(reentry_trace: Trace) -> None:
    """Test that the frames at one depth are returned in order."""
    calls = reentry_trace.at_depth(2)
    assert len(calls) == 2
    assert calls[0].error is None
    assert calls[1].error == TraceError.REVERT
    assert reentry_trace.at_depth(1)[0].address == A
    assert reentry_trace.at_depth(4) == []


def test_at_address(reentry_trace: Trace) -> None:
    """Test that every frame at one address is returned, re-entries too."""
    assert [f.depth for f in reentry_trace.at_address(B)] == [2, 3, 2]
    assert [f.depth for f in reentry_trace.at_address(0xA)] == [1]


def test_addresses(reentry_trace: Trace) -> None:
    """Test that each address is listed once, in order of execution."""
    assert reentry_trace.addresses == [A, B]
    assert reentry_trace.at_depth(3)[0].addresses == [B]


def test_frame_subsets_itself(reentry_trace: Trace) -> None:
    """Test that a frame is its own only frame."""
    frame = reentry_trace.at_depth(3)[0]
    assert frame.at_depth(3) == [frame]
    assert frame.at_depth(2) == []
    assert frame.at_address(B) == [frame]
    assert frame.addresses == [B]


def test_failed_at(reentry_trace: Trace) -> None:
    """Test that only a frame whose last line raised has failed."""
    assert reentry_trace.failed_at is None
    assert reentry_trace.at_depth(2)[1].failed_at == Op.REVERT
    assert reentry_trace.at_depth(2)[0].failed_at is None


def test_transaction_error() -> None:
    """Test that a transaction reports its error and failing opcode."""
    trace = trace_of(
        [line(Op.ADD, 1, error="StackUnderflowError")],
        error="StackUnderflowError",
    )
    assert trace.error == TraceError.STACK_UNDERFLOW
    assert trace.failed_at == Op.ADD


def test_ops_and_membership(reentry_trace: Trace) -> None:
    """Test the opcodes, membership and counts of a trace."""
    assert Op.SSTORE in reentry_trace
    assert Op.SLOAD not in reentry_trace
    assert reentry_trace.count(Op.CALL) == 3
    assert len(reentry_trace) == 13


def test_undefined_opcode() -> None:
    """Test that a byte that is not an opcode has no opcode."""
    trace = trace_of(
        [line(0x0C, 1, error="InvalidOpcode")], error="InvalidOpcode"
    )
    assert trace.ops == []
    assert trace.error == TraceError.INVALID_OPCODE
    assert trace.failed_at is None


def test_delegatecall_executes_at_caller() -> None:
    """Test that a DELEGATECALL frame executes at its caller's address."""
    trace = trace_of(
        [
            call(Op.DELEGATECALL, LIBRARY, 1),
            line(Op.SSTORE, 2),
            line(Op.STOP, 2),
            line(Op.STOP, 1),
        ]
    )
    assert trace.at_depth(2)[0].address == A
    assert trace.at_address(LIBRARY) == []
    assert trace.addresses == [A]


@pytest.mark.parametrize(
    "pushed,address",
    [
        pytest.param(int.from_bytes(CREATED), CREATED, id="created"),
        pytest.param(0, None, id="failed"),
    ],
)
def test_create_address(pushed: int, address: Address | None) -> None:
    """Test that a CREATE frame takes the address its caller receives."""
    trace = trace_of(
        [
            line(Op.CREATE, 1, stack=[1, 0, 0]),
            line(Op.RETURN, 2),
            line(Op.POP, 1, stack=[pushed]),
            line(Op.STOP, 1),
        ]
    )
    assert trace.at_depth(2)[0].address == address
    assert trace.addresses == [A] + ([address] if address else [])


def test_transaction_without_lines() -> None:
    """Test that a transaction that ran no code has no frames."""
    trace = trace_of([])
    assert trace.frames == []
    assert trace.addresses == []
    assert trace.error is None
    assert trace.failed_at is None


def test_unknown_error() -> None:
    """Test that an unknown error name raises instead of a string."""
    with pytest.raises(ValueError, match="UnknownHalt"):
        TraceError.from_name("UnknownHalt")


def test_creating_transaction_address() -> None:
    """Test that a contract-creating transaction runs at its new address."""
    trace = trace_of([line(Op.PUSH1, 1), line(Op.RETURN, 1)], address=CREATED)
    assert trace.addresses == [CREATED]
