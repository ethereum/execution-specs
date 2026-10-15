"""Public mempool admission expectations of transactions."""

from typing import Tuple

from execution_testing.base_types import Address, CamelModel

from .transaction_types import Transaction


class MempoolTransaction(CamelModel):
    """
    A transaction sent to a client's public mempool, together with
    whether the mempool must admit it.
    """

    tx: Transaction
    accepted: bool
    in_block: bool | None = None
    """
    Whether the transaction is placed in the block filled from the
    mempool test; unset applies the default rule of `MempoolTest`.
    """
    reason: str | None = None
    """The mempool rule the expectation pins, logged with the outcome."""

    @property
    def pool_key(self) -> Tuple[Address | None, Tuple[int, ...], int]:
        """
        Return the identity a mempool replaces transactions by: the
        sender, its nonce keys and the nonce.
        """
        nonce_keys = tuple(int(key) for key in self.tx.nonce_keys or ())
        return (self.tx.sender, nonce_keys, int(self.tx.nonce))
