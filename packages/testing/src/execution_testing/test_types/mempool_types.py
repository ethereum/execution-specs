"""Public mempool admission expectations of transactions."""

from typing import Tuple

from execution_testing.base_types import Address, CamelModel

from .transaction_types import NetworkWrappedTransaction, Transaction


class MempoolTransaction(CamelModel):
    """
    A transaction sent to a client's public mempool, together with
    whether the mempool must admit it.
    """

    tx: Transaction | NetworkWrappedTransaction
    accepted: bool | None
    """
    Whether the mempool must admit the transaction. `None` leaves the
    verdict to mempool policy, for a transaction valid in a block that
    the policy may still refuse.
    """
    in_block: bool | None = None
    """
    Whether the transaction is placed in the block filled from the
    mempool test; unset applies the default rule of `MempoolTest`.
    """
    reason: str | None = None
    """The mempool rule the expectation pins, logged with the outcome."""

    @property
    def unwrapped(self) -> Transaction:
        """Return the transaction without its network wrapper."""
        if isinstance(self.tx, NetworkWrappedTransaction):
            return self.tx.tx
        return self.tx

    @property
    def pool_key(self) -> Tuple[Address | None, int]:
        """
        Return the identity a mempool replaces transactions by: the
        sender and the nonce.
        """
        return (self.unwrapped.sender, int(self.unwrapped.nonce))
