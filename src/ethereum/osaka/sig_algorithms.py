from ethereum_types.frozen import slotted_freezable
from ethereum_types.bytes import Bytes, Bytes32
from ethereum_types.numeric import U8

from dataclasses import dataclass
from typing import Union

from .fork_types import Address

@slotted_freezable
@dataclass
class NullAlgorithm:
    """
    The Null algorithm added by EIP-7932
    """

    gas_penalty = 0
    max_length = 0
    
    @classmethod
    def verify(cls, _sig_data: Bytes, _hash: Bytes32) -> Address:
        """
        Verify given `sig_data: Bytes` and `hash: Bytes32` and return
        either the signers address or `0x0`
        """
        raise Exception(f"The NULL algorithm requires special handling and cannot call `verify`")


EIP_7932_Algorithm = Union[
    NullAlgorithm
]

def algorithm_from_type(type: U8, **kwargs) -> EIP_7932_Algorithm:
    match type:
        case 0xff:
            return NullAlgorithm(**kwargs)
        
        case _:
            raise Exception(f"Unknown algorithm type : 0x{type:x}")
