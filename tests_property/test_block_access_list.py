"""
Properties of the [EIP-7928] block access list the spec builds.

The list comes out in one canonical form, sorted and deduplicated, its item
count is what the block gas limit prices, and it names every account a
block touched, records every change against the state at the start of the
change's block access index, and lists every other touched slot as a read.
The last rule runs over random blocks, with the spec's list read back as
the framework's `BlockAccessList`.

[EIP-7928]: https://eips.ethereum.org/EIPS/eip-7928
"""

import copy
from dataclasses import dataclass, field
from types import ModuleType
from typing import Any, Dict, List, Set, Tuple

import pytest
from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes32
from ethereum_types.numeric import U256, Uint
from execution_testing.base_types import Bytes
from execution_testing.forks import Fork
from execution_testing.test_types.block_access_list import BlockAccessList
from hypothesis import assume, example, given, target
from hypothesis import strategies as st

from ethereum.crypto.hash import keccak256
from ethereum.state import Account, Address
from ethereum.state_mpt import State, set_account, set_storage, store_code

from .forks import requires
from .strategies import bytes_data, u64s, u256s

pytestmark = requires(lambda fork: fork.header_bal_hash_required())

# Addresses whose sorted order differs from their listed order, so a
# missing sort shows up.
ADDR_POOL = [
    Address(b"\x03" + b"\x00" * 19),
    Address(b"\x01" + b"\x00" * 19),
    Address(b"\x02" + b"\xff" * 19),
    Address(b"\xff" * 20),
]

# A few slots, so that writes to the same slot happen often.
SLOT_POOL = [U256(0), U256(1), U256(2), U256((1 << 256) - 1)]


def _slots() -> st.SearchStrategy[U256]:
    return st.one_of(st.sampled_from(SLOT_POOL), u256s())


def _indices() -> st.SearchStrategy[int]:
    # Small indices collide often; large ones exercise the full U32 range.
    return st.one_of(
        st.integers(min_value=0, max_value=6),
        st.integers(min_value=0, max_value=(1 << 32) - 1),
    )


BuilderOp = Tuple[Any, ...]


def _ops() -> st.SearchStrategy[List[BuilderOp]]:
    """Return sequences of builder operations over the address pool."""
    addr = st.sampled_from(ADDR_POOL)
    return st.lists(
        st.one_of(
            st.tuples(
                st.just("storage_write"), addr, _slots(), _indices(), u256s()
            ),
            st.tuples(st.just("storage_read"), addr, _slots()),
            st.tuples(st.just("balance"), addr, _indices(), u256s()),
            st.tuples(st.just("nonce"), addr, _indices(), u64s()),
            st.tuples(
                st.just("code"), addr, _indices(), bytes_data(max_size=8)
            ),
            st.tuples(st.just("touch"), addr),
        ),
        max_size=30,
    )


def _feed(bal: ModuleType, builder: Any, ops: List[BuilderOp]) -> None:
    """Replay a list of operations against a builder."""
    for op in ops:
        kind = op[0]
        if kind == "storage_write":
            _, address, slot, index, value = op
            bal.add_storage_write(
                builder, address, slot, bal.BlockAccessIndex(index), value
            )
        elif kind == "storage_read":
            _, address, slot = op
            bal.add_storage_read(builder, address, slot)
        elif kind == "balance":
            _, address, index, balance = op
            bal.add_balance_change(
                builder, address, bal.BlockAccessIndex(index), balance
            )
        elif kind == "nonce":
            _, address, index, nonce = op
            bal.add_nonce_change(
                builder, address, bal.BlockAccessIndex(index), nonce
            )
        elif kind == "code":
            _, address, index, code = op
            bal.add_code_change(
                builder, address, bal.BlockAccessIndex(index), code
            )
        elif kind == "touch":
            _, address = op
            bal.add_touched_account(builder, address)
        else:
            raise ValueError(f"unhandled op: {kind}")


def _build(bal: ModuleType, tracker: ModuleType, builder: Any) -> Any:
    """Build the list from `builder` over a block that read nothing."""
    block_state = tracker.BlockState(pre_state=State())
    return bal.build_block_access_list(builder, block_state)


def _built(bal: ModuleType, tracker: ModuleType, ops: List[BuilderOp]) -> Any:
    """Feed `ops` into a fresh builder and return the built list."""
    builder = bal.BlockAccessListBuilder()
    _feed(bal, builder, ops)
    return _build(bal, tracker, builder)


def _norm(block_access_list: Any) -> List[Tuple[Any, ...]]:
    """Convert a built list into plain, comparable tuples."""
    out = []
    for account in block_access_list:
        storage_changes = tuple(
            (
                int(slot_changes.slot),
                tuple(
                    (int(c.block_access_index), int(c.new_value))
                    for c in slot_changes.changes
                ),
            )
            for slot_changes in account.storage_changes
        )
        storage_reads = tuple(int(slot) for slot in account.storage_reads)
        balance_changes = tuple(
            (int(c.block_access_index), int(c.post_balance))
            for c in account.balance_changes
        )
        nonce_changes = tuple(
            (int(c.block_access_index), int(c.new_nonce))
            for c in account.nonce_changes
        )
        code_changes = tuple(
            (int(c.block_access_index), bytes(c.new_code))
            for c in account.code_changes
        )
        out.append(
            (
                bytes(account.address),
                storage_changes,
                storage_reads,
                balance_changes,
                nonce_changes,
                code_changes,
            )
        )
    return out


def _model(ops: List[BuilderOp]) -> List[Tuple[Any, ...]]:
    """
    Reference model of the canonical list, written from the EIP-7928 rules
    rather than from the builder's code.
    """
    seen: Set[bytes] = set()
    storage: Dict[bytes, Dict[int, Dict[int, int]]] = {}
    reads: Dict[bytes, Set[int]] = {}
    balances: Dict[bytes, Dict[int, int]] = {}
    nonces: Dict[bytes, Dict[int, int]] = {}
    codes: Dict[bytes, Dict[int, bytes]] = {}

    for op in ops:
        kind = op[0]
        address = bytes(op[1])
        seen.add(address)
        if kind == "storage_write":
            _, _, slot, index, value = op
            by_slot = storage.setdefault(address, {})
            by_slot.setdefault(int(slot), {})[int(index)] = int(value)
        elif kind == "storage_read":
            _, _, slot = op
            reads.setdefault(address, set()).add(int(slot))
        elif kind == "balance":
            _, _, index, balance = op
            balances.setdefault(address, {})[int(index)] = int(balance)
        elif kind == "nonce":
            _, _, index, nonce = op
            # The builder keeps the highest nonce written at an index, as a
            # nonce never goes down within one; EIP-7928 records the nonce
            # the index ends with.
            nonce_at = nonces.setdefault(address, {})
            key = int(index)
            nonce_at[key] = max(int(nonce), nonce_at.get(key, int(nonce)))
        elif kind == "code":
            _, _, index, code = op
            codes.setdefault(address, {})[int(index)] = bytes(code)
        elif kind == "touch":
            pass
        else:
            raise ValueError(f"unhandled op: {kind}")

    def by_index(changes: Dict[int, Any]) -> Tuple[Any, ...]:
        return tuple((index, changes[index]) for index in sorted(changes))

    out = []
    for address in sorted(seen):
        written = storage.get(address, {})
        out.append(
            (
                address,
                tuple(
                    (slot, by_index(written[slot])) for slot in sorted(written)
                ),
                tuple(sorted(reads.get(address, set()) - set(written))),
                by_index(balances.get(address, {})),
                by_index(nonces.get(address, {})),
                by_index(codes.get(address, {})),
            )
        )
    return out


@pytest.mark.spec_unit
@given(ops=_ops())
def test_builder_matches_reference_model(
    bal: ModuleType, tracker: ModuleType, ops: List[BuilderOp]
) -> None:
    """
    The built list matches the reference model: last write wins per index,
    the builder keeps the highest nonce, read slots that were written are
    dropped, and everything is sorted.
    """
    assert _norm(_built(bal, tracker, ops)) == _model(ops)


@pytest.mark.spec_unit
@given(ops=_ops(), addr=st.sampled_from(ADDR_POOL))
def test_ensure_account_acts_as_a_touch(
    bal: ModuleType, tracker: ModuleType, ops: List[BuilderOp], addr: Address
) -> None:
    """
    `ensure_account` adds the address with no changes if it is missing,
    keeps everything already recorded, and a second call changes nothing.
    """
    builder = bal.BlockAccessListBuilder()
    _feed(bal, builder, ops)
    bal.ensure_account(builder, addr)
    once = _norm(_build(bal, tracker, builder))
    bal.ensure_account(builder, addr)
    twice = _norm(_build(bal, tracker, builder))
    assert once == _model(ops + [("touch", addr)])
    assert twice == once


@given(ops=_ops())
def test_gas_limit_boundary_is_exact(
    bal: ModuleType, fork: Fork, tracker: ModuleType, ops: List[BuilderOp]
) -> None:
    """
    Validation accepts a list whose addresses plus unique storage keys use
    exactly the block gas limit's item budget, and rejects one gas less.
    """
    built = _built(bal, tracker, ops)
    # The framework counts the items the EIP-7928 cap prices.
    items = BlockAccessList.from_rlp(Bytes(rlp.encode(built))).item_count()
    assume(items >= 1)
    # Longer lists put more weight on the item count the limit prices.
    target(items, label="items in the list")

    item_cost = fork.gas_costs().BLOCK_ACCESS_LIST_ITEM
    at_limit = Uint(items * item_cost)
    bal.validate_block_access_list_gas_limit(built, at_limit)

    below = Uint(items * item_cost - 1)
    with pytest.raises(bal.BlockAccessListGasLimitExceededError):
        bal.validate_block_access_list_gas_limit(built, below)


# Small pools, so that transactions often name the same account or slot.
ADDRESSES = [Address(bytes([i]) * 20) for i in (3, 1, 2)]
# Only creations and reads name this address, so it holds no nonce, code or
# storage whenever a creation starts.
CREATED = Address(b"\x04" * 20)
SLOTS = [Bytes32(bytes([i]) * 32) for i in (1, 2)]
CODES = [Bytes(b""), Bytes(b"\x00"), Bytes(b"\x60\x00")]


@dataclass
class ModelAccount:
    """An account as the property tracks it: a client's view of state."""

    balance: int = 0
    nonce: int = 0
    code: bytes = b""
    storage: Dict[int, int] = field(default_factory=dict)


ModelState = Dict[bytes, ModelAccount]

# The balance and code a transaction sets on an account, and how far it
# moves the nonce (a nonce never goes down). Small ranges, so a write often
# leaves a field where it was.
Write = Tuple[int, int, bytes]
SlotWrites = List[Tuple[Bytes32, int]]
# What a transaction does to an account: `write` writes it, `revert` writes
# it in a call that rolls back, `read` only reads it, and `create` creates
# it and destroys it in the same transaction, as EIP-6780 allows.
Tx = Tuple[str, Address, Write, SlotWrites]


def writes() -> st.SearchStrategy[Write]:
    """Return the balance, nonce increment and code a transaction sets."""
    return st.tuples(
        st.integers(0, 3), st.integers(0, 2), st.sampled_from(CODES)
    )


def blocks() -> st.SearchStrategy[List[List[Tx]]]:
    """Return a block: per block access index, the transactions in it."""
    slot_writes = st.lists(
        st.tuples(st.sampled_from(SLOTS), st.integers(0, 3)), max_size=2
    )
    named = st.sampled_from(ADDRESSES)
    tx = st.one_of(
        st.tuples(st.just("write"), named, writes(), slot_writes),
        st.tuples(st.just("revert"), named, writes(), slot_writes),
        st.tuples(
            st.just("read"),
            st.sampled_from([*ADDRESSES, CREATED]),
            writes(),
            slot_writes,
        ),
        st.tuples(st.just("create"), st.just(CREATED), writes(), slot_writes),
    )
    return st.lists(st.lists(tx, min_size=1, max_size=2), max_size=4)


def pre_states() -> st.SearchStrategy[ModelState]:
    """Return a few accounts with balances, nonces, code and storage."""
    account = st.builds(
        ModelAccount,
        balance=st.integers(0, 3),
        nonce=st.integers(1, 3),
        code=st.sampled_from(CODES),
        storage=st.dictionaries(
            st.sampled_from([int.from_bytes(s, "big") for s in SLOTS]),
            st.integers(1, 3),
            max_size=2,
        ),
    )
    return st.dictionaries(
        st.sampled_from([bytes(a) for a in ADDRESSES]), account, max_size=3
    )


def spec_pre_state(model: ModelState) -> State:
    """Return the spec's `State` holding the model accounts."""
    state = State()
    for address, account in model.items():
        code_hash = store_code(state, Bytes(account.code))
        set_account(
            state,
            Address(address),
            Account(Uint(account.nonce), U256(account.balance), code_hash),
        )
        for slot, value in account.storage.items():
            set_storage(
                state,
                Address(address),
                Bytes32(slot.to_bytes(32)),
                U256(value),
            )
    return state


def never_empty(nonce: int, write: Write) -> Write:
    """
    Return the write, moving the nonce if it would leave the account empty.

    EIP-7523 leaves the spec undefined for an empty account after the
    merge, so no transaction here leaves one.
    """
    balance, increment, code = write
    if nonce + increment == 0 and balance == 0 and not code:
        increment = 1
    return balance, increment, code


def write_account(
    tracker: ModuleType,
    tx_state: object,
    address: Address,
    write: Write,
    slot_writes: SlotWrites,
) -> None:
    """Write an account and its slots through the spec's state tracker."""
    nonce = tracker.get_account(tx_state, address).nonce
    balance, increment, code = never_empty(int(nonce), write)
    tracker.set_account(
        tx_state,
        address,
        Account(nonce + Uint(increment), U256(balance), keccak256(code)),
    )
    tracker.set_code(tx_state, address, Bytes(code))
    for slot, value in slot_writes:
        # `SSTORE` reads the slot before it writes it.
        tracker.get_storage(tx_state, address, slot)
        tracker.set_storage(tx_state, address, slot, U256(value))


def run_tx(tracker: ModuleType, tx_state: object, tx: Tx) -> None:
    """Run a transaction through the spec's state tracker."""
    kind, address, write, slot_writes = tx
    if kind == "write":
        write_account(tracker, tx_state, address, write, slot_writes)
    elif kind == "revert":
        snapshot = tracker.copy_tx_state(tx_state)
        write_account(tracker, tx_state, address, write, slot_writes)
        tracker.restore_tx_state(tx_state, snapshot)
    elif kind == "read":
        tracker.get_account(tx_state, address)
        for slot, _ in slot_writes:
            tracker.get_storage(tx_state, address, slot)
    elif kind == "create":
        balance, _, code = write
        tracker.mark_account_created(tx_state, address)
        write_account(
            tracker, tx_state, address, (balance, 1, code), slot_writes
        )
        tracker.clear_account_preserving_balance(tx_state, address)
    else:
        raise ValueError(f"unhandled transaction kind: {kind}")


@dataclass
class Touched:
    """The accounts and slots a block's transactions named."""

    accounts: Set[bytes] = field(default_factory=set)
    slots: Dict[bytes, Set[int]] = field(default_factory=dict)


def apply_tx(model: ModelState, touched: Touched, tx: Tx) -> None:
    """Apply a transaction to the model state and the touched set."""
    kind, address, write, slot_writes = tx
    key = bytes(address)
    touched.accounts.add(key)
    touched.slots.setdefault(key, set()).update(
        int.from_bytes(slot, "big") for slot, _ in slot_writes
    )
    if kind in ("revert", "read"):
        return
    account = model.setdefault(key, ModelAccount())
    if kind == "create":
        # Destroying the account keeps only its balance, and an account
        # left with none is gone.
        model[key] = ModelAccount(balance=write[0])
        if write[0] == 0:
            del model[key]
        return
    balance, increment, code = never_empty(account.nonce, write)
    account.balance, account.code = balance, code
    account.nonce += increment
    for slot, value in slot_writes:
        account.storage[int.from_bytes(slot, "big")] = value


Field = Tuple[bytes, str | int]
"""An address with `balance`, `nonce`, `code` or a storage slot."""


def changes_of(pre: ModelState, post: ModelState) -> Dict[Field, int | bytes]:
    """Return every field whose value differs between two states."""
    changed: Dict[Field, int | bytes] = {}
    for address in pre.keys() | post.keys():
        before = pre.get(address, ModelAccount())
        after = post.get(address, ModelAccount())
        fields: Dict[str | int, Tuple[int | bytes, int | bytes]] = {
            "balance": (before.balance, after.balance),
            "nonce": (before.nonce, after.nonce),
            "code": (before.code, after.code),
        }
        for slot in before.storage.keys() | after.storage.keys():
            fields[slot] = (
                before.storage.get(slot, 0),
                after.storage.get(slot, 0),
            )
        for name, (old, new) in fields.items():
            if old != new:
                changed[address, name] = new
    return changed


Changes = List[Tuple[int, int | bytes]]
"""The values a field took, by block access index."""
Entry = Dict[str | int, Any]
"""One account's entry: its changes by field, and its read slots."""


def listed(bal: BlockAccessList) -> Dict[bytes, Entry]:
    """Return every account the list names, with all it records."""
    accounts: Dict[bytes, Entry] = {}
    for entry in bal.root:
        recorded: Entry = {
            "balance": [
                (int(c.block_access_index), int(c.post_balance))
                for c in entry.balance_changes
            ],
            "nonce": [
                (int(c.block_access_index), int(c.post_nonce))
                for c in entry.nonce_changes
            ],
            "code": [
                (int(c.block_access_index), bytes(c.new_code))
                for c in entry.code_changes
            ],
            "reads": [int(slot) for slot in entry.storage_reads],
        }
        for slot in entry.storage_changes:
            recorded[int(slot.slot)] = [
                (int(c.block_access_index), int(c.post_value))
                for c in slot.slot_changes
            ]
        accounts[bytes(entry.address)] = recorded
    return accounts


def expected_list(
    touched: Touched, changes: Dict[Field, Changes]
) -> Dict[bytes, Entry]:
    """
    Return what EIP-7928 says the list holds: every account a transaction
    named, its changes by index, and the slots it touched but never changed
    as reads.
    """
    accounts: Dict[bytes, Entry] = {}
    for address in touched.accounts | {address for address, _ in changes}:
        changed_slots = {
            name
            for (a, name), _ in changes.items()
            if a == address and isinstance(name, int)
        }
        entry: Entry = {
            name: changes.get((address, name), [])
            for name in ("balance", "nonce", "code")
        }
        entry["reads"] = sorted(
            touched.slots.get(address, set()) - changed_slots
        )
        for slot in changed_slots:
            entry[slot] = changes[address, slot]
        accounts[address] = entry
    return accounts


@given(pre=pre_states(), block=blocks())
@example(
    pre={},
    block=[
        [("write", ADDRESSES[0], (0, 0, b""), [(SLOTS[0], 1)])],
        [("write", ADDRESSES[0], (0, 0, b""), [])],
        [("write", ADDRESSES[0], (0, 0, b""), [(SLOTS[0], 1)])],
    ],
)
# Two transactions at one index, the second restoring the slot the first
# changed: the index changed nothing, so the slot is only a read.
@example(
    pre={
        bytes(ADDRESSES[0]): ModelAccount(
            balance=1, nonce=1, storage={int.from_bytes(SLOTS[0], "big"): 1}
        )
    },
    block=[
        [
            ("write", ADDRESSES[0], (1, 0, b""), [(SLOTS[0], 2)]),
            ("write", ADDRESSES[0], (1, 0, b""), [(SLOTS[0], 1)]),
        ]
    ],
)
def test_list_records_the_block_exactly(
    bal: ModuleType,
    tracker: ModuleType,
    pre: ModelState,
    block: List[List[Tx]],
) -> None:
    """
    The list names every account a transaction touched, records a field at
    an index exactly when the index changed it, with the value the index
    left, and lists every other slot a transaction touched as a read.
    """
    block_state = tracker.BlockState(pre_state=spec_pre_state(pre))
    builder = bal.BlockAccessListBuilder()
    model = copy.deepcopy(pre)
    touched = Touched()
    changes: Dict[Field, Changes] = {}
    for index, txs in enumerate(block, start=1):
        builder.block_access_index = bal.BlockAccessIndex(index)
        at_start = copy.deepcopy(model)
        for tx in txs:
            tx_state = tracker.TransactionState(parent=block_state)
            run_tx(tracker, tx_state, tx)
            tracker.incorporate_tx_into_block(tx_state, builder)
            apply_tx(model, touched, tx)
        for name, value in changes_of(at_start, model).items():
            changes.setdefault(name, []).append((index, value))

    spec_list = bal.build_block_access_list(builder, block_state)
    encoded = rlp.encode(spec_list)
    built = BlockAccessList.from_rlp(Bytes(encoded))
    built.validate_structure()
    assert listed(built) == expected_list(touched, changes)
    # The framework encodes and hashes the same list to the same bytes.
    assert bytes(built.rlp) == encoded
    assert bytes(built.rlp_hash) == bytes(
        bal.hash_block_access_list(spec_list)
    )
