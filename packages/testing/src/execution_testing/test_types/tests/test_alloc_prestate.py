"""
Unit tests for `Alloc` acting as a `PreState` provider.

Covers four invariants of the lifecycle phase machinery:
    1. The code-hash → bytes cache is built correctly when the alloc goes
       LIVE, and the PreState read methods agree with the source dict.
    2. `compute_state_root` on `Alloc` matches the same call on a
       freshly built `ethereum.state_mpt.State` over the same data.
    3. Mutating an `Alloc` via `__setitem__`/`__delitem__` is rejected
       after it has been used as a PreState.
    4. Building alloc B by `apply_diff`ing a diff onto alloc A produces a
       post-state whose root matches an alloc independently constructed
       to look like the post-state.
"""

from typing import Dict, Optional

import ethereum.state as spec_state
import ethereum.state_mpt as spec_state_mpt
import pytest
from ethereum.crypto.hash import keccak256
from ethereum_types.bytes import Bytes20, Bytes32
from ethereum_types.numeric import U256, Uint

from execution_testing.base_types import Account, StateCommitment
from execution_testing.test_types import Alloc
from execution_testing.test_types.account_types import _Phase


def _b20(hex_str: str) -> Bytes20:
    """Build a `Bytes20` address from a 40-char hex string (no `0x`)."""
    return Bytes20(bytes.fromhex(hex_str))


# A small, fixed set of addresses for ergonomic reuse in tests. They are
# `Bytes20` so they satisfy the `PreState` protocol's address parameter
# type, and pydantic re-validates them into `Address` when used as `Alloc`
# keys.
ADDR_A = _b20("000000000000000000000000000000000000aaaa")
ADDR_B = _b20("000000000000000000000000000000000000bbbb")
ADDR_C = _b20("000000000000000000000000000000000000cccc")
ADDR_MISSING = _b20("dead000000000000000000000000000000000000")
CODE = bytes.fromhex("60016002")  # PUSH1 1 PUSH1 2


def _fixture_alloc() -> Alloc:
    """Build a small alloc with one EOA, one contract, and one empty acct."""
    alloc = Alloc.model_validate(
        {
            ADDR_A: {"balance": 100, "nonce": 1},
            ADDR_B: {
                "balance": 7,
                "nonce": 3,
                "code": "0x" + CODE.hex(),
                "storage": {1: 0x42, 2: 0xCAFE},
            },
            ADDR_C: {"balance": 0, "nonce": 0},
        }
    )
    alloc.migrate_state_commitment(StateCommitment.MPT)
    return alloc


def _state_from_alloc(alloc: Alloc) -> spec_state_mpt.State:
    """Build a spec `State` mirroring `alloc` for parity comparisons."""
    state = spec_state_mpt.State()
    for address, account in alloc.root.items():
        if account is None:
            continue
        addr = Bytes20(address)
        code = bytes(account.code) if account.code else b""
        code_hash = keccak256(code) if code else spec_state.EMPTY_CODE_HASH
        spec_state_mpt.set_account(
            state,
            addr,
            spec_state.Account(
                nonce=Uint(int(account.nonce)),
                balance=U256(int(account.balance)),
                code_hash=code_hash,
            ),
        )
        if code:
            state._code_store[code_hash] = code
        for key_hi, value_hi in account.storage.root.items():
            if int(value_hi) == 0:
                continue
            spec_state_mpt.set_storage(
                state,
                addr,
                Bytes32(int(key_hi).to_bytes(32, "big")),
                U256(int(value_hi)),
            )
    return state


def test_cache_build_and_read_methods_agree_with_source() -> None:
    """PreState reads on the alloc agree with the source dict."""
    alloc = _fixture_alloc()
    assert alloc._phase is _Phase.CONSTRUCTION

    # The first PreState call must transition the alloc to LIVE.
    acct_b = alloc.get_account_optional(ADDR_B)
    assert alloc._phase is _Phase.LIVE
    assert acct_b is not None
    assert acct_b.nonce == Uint(3)
    assert acct_b.balance == U256(7)
    assert acct_b.code_hash == keccak256(CODE)

    # _code_store contains the empty hash and the only contract's code.
    assert alloc._code_store[spec_state.EMPTY_CODE_HASH] == b""
    assert alloc._code_store[keccak256(CODE)] == CODE
    # EOA + empty account contribute no code entries.
    assert len(alloc._code_store) == 2

    # Storage reads agree with the source for set and unset keys.
    assert alloc.get_storage(ADDR_B, Bytes32(b"\x00" * 31 + b"\x01")) == U256(
        0x42
    )
    assert alloc.get_storage(ADDR_B, Bytes32(b"\x00" * 31 + b"\x02")) == U256(
        0xCAFE
    )
    assert alloc.get_storage(ADDR_B, Bytes32(b"\x00" * 31 + b"\x03")) == U256(
        0
    )
    # Account with no storage returns zero for any key.
    assert alloc.get_storage(ADDR_A, Bytes32(b"\x00" * 32)) == U256(0)
    # Missing account returns zero.
    assert alloc.get_storage(ADDR_MISSING, Bytes32(b"\x00" * 32)) == U256(0)

    # get_code round-trips, including the empty-code sentinel.
    assert alloc.get_code(spec_state.EMPTY_CODE_HASH) == b""
    assert alloc.get_code(keccak256(CODE)) == CODE

    # Missing accounts return None from get_account_optional.
    assert alloc.get_account_optional(ADDR_MISSING) is None


def test_state_root_parity_against_spec_state() -> None:
    """`Alloc.compute_state_root` matches spec `State`."""
    alloc = _fixture_alloc()
    state = _state_from_alloc(alloc)

    alloc_root = alloc.compute_state_root(spec_state.BlockDiff())
    spec_root = state.compute_state_root(spec_state.BlockDiff())
    assert alloc_root == spec_root

    # Same parity under non-trivial change sets.
    account_changes: Dict[Bytes20, Optional[spec_state.Account]] = {
        ADDR_A: spec_state.Account(
            nonce=Uint(2), balance=U256(200), code_hash=keccak256(CODE)
        ),
    }
    storage_changes: Dict[Bytes20, Dict[Bytes32, U256]] = {
        ADDR_B: {Bytes32(b"\x00" * 31 + b"\x01"): U256(0x99)},
    }
    alloc_root_changed = alloc.compute_state_root(
        spec_state.BlockDiff(
            account_changes=account_changes,
            storage_changes=storage_changes,
            code_changes={},
        )
    )
    spec_root_changed = state.compute_state_root(
        spec_state.BlockDiff(
            account_changes=account_changes,
            storage_changes=storage_changes,
            code_changes={},
        )
    )
    assert alloc_root_changed == spec_root_changed
    assert alloc_root_changed != alloc_root


def test_phase_guard_rejects_mutation_after_live() -> None:
    """`__setitem__` and `__delitem__` raise once the alloc is LIVE."""
    alloc = _fixture_alloc()
    # Still in CONSTRUCTION — mutations are allowed.
    alloc[_b20("000000000000000000000000000000000000dddd")] = Account(
        balance=1
    )

    # Any PreState read transitions to LIVE.
    _ = alloc.get_account_optional(ADDR_A)
    assert alloc._phase is _Phase.LIVE

    with pytest.raises(RuntimeError, match="not allowed"):
        alloc[_b20("000000000000000000000000000000000000eeee")] = Account(
            balance=1
        )

    with pytest.raises(RuntimeError, match="not allowed"):
        del alloc[ADDR_A]

    # freeze() locks further mutation including apply_diff.
    alloc.freeze()
    with pytest.raises(RuntimeError, match="FROZEN"):
        alloc.apply_diff(
            spec_state.BlockDiff(
                account_changes={}, storage_changes={}, code_changes={}
            )
        )


def test_apply_diff_round_trip_matches_independent_post_state() -> None:
    """A.apply_diff(diff) reproduces an independently built post-state."""
    new_code = bytes.fromhex("6005600555")  # arbitrary, distinct from CODE
    new_code_hash = keccak256(new_code)

    alloc_pre = _fixture_alloc()

    # Independently build the expected post-state:
    #   - ADDR_A: nonce 1 → 2, balance 100 → 50
    #   - ADDR_B: keeps account, storage slot 1 cleared, slot 3 added,
    #             slot 2 left alone
    #   - ADDR_C: deleted
    #   - new ADDR_NEW: brand-new contract with `new_code` and a slot set
    addr_new = _b20("000000000000000000000000000000000000ffff")
    alloc_post_expected = Alloc.model_validate(
        {
            ADDR_A: {"balance": 50, "nonce": 2},
            ADDR_B: {
                "balance": 7,
                "nonce": 3,
                "code": "0x" + CODE.hex(),
                "storage": {2: 0xCAFE, 3: 0x77},
            },
            addr_new: {
                "balance": 1,
                "nonce": 1,
                "code": "0x" + new_code.hex(),
                "storage": {0: 0x11},
            },
        }
    )
    alloc_post_expected.migrate_state_commitment(StateCommitment.MPT)

    # Build the diff that, applied to alloc_pre, should produce
    # alloc_post_expected.
    diff = spec_state.BlockDiff(
        account_changes={
            ADDR_A: spec_state.Account(
                nonce=Uint(2),
                balance=U256(50),
                code_hash=spec_state.EMPTY_CODE_HASH,
            ),
            ADDR_C: None,
            addr_new: spec_state.Account(
                nonce=Uint(1),
                balance=U256(1),
                code_hash=new_code_hash,
            ),
        },
        storage_changes={
            ADDR_B: {
                Bytes32(b"\x00" * 31 + b"\x01"): U256(0),
                Bytes32(b"\x00" * 31 + b"\x03"): U256(0x77),
            },
            addr_new: {Bytes32(b"\x00" * 32): U256(0x11)},
        },
        code_changes={new_code_hash: new_code},
    )

    # Force LIVE so apply_diff is allowed.
    _ = alloc_pre.get_account_optional(ADDR_A)
    alloc_pre.apply_diff(diff)

    # State roots should match.
    pre_root = alloc_pre.compute_state_root(spec_state.BlockDiff())
    expected_root = alloc_post_expected.compute_state_root(
        spec_state.BlockDiff()
    )
    assert pre_root == expected_root

    # Cache must be updated additively with the new code.
    assert alloc_pre._code_store[new_code_hash] == new_code
    # The contract's pre-existing code is still cached too.
    assert alloc_pre._code_store[keccak256(CODE)] == CODE

    # apply_diff is still allowed (alloc stays LIVE) for the next block.
    alloc_pre.apply_diff(
        spec_state.BlockDiff(
            account_changes={}, storage_changes={}, code_changes={}
        )
    )
