"""
Malformed nodes in the witness state.

The guest decodes and checks a witness node only when executing the block
needs it, so only a malformed node that the block needs makes it invalid.
"""

from dataclasses import replace
from typing import Callable, Dict, Optional, Set, Tuple
from unittest.mock import patch

import pytest
from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes as TrieBytes
from ethereum_types.numeric import U256
from execution_testing import (
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytes,
    Op,
    Transaction,
)

import ethereum.forks.amsterdam.fork as amsterdam_fork
import ethereum.forks.amsterdam.incremental_mpt as incremental_mpt
from ethereum.crypto.hash import keccak256
from ethereum.forks.amsterdam.block_access_lists import BlockAccessList
from ethereum.forks.amsterdam.blocks import Header
from ethereum.forks.amsterdam.execution_engine.types import (
    NewPayloadRequest,
)
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
    MutableNode,
    compact_to_nibbles,
    decode_witness_to_mpt,
    mpt_get,
    mpt_root,
    mpt_set,
)
from ethereum.forks.amsterdam.stateless_guest import (
    deserialize_stateless_input,
)
from ethereum.forks.amsterdam.stateless_host import serialize_stateless_input
from ethereum.forks.amsterdam.witness_state import (
    WitnessState,
    _decode_account_from_leaf,
    build_code_db,
    build_node_db,
)
from ethereum.merkle_patricia_trie import (
    EMPTY_TRIE_ROOT,
    bytes_to_nibble_list,
    nibble_list_to_compact,
)
from ethereum.state import EMPTY_CODE_HASH, BlockDiff, Root
from ethereum.state import Account as StateAccount

from .state_helpers import merge_with_amsterdam_pre_alloc

pytestmark = pytest.mark.valid_at("Amsterdam")

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

StateMutation = Callable[
    [Dict[TrieBytes, TrieBytes], Root],
    Tuple[Root, Set[TrieBytes]],
]
"""
Build a malformed state from the witness nodes and the state root, and
return its state root and the nodes to add to the witness.
"""

ACCOUNT_LEAF_VALUE = rlp.encode(
    [b"", b"\x01", EMPTY_TRIE_ROOT, EMPTY_CODE_HASH]
)
"""Encoding of an account with a balance of one wei."""

STORAGE_SLOT = 1

STORAGE_LEAF_VALUE = rlp.encode(U256(1))
"""Encoding of a storage value of one."""


def _leaf(path_nibbles: int, value: bytes) -> TrieBytes:
    """Encode a leaf whose path is `path_nibbles` zero nibbles long."""
    path = TrieBytes(b"\x00" * path_nibbles)
    return TrieBytes(rlp.encode([nibble_list_to_compact(path, True), value]))


def _reference(
    nodes: Set[TrieBytes], node_rlp: TrieBytes, *, by_hash: bool = False
) -> rlp.Extended:
    """
    Return how a parent refers to the node encoded as `node_rlp`, adding the
    node to `nodes` unless it is short enough to embed in the parent and
    `by_hash` is not set.
    """
    if len(node_rlp) < 32 and not by_hash:
        return rlp.decode(node_rlp)
    nodes.add(node_rlp)
    return keccak256(node_rlp)


def _decoded_nodes(node: MutableNode) -> Set[TrieBytes]:
    """
    Return the encodings of the decoded, hashed nodes under `node`.

    After a mutation edits a decoded trie, these include the new nodes along
    the edited path, which have to go into the witness.
    """
    if isinstance(node, MutableBranchNode):
        children = list(node.children)
    elif isinstance(node, MutableExtensionNode):
        children = [node.child]
    elif isinstance(node, MutableLeafNode):
        children = []
    else:
        return set()
    nodes = set()
    if node._rlp is not None and len(node._rlp) >= 32:
        nodes.add(TrieBytes(node._rlp))
    for child in children:
        nodes |= _decoded_nodes(child)
    return nodes


def _in_state_root_slot(
    slot: int,
    node_rlp: TrieBytes,
    children: Tuple[TrieBytes, ...] = (),
    *,
    by_hash: bool = False,
) -> StateMutation:
    """
    Return a mutation that puts the node encoded as `node_rlp`, with the
    hashed `children` it refers to, in an empty slot of the root branch of
    the state trie. The root refers to the node by hash if `by_hash` is set,
    however short it is.
    """

    def mutate(
        node_db: Dict[TrieBytes, TrieBytes], state_root: Root
    ) -> Tuple[Root, Set[TrieBytes]]:
        decoded_root = rlp.decode(node_db[state_root])
        assert isinstance(decoded_root, list) and len(decoded_root) == 17, (
            "the state trie root must be a branch"
        )
        assert decoded_root[slot] == b"", "the slot must be empty"
        root: list[rlp.Extended] = list(decoded_root)
        nodes = set(children)
        root[slot] = _reference(nodes, node_rlp, by_hash=by_hash)
        root_rlp = TrieBytes(rlp.encode(root))
        nodes.add(root_rlp)
        return Root(keccak256(root_rlp)), nodes

    return mutate


def _as_only_storage_sibling(
    address: Address,
    slot: int,
    node_rlp: TrieBytes,
    children: Tuple[TrieBytes, ...] = (),
) -> StateMutation:
    """
    Return a mutation that splits the storage trie of `address`, which holds
    `STORAGE_SLOT` alone, into a root branch whose only other child, in
    `slot`, is the node encoded as `node_rlp` with the hashed `children` it
    refers to.
    """

    def mutate(
        node_db: Dict[TrieBytes, TrieBytes], state_root: Root
    ) -> Tuple[Root, Set[TrieBytes]]:
        state_mpt: IncrementalMPT[Address, Optional[StateAccount]] = (
            decode_witness_to_mpt(
                node_db, state_root, secured=True, default=None
            )
        )
        account_leaf = mpt_get(state_mpt, address)
        assert account_leaf is not None
        account, storage_root = _decode_account_from_leaf(account_leaf)

        storage_leaf = rlp.decode(node_db[storage_root])
        assert isinstance(storage_leaf, list) and len(storage_leaf) == 2
        path_bytes, value = storage_leaf
        assert isinstance(path_bytes, bytes) and isinstance(value, bytes)
        path, is_leaf = compact_to_nibbles(path_bytes)
        assert is_leaf
        assert path == bytes_to_nibble_list(
            keccak256(U256(STORAGE_SLOT).to_be_bytes32())
        )
        assert slot != path[0], "the slot must not be the one of STORAGE_SLOT"

        nodes = set(children)
        branch: list[rlp.Extended] = [b""] * 17
        branch[path[0]] = _reference(
            nodes,
            TrieBytes(
                rlp.encode([nibble_list_to_compact(path[1:], True), value])
            ),
        )
        branch[slot] = _reference(nodes, node_rlp)
        branch_rlp = TrieBytes(rlp.encode(branch))
        nodes.add(branch_rlp)

        mpt_set(state_mpt, address, account, Root(keccak256(branch_rlp)))
        malformed_root = mpt_root(state_mpt)
        return malformed_root, nodes | _decoded_nodes(state_mpt.root_node)

    return mutate


def _dry_run(
    request: NewPayloadRequest,
    pre_state: WitnessState,
    chain_context: ChainContext,
) -> Tuple[BlockDiff, BlockAccessList]:
    """
    Execute the block in `request` on `pre_state`, and return the block diff
    and block access list that it actually produces.
    """
    block = _payload_block(
        request.execution_payload,
        request.parent_beacon_block_root,
        request.execution_requests,
    )

    # The header still claims the post-state root and block access list of
    # the original block, so both checks against it are patched to pass.
    # The caller re-seals the payload with the block access list that the
    # run builds, and a post-state root computed from the block diff.
    with (
        patch.object(
            WitnessState,
            "compute_state_root",
            return_value=block.header.state_root,
        ),
        patch.object(
            amsterdam_fork,
            "hash_block_access_list",
            return_value=block.header.block_access_list_hash,
        ) as hash_block_access_list,
    ):
        block_diff = execute_block(block, pre_state, chain_context)

    hash_block_access_list.assert_called_once()
    (block_access_list,) = hash_block_access_list.call_args.args
    return block_diff, block_access_list


def _with_malformed_parent_state(
    mutate: StateMutation,
) -> Callable[[Bytes], Bytes]:
    """
    Return a modifier that gives the block a malformed parent state.

    The parent header and payload are updated together, so the stateless
    input is otherwise valid for a parent with the malformed state. A dry run
    of the block provides the block access list, and the block diff that the
    post-state root of the malformed state is computed from.
    """

    def modifier(input_bytes: Bytes) -> Bytes:
        stateless_input = deserialize_stateless_input(
            TrieBytes(bytes(input_bytes))
        )
        witness = stateless_input.witness
        assert witness.headers
        parent_header = rlp.decode_to(
            # The Amsterdam witness always carries the immediately preceding
            # header for this block.
            Header,
            witness.headers[-1],
        )
        state = tuple(TrieBytes(node) for node in witness.state)
        codes = tuple(TrieBytes(code) for code in witness.codes)

        malformed_root, added_nodes = mutate(
            build_node_db(state), parent_header.state_root
        )
        modified_state = tuple(sorted(set(state) | added_nodes))
        modified_parent_header = replace(
            parent_header, state_root=malformed_root
        )
        modified_parent_header_rlp = TrieBytes(
            rlp.encode(modified_parent_header)
        )
        modified_parent_hash = keccak256(modified_parent_header_rlp)

        request = stateless_input.new_payload_request
        modified_payload = replace(
            request.execution_payload, parent_hash=modified_parent_hash
        )
        # The malformed node only sits where the original state holds nothing
        # that the block sees, so the block runs the same on both states. The
        # dry run uses the original one, where nothing stops a read.
        block_diff, block_access_list = _dry_run(
            replace(request, execution_payload=modified_payload),
            WitnessState(
                _node_db=build_node_db(state),
                _state_root=parent_header.state_root,
                _code_db=build_code_db(codes),
            ),
            ChainContext(
                chain_id=stateless_input.chain_id,
                block_hashes=[modified_parent_hash],
                parent_header=modified_parent_header,
            ),
        )
        # Let a deletion collapse onto an over-length leaf, so that a case
        # expecting rejection is otherwise valid.
        with patch.object(incremental_mpt, "_check_secured_path"):
            post_state_root = WitnessState(
                _node_db=build_node_db(modified_state),
                _state_root=malformed_root,
                _code_db=build_code_db(codes),
            ).compute_state_root(block_diff)

        modified_payload = replace(
            modified_payload,
            state_root=post_state_root,
            block_access_list=TrieBytes(rlp.encode(block_access_list)),
        )
        modified_payload = replace(
            modified_payload,
            block_hash=keccak256(
                rlp.encode(
                    _payload_header(
                        modified_payload,
                        request.parent_beacon_block_root,
                        request.execution_requests,
                    )
                )
            ),
        )
        modified_input = replace(
            stateless_input,
            new_payload_request=replace(
                request, execution_payload=modified_payload
            ),
            witness=replace(
                witness,
                state=modified_state,
                headers=(modified_parent_header_rlp,),
            ),
        )
        return Bytes(bytes(serialize_stateless_input(modified_input)))

    return modifier


def _state_root_slot(address: Address) -> int:
    """Return the slot of the state trie root that `address` leads to."""
    return keccak256(bytes(address))[0] >> 4


def _absent_target(pre: Alloc) -> Tuple[Address, int]:
    """
    Pick an absent account, and an empty slot of the state trie root other
    than the one that the account's first nibble selects.

    The account's own slot is empty too. A read of the account reaches a
    malformed node put in its own slot, but never one put in the returned
    slot.

    The account's second nibble is zero. A read of the account then takes
    slot zero of a branch put in its slot, and runs along the zero-nibble
    extension from `_extension_to_leaf` into its child instead of stopping
    where the paths would otherwise part.
    """
    used_slots = {
        _state_root_slot(address)
        for address in merge_with_amsterdam_pre_alloc(pre)
    }
    free_slots = [slot for slot in range(16) if slot not in used_slots]
    assert len(free_slots) >= 2, "the state trie root needs two empty slots"
    target = next(
        Address(value)
        for value in range(0x1000, 0x2000)
        if _state_root_slot(Address(value)) in free_slots
        and keccak256(bytes(Address(value)))[0] & 0xF == 0
    )
    other_slot = next(
        slot for slot in free_slots if slot != _state_root_slot(target)
    )
    return target, other_slot


def _storage_root_slot(key: int) -> int:
    """Return the slot of a storage trie root that storage `key` leads to."""
    return keccak256(U256(key).to_be_bytes32())[0] >> 4


def _absent_storage_key() -> Tuple[int, int]:
    """
    Pick an absent storage key, and a slot of the storage trie root other
    than the ones that the first nibbles of the key and of `STORAGE_SLOT`
    select.

    The key doesn't share a slot with `STORAGE_SLOT` either. A read of the
    key reaches a malformed node put in its own slot, but never one put in
    the returned slot.
    """
    used_slot = _storage_root_slot(STORAGE_SLOT)
    key = next(
        key for key in range(256) if _storage_root_slot(key) != used_slot
    )
    other_slot = next(
        slot
        for slot in range(16)
        if slot not in (used_slot, _storage_root_slot(key))
    )
    return key, other_slot


def _target_read_block(
    pre: Alloc,
    node_rlp: TrieBytes,
    children: Tuple[TrieBytes, ...] = (),
    *,
    on_target_path: bool,
    expected_success: bool,
    by_hash: bool = False,
) -> Block:
    """
    Build a block that calls an absent target account, on a parent state
    with the node encoded as `node_rlp`, and the hashed `children` it refers
    to, in a free slot of the state trie root.

    The node goes in the slot that the target's path leaves the root through
    if `on_target_path` is set, and in a slot that the block doesn't read
    otherwise. The root refers to the node by hash if `by_hash` is set.
    """
    sender = pre.fund_eoa()
    target, unread_slot = _absent_target(pre)
    slot = _state_root_slot(target) if on_target_path else unread_slot
    return Block(
        txs=[Transaction(sender=sender, to=target, value=0)],
        # Paying the fees to the sender keeps the fee recipient off the
        # absent accounts that the block reads.
        fee_recipient=sender,
        stateless_input_bytes_modifier=_with_malformed_parent_state(
            _in_state_root_slot(slot, node_rlp, children, by_hash=by_hash)
        ),
        expected_stateless_validation_success=expected_success,
    )


@pytest.mark.parametrize(
    "leaf",
    [
        # Longer than a full key on its own.
        pytest.param(
            _leaf(67, ACCOUNT_LEAF_VALUE),
            id="leaf_segment_exceeds_key_length",
        ),
        # As long as a full key, so one nibble too long below the root.
        pytest.param(
            _leaf(64, ACCOUNT_LEAF_VALUE),
            id="cumulative_path_exceeds_key_length",
        ),
        # Far too short. An account is too long to embed, so this leaf holds
        # a short value instead.
        pytest.param(_leaf(2, b"\x01"), id="embedded_leaf_short_of_key"),
    ],
)
@pytest.mark.parametrize("read", [False, True], ids=["unread", "read"])
def test_witness_state_secured_trie_path_length(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    leaf: TrieBytes,
    read: bool,
) -> None:
    """
    Reject a leaf whose path does not end at the secured key length only
    when the block reads through it.
    """
    blockchain_test(
        pre=pre,
        blocks=[
            _target_read_block(
                pre, leaf, on_target_path=read, expected_success=not read
            )
        ],
        post={},
    )


@pytest.mark.parametrize(
    "leaf",
    [
        # Longer than a full key on its own.
        pytest.param(
            _leaf(67, STORAGE_LEAF_VALUE),
            id="leaf_segment_exceeds_key_length",
        ),
        # As long as a full key, so one nibble too long below the root.
        pytest.param(
            _leaf(64, STORAGE_LEAF_VALUE),
            id="cumulative_path_exceeds_key_length",
        ),
        # Far too short, and small enough to embed in the root.
        pytest.param(
            _leaf(2, STORAGE_LEAF_VALUE), id="embedded_leaf_short_of_key"
        ),
    ],
)
@pytest.mark.parametrize("read", [False, True], ids=["unread", "read"])
def test_witness_state_secured_storage_trie_path_length(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    leaf: TrieBytes,
    read: bool,
) -> None:
    """
    Reject a storage leaf whose path does not end at the secured key length
    only when the block reads through it.
    """
    absent_key, unread_slot = _absent_storage_key()
    slot = _storage_root_slot(absent_key) if read else unread_slot
    contract = pre.deploy_contract(
        code=Op.SLOAD(absent_key) + Op.STOP,
        storage={STORAGE_SLOT: 1},
    )
    sender = pre.fund_eoa()

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[Transaction(sender=sender, to=contract)],
                stateless_input_bytes_modifier=_with_malformed_parent_state(
                    _as_only_storage_sibling(contract, slot, leaf)
                ),
                expected_stateless_validation_success=not read,
            )
        ],
        post={},
    )


@pytest.mark.parametrize(
    "collapse", [False, True], ids=["no_collapse", "collapse"]
)
def test_witness_state_secured_trie_path_length_on_collapse(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    collapse: bool,
) -> None:
    """
    Reject a leaf whose path does not end at the secured key length only
    when a storage deletion collapses its parent branch onto it.
    """
    # Clearing the slot leaves the malformed leaf as the only child of the
    # storage root branch, while rewriting it keeps the branch as it is.
    new_value = 0 if collapse else 2
    contract = pre.deploy_contract(
        code=Op.SSTORE(STORAGE_SLOT, new_value) + Op.STOP,
        storage={STORAGE_SLOT: 1},
    )
    sender = pre.fund_eoa()
    _, sibling_slot = _absent_storage_key()

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[Transaction(sender=sender, to=contract)],
                stateless_input_bytes_modifier=_with_malformed_parent_state(
                    _as_only_storage_sibling(
                        contract,
                        sibling_slot,
                        # One nibble too long below the storage root.
                        _leaf(64, STORAGE_LEAF_VALUE),
                    )
                ),
                expected_stateless_validation_success=not collapse,
            )
        ],
        post={},
    )


def _extension_to_leaf(
    value: bytes,
) -> Tuple[TrieBytes, Tuple[TrieBytes]]:
    """
    Encode an extension along a zero nibble, one level below the root, whose
    child is a leaf holding `value` that ends at the secured key length.
    """
    leaf = _leaf(62, value)
    extension = TrieBytes(
        rlp.encode([nibble_list_to_compact(b"\x00", False), keccak256(leaf)])
    )
    return extension, (leaf,)


def _branch_with_value() -> TrieBytes:
    """
    Encode a branch that holds a value, which no secured key ends at, with
    its children out of slot zero.
    """
    branch: list[rlp.Extended] = [b""] * 17
    branch[16] = b"\x01"
    branch[1] = keccak256(b"left")
    branch[2] = keccak256(b"right")
    return TrieBytes(rlp.encode(branch))


def _branch_with_oversized_embedded_leaf() -> TrieBytes:
    """
    Encode a branch that embeds, in slot zero, a leaf long enough to hash.
    The leaf ends at the secured key length one level below the root.
    """
    branch: list[rlp.Extended] = [b""] * 17
    branch[0] = [
        nibble_list_to_compact(b"\x00" * 62, True),
        ACCOUNT_LEAF_VALUE,
    ]
    branch[1] = keccak256(b"sibling")
    return TrieBytes(rlp.encode(branch))


def _short_branch() -> TrieBytes:
    """
    Encode a branch short enough to embed, with two tiny embedded leaves out
    of slot zero.

    The branch passes every check on its own encoding. Its leaves are too
    short for a secured key, but a read through slot zero never reaches
    them.
    """
    tiny_leaf = [nibble_list_to_compact(b"\x00", True), b"\x01"]
    branch: list[rlp.Extended] = [b""] * 17
    branch[1] = tiny_leaf
    branch[2] = tiny_leaf
    branch_rlp = TrieBytes(rlp.encode(branch))
    assert len(branch_rlp) < 32
    return branch_rlp


@pytest.mark.parametrize(
    "child_in_witness",
    [True, False],
    ids=["malformed_child", "child_missing_from_witness"],
)
def test_witness_state_collapse_onto_extension_skips_its_child(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    child_in_witness: bool,
) -> None:
    """
    Accept a storage deletion that collapses a branch onto an extension whose
    child is malformed, since the collapse only needs the child's reference.
    """
    contract = pre.deploy_contract(
        code=Op.SSTORE(STORAGE_SLOT, 0) + Op.STOP,
        storage={STORAGE_SLOT: 1},
    )
    sender = pre.fund_eoa()
    _, sibling_slot = _absent_storage_key()
    # The child is a leaf, which an extension may not point to.
    extension, children = _extension_to_leaf(STORAGE_LEAF_VALUE)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[Transaction(sender=sender, to=contract)],
                stateless_input_bytes_modifier=_with_malformed_parent_state(
                    _as_only_storage_sibling(
                        contract,
                        sibling_slot,
                        extension,
                        children if child_in_witness else (),
                    )
                ),
                expected_stateless_validation_success=True,
            )
        ],
        post={},
    )


@pytest.mark.parametrize(
    "node,children",
    [
        pytest.param(TrieBytes(b"\xff" * 40), (), id="invalid_rlp"),
        pytest.param(
            TrieBytes(rlp.encode([keccak256(b"child")] + [b""] * 16)),
            (),
            id="branch_with_one_child",
        ),
        pytest.param(
            TrieBytes(
                rlp.encode(
                    [[nibble_list_to_compact(b"\x00", True), b"\x01"]]
                    + [b""] * 16
                )
            ),
            (),
            id="embedded_branch_with_one_child",
        ),
        pytest.param(
            *_extension_to_leaf(ACCOUNT_LEAF_VALUE), id="extension_to_leaf"
        ),
        pytest.param(_branch_with_value(), (), id="branch_with_value"),
        pytest.param(
            _branch_with_oversized_embedded_leaf(),
            (),
            id="oversized_embedded_leaf",
        ),
    ],
)
@pytest.mark.parametrize("read", [False, True], ids=["unread", "read"])
def test_witness_state_malformed_node(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    node: TrieBytes,
    children: Tuple[TrieBytes, ...],
    read: bool,
) -> None:
    """Reject a malformed state node only when the block reads through it."""
    blockchain_test(
        pre=pre,
        blocks=[
            _target_read_block(
                pre,
                node,
                children,
                on_target_path=read,
                expected_success=not read,
            )
        ],
        post={},
    )


@pytest.mark.parametrize("read", [False, True], ids=["unread", "read"])
def test_witness_state_hash_reference_to_short_node(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    read: bool,
) -> None:
    """
    Reject a state node referenced by hash although it is short enough to
    embed, only when the block reads through it.
    """
    blockchain_test(
        pre=pre,
        blocks=[
            _target_read_block(
                pre,
                _short_branch(),
                on_target_path=read,
                expected_success=not read,
                by_hash=True,
            )
        ],
        post={},
    )
