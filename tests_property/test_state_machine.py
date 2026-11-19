"""
Model-based test of each fork's `state_tracker`.

A state machine runs account, storage, snapshot, rollback and commit
operations on a `TransactionState` over a random pre-state, and checks every
read, original value and transient value against a plain Python model, so
reads also fall through to earlier transactions and the pre-state. Which
operations a fork has comes from its `state_tracker` module, as a unit test
of the spec's own data structure.
"""

import copy
from dataclasses import replace
from types import ModuleType
from typing import Any, Dict, List, NamedTuple, Optional, Set, Tuple

import pytest
from ethereum_types.bytes import Bytes, Bytes20, Bytes32
from ethereum_types.numeric import U256, Uint
from execution_testing.forks import Fork
from hypothesis import settings
from hypothesis import strategies as st
from hypothesis.stateful import (
    RuleBasedStateMachine,
    initialize,
    invariant,
    precondition,
    rule,
    run_state_machine_as_test,
)

from ethereum.crypto.hash import keccak256
from ethereum.state import EMPTY_CODE_HASH, Account
from ethereum.state_mpt import State, set_account, set_storage, store_code
from ethereum_spec_tools.forks import Hardfork

from .spec_api import (
    modify_deletes_empty_accounts,
)

# Small pools, so that operations often hit the same account or slot.
ADDRESSES = [Bytes20(bytes([i]) * 20) for i in range(1, 5)]
KEYS = [Bytes32(bytes([i]) * 32) for i in range(1, 4)]
CODES = [b"", b"\x01", b"\x02"]
CODE_HASHES = [keccak256(code) for code in CODES]


pytestmark = pytest.mark.spec_unit


class ModelAccount(NamedTuple):
    """An account in the model; the defaults make an empty account."""

    nonce: int = 0
    balance: int = 0
    code_hash: bytes = bytes(EMPTY_CODE_HASH)


Accounts = Dict[Bytes20, ModelAccount]
Storage = Dict[Bytes20, Dict[Bytes32, int]]


@st.composite
def pre_states(draw: st.DrawFn) -> Tuple[Accounts, Storage]:
    """Return a few non-empty accounts, some with storage."""
    accounts = draw(
        st.dictionaries(
            st.sampled_from(ADDRESSES),
            st.builds(
                ModelAccount,
                st.integers(1, 3),
                st.integers(0, 3),
                st.sampled_from([bytes(h) for h in CODE_HASHES]),
            ),
            max_size=3,
        )
    )
    storage = {
        address: draw(
            st.dictionaries(st.sampled_from(KEYS), st.integers(1, 3))
        )
        for address in accounts
    }
    return accounts, {a: slots for a, slots in storage.items() if slots}


def spec_state(accounts: Accounts, storage: Storage) -> State:
    """Return the spec's pre-state holding the model's accounts."""
    state = State()
    # A committed account's code is looked up by its hash, so the state
    # holds every code an account here can name.
    for code in CODES:
        store_code(state, Bytes(code))
    for address, account in accounts.items():
        set_account(
            state,
            address,
            Account(
                nonce=Uint(account.nonce),
                balance=U256(account.balance),
                code_hash=Bytes32(account.code_hash),
            ),
        )
        for key, value in storage.get(address, {}).items():
            set_storage(state, address, key, U256(value))
    return state


class StateTrackerMachine(RuleBasedStateMachine):
    """Run a fork's `state_tracker` against a model of accounts."""

    tracker: ModuleType
    bal: Optional[ModuleType]
    """The fork's block access list module, where its blocks carry one."""

    def __init__(self) -> None:
        super().__init__()
        self.accounts: Accounts = {}
        self.storage: Storage = {}
        self.original: Storage = {}
        self.committed: Accounts = {}
        self.transient: Dict[Tuple[Bytes20, Bytes32], int] = {}
        self.created: Set[Bytes20] = set()
        self.read_accounts: Set[Bytes20] = set()
        self.read_slots: Set[Tuple[Bytes20, Bytes32]] = set()
        self.snapshots: List[Tuple[object, Accounts, Storage, Dict]] = []

    @initialize(pre=pre_states())
    def start(self, pre: Tuple[Accounts, Storage]) -> None:
        """Open a transaction in a block over a random pre-state."""
        accounts, storage = pre
        block = self.tracker.BlockState(
            pre_state=spec_state(accounts, storage)
        )
        self.tx = self.tracker.TransactionState(parent=block)
        self.accounts = dict(accounts)
        self.storage = copy.deepcopy(storage)
        self.original = copy.deepcopy(storage)
        self.committed = dict(accounts)

    def _probe(self) -> Any:
        """
        Return a view of the transaction to check reads on, so the checks
        add nothing to the reads the transaction records.
        """
        if self.bal is None:
            return self.tx
        return replace(self.tx, account_reads=set(), storage_reads=set())

    def _account(self, addr: Bytes20) -> ModelAccount:
        """Return the model account, or an empty one if it is absent."""
        return self.accounts.get(addr, ModelAccount())

    def _modify(self, addr: Bytes20, account: ModelAccount) -> None:
        """Write an account, deleting it if it is empty and the fork does."""
        if account == ModelAccount() and modify_deletes_empty_accounts(
            self.tracker
        ):
            self.accounts.pop(addr, None)
            self.storage.pop(addr, None)
        else:
            self.accounts[addr] = account

    @rule(
        addr=st.sampled_from(ADDRESSES),
        nonce=st.integers(0, 5),
        balance=st.integers(0, 10),
        code_hash=st.sampled_from(CODE_HASHES),
    )
    def set_account(
        self, addr: Bytes20, nonce: int, balance: int, code_hash: Bytes32
    ) -> None:
        """Write an account directly, keeping it even when empty."""
        self.tracker.set_account(
            self.tx,
            addr,
            Account(
                nonce=Uint(nonce), balance=U256(balance), code_hash=code_hash
            ),
        )
        self.accounts[addr] = ModelAccount(nonce, balance, bytes(code_hash))

    @rule(addr=st.sampled_from(ADDRESSES))
    def delete_account(self, addr: Bytes20) -> None:
        """Delete an account but keep its storage."""
        self.tracker.set_account(self.tx, addr, None)
        self.accounts.pop(addr, None)

    @rule(addr=st.sampled_from(ADDRESSES))
    def increment_nonce(self, addr: Bytes20) -> None:
        """Increment an account's nonce."""
        self.tracker.increment_nonce(self.tx, addr)
        account = self._account(addr)
        self._modify(addr, account._replace(nonce=account.nonce + 1))

    @rule(addr=st.sampled_from(ADDRESSES), amount=st.integers(0, 10))
    def create_ether(self, addr: Bytes20, amount: int) -> None:
        """Add ether to an account."""
        self.tracker.create_ether(self.tx, addr, U256(amount))
        account = self._account(addr)
        self._modify(addr, account._replace(balance=account.balance + amount))

    @rule(
        sender=st.sampled_from(ADDRESSES),
        recipient=st.sampled_from(ADDRESSES),
        amount=st.integers(0, 10),
    )
    def move_ether(
        self, sender: Bytes20, recipient: Bytes20, amount: int
    ) -> None:
        """Transfer ether between two accounts."""
        if sender not in self.accounts:
            return
        if self.accounts[sender].balance < amount:
            return
        self.tracker.move_ether(self.tx, sender, recipient, U256(amount))
        # The sender is debited before the recipient is credited, which
        # matters when they are the same account or the sender empties.
        debited = self._account(sender)
        self._modify(
            sender, debited._replace(balance=debited.balance - amount)
        )
        credited = self._account(recipient)
        self._modify(
            recipient, credited._replace(balance=credited.balance + amount)
        )

    @rule(
        sender=st.sampled_from(ADDRESSES),
        recipient=st.sampled_from(ADDRESSES),
    )
    def overdraw(self, sender: Bytes20, recipient: Bytes20) -> None:
        """Moving more ether than the sender holds is refused."""
        amount = self._account(sender).balance + 1
        with pytest.raises(AssertionError):
            self.tracker.move_ether(self.tx, sender, recipient, U256(amount))

    @rule(
        addr=st.sampled_from(ADDRESSES),
        code=st.sampled_from([b"", b"\x60\x00", b"\x01\x02\x03"]),
    )
    def set_code(self, addr: Bytes20, code: bytes) -> None:
        """Set an account's code."""
        self.tracker.set_code(self.tx, addr, Bytes(code))
        account = self._account(addr)
        self._modify(addr, account._replace(code_hash=bytes(keccak256(code))))

    @precondition(lambda self: bool(self.accounts))
    @rule(
        data=st.data(),
        key=st.sampled_from(KEYS),
        value=st.integers(0, 10),
    )
    def set_storage(
        self, data: st.DataObject, key: Bytes32, value: int
    ) -> None:
        """Set a storage slot on an account that exists."""
        addr = data.draw(st.sampled_from(sorted(self.accounts)))
        self.tracker.set_storage(self.tx, addr, key, U256(value))
        self.storage.setdefault(addr, {})[key] = value

    @rule(addr=st.sampled_from(ADDRESSES))
    def destroy_account(self, addr: Bytes20) -> None:
        """Destroy an account and its storage."""
        self.tracker.destroy_account(self.tx, addr)
        self.accounts.pop(addr, None)
        self.storage.pop(addr, None)

    @rule(addr=st.sampled_from(ADDRESSES))
    def mark_created(self, addr: Bytes20) -> None:
        """Mark an account created in this transaction."""
        self.tracker.mark_account_created(self.tx, addr)
        self.created.add(addr)

    @precondition(
        lambda self: hasattr(self.tracker, "clear_account_preserving_balance")
    )
    @rule(addr=st.sampled_from(ADDRESSES))
    def clear_account(self, addr: Bytes20) -> None:
        """Clear an account's nonce, code and storage, keeping its balance."""
        self.tracker.clear_account_preserving_balance(self.tx, addr)
        self.storage.pop(addr, None)
        balance = self._account(addr).balance
        self._modify(addr, ModelAccount(balance=balance))

    @rule(
        addr=st.sampled_from(ADDRESSES),
        key=st.sampled_from(KEYS),
        value=st.integers(0, 10),
    )
    def set_transient(self, addr: Bytes20, key: Bytes32, value: int) -> None:
        """Set a transient storage slot (EIP-1153)."""
        self.tracker.set_transient_storage(self.tx, addr, key, U256(value))
        self.transient[addr, key] = value

    @rule(addr=st.sampled_from(ADDRESSES), key=st.sampled_from(KEYS))
    def read(self, addr: Bytes20, key: Bytes32) -> None:
        """Read an account and one of its slots."""
        self.tracker.get_account_optional(self.tx, addr)
        self.tracker.get_storage(self.tx, addr, key)
        self.read_accounts.add(addr)
        self.read_slots.add((addr, key))

    @rule()
    def snapshot(self) -> None:
        """Snapshot the transaction state for rollback."""
        snap = self.tracker.copy_tx_state(self.tx)
        self.snapshots.append(
            (
                snap,
                copy.deepcopy(self.accounts),
                copy.deepcopy(self.storage),
                dict(self.transient),
            )
        )

    @precondition(lambda self: bool(self.snapshots))
    @rule()
    def rollback(self) -> None:
        """Roll back to the most recent snapshot; reads are kept."""
        snap, accounts, storage, transient = self.snapshots.pop()
        self.tracker.restore_tx_state(self.tx, snap)
        # `mark_account_created` documents that a rollback keeps the mark.
        self.accounts = accounts
        self.storage = storage
        self.transient = transient

    @rule()
    def commit(self) -> None:
        """Commit the transaction to the block and start the next one."""
        if self.bal is None:
            self.tracker.incorporate_tx_into_block(self.tx)
        else:
            builder = self.bal.BlockAccessListBuilder()
            self.tracker.incorporate_tx_into_block(self.tx, builder)
        self.original = copy.deepcopy(self.storage)
        self.committed = dict(self.accounts)
        self.transient = {}
        self.created = set()
        self.snapshots = []

    @invariant()
    def accounts_match(self) -> None:
        """Every account read matches the model."""
        probe = self._probe()
        for addr in ADDRESSES:
            actual = self.tracker.get_account_optional(probe, addr)
            model = self.accounts.get(addr)
            if model is None:
                assert actual is None, f"{addr!r} should be absent"
            else:
                assert actual is not None, f"{addr!r} should exist"
                assert (
                    ModelAccount(
                        int(actual.nonce),
                        int(actual.balance),
                        bytes(actual.code_hash),
                    )
                    == model
                )

    @invariant()
    def storage_matches(self) -> None:
        """Every storage read matches the model."""
        probe = self._probe()
        for addr in ADDRESSES:
            for key in KEYS:
                actual = self.tracker.get_storage(probe, addr, key)
                expected = self.storage.get(addr, {}).get(key, 0)
                assert int(actual) == expected

    @invariant()
    def account_predicates_match(self) -> None:
        """
        Existence, EIP-161 emptiness and liveness, and EIP-684's room for
        a new contract (no nonce and no code) match the model.
        """
        probe = self._probe()
        empty = ModelAccount()
        for addr in ADDRESSES:
            model = self.accounts.get(addr)
            account = model or empty
            assert self.tracker.account_exists(probe, addr) == (
                model is not None
            )
            assert self.tracker.account_exists_and_is_empty(probe, addr) == (
                model == empty
            )
            assert self.tracker.is_account_alive(probe, addr) == (
                model is not None and model != empty
            )
            assert self.tracker.account_deployable(probe, addr) == (
                account.nonce == 0
                and account.code_hash == bytes(EMPTY_CODE_HASH)
            )

    @precondition(lambda self: hasattr(self.tracker, "get_pre_state_account"))
    @invariant()
    def pre_transaction_accounts_match(self) -> None:
        """The account before the transaction is the one last committed."""
        for addr in ADDRESSES:
            actual = self.tracker.get_pre_state_account(self.tx, addr)
            expected = self.committed.get(addr, ModelAccount())
            assert (
                ModelAccount(
                    int(actual.nonce),
                    int(actual.balance),
                    bytes(actual.code_hash),
                )
                == expected
            )

    @invariant()
    def original_storage_matches(self) -> None:
        """
        The original value of a slot is the one the transaction started
        with, and zero for an account the transaction created.
        """
        for addr in ADDRESSES:
            for key in KEYS:
                actual = self.tracker.get_storage_original(self.tx, addr, key)
                expected = (
                    0
                    if addr in self.created
                    else self.original.get(addr, {}).get(key, 0)
                )
                assert int(actual) == expected

    @invariant()
    def transient_storage_matches(self) -> None:
        """Every transient read matches the model."""
        for addr in ADDRESSES:
            for key in KEYS:
                actual = self.tracker.get_transient_storage(self.tx, addr, key)
                assert int(actual) == self.transient.get((addr, key), 0)

    @invariant()
    def reads_are_kept(self) -> None:
        """
        Every account and slot read stays recorded through rollbacks, in
        the transaction or, once committed, the block.
        """
        if self.bal is None:
            return
        block = self.tx.parent
        assert self.read_accounts <= (
            self.tx.account_reads | block.account_reads
        )
        assert self.read_slots <= (self.tx.storage_reads | block.storage_reads)

    @invariant()
    def created_matches(self) -> None:
        """The created-accounts set matches the model."""
        assert set(self.tx.created_accounts) == self.created


def test_state_tracker_matches_model(
    fork: Fork, spec: Hardfork, tracker: ModuleType
) -> None:
    """The state tracker agrees with the model on every operation sequence."""
    bal = (
        spec.module("block_access_lists")
        if fork.header_bal_hash_required()
        else None
    )
    machine = type(
        "StateTrackerMachine",
        (StateTrackerMachine,),
        {"tracker": tracker, "bal": bal},
    )
    run_state_machine_as_test(
        machine, settings=settings(stateful_step_count=40)
    )
