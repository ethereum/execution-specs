"""
Types shared by the stateless validation of every fork.
"""

from dataclasses import dataclass
from typing import Annotated, Tuple, final

from ethereum_types.bytes import Bytes
from ethereum_types.frozen import slotted_freezable

from ethereum.utils.ssz import (
    SszContainer,
    byte_list,
    progressive_list,
    ssz_list,
)

MAX_WITNESS_HEADERS = 256
MAX_BYTES_PER_CODE = 2**16
MAX_BYTES_PER_HEADER = 2**10
MAX_BYTES_PER_WITNESS_NODE = 2**10


@final
@slotted_freezable
@dataclass
class ExecutionWitness(SszContainer):
    """
    Execution witness data for stateless validation.
    """

    state: Annotated[
        Tuple[Annotated[Bytes, byte_list(MAX_BYTES_PER_WITNESS_NODE)], ...],
        progressive_list(),
    ]
    """
    Hashed trie-node preimages needed during execution and state-root
    recomputation.
    """

    codes: Annotated[
        Tuple[Annotated[Bytes, byte_list(MAX_BYTES_PER_CODE)], ...],
        progressive_list(),
    ]
    """
    Contract-code preimages (created or accessed) needed during execution.
    """

    headers: Annotated[
        Tuple[Annotated[Bytes, byte_list(MAX_BYTES_PER_HEADER)], ...],
        ssz_list(MAX_WITNESS_HEADERS),
    ]
    """
    RLP-encoded block headers used for pre-state and ``BLOCKHASH`` correctness
    proofs. This may trend toward empty EIP-7709.
    """
