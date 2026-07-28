"""
Unit test proving the BinaryTree fork's block-execution path rejects a
block whose header claims a `state_root` that does not match the
tree-computed root.

`tests/binary_tree/eip8297_partitioned_binary_tree/test_multi_block.py
::test_block_with_wrong_state_root_is_rejected` only *records* this
expectation: fill-time verification is skipped whenever `rlp_modifier`
is set (`execution_testing`'s `specs/blockchain.py:1073-1084`), and no
client consumes `BinaryTree` fixtures either, so nothing exercises the
check end to end today. This test drives it directly, through the
actual code path: `ethereum.forks.binary_tree.fork.execute_block`,
whose `block_state_root != block.header.state_root` comparison is what
raises `InvalidBlock`.

Building a self-consistent block by hand runs into the same
chicken-and-egg problem every block builder faces: `execute_block`
only *validates* a header against outputs it (re)computes, it never
*returns* the correct header. `_build_valid_block_one` resolves this
the way a real block builder would: it runs the block body once
(`apply_body`, on a from-scratch `BlockEnvironment`) to learn what the
outputs actually are, using the exact same helper functions
`execute_block` itself calls right after `apply_body`
(`extract_block_diff`, `State.compute_state_root`, the MPT `root`,
`logs_bloom`, `compute_requests_hash`, `hash_block_access_list`) --
none of which is the comparison under test here -- and packages a
header from the results. `test_execute_block_rejects_a_tampered_state_root`
then asserts the block returned by `_build_valid_block_one` executes
cleanly (the control) before tampering with its `state_root` in
isolation. This keeps `execute_block` itself, unmodified, as the thing
that raises `InvalidBlock`: nothing here reimplements or shortcuts the
root comparison it performs.

The block itself is deliberately minimal: no transactions, no
withdrawals, and a one-byte `STOP` stub deployed at every system
contract address `apply_body` unconditionally calls -- just enough for
`process_checked_system_transaction`'s "contract has code" precondition
to pass for the withdrawal, consolidation, and builder deposit/exit
contracts. None of that machinery is under test; a block this empty
produces an empty `BlockDiff` (nothing writes any state), so its
`state_root` is simply the pre-state's own, already-known root.
"""

from dataclasses import replace
from typing import Tuple

import pytest
from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes, Bytes8, Bytes32
from ethereum_types.numeric import U64, U256, Uint

from ethereum.crypto.hash import Hash32, keccak256
from ethereum.exceptions import InvalidBlock
from ethereum.forks.binary_tree.block_access_lists import (
    BlockAccessListBuilder,
    hash_block_access_list,
)
from ethereum.forks.binary_tree.blocks import Block, Header
from ethereum.forks.binary_tree.bloom import logs_bloom
from ethereum.forks.binary_tree.fork import (
    BEACON_ROOTS_ADDRESS,
    BUILDER_DEPOSIT_CONTRACT_ADDRESS,
    BUILDER_EXIT_CONTRACT_ADDRESS,
    CONSOLIDATION_REQUEST_PREDEPLOY_ADDRESS,
    EMPTY_OMMER_HASH,
    HISTORY_STORAGE_ADDRESS,
    WITHDRAWAL_REQUEST_PREDEPLOY_ADDRESS,
    ChainContext,
    apply_body,
    calculate_base_fee_per_gas,
    execute_block,
)
from ethereum.forks.binary_tree.fork_types import Bloom
from ethereum.forks.binary_tree.requests import compute_requests_hash
from ethereum.forks.binary_tree.state_tracker import (
    BlockState,
    extract_block_diff,
)
from ethereum.forks.binary_tree.vm import BlockEnvironment
from ethereum.forks.binary_tree.vm.gas import calculate_excess_blob_gas
from ethereum.merkle_patricia_trie import root as mpt_root
from ethereum.state import Account, Address
from ethereum.state_pbt import State, set_account, state_root, store_code

STUB_CODE = Bytes(b"\x00")
"""
Minimal, always-successful contract body: a single `STOP`. Long enough
(one byte) to satisfy `process_checked_system_transaction`'s
"contract has code" precondition, and simple enough to halt every call
made to it with no state effect.
"""

SYSTEM_CONTRACT_ADDRESSES = (
    BEACON_ROOTS_ADDRESS,
    HISTORY_STORAGE_ADDRESS,
    WITHDRAWAL_REQUEST_PREDEPLOY_ADDRESS,
    CONSOLIDATION_REQUEST_PREDEPLOY_ADDRESS,
    BUILDER_DEPOSIT_CONTRACT_ADDRESS,
    BUILDER_EXIT_CONTRACT_ADDRESS,
)
"""
Every system contract address `apply_body` unconditionally calls
during block processing, checked or not.
"""


def _stubbed_pre_state() -> State:
    """
    Build a `State` with `STUB_CODE` deployed at every system contract
    address `apply_body` unconditionally calls.

    `process_checked_system_transaction` raises `InvalidBlock` outright
    if the withdrawal, consolidation, or either builder-request
    contract has no code; without this, every call to `execute_block`
    below would raise for that reason, regardless of `state_root`.
    """
    state = State()
    for address in SYSTEM_CONTRACT_ADDRESSES:
        code_hash = store_code(state, STUB_CODE)
        set_account(
            state,
            address,
            Account(nonce=Uint(0), balance=U256(0), code_hash=code_hash),
        )
    return state


def _synthetic_parent_header() -> Header:
    """
    Build the arbitrary "block 0" header that block one extends.

    Only the fields `validate_header` actually reads off the parent
    (`gas_limit`, `gas_used`, `base_fee_per_gas`, `timestamp`,
    `number`, `excess_blob_gas`, `blob_gas_used`, and its own RLP
    encoding, for the child's `parent_hash`) matter here; every other
    field is an unused placeholder.
    """
    return Header(
        parent_hash=Hash32(b"\x00" * 32),
        ommers_hash=EMPTY_OMMER_HASH,
        coinbase=Address(b"\x00" * 20),
        state_root=Hash32(b"\x00" * 32),
        transactions_root=Hash32(b"\x00" * 32),
        receipt_root=Hash32(b"\x00" * 32),
        bloom=Bloom(b"\x00" * 256),
        difficulty=Uint(0),
        number=Uint(0),
        gas_limit=Uint(30_000_000),
        gas_used=Uint(0),
        timestamp=U256(1_000),
        extra_data=Bytes(b""),
        prev_randao=Bytes32(b"\x00" * 32),
        nonce=Bytes8(b"\x00" * 8),
        base_fee_per_gas=Uint(1_000_000_000),
        withdrawals_root=Hash32(b"\x00" * 32),
        blob_gas_used=U64(0),
        excess_blob_gas=U64(0),
        parent_beacon_block_root=Hash32(b"\x00" * 32),
        requests_hash=Hash32(b"\x00" * 32),
        block_access_list_hash=Hash32(b"\x00" * 32),
        slot_number=U64(0),
    )


def _build_valid_block_one(
    pre_state: State,
) -> Tuple[Block, ChainContext]:
    """
    Build block one and the `ChainContext` it extends, with every
    header field set to what `execute_block` will itself recompute and
    check it against.

    Runs the real block body (`apply_body`, empty transactions and
    withdrawals) once against a from-scratch `BlockEnvironment` to
    learn the outputs, exactly as `execute_block` does internally
    right up to (but not including) its validation `if`s -- see the
    module docstring for why this bootstrap is necessary and does not
    weaken the test.
    """
    parent_header = _synthetic_parent_header()
    parent_hash = keccak256(rlp.encode(parent_header))
    chain_context = ChainContext(
        chain_id=U64(1),
        block_hashes=[parent_hash],
        parent_header=parent_header,
    )

    gas_limit = parent_header.gas_limit
    base_fee_per_gas = calculate_base_fee_per_gas(
        gas_limit,
        parent_header.gas_limit,
        parent_header.gas_used,
        parent_header.base_fee_per_gas,
    )
    excess_blob_gas = calculate_excess_blob_gas(parent_header)

    # Every field below is either read straight off the parent (the
    # ones just computed above) or this test's own arbitrary, but
    # self-consistent, choice. `state_root`, `transactions_root`,
    # `receipt_root`, `bloom`, `gas_used`, `withdrawals_root`,
    # `requests_hash`, and `block_access_list_hash` are placeholders
    # here, overwritten below from the real outputs of running the
    # block body.
    header_shell = Header(
        parent_hash=parent_hash,
        ommers_hash=EMPTY_OMMER_HASH,
        coinbase=Address(b"\xbb" * 20),
        state_root=Hash32(b"\x00" * 32),
        transactions_root=Hash32(b"\x00" * 32),
        receipt_root=Hash32(b"\x00" * 32),
        bloom=Bloom(b"\x00" * 256),
        difficulty=Uint(0),
        number=parent_header.number + Uint(1),
        gas_limit=gas_limit,
        gas_used=Uint(0),
        timestamp=parent_header.timestamp + U256(12),
        extra_data=Bytes(b""),
        prev_randao=Bytes32(b"\x00" * 32),
        nonce=Bytes8(b"\x00" * 8),
        base_fee_per_gas=base_fee_per_gas,
        withdrawals_root=Hash32(b"\x00" * 32),
        blob_gas_used=U64(0),
        excess_blob_gas=excess_blob_gas,
        parent_beacon_block_root=Hash32(b"\x00" * 32),
        requests_hash=Hash32(b"\x00" * 32),
        block_access_list_hash=Hash32(b"\x00" * 32),
        slot_number=U64(1),
    )

    block_state = BlockState(pre_state=pre_state)
    block_env = BlockEnvironment(
        chain_id=chain_context.chain_id,
        state=block_state,
        block_gas_limit=header_shell.gas_limit,
        block_hashes=chain_context.block_hashes,
        coinbase=header_shell.coinbase,
        number=header_shell.number,
        base_fee_per_gas=header_shell.base_fee_per_gas,
        time=header_shell.timestamp,
        prev_randao=header_shell.prev_randao,
        excess_blob_gas=header_shell.excess_blob_gas,
        parent_beacon_block_root=header_shell.parent_beacon_block_root,
        block_access_list_builder=BlockAccessListBuilder(),
        slot_number=header_shell.slot_number,
    )
    block_output = apply_body(
        block_env=block_env, transactions=(), withdrawals=()
    )
    block_diff = extract_block_diff(block_state)

    header = replace(
        header_shell,
        state_root=pre_state.compute_state_root(block_diff),
        transactions_root=mpt_root(block_output.transactions_trie),
        receipt_root=mpt_root(block_output.receipts_trie),
        bloom=logs_bloom(block_output.block_logs),
        withdrawals_root=mpt_root(block_output.withdrawals_trie),
        requests_hash=Hash32(compute_requests_hash(block_output.requests)),
        block_access_list_hash=hash_block_access_list(
            block_output.block_access_list
        ),
        gas_used=max(
            block_output.block_gas_used, block_output.block_state_gas_used
        ),
    )
    block = Block(header=header, transactions=(), ommers=(), withdrawals=())
    return block, chain_context


def test_execute_block_rejects_a_tampered_state_root() -> None:
    """
    `execute_block` accepts a correctly built block one and rejects an
    otherwise-identical copy whose header's `state_root` has one byte
    flipped.

    The control call (the real, computed root) must succeed first --
    proving the block built above is genuinely valid, not merely "some
    header that happens to raise" -- so the second call's
    `InvalidBlock` is attributable to the tampered `state_root`
    specifically. Both calls go through `execute_block` unmodified;
    its own `block_state_root != block.header.state_root` comparison
    in `fork.py` is what raises.
    """
    pre_state = _stubbed_pre_state()
    block, chain_context = _build_valid_block_one(pre_state)

    # This block writes no state (no transactions, no withdrawals, and
    # the system-contract stubs are pure STOPs), so its state_root is
    # simply the pre-state's own, unchanged, root.
    assert block.header.state_root == state_root(pre_state)

    execute_block(block, pre_state, chain_context)

    original_root = block.header.state_root
    tampered_root = Hash32(
        bytes([original_root[0] ^ 0xFF]) + original_root[1:]
    )
    tampered_block = replace(
        block, header=replace(block.header, state_root=tampered_root)
    )

    with pytest.raises(InvalidBlock):
        execute_block(tampered_block, pre_state, chain_context)
