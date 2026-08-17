"""
The `engine_notifyBlockAccessListV1` method.

The consensus layer forwards a block access list the moment its
sidecar passes gossip validation, without waiting for the payload
envelope. Delivered lists wait in the engine keyed by block hash until
[`new_payload_v5`] pairs them with their payload; an early list also
lets a client prefetch the state it declares, which this reference
implementation does not model.

[`new_payload_v5`]:
    ref:ethereum.forks.amsterdam.execution_engine.new_payload.new_payload_v5
"""

from ethereum_rlp import rlp
from ethereum_rlp.exceptions import DecodingError
from ethereum_types.bytes import Bytes

from ethereum.crypto.hash import Hash32
from ethereum.exceptions import InvalidEngineParamsError

from ..block_access_lists import BlockAccessList
from .types import ExecutionEngine


def notify_block_access_list_v1(
    engine: ExecutionEngine,
    block_access_list: Bytes,
    block_hash: Hash32,
) -> None:
    """
    `engine_notifyBlockAccessListV1`: deliver a block access list ahead
    of its payload.

    A structurally undecodable list is an invalid parameter. Whether
    the list matches the payload is settled when the payload arrives:
    the block hash commits to the list's keccak, so a mismatched list
    simply fails that check.
    """
    try:
        rlp.decode_to(BlockAccessList, block_access_list)
    except DecodingError as e:
        # A structurally undecodable block access list is an invalid
        # parameter, not an invalid block.
        raise InvalidEngineParamsError(f"blockAccessList: {e}") from e

    engine.block_access_lists[block_hash] = block_access_list
