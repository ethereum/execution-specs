"""
Stateless validation types.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from ethereum_types.bytes import Bytes
from ethereum_types.frozen import slotted_freezable
from ethereum_types.numeric import Uint

from .state_tracker import BlockState


@slotted_freezable
@dataclass
class ExecutionWitness:
    """
    Execution witness data for stateless validation.
    """

    state: Tuple[Bytes, ...]
    """
    Hashed trie-node preimages needed during execution and state-root
    recomputation.
    """

    codes: Tuple[Bytes, ...]
    """
    Contract-code preimages (created or accessed) needed during execution.
    """

    headers: Tuple[Bytes, ...]
    """
    RLP-encoded block headers used for pre-state and ``BLOCKHASH`` correctness
    proofs. This may trend toward empty EIP-7709.
    """


@dataclass
class ExecutionWitnessBuilder:
    """
    Mutable accumulator for execution witness data during block execution.
    """

    blockchain_headers: List[Bytes] = field(default_factory=list)
    state: List[Bytes] = field(default_factory=list)
    codes: List[Bytes] = field(default_factory=list)


def build_execution_witness(
    builder: ExecutionWitnessBuilder,
    block_state: BlockState,
) -> ExecutionWitness:
    """
    Build the execution witness from the accumulated builder data.

    Sort state and codes lexicographically, headers by block number
    ascending.
    """
    ancestor_headers = get_witness_ancestors(
        builder.blockchain_headers,
        block_state.oldest_ancestor_offset,
    )
    return ExecutionWitness(
        state=tuple(sorted(builder.state)),
        codes=tuple(sorted(builder.codes)),
        headers=tuple(ancestor_headers),
    )


def get_witness_ancestors(
    block_headers: List[Bytes],
    oldest_ancestor_offset: Optional[Uint],
) -> List[Bytes]:
    """
    Collect RLP-encoded ancestor headers from ``oldest_ancestor_offset``
    blocks back onward.

    Parameters
    ----------
    block_headers :
        RLP-encoded headers.
    oldest_ancestor_offset :
        Offset from the current block to the oldest ancestor accessed
        during execution, or ``None`` if no ancestor was accessed.

    """
    if oldest_ancestor_offset is None:
        return []
    return list(block_headers[-int(oldest_ancestor_offset) :])
