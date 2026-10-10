"""Regression tests for storage roots in Bogota block access lists."""

import importlib
from types import SimpleNamespace
from typing import cast

import pytest
from ethereum.crypto.hash import keccak256
from ethereum.forks.bogota.block_access_lists import (
    BlockAccessListBuilder,
    add_balance_change,
    add_code_change,
    add_nonce_change,
    add_storage_write,
    build_block_access_list,
    hash_block_access_list,
    post_block_storage_root,
)
from ethereum.forks.bogota.fork_types import BlockAccessIndex
from ethereum.forks.bogota.state_tracker import BlockState
from ethereum.merkle_patricia_trie import EMPTY_TRIE_ROOT, Trie
from ethereum.state import EMPTY_CODE_HASH, Account, BlockDiff
from ethereum.state_mpt import State, set_account, set_storage
from ethereum_rlp import Extended, rlp
from ethereum_spec_tools.forks import Hardfork
from ethereum_spec_tools.loaders.fork_loader import ForkLoad
from ethereum_types.bytes import Bytes, Bytes20, Bytes32
from ethereum_types.numeric import U64, U256, Uint

from execution_testing.base_types import StateCommitment
from execution_testing.evm_tools.t8n import T8N
from execution_testing.evm_tools.t8n.result import build_result
from execution_testing.test_types import Alloc

ADDRESS = Bytes20(b"\x11" * 20)
SLOT = Bytes32(b"\x00" * 31 + b"\x01")
OTHER_SLOT = Bytes32(b"\x00" * 31 + b"\x02")


def make_state(storage: dict[Bytes32, U256]) -> State:
    """Build an account with the specified storage."""
    state = State()
    set_account(state, ADDRESS, Account(Uint(1), U256(10), EMPTY_CODE_HASH))
    for key, value in storage.items():
        set_storage(state, ADDRESS, key, value)
    return state


@pytest.mark.parametrize(
    "cleared,writes,expected_storage",
    [
        pytest.param(False, {}, {SLOT: U256(7)}, id="unchanged-storage"),
        pytest.param(False, {SLOT: U256(0)}, {}, id="last-slot-deleted"),
        pytest.param(True, {}, {}, id="storage-cleared"),
        pytest.param(
            True,
            {OTHER_SLOT: U256(9)},
            {OTHER_SLOT: U256(9)},
            id="write-after-clear",
        ),
        pytest.param(
            False,
            {OTHER_SLOT: U256(9)},
            {SLOT: U256(7), OTHER_SLOT: U256(9)},
            id="unmodified-slot-preserved",
        ),
    ],
)
@pytest.mark.parametrize("provider", ["state", "alloc"])
def test_post_block_storage_root(
    cleared: bool,
    writes: dict[Bytes32, U256],
    expected_storage: dict[Bytes32, U256],
    provider: str,
) -> None:
    """Commit all post-block storage, including clears, without mutation."""
    pre_state: State | Alloc
    if provider == "state":
        pre_state = make_state({SLOT: U256(7)})
    elif provider == "alloc":
        pre_state = Alloc.model_validate(
            {ADDRESS: {"nonce": 1, "balance": 10, "storage": {1: 7}}}
        )
        pre_state.migrate_state_commitment(StateCommitment.MPT)
    else:
        raise ValueError(provider)
    before = pre_state.compute_state_root(BlockDiff())
    block_state = BlockState(
        pre_state=pre_state,
        storage_writes={ADDRESS: writes},
        storage_clears={ADDRESS} if cleared else set(),
    )
    expected_root = make_state(expected_storage).compute_storage_root(
        ADDRESS, BlockDiff()
    )
    expected = b"" if expected_root == EMPTY_TRIE_ROOT else expected_root
    assert post_block_storage_root(block_state, ADDRESS) == expected
    assert pre_state.get_storage(ADDRESS, SLOT) == U256(7)
    assert pre_state.compute_state_root(BlockDiff()) == before


@pytest.mark.parametrize("change", ["storage", "balance", "nonce", "code"])
@pytest.mark.parametrize("has_storage", [False, True])
def test_changed_account_encoding(change: str, has_storage: bool) -> None:
    """Include the storage root for every kind of account state change."""
    state = make_state({SLOT: U256(7)} if has_storage else {})
    block_state = BlockState(pre_state=state)
    builder = BlockAccessListBuilder()
    index = BlockAccessIndex(1)
    if change == "storage":
        add_storage_write(builder, ADDRESS, U256(2), index, U256(9))
        block_state.storage_writes[ADDRESS] = {OTHER_SLOT: U256(9)}
    elif change == "balance":
        add_balance_change(builder, ADDRESS, index, U256(11))
    elif change == "nonce":
        add_nonce_change(builder, ADDRESS, index, U64(2))
    elif change == "code":
        add_code_change(builder, ADDRESS, index, Bytes(b"\x00"))
    else:
        raise ValueError(change)
    bal = build_block_access_list(builder, block_state)
    account = bal[0]
    assert account.storage_root is not None
    expected = rlp.encode(
        (
            (
                ADDRESS,
                account.storage_changes,
                account.storage_reads,
                account.balance_changes,
                account.nonce_changes,
                account.code_changes,
                account.storage_root,
            ),
        )
    )
    fork = ForkLoad(Hardfork(importlib.import_module("ethereum.forks.bogota")))
    assert rlp.encode(fork.block_access_list_to_rlp(bal)) == expected
    assert hash_block_access_list(bal) == keccak256(expected)
    if change != "storage" and not has_storage:
        assert account.storage_root == b""


@pytest.mark.parametrize("fork_name", ["amsterdam", "bogota"])
def test_access_only_encoding(fork_name: str) -> None:
    """Preserve the six-field encoding for unchanged accounts in both forks."""
    fork = ForkLoad(
        Hardfork(importlib.import_module(f"ethereum.forks.{fork_name}"))
    )
    tracker = importlib.import_module(
        f"ethereum.forks.{fork_name}.state_tracker"
    )
    block_state = tracker.BlockState(
        pre_state=make_state({SLOT: U256(7)}), account_reads={ADDRESS}
    )
    bal = fork.build_block_access_list(
        fork.BlockAccessListBuilder(), block_state
    )
    expected = rlp.encode(((ADDRESS, (), (), (), (), ()),))
    assert rlp.encode(fork.block_access_list_to_rlp(bal)) == expected
    assert fork.hash_block_access_list(bal) == keccak256(expected)


def test_amsterdam_changed_account_encoding() -> None:
    """Keep Amsterdam changes in the original six-field layout."""
    from ethereum.forks.amsterdam.block_access_lists import (
        BalanceChange,
        BlockAccessListBuilder,
        add_balance_change,
        build_block_access_list,
    )
    from ethereum.forks.amsterdam.fork_types import BlockAccessIndex
    from ethereum.forks.amsterdam.state_tracker import BlockState

    fork = ForkLoad(
        Hardfork(importlib.import_module("ethereum.forks.amsterdam"))
    )
    builder = BlockAccessListBuilder()
    index = BlockAccessIndex(1)
    add_balance_change(builder, ADDRESS, index, U256(11))
    bal = build_block_access_list(builder, BlockState(pre_state=State()))
    expected = rlp.encode(
        ((ADDRESS, (), (), (BalanceChange(index, U256(11)),), (), ()),)
    )
    assert rlp.encode(fork.block_access_list_to_rlp(bal)) == expected
    assert fork.hash_block_access_list(bal) == keccak256(expected)


@pytest.mark.parametrize("fork_name", ["amsterdam", "bogota"])
def test_transition_result_encoding(fork_name: str) -> None:
    """Use the fork's canonical BAL encoding in transition-tool results."""
    fork = ForkLoad(
        Hardfork(importlib.import_module(f"ethereum.forks.{fork_name}"))
    )
    tracker = importlib.import_module(
        f"ethereum.forks.{fork_name}.state_tracker"
    )
    bal_module = importlib.import_module(
        f"ethereum.forks.{fork_name}.block_access_lists"
    )
    state = make_state({})
    read_address = Bytes20(b"\x22" * 20)
    block_state = tracker.BlockState(
        pre_state=state, account_reads={read_address}
    )
    builder = fork.BlockAccessListBuilder()
    bal_module.add_balance_change(
        builder, ADDRESS, BlockAccessIndex(1), U256(11)
    )
    bal = fork.build_block_access_list(builder, block_state)
    block_output = SimpleNamespace(
        receipt_keys=[],
        transactions_trie=Trie(secured=False, default=None),
        receipts_trie=Trie(secured=False, default=None),
        block_logs=(),
        block_gas_used=Uint(0),
        block_access_list=bal,
    )
    t8n = cast(
        T8N,
        SimpleNamespace(
            fork=fork,
            alloc=state,
            _block_state=block_state,
            exception_mapper=None,
        ),
    )
    result = build_result(t8n, SimpleNamespace(), block_output, None, [])
    expected_entry: list[Extended] = [
        ADDRESS,
        (),
        (),
        ((Uint(1), U256(11)),),
        (),
        (),
    ]
    if fork_name == "bogota":
        expected_entry.append(b"")
    expected = rlp.encode(
        (tuple(expected_entry), (read_address, (), (), (), (), ()))
    )
    assert result.block_access_list == expected
    assert result.block_access_list_hash == keccak256(expected)
