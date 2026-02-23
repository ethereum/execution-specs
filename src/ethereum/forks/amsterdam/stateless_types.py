"""
Stateless validation types.
"""

from dataclasses import dataclass, field
from typing import List, Tuple

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes
from ethereum_types.frozen import slotted_freezable

from .blocks import Header


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

    state: List[Bytes] = field(default_factory=list)
    codes: List[Bytes] = field(default_factory=list)
    headers: List[Header] = field(default_factory=list)


def build_execution_witness(
    builder: ExecutionWitnessBuilder,
) -> ExecutionWitness:
    """
    Build the execution witness from the accumulated builder data.

    Sort state and codes lexicographically, headers by block number
    ascending.
    """
    return ExecutionWitness(
        state=tuple(sorted(builder.state)),
        codes=tuple(sorted(builder.codes)),
        headers=tuple(
            rlp.encode(h)
            for h in sorted(builder.headers, key=lambda h: h.number)
        ),
    )
