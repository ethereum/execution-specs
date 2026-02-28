"""End-to-end test for stateless_guest.entrypoint."""

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes, Bytes8, Bytes32
from ethereum_types.numeric import U64, U256, Uint

from ethereum.crypto.hash import Hash32, keccak256
from ethereum.forks.amsterdam.blocks import Header
from ethereum.forks.amsterdam.execution_engine.types import (
    ExecutionPayload,
    NewPayloadRequest,
)
from ethereum.forks.amsterdam.execution_engine.validation_helpers import (
    _payload_header,
)
from ethereum.forks.amsterdam.fork import EMPTY_OMMER_HASH
from ethereum.forks.amsterdam.fork_types import Bloom
from ethereum.forks.amsterdam.requests import compute_requests_hash
from ethereum.forks.amsterdam.stateless import (
    ChainConfig,
    StatelessInput,
    StatelessValidationResult,
)
from ethereum.forks.amsterdam.stateless_guest import (
    entrypoint,
    rewind_input,
    serialize_stateless_input,
    write_input_bytes,
)
from ethereum.forks.amsterdam.stateless_types import ExecutionWitness
from ethereum.forks.amsterdam.trie import EMPTY_TRIE_ROOT
from ethereum.state import Address, Root

_ZERO_HASH = Hash32(b"\x00" * 32)
_ZERO_ROOT = Root(b"\x00" * 32)
_ZERO_ADDR = Address(b"\x00" * 20)
_ZERO_BLOOM = Bloom(b"\x00" * 256)
_ZERO_BYTES32 = Bytes32(b"\x00" * 32)
_ZERO_BYTES8 = Bytes8(b"\x00" * 8)

_EMPTY_REQUESTS_HASH = Hash32(compute_requests_hash([]))
_EMPTY_ACCESS_LIST_HASH = Hash32(keccak256(b""))


def _make_parent_header() -> Header:
    """Build a minimal parent header with empty state."""
    return Header(
        parent_hash=_ZERO_HASH,
        ommers_hash=EMPTY_OMMER_HASH,
        coinbase=_ZERO_ADDR,
        state_root=EMPTY_TRIE_ROOT,
        transactions_root=EMPTY_TRIE_ROOT,
        receipt_root=EMPTY_TRIE_ROOT,
        bloom=_ZERO_BLOOM,
        difficulty=Uint(0),
        number=Uint(0),
        gas_limit=Uint(30_000_000),
        gas_used=Uint(0),
        timestamp=U256(1_000_000),
        extra_data=Bytes(b""),
        prev_randao=_ZERO_BYTES32,
        nonce=_ZERO_BYTES8,
        base_fee_per_gas=Uint(7),
        withdrawals_root=EMPTY_TRIE_ROOT,
        blob_gas_used=U64(0),
        excess_blob_gas=U64(0),
        parent_beacon_block_root=_ZERO_ROOT,
        requests_hash=_EMPTY_REQUESTS_HASH,
        block_access_list_hash=_EMPTY_ACCESS_LIST_HASH,
    )


def _make_child_payload(parent_header: Header) -> ExecutionPayload:
    """Build a child execution payload whose block_hash is correct."""
    parent_hash = Hash32(keccak256(rlp.encode(parent_header)))
    parent_beacon_block_root = Root(_ZERO_ROOT)

    # Build a provisional payload (block_hash will be computed below).
    provisional = ExecutionPayload(
        parent_hash=parent_hash,
        fee_recipient=_ZERO_ADDR,
        state_root=EMPTY_TRIE_ROOT,
        receipts_root=EMPTY_TRIE_ROOT,
        logs_bloom=_ZERO_BLOOM,
        prev_randao=_ZERO_BYTES32,
        block_number=Uint(1),
        gas_limit=Uint(30_000_000),
        gas_used=Uint(0),
        timestamp=U256(1_000_001),
        extra_data=Bytes(b""),
        base_fee_per_gas=Uint(7),
        block_hash=_ZERO_HASH,
        transactions=(),
        withdrawals=(),
        blob_gas_used=U64(0),
        excess_blob_gas=U64(0),
        block_access_list=Bytes(b""),
    )

    child_header = _payload_header(provisional, parent_beacon_block_root, ())
    block_hash = Hash32(keccak256(rlp.encode(child_header)))

    return ExecutionPayload(
        parent_hash=parent_hash,
        fee_recipient=_ZERO_ADDR,
        state_root=EMPTY_TRIE_ROOT,
        receipts_root=EMPTY_TRIE_ROOT,
        logs_bloom=_ZERO_BLOOM,
        prev_randao=_ZERO_BYTES32,
        block_number=Uint(1),
        gas_limit=Uint(30_000_000),
        gas_used=Uint(0),
        timestamp=U256(1_000_001),
        extra_data=Bytes(b""),
        base_fee_per_gas=Uint(7),
        block_hash=block_hash,
        transactions=(),
        withdrawals=(),
        blob_gas_used=U64(0),
        excess_blob_gas=U64(0),
        block_access_list=Bytes(b""),
    )


def _make_stateless_input() -> StatelessInput:
    """Build a minimal StatelessInput with a valid parent header."""
    parent_header = _make_parent_header()
    encoded_parent = Bytes(rlp.encode(parent_header))
    child_payload = _make_child_payload(parent_header)

    return StatelessInput(
        new_payload_request=NewPayloadRequest(
            execution_payload=child_payload,
            versioned_hashes=(),
            parent_beacon_block_root=_ZERO_ROOT,
            execution_requests=(),
        ),
        witness=ExecutionWitness(
            state=(),
            codes=(),
            headers=(encoded_parent,),
        ),
        chain_config=ChainConfig(chain_id=U64(1)),
        public_keys=(),
    )


def test_entrypoint_produces_output() -> None:
    """entrypoint() returns serialized StatelessValidationResult."""
    stateless_input = _make_stateless_input()
    input_data = serialize_stateless_input(stateless_input)

    write_input_bytes(input_data)
    rewind_input()

    output_data = entrypoint()

    result = rlp.decode_to(StatelessValidationResult, output_data)
    assert result.chain_config == stateless_input.chain_config
