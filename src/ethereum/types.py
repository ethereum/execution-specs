"""
Shared account and address types used across all forks.
"""

from dataclasses import dataclass

from ethereum_types.bytes import Bytes20
from ethereum_types.frozen import slotted_freezable
from ethereum_types.numeric import U256, Uint

from ethereum.crypto.hash import Hash32, keccak256

Address = Bytes20
Root = Hash32

EMPTY_CODE_HASH = keccak256(b"")


@slotted_freezable
@dataclass
class Account:
    """
    State associated with an address.
    """

    nonce: Uint
    balance: U256
    code_hash: Hash32


EMPTY_ACCOUNT = Account(
    nonce=Uint(0),
    balance=U256(0),
    code_hash=EMPTY_CODE_HASH,
)
