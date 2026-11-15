"""
Execution traces of the transactions of an evaluation run.

A `Trace` holds the EIP-3155 trace lines that the transition tool emits for
one transaction, or for one call frame of it. The frames of a transaction
are found by `at_depth` and `at_address`, each one a `Trace` of its own.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List

from execution_testing.base_types import Address
from execution_testing.client_clis.cli_types import (
    TraceLine,
    TransactionTraces,
)
from execution_testing.vm import Op

OPCODES_BY_VALUE: Dict[int, Op] = {op.int(): op for op in Op}
"""Opcode of each byte value that has one."""


class TraceError(Enum):
    """
    Error that stopped a call frame or a transaction.

    The values are the names of the exceptions of the specification that the
    transition tool reports in its traces.
    """

    REVERT = "Revert"
    OUT_OF_GAS = "OutOfGasError"
    STACK_UNDERFLOW = "StackUnderflowError"
    STACK_OVERFLOW = "StackOverflowError"
    STACK_DEPTH_LIMIT = "StackDepthLimitError"
    INVALID_OPCODE = "InvalidOpcode"
    INVALID_JUMP_DESTINATION = "InvalidJumpDestError"
    WRITE_IN_STATIC_CONTEXT = "WriteInStaticContext"
    OUT_OF_BOUNDS_READ = "OutOfBoundsRead"
    INVALID_PARAMETER = "InvalidParameter"
    INVALID_CONTRACT_PREFIX = "InvalidContractPrefix"
    ADDRESS_COLLISION = "AddressCollision"
    KZG_PROOF = "KZGProofError"

    @classmethod
    def from_name(cls, name: str) -> "TraceError":
        """Return the error with the exception name `name`."""
        try:
            return cls(name)
        except ValueError:
            raise ValueError(
                f"unknown trace error `{name}`: add it to `TraceError`"
            ) from None


def _stack_address(line: TraceLine, position: int) -> Address | None:
    """Return the address at `position` from the top of the stack."""
    if len(line.stack) < position:
        return None
    value = line.stack[-position]
    return None if value is None else Address(value)


@dataclass(kw_only=True)
class Trace:
    """
    Trace of a transaction, or of one call frame of it.

    The trace of a transaction holds all of its lines. A frame holds the
    lines that one call executed at its own depth, so the lines of the calls
    it made are in frames of their own, and two calls to the same contract
    are two frames. The transition tool does not trace precompiles, so a call
    to a precompile has no frame: its result is on the caller's stack.
    """

    lines: List[TraceLine]
    """Trace lines, in the order they executed."""

    depth: int | None = None
    """Depth of the frame (1 for the top frame), `None` for a transaction."""

    address: Address | None = None
    """
    Address the frame executed at: its own address for a `CALL` or
    `STATICCALL`, its caller's for a `DELEGATECALL` or `CALLCODE`, and
    `None` for a `CREATE` or `CREATE2` that failed.
    """

    transaction_error: str | None = None
    """Error the transaction reports (only set on a transaction trace)."""

    frames: List["Trace"] = field(default_factory=list, repr=False)
    """Frames of a transaction, in the order they started."""

    @classmethod
    def from_transaction(
        cls, traces: TransactionTraces, *, address: Address | None
    ) -> "Trace":
        """
        Return the trace of a transaction that started at `address`.

        A frame starts each time execution enters a depth from the depth
        above it and keeps the lines at that depth until it returns.
        """
        frames: List[Trace] = []
        open_frames: List[Trace] = []
        creations: Dict[int, Trace] = {}
        for line in traces.traces:
            # Leave the frames that returned.
            while open_frames and (open_frames[-1].depth or 0) > line.depth:
                open_frames.pop()
            if open_frames and open_frames[-1].depth == line.depth:
                frame = open_frames[-1]
                created = creations.pop(id(frame), None)
                if created is not None:
                    # Back in the frame that ran CREATE / CREATE2, which
                    # pushed the address it created (0 on failure).
                    created_address = _stack_address(line, 1)
                    if created_address != Address(0):
                        created.address = created_address
            else:
                parent = open_frames[-1] if open_frames else None
                frame = cls(lines=[], depth=line.depth)
                if parent is None:
                    frame.address = address
                else:
                    call = parent.lines[-1]
                    if call.op in (Op.CALL.int(), Op.STATICCALL.int()):
                        frame.address = _stack_address(call, 2)
                    elif call.op in (
                        Op.CALLCODE.int(),
                        Op.DELEGATECALL.int(),
                    ):
                        frame.address = parent.address
                    elif call.op in (Op.CREATE.int(), Op.CREATE2.int()):
                        creations[id(parent)] = frame
                frames.append(frame)
                open_frames.append(frame)
            frame.lines.append(line)
        return cls(
            lines=list(traces.traces),
            address=address,
            transaction_error=traces.error,
            frames=frames,
        )

    def _frames(self) -> List["Trace"]:
        """Return the frames of the trace (a frame is its only frame)."""
        return self.frames if self.depth is None else [self]

    def __len__(self) -> int:
        """Return the number of trace lines."""
        return len(self.lines)

    def __contains__(self, op: object) -> bool:
        """Return whether `op` ran in the trace."""
        return op in self.ops

    @property
    def ops(self) -> List[Op]:
        """
        Opcodes that ran, in order.

        A byte that is not an opcode is left out.
        """
        return [
            OPCODES_BY_VALUE[line.op]
            for line in self.lines
            if line.op in OPCODES_BY_VALUE
        ]

    def count(self, op: Op) -> int:
        """Return the number of times `op` ran in the trace."""
        return self.ops.count(op)

    def at_depth(self, depth: int) -> List["Trace"]:
        """Return the frames at `depth` (1 for the top frame)."""
        return [frame for frame in self._frames() if frame.depth == depth]

    def at_address(self, address: Address | int | str) -> List["Trace"]:
        """Return the frames that executed at `address`."""
        address = Address(address)
        return [frame for frame in self._frames() if frame.address == address]

    @property
    def addresses(self) -> List[Address]:
        """
        Addresses that frames executed at, in the order they first did.

        As in `at_address`, a `DELEGATECALL` or `CALLCODE` frame executes at
        its caller's address, so the address of the code it ran is not
        listed. A frame that ran initcode (a `CREATE`, a `CREATE2` or a
        contract-creating transaction) is listed at the address it created;
        a `CREATE` or `CREATE2` that failed has no address.
        """
        addresses: List[Address] = []
        for frame in self._frames():
            if frame.address is not None and frame.address not in addresses:
                addresses.append(frame.address)
        return addresses

    @property
    def error(self) -> TraceError | None:
        """
        Error that stopped the frame or transaction (`None` if none did).

        A frame fails when its last line raised. A transaction reports its
        own error, which a failing top frame causes.
        """
        if self.depth is None:
            name = self.transaction_error
        else:
            name = self.lines[-1].error if self.lines else None
        return None if name is None else TraceError.from_name(name)

    @property
    def failed_at(self) -> Op | None:
        """
        Opcode that stopped the frame, or the top frame of a transaction.

        `None` when the frame did not fail, failed at a byte that is not an
        opcode, or the transaction has no frames.
        """
        frames = self.at_depth(1) if self.depth is None else [self]
        if not frames or not frames[0].lines:
            return None
        last = frames[0].lines[-1]
        if last.error is None:
            return None
        return OPCODES_BY_VALUE.get(last.op)
