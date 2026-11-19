"""Block-level verification rules for transition tool results."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from execution_testing.client_clis import LazyAlloc, Result
from execution_testing.test_types import Alloc


@dataclass
class BlockVerification(ABC):
    """
    Base class for block-level verification rules.

    Each rule inspects the transition tool result and the
    post-state for a single block and raises on failure. Add
    new rules by subclassing and implementing ``verify``.
    """

    @abstractmethod
    def verify(
        self,
        *,
        result: Result,
        block_number: int,
        alloc: Alloc | LazyAlloc | None,
    ) -> None:
        """
        Verify the block, raise on failure.

        ``alloc`` is the block's post-state, unmaterialized when
        lazy, or ``None`` where the backend returns none
        (``fill-stateful``).
        """
        ...


@dataclass
class NoTraceErrors(BlockVerification):
    """
    Verify that no trace line contains an error.

    Catches silent subcall failures, out of gas,
    invalid jumps, and stack errors.
    """

    def verify(
        self,
        *,
        result: Result,
        block_number: int,
        alloc: Alloc | LazyAlloc | None,
    ) -> None:
        """Raise if any trace line has an error."""
        del alloc
        if result.traces is None:
            return
        for tx_idx, tx in enumerate(result.traces.root):
            for step, line in enumerate(tx.traces):
                if line.error is not None:
                    raise Exception(
                        f"Trace error in block "
                        f"{block_number}, "
                        f"tx {tx_idx}, "
                        f"step {step} "
                        f"(pc={line.pc}, "
                        f"op={line.op_name}, "
                        f"depth={line.depth}): "
                        f"{line.error}"
                    )


@dataclass
class ReceiptStatusExpected(BlockVerification):
    """
    Verify all transaction receipts have the expected
    status. Default expects success (status=1).

    Catches silent OOG failures that roll back state
    and invalidate benchmarks.
    """

    status: int = 1

    def verify(
        self,
        *,
        result: Result,
        block_number: int,
        alloc: Alloc | LazyAlloc | None,
    ) -> None:
        """Raise if any receipt status mismatches."""
        del alloc
        for i, receipt in enumerate(result.receipts):
            if receipt.status is not None and (
                int(receipt.status) != self.status
            ):
                raise Exception(
                    f"Transaction {i} in block "
                    f"{block_number} has receipt "
                    f"status {int(receipt.status)}, "
                    f"expected {self.status}."
                )
