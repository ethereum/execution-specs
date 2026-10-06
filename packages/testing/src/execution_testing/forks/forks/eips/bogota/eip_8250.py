"""
EIP-8250: Keyed Nonces for Frame Transactions.

Replace the single sender nonce of a frame transaction with a bounded
set of nonce keys sharing one sequence number, the non-zero keys
selecting independent sequences held by a nonce manager system
contract.

https://eips.ethereum.org/EIPS/eip-8250
"""

from typing import List, Mapping, Sequence

from ethereum_rlp import rlp
from ethereum_types.numeric import U256

from execution_testing.base_types import Bytes

from ....base_fork import ActivationInstall, BaseFork

NONCE_MANAGER_ADDRESS = 0x0000000000000000000000000000000000008250
NONCE_MANAGER_BYTECODE = bytes.fromhex("60006000fd")


class EIP8250(BaseFork):
    """EIP-8250 class."""

    @classmethod
    def _frame_transaction_nonce_bytes(
        cls, nonce_keys: Sequence[int], nonce_seq: int
    ) -> List[Bytes]:
        """
        Price the encoding of the nonce key set followed by the nonce
        sequence as calldata.
        """
        return [
            Bytes(
                rlp.encode([U256(key) for key in nonce_keys])
                + rlp.encode(U256(nonce_seq))
            )
        ]

    @classmethod
    def pre_allocation(cls) -> Mapping:
        """Pre-allocate the nonce manager as installed at activation."""
        return {
            NONCE_MANAGER_ADDRESS: {
                "nonce": 1,
                "code": NONCE_MANAGER_BYTECODE,
            }
        } | super(EIP8250, cls).pre_allocation()  # type: ignore

    @classmethod
    def activation_code_installs(cls) -> Mapping:
        """
        Install the nonce manager when the fork activates: its code, and
        a nonce of at least one, keeping any balance it already held.
        """
        return {
            NONCE_MANAGER_ADDRESS: ActivationInstall(
                code=NONCE_MANAGER_BYTECODE, min_nonce=1
            ),
        } | super(EIP8250, cls).activation_code_installs()  # type: ignore
