"""
EIP-8250: Keyed Nonces for Frame Transactions.

Replace the single sender nonce of a frame transaction with a bounded
set of nonce keys sharing one sequence number, the non-zero keys
selecting independent sequences held by a nonce manager contract.

https://eips.ethereum.org/EIPS/eip-8250
"""

from dataclasses import replace
from typing import List, Mapping, Sequence

from ethereum_rlp import rlp
from ethereum_types.numeric import U256

from execution_testing.base_types import Bytes

from ....base_fork import BaseFork
from ....gas_costs import GasCosts

NONCE_MANAGER_ADDRESS = 0x8250968C12E01A19D6F667B9B2F3B3A4D0E51CB7
NONCE_MANAGER_BYTECODE = bytes.fromhex("60006000fd")


class EIP8250(BaseFork):
    """EIP-8250 class."""

    @classmethod
    def gas_costs(cls) -> GasCosts:
        """
        Add the keyed nonce access cost: EIP-8038's cold storage access
        plus storage write, which the framework models together as
        `COLD_STORAGE_WRITE`.
        """
        parent = super(EIP8250, cls).gas_costs()
        return replace(parent, KEYED_NONCE_ACCESS=parent.COLD_STORAGE_WRITE)

    @classmethod
    def _frame_transaction_nonce_access_cost(
        cls, nonce_keys: Sequence[int]
    ) -> int:
        """
        Charge the read and write of each non-zero key's nonce manager
        slot. The legacy key set uses the account nonce instead.
        """
        if list(nonce_keys) == [0]:
            return 0
        return len(nonce_keys) * cls.gas_costs().KEYED_NONCE_ACCESS

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
        """Pre-allocate the nonce manager contract."""
        return {
            NONCE_MANAGER_ADDRESS: {
                "nonce": 1,
                "code": NONCE_MANAGER_BYTECODE,
            }
        } | super(EIP8250, cls).pre_allocation()  # type: ignore

    @classmethod
    def pre_allocation_blockchain(cls) -> Mapping:
        """Pre-allocate the nonce manager contract."""
        return {
            NONCE_MANAGER_ADDRESS: {
                "nonce": 1,
                "code": NONCE_MANAGER_BYTECODE,
            }
        } | super(EIP8250, cls).pre_allocation_blockchain()  # type: ignore
