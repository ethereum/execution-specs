"""Witness MPT decoding of an over-length secured-trie path."""

from dataclasses import replace
from typing import AbstractSet
from unittest.mock import patch

import pytest
from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes as AmsterdamBytes
from ethereum_types.bytes import Bytes32
from ethereum_types.numeric import U256
from execution_testing import Alloc, Block, BlockchainTestFiller, Bytes

import ethereum.forks.amsterdam.fork as amsterdam_fork
import ethereum.forks.amsterdam.incremental_mpt as incremental_mpt
from ethereum.crypto.hash import keccak256
from ethereum.forks.amsterdam.block_access_lists import BlockAccessList
from ethereum.forks.amsterdam.blocks import Header
from ethereum.forks.amsterdam.execution_engine.validation_helpers import (
    _payload_block,
    _payload_header,
)
from ethereum.forks.amsterdam.fork import ChainContext, execute_block
from ethereum.forks.amsterdam.incremental_mpt import (
    IncrementalMPT,
    MutableBranchNode,
    MutableExtensionNode,
    MutableLeafNode,
    decode_witness_to_mpt,
    mpt_root,
)
from ethereum.forks.amsterdam.stateless_guest import (
    deserialize_stateless_input,
)
from ethereum.forks.amsterdam.stateless_host import serialize_stateless_input
from ethereum.forks.amsterdam.witness_state import (
    WitnessState,
    build_code_db,
    build_node_db,
)
from ethereum.merkle_patricia_trie import InternalNode
from ethereum.state import Account, Address, Root

pytestmark = pytest.mark.valid_from("Amsterdam")

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


def _secured_trie_path_with_leaf_length(
    input_bytes: Bytes,
    leaf_path_nibbles: int,
) -> Bytes:
    """
    Put a self-consistent malformed leaf in the parent state trie.

    The parent header and payload are updated together so that the resulting
    stateless input is an otherwise valid empty block whose pre- and post-state
    root is this malformed trie.
    """
    stateless_input = deserialize_stateless_input(
        AmsterdamBytes(bytes(input_bytes))
    )
    witness = stateless_input.witness
    assert witness.headers

    parent_header = rlp.decode_to(
        # The Amsterdam witness always carries the immediately preceding
        # header for this empty block.
        Header,
        witness.headers[-1],
    )
    original_root = parent_header.state_root
    decoded_mpt: IncrementalMPT[AmsterdamBytes, None] = decode_witness_to_mpt(
        build_node_db(tuple(AmsterdamBytes(node) for node in witness.state)),
        original_root,
        secured=True,
        default=None,
    )

    def add_malformed_leaf(node: object) -> bool:
        """Add the malformed leaf below an unused branch slot."""
        if isinstance(node, MutableBranchNode):
            for index, child in enumerate(node.children):
                if child is None:
                    node.children[index] = MutableLeafNode(
                        rest_of_key=AmsterdamBytes(
                            b"\x00" * leaf_path_nibbles
                        ),
                        value=b"",
                        _dirty=True,
                    )
                    node._hash = None
                    node._rlp = None
                    node._dirty = True
                    return True
            return any(
                child is not None and add_malformed_leaf(child)
                for child in node.children
            )
        if isinstance(node, MutableExtensionNode):
            if add_malformed_leaf(node.child):
                node._hash = None
                node._rlp = None
                node._dirty = True
                return True
        return False

    assert decoded_mpt.root_node is not None
    assert add_malformed_leaf(decoded_mpt.root_node)
    malformed_root = mpt_root(decoded_mpt)
    changed_nodes: set[AmsterdamBytes] = set()

    def collect_changed_nodes(node: object) -> None:
        """Collect RLP preimages generated for the changed path."""
        if isinstance(node, (MutableLeafNode, MutableExtensionNode)):
            if node._rlp is not None:
                changed_nodes.add(AmsterdamBytes(node._rlp))
        if isinstance(node, MutableBranchNode):
            if node._rlp is not None:
                changed_nodes.add(AmsterdamBytes(node._rlp))
            for child in node.children:
                if child is not None:
                    collect_changed_nodes(child)
        elif isinstance(node, MutableExtensionNode):
            collect_changed_nodes(node.child)

    collect_changed_nodes(decoded_mpt.root_node)
    modified_state = tuple(
        sorted(
            {AmsterdamBytes(node) for node in witness.state} | changed_nodes
        )
    )
    modified_parent_header = replace(
        parent_header,
        state_root=malformed_root,
    )
    modified_parent_header_rlp = AmsterdamBytes(
        rlp.encode(modified_parent_header)
    )
    modified_parent_hash = keccak256(modified_parent_header_rlp)

    payload = stateless_input.new_payload_request.execution_payload
    requests = stateless_input.new_payload_request.execution_requests
    modified_payload = replace(
        payload,
        parent_hash=modified_parent_hash,
        state_root=malformed_root,
    )
    computed_post_root: list[Root] = []
    original_compute_state_root = (
        WitnessState.compute_state_root_and_trie_changes
    )

    def record_state_root(
        state: WitnessState,
        account_changes: dict[Address, Account | None],
        storage_changes: dict[Address, dict[Bytes32, U256]],
        storage_clears: AbstractSet[Address] = frozenset(),
    ) -> tuple[Root, list[InternalNode]]:
        result = original_compute_state_root(
            state,
            account_changes,
            storage_changes,
            storage_clears,
        )
        computed_post_root.append(result[0])
        return (modified_payload.state_root, result[1])

    recording_state = WitnessState(
        _node_db=build_node_db(tuple(modified_state)),
        _state_root=malformed_root,
        _code_db=build_code_db(
            tuple(AmsterdamBytes(code) for code in witness.codes)
        ),
    )
    computed_block_access_list: list[BlockAccessList] = []

    def record_block_access_list(block_access_list: BlockAccessList) -> Root:
        computed_block_access_list.append(block_access_list)
        # Let the dry run continue; the modified payload gets the actual
        # block access list immediately afterwards.
        return keccak256(modified_payload.block_access_list)

    with (
        patch.object(
            WitnessState,
            "compute_state_root_and_trie_changes",
            new=record_state_root,
        ),
        patch.object(
            amsterdam_fork,
            "hash_block_access_list",
            new=record_block_access_list,
        ),
        # Permit the dry run to process the intentionally malformed state.
        patch.object(
            incremental_mpt,
            "_validate_secured_trie_paths",
            create=True,
        ),
    ):
        execute_block(
            _payload_block(
                modified_payload,
                stateless_input.new_payload_request.parent_beacon_block_root,
                requests,
            ),
            recording_state,
            ChainContext(
                chain_id=stateless_input.chain_config.chain_id,
                block_hashes=[modified_parent_hash],
                parent_header=modified_parent_header,
            ),
        )
    assert len(computed_post_root) == 1
    assert len(computed_block_access_list) == 1
    modified_payload = replace(
        modified_payload,
        state_root=computed_post_root[0],
        block_access_list=AmsterdamBytes(
            rlp.encode(computed_block_access_list[0])
        ),
    )
    modified_payload = replace(
        modified_payload,
        block_hash=keccak256(
            rlp.encode(
                _payload_header(
                    modified_payload,
                    stateless_input.new_payload_request.parent_beacon_block_root,
                    requests,
                )
            )
        ),
    )
    modified_request = replace(
        stateless_input.new_payload_request,
        execution_payload=modified_payload,
    )
    modified_witness = replace(
        witness,
        state=modified_state,
        headers=(modified_parent_header_rlp,),
    )
    modified_input = replace(
        stateless_input,
        new_payload_request=modified_request,
        witness=modified_witness,
    )
    return Bytes(bytes(serialize_stateless_input(modified_input)))


@pytest.mark.parametrize(
    "leaf_path_nibbles",
    [
        pytest.param(
            67,
            id="leaf_segment_exceeds_key_length",
        ),
        pytest.param(
            64,
            id="cumulative_path_exceeds_key_length",
        ),
    ],
)
def test_witness_state_rejects_overlength_secured_trie_path(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    leaf_path_nibbles: int,
) -> None:
    """Reject a secured trie path longer than its 64-nibble key."""

    def modifier(input_bytes: Bytes) -> Bytes:
        return _secured_trie_path_with_leaf_length(
            input_bytes,
            leaf_path_nibbles,
        )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[],
                stateless_input_bytes_modifier=modifier,
                expected_stateless_validation_success=False,
            )
        ],
        post={},
    )
