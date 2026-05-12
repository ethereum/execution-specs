"""
[EIP-8237] introduces a [SHA2-256] commitment over a fixed subset of fields
that the consensus layer also observes. The same value is embedded in the
header (covered by the block hash) and in the `ExecutionPayload` delivered
through the Engine API; the state transition function rejects the block
unless the recomputed value equals `header.partial_header_hash`. Because
the block hash RLP-covers that field, a faithful payload-to-block
conversion makes the EIP's `payload == expected == header` chain reduce to
the single header check performed here.

Byte layout, in order: `parent_hash || prev_randao || gas_limit ||
timestamp || withdrawals || parent_beacon_block_root || slot_number ||
execution_requests`. Integers are little-endian `uint64`; each
`Withdrawal` contributes `index || validator_index || address || amount`
(44 bytes); lists are raw concatenation; `execution_requests` follow the
[EIP-7685] type-prefixed layout. Empty CL slots produce no
execution-layer block at all (the EL has no notion of an "empty block");
the chain is linked through `parent_hash` and `slot_number` may jump by
more than one between adjacent blocks.

The choice of SHA2-256 over a pinned byte layout (rather than an SSZ
hash-tree-root) is deferred pending [EIP-8025] / `ProofEngine`.

[EIP-7685]: https://eips.ethereum.org/EIPS/eip-7685
[EIP-8025]: https://eips.ethereum.org/EIPS/eip-8025
[EIP-8237]: https://eips.ethereum.org/EIPS/eip-8237
[SHA2-256]: https://en.wikipedia.org/wiki/SHA-2
"""

from hashlib import sha256
from typing import Tuple

from ethereum_types.bytes import Bytes, Bytes32
from ethereum_types.numeric import U64

from ethereum.crypto.hash import Hash32

from .blocks import Withdrawal


def compute_partial_header_hash(
    parent_hash: Hash32,
    prev_randao: Bytes32,
    gas_limit: U64,
    timestamp: U64,
    withdrawals: Tuple[Withdrawal, ...],
    parent_beacon_block_root: Hash32,
    slot_number: U64,
    execution_requests: Tuple[Bytes, ...],
) -> Hash32:
    """Compute the [EIP-8237] partial header hash over the pinned layout."""
    digest = sha256()
    digest.update(bytes(parent_hash))
    digest.update(bytes(prev_randao))
    digest.update(gas_limit.to_le_bytes8())
    digest.update(timestamp.to_le_bytes8())
    for w in withdrawals:
        digest.update(w.index.to_le_bytes8())
        digest.update(w.validator_index.to_le_bytes8())
        digest.update(bytes(w.address))
        digest.update(U64(w.amount).to_le_bytes8())
    digest.update(bytes(parent_beacon_block_root))
    digest.update(slot_number.to_le_bytes8())
    for request in execution_requests:
        digest.update(bytes(request))
    return Hash32(digest.digest())
