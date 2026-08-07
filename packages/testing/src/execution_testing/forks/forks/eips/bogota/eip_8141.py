"""
EIP-8141: Frame Transaction.

Add a new transaction type constructed from a series of frames,
abstractly defining validity conditions and gas payment.

https://eips.ethereum.org/EIPS/eip-8141
"""

from typing import List, Mapping

from ....base_fork import BaseFork

EXPIRY_VERIFIER_ADDRESS = 0x0000000000000000000000000000000000008141
EXPIRY_VERIFIER_BYTECODE = bytes.fromhex(
    "60083614600a575f5ffd5b5f3560c01c4211601657005b5f5ffd"
)


class EIP8141(BaseFork):
    """EIP-8141 class."""

    @classmethod
    def tx_types(cls) -> List[int]:
        """Frame transactions (type 6) are introduced."""
        return super(EIP8141, cls).tx_types() + [6]

    @classmethod
    def pre_allocation(cls) -> Mapping:
        """Pre-allocate the expiry verifier contract."""
        return {
            EXPIRY_VERIFIER_ADDRESS: {
                # EIP-8141 installs only the runtime code at
                # activation; the nonce stays zero.
                "nonce": 0,
                "code": EXPIRY_VERIFIER_BYTECODE,
            }
        } | super(EIP8141, cls).pre_allocation()  # type: ignore

    @classmethod
    def pre_allocation_blockchain(cls) -> Mapping:
        """Pre-allocate the expiry verifier contract."""
        return {
            EXPIRY_VERIFIER_ADDRESS: {
                # EIP-8141 installs only the runtime code at
                # activation; the nonce stays zero.
                "nonce": 0,
                "code": EXPIRY_VERIFIER_BYTECODE,
            }
        } | super(EIP8141, cls).pre_allocation_blockchain()  # type: ignore
