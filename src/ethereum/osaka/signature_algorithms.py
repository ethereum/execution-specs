"""
All of the potential algorithms than can be used by EIP-7932
"Algorithmic" transactions are stored here. All of these
algorithms provide `gas_penalty: Uint`, `max_length: Uint` and
`verify(cls, signature_data: Bytes, hash: Bytes32) -> Address`

[EIP-7932]: https://eips.ethereum.org/EIPS/eip-7932
"""

from typing import Union

from ethereum_types.bytes import Bytes, Bytes32
from ethereum_types.numeric import U8, Uint

from .fork_types import Address


class NullAlgorithm:
    """
    The Null algorithm added by EIP-7932
    """

    gas_penalty: Uint = Uint(0)
    max_length: Uint = Uint(0)

    @classmethod
    def verify(cls, _signature_data: Bytes, _hash: Bytes32) -> Address:
        """
        Verify given `sig_data: Bytes` and `hash: Bytes32` and return
        either the signers address or `0x0`
        """
        raise Exception(
            "The NULL algorithm requires special handling "
            + "and cannot call `verify`"
        )


EIP_7932_Algorithm = Union[NullAlgorithm]


def algorithm_from_type(type: U8) -> EIP_7932_Algorithm:
    """
    Return the known algorithm class from a type, if
    no algorithm is known an `Exception` is generated.
    """
    match type:
        case 0xFF:
            return NullAlgorithm()

        case _:
            raise Exception(f"Unknown algorithm type : 0x{type:x}")
