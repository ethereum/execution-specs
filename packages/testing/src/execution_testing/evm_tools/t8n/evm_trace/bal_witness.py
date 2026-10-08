"""
A witness of the storage slots execution accessed, for checking the BAL.

The BAL is built from the state tracker's read and write sets, so a slot the
tracker forgets is missing from those sets too. This tracer observes slots
from the trace stream instead, recording the slots each `SLOAD` or `SSTORE`
started on and the slots it finished on. `check_bal_access_witness` in
`execution_testing.specs.invariants` checks the BAL against both.
"""

from dataclasses import dataclass
from typing import Any, FrozenSet, Optional, Set, Tuple

from ethereum.trace import EvmTracer, OpEnd, OpException, OpStart, TraceEvent

SlotAccess = Tuple[int, int]
"""An accessed storage slot as `(account address, slot key)`."""

STORAGE_OPS = frozenset({"SLOAD", "SSTORE"})


@dataclass(frozen=True)
class BalWitness:
    """The storage slots a run started and finished accessing."""

    started: FrozenSet[SlotAccess] = frozenset()
    ended: FrozenSet[SlotAccess] = frozenset()


class BalWitnessTracer(EvmTracer):
    """Collect the storage slots each `SLOAD` and `SSTORE` touches."""

    def __init__(self) -> None:
        self._started: Set[SlotAccess] = set()
        self._ended: Set[SlotAccess] = set()
        self._pending: Optional[SlotAccess] = None

    def __call__(self, evm: Any, event: TraceEvent) -> None:
        """Record the slot of a storage op when it starts and ends."""
        if isinstance(event, OpStart):
            self._pending = None
            # The slot key is on top of the stack, and `current_target`
            # (on `evm.message` in older forks) is the storage owner under
            # DELEGATECALL and CALLCODE too. An op on an empty stack fails
            # before it touches storage.
            if event.op.name in STORAGE_OPS and evm.stack:
                message = getattr(evm, "message", evm)
                target = int.from_bytes(message.current_target, "big")
                self._pending = (target, int(evm.stack[-1]))
                self._started.add(self._pending)
        elif isinstance(event, OpEnd):
            if self._pending is not None:
                self._ended.add(self._pending)
            self._pending = None
        elif isinstance(event, OpException):
            self._pending = None

    def witness(self) -> BalWitness:
        """Return the slots observed so far."""
        return BalWitness(frozenset(self._started), frozenset(self._ended))
