"""Account-related types for Ethereum tests."""

import json
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum, auto
from hashlib import sha256
from types import ModuleType
from typing import (
    Any,
    Dict,
    ItemsView,
    Iterator,
    List,
    Literal,
    Optional,
    Self,
)

import ethereum.state as spec_state
import ethereum.state_mpt as spec_state_mpt
from ethereum.crypto.hash import Hash32
from ethereum.crypto.hash import keccak256 as spec_keccak256
from ethereum_types.bytes import Bytes, Bytes20
from ethereum_types.numeric import U256, Bytes32, Uint
from pydantic import PrivateAttr
from spec256k1 import PrivateKey

from execution_testing.base_types import (
    Account,
    Address,
    FixedSizeBytes,
    Hash,
    HashInt,
    Number,
    StateCommitment,
    Storage,
    StorageRootType,
)
from execution_testing.base_types import Alloc as BaseAlloc
from execution_testing.base_types.conversions import (
    BytesConvertible,
    FixedSizeBytesConvertible,
    NumberConvertible,
)

from .utils import keccak256


class _Phase(Enum):
    """
    Lifecycle phase of an `Alloc` instance used as a `PreState`.

    See `Alloc` for the rules each phase enforces.
    """

    CONSTRUCTION = auto()
    """Free mutations on `self.root` are allowed; no cache exists."""
    LIVE = auto()
    """Cache built; only `apply_diff` may mutate."""
    FROZEN = auto()
    """No mutations are allowed."""


class EOA(Address):
    """
    An Externally Owned Account (EOA) is an account controlled by a private
    key.

    The EOA is defined by its address and (optionally) by its corresponding
    private key.
    """

    key: Hash | None
    nonce: Number

    def __new__(
        cls,
        address: "FixedSizeBytesConvertible | Address | EOA | None" = None,
        *,
        key: FixedSizeBytesConvertible | None = None,
        nonce: NumberConvertible = 0,
    ) -> "EOA":
        """Init the EOA."""
        if address is None:
            if key is None:
                raise ValueError(
                    "impossible to initialize EOA without address"
                )
            private_key = PrivateKey(Hash(key))
            public_key = private_key.public_key
            address = Address(
                keccak256(public_key.format(compressed=False)[1:])[32 - 20 :]
            )
        elif isinstance(address, EOA):
            return address
        instance = super(EOA, cls).__new__(cls, address)
        instance.key = Hash(key) if key is not None else None
        instance.nonce = Number(nonce)
        return instance

    def get_nonce(self) -> Number:
        """Return current nonce of the EOA and increments it by one."""
        nonce = self.nonce
        self.nonce = Number(nonce + 1)
        return nonce

    def copy(self) -> Self:
        """Return copy of the EOA."""
        return self.__class__(Address(self), key=self.key, nonce=self.nonce)


class AllocGroupHash(FixedSizeBytes[8]):  # type: ignore
    """Class that helps represent hashes used to group allocs."""

    @classmethod
    def from_preimage(cls, x: str | bytes) -> "AllocGroupHash":
        """
        Perform a hash (sha256) then truncate the output to get the alloc
        hash.
        """
        if isinstance(x, str):
            x = x.encode("utf-8")
        return cls(sha256(x).digest()[:8])

    def __xor__(self, other: "int | AllocGroupHash") -> "AllocGroupHash":
        """
        Alloc hashes are usually combination of multiple inputs via
        XOR operation.
        """
        if isinstance(other, int):
            other = AllocGroupHash(other)
        return AllocGroupHash(
            bytes(a ^ b for a, b in zip(self, other, strict=True))
        )


class Alloc(BaseAlloc):
    """
    Allocation of accounts in the state, pre and post test execution.

    Doubles as a `PreState` provider for the spec's state transition: once
    any `PreState` method is called the instance transitions from
    `CONSTRUCTION` to `LIVE` (a code-hash → bytes cache is built once) and
    further free mutations via `__setitem__`/`__delitem__` are rejected.
    The only mutation entry point in `LIVE` is `apply_diff`, which patches
    `self.root` and updates the cache in lockstep. `freeze` locks the
    allocation for read-only assertion use.
    """

    _phase: _Phase = PrivateAttr(default=_Phase.CONSTRUCTION)
    _code_store: Dict[Hash32, Bytes] = PrivateAttr(default_factory=dict)
    _state_commitment: StateCommitment | None = PrivateAttr(default=None)
    """
    Commitment scheme this allocation's state root is computed under.

    Unset by default: it must be seeded from the accompanying fork before any
    state-root computation.
    """

    @dataclass(kw_only=True)
    class UnexpectedAccountError(Exception):
        """Unexpected account found in the allocation."""

        address: Address
        account: Account | None

        def __str__(self) -> str:
            """Print exception string."""
            return (
                f"unexpected account in allocation {self.address}: "
                f"{self.account}"
            )

    @dataclass(kw_only=True)
    class MissingAccountError(Exception):
        """Expected account not found in the allocation."""

        address: Address

        def __str__(self) -> str:
            """Print exception string."""
            return f"Account missing from allocation {self.address}"

    @dataclass(kw_only=True)
    class CollisionError(Exception):
        """Different accounts at the same address."""

        address: Address
        account_1: Account | None
        account_2: Account | None

        def to_json(self) -> Dict[str, Any]:
            """Dump to json object."""
            return {
                "address": self.address.hex(),
                "account_1": self.account_1.model_dump(mode="json")
                if self.account_1 is not None
                else None,
                "account_2": self.account_2.model_dump(mode="json")
                if self.account_2 is not None
                else None,
            }

        @classmethod
        def from_json(cls, obj: Dict[str, Any]) -> Self:
            """Parse from a json dict."""
            return cls(
                address=Address(obj["address"]),
                account_1=Account.model_validate(obj["account_1"])
                if obj["account_1"] is not None
                else None,
                account_2=Account.model_validate(obj["account_2"])
                if obj["account_2"] is not None
                else None,
            )

        def __str__(self) -> str:
            """Print exception string."""
            return (
                "Overlapping key defining different accounts detected:\n"
                f"{json.dumps(self.to_json(), indent=2)}"
            )

    class KeyCollisionMode(Enum):
        """Mode for handling key collisions when merging allocations."""

        ERROR = auto()
        OVERWRITE = auto()
        ALLOW_IDENTICAL_ACCOUNTS = auto()

    @classmethod
    def merge(
        cls,
        alloc_1: "Alloc",
        alloc_2: "Alloc",
        key_collision_mode: KeyCollisionMode = KeyCollisionMode.OVERWRITE,
        state_commitment: StateCommitment | None = None,
    ) -> "Alloc":
        """Return merged allocation of two sources."""
        overlapping_keys = alloc_1.root.keys() & alloc_2.root.keys()
        if overlapping_keys:
            if key_collision_mode == cls.KeyCollisionMode.ERROR:
                raise Exception(
                    f"Overlapping keys detected: "
                    f"{[key.hex() for key in overlapping_keys]}"
                )
            elif (
                key_collision_mode
                == cls.KeyCollisionMode.ALLOW_IDENTICAL_ACCOUNTS
            ):
                # The overlapping keys must point to the exact same account
                for key in overlapping_keys:
                    account_1 = alloc_1[key]
                    account_2 = alloc_2[key]
                    if account_1 != account_2:
                        raise Alloc.CollisionError(
                            address=key,
                            account_1=account_1,
                            account_2=account_2,
                        )
        merged = alloc_1.model_copy(deep=True)

        for address, other_account in alloc_2.root.items():
            merged_account = Account.merge(merged.get(address), other_account)
            if merged_account:
                merged[address] = merged_account
            elif address in merged:
                merged.root.pop(address, None)

        if state_commitment is not None:
            merged.migrate_state_commitment(state_commitment)
        else:
            # By default, state commitment of the second alloc takes precedence
            merged.migrate_state_commitment(alloc_2.state_commitment())
        return merged

    def __iter__(self) -> Iterator[Address]:  # type: ignore [override]
        """Return iterator over the allocation."""
        return iter(self.root)

    def items(self) -> ItemsView[Address, Account | None]:
        """Return iterator over the allocation items."""
        return self.root.items()

    def __getitem__(
        self, address: Address | FixedSizeBytesConvertible
    ) -> Account | None:
        """Return account associated with an address."""
        if not isinstance(address, Address):
            address = Address(address)
        return self.root[address]

    def __setitem__(
        self,
        address: Address | FixedSizeBytesConvertible,
        account: Account | None,
    ) -> None:
        """Set account associated with an address."""
        self._require_construction("__setitem__")
        if not isinstance(address, Address):
            address = Address(address)
        self.root[address] = account

    def __delitem__(
        self, address: Address | FixedSizeBytesConvertible
    ) -> None:
        """Delete account associated with an address."""
        self._require_construction("__delitem__")
        if not isinstance(address, Address):
            address = Address(address)
        self.root.pop(address, None)

    def __eq__(self, other: object) -> bool:
        """Return True if both allocations are equal."""
        if not isinstance(other, Alloc):
            return False
        return self.root == other.root

    def __contains__(
        self, address: Address | FixedSizeBytesConvertible
    ) -> bool:
        """Check if an account is in the allocation."""
        if not isinstance(address, Address):
            address = Address(address)
        return address in self.root

    def get(self, address: Address) -> Account | None:
        """Get an account if it's present in the allocation, otherwise None."""
        account = self.root.get(address)
        if not account:
            return None
        return account

    def empty_accounts(self) -> List[Address]:
        """Return list of addresses of empty accounts."""
        return [
            address for address, account in self.root.items() if not account
        ]

    def state_root(self) -> Hash:
        """Return state root of the allocation."""
        return Hash(self._state_module().state_root(self._materialize_state()))

    def verify_post_alloc(self, got_alloc: "Alloc") -> None:
        """
        Verify that the allocation matches the expected post in the test.
        Raises exception on unexpected values.
        """
        assert isinstance(got_alloc, Alloc), (
            f"got_alloc is not an Alloc: {got_alloc}"
        )
        for address, account in self.root.items():
            if account is None:
                # Account must not exist
                got_account = got_alloc.get(address)
                if got_account:
                    raise Alloc.UnexpectedAccountError(
                        address=address, account=got_account
                    )
            else:
                if address in got_alloc.root:
                    got_account = got_alloc.root[address]
                    assert isinstance(got_account, Account)
                    assert isinstance(account, Account)
                    account.check_alloc(address, got_account)
                else:
                    raise Alloc.MissingAccountError(address=address)

    def get_alloc_grouping_hash(self) -> AllocGroupHash | None:
        """
        Return the grouping hash if the allocation belongs to a particular
        group, otherwise `None`.

        Method can be overloaded by other implementations of the Alloc to
        return the appropriate group.
        """
        return None

    def calculate_diff(self, base_alloc: "Alloc") -> "Alloc":
        """
        Calculate the state difference between self and a base.

        Returns an Alloc containing only the accounts that:
        - Changed between base and self (balance, nonce, storage, code)
        - Were created during test execution (new accounts)
        - Were deleted during test execution (represented as None)

        Args:
            base_alloc: Genesis pre-allocation state

        Returns:
            Alloc containing only the state differences for efficient storage

        """
        diff: Dict[Address, Account | None] = {}

        # Find all addresses that exist in either state
        all_addresses = set(self.root.keys()) | set(base_alloc.root.keys())

        for address in all_addresses:
            genesis_account = base_alloc.root.get(address)
            post_account = self.root.get(address)

            # Account was deleted (exists in genesis but not in post)
            if genesis_account is not None and post_account is None:
                diff[address] = None

            # Account was created (doesn't exist in genesis but exists in post)
            elif genesis_account is None and post_account is not None:
                diff[address] = post_account

            # Account was modified (exists in both but different)
            elif genesis_account != post_account:
                diff[address] = post_account

            # Account unchanged - don't include in diff

        return Alloc(diff)

    # ------------------------------------------------------------------
    # PreState protocol implementation
    # ------------------------------------------------------------------

    def _require_construction(self, operation: str) -> None:
        """Reject mutations once the allocation has left construction."""
        if self._phase is not _Phase.CONSTRUCTION:
            raise RuntimeError(
                f"{operation} not allowed: Alloc is in phase "
                f"{self._phase.name}. Mutate via apply_diff during LIVE, "
                f"or call freeze() to lock the allocation."
            )

    def _build_cache(self) -> None:
        """Populate the code-hash → bytes cache from `self.root`."""
        self._code_store = {spec_state.EMPTY_CODE_HASH: Bytes(b"")}
        for account in self.root.values():
            if account is None:
                continue
            code = bytes(account.code) if account.code else b""
            if not code:
                continue
            self._code_store[spec_keccak256(code)] = Bytes(code)

    def _ensure_live(self) -> None:
        """Transition from `CONSTRUCTION` to `LIVE`, building the cache."""
        if self._phase is _Phase.CONSTRUCTION:
            self._build_cache()
            self._phase = _Phase.LIVE

    def _state_module(self) -> ModuleType:
        """
        Return the spec state module implementing `self._state_commitment`.
        """
        if self._state_commitment is None:
            raise ValueError(
                "Alloc state commitment is unset; seed it from the "
                "accompanying fork."
            )
        if self._state_commitment is StateCommitment.MPT:
            return spec_state_mpt
        raise NotImplementedError("State commitment type not yet implemented.")

    def _materialize_state(self) -> spec_state.PreState:
        """
        Build a spec-side `PreState` mirror of `self.root` using the
        implementation module for this allocation's commitment scheme.

        Used as the trie-backed delegate for `compute_state_root` (a
        cold, once-per-block call). The materialized state is not
        retained.
        """
        mod = self._state_module()
        state: spec_state.PreState = mod.State()
        for address, account in self.root.items():
            if account is None:
                continue
            addr = Bytes20(address)
            code = bytes(account.code) if account.code else b""
            if code:
                code_hash = mod.store_code(state, code)
            else:
                code_hash = spec_state.EMPTY_CODE_HASH
            mod.set_account(
                state,
                addr,
                spec_state.Account(
                    nonce=Uint(int(account.nonce)),
                    balance=U256(int(account.balance)),
                    code_hash=code_hash,
                ),
            )
            for key_hi, value_hi in account.storage.root.items():
                value_int = int(value_hi)
                if value_int == 0:
                    continue
                mod.set_storage(
                    state,
                    addr,
                    Bytes32(int(key_hi).to_bytes(32, "big")),
                    U256(value_int),
                )
        return state

    def get_account_optional(
        self, address: Bytes20
    ) -> Optional[spec_state.Account]:
        """
        Return the spec-side `Account` at `address`, or `None`.

        Conforms to `ethereum.state.PreState.get_account_optional`.
        """
        self._ensure_live()
        account = self.root.get(Address(address))
        if account is None:
            return None
        code = bytes(account.code) if account.code else b""
        code_hash = (
            spec_keccak256(code) if code else spec_state.EMPTY_CODE_HASH
        )
        return spec_state.Account(
            nonce=Uint(int(account.nonce)),
            balance=U256(int(account.balance)),
            code_hash=code_hash,
        )

    def get_storage(self, address: Bytes20, key: Bytes32) -> U256:
        """
        Return the storage value at `key` for `address`, or `U256(0)`.

        Conforms to `ethereum.state.PreState.get_storage`.
        """
        self._ensure_live()
        account = self.root.get(Address(address))
        if account is None:
            return U256(0)
        key_int = int.from_bytes(bytes(key), "big")
        value_hi = account.storage.root.get(HashInt(key_int))
        if value_hi is None:
            return U256(0)
        return U256(int(value_hi))

    def get_code(self, code_hash: Hash32) -> Bytes:
        """
        Return the bytecode for `code_hash`.

        Conforms to `ethereum.state.PreState.get_code`.
        """
        self._ensure_live()
        if code_hash == spec_state.EMPTY_CODE_HASH:
            return Bytes(b"")
        return self._code_store[code_hash]

    def account_has_storage(self, address: Bytes20) -> bool:
        """
        Return whether the account at `address` has any storage slots set.

        Conforms to `ethereum.state.PreState.account_has_storage`.
        """
        self._ensure_live()
        account = self.root.get(Address(address))
        return account is not None and bool(account.storage.root)

    def compute_state_root(self, block_diff: spec_state.BlockDiff) -> Hash32:
        """
        Compute the state root after applying `block_diff` to the
        pre-state.

        Conforms to `ethereum.state.PreState.compute_state_root`.
        Builds the trie inline; `Alloc` does not cache `Trie`
        instances.
        """
        self._ensure_live()
        state = self._materialize_state()
        return state.compute_state_root(block_diff)

    # ------------------------------------------------------------------
    # Lifecycle: apply_diff and freeze
    # ------------------------------------------------------------------

    def apply_diff(self, diff: spec_state.BlockDiff) -> None:
        """
        Apply a `BlockDiff` to mutate the allocation in place.

        The only mutation entry point in the `LIVE` phase. Writes bypass
        `__setitem__` intentionally — `_code_store` is updated additively
        in lockstep with `self.root`.
        """
        if self._phase is _Phase.FROZEN:
            raise RuntimeError("apply_diff not allowed: Alloc is FROZEN")
        if self._phase is _Phase.CONSTRUCTION:
            raise RuntimeError(
                "apply_diff not allowed in CONSTRUCTION: the allocation "
                "has not been used as a PreState yet, so its cache is not "
                "built. Trigger a PreState method (or hand it to a "
                "BlockState) before calling apply_diff."
            )

        for code_hash, code in diff.code_changes.items():
            self._code_store[Hash32(code_hash)] = Bytes(code)

        for address in diff.storage_clears:
            addr = Address(address)
            current = self.root.get(addr)
            if current is not None and current.storage.root:
                self.root[addr] = current.model_copy(
                    update={"storage": Storage(root={})}
                )

        for address, spec_account in diff.account_changes.items():
            addr = Address(address)
            if spec_account is None:
                self.root.pop(addr, None)
                continue
            code_hash = Hash32(spec_account.code_hash)
            if code_hash == spec_state.EMPTY_CODE_HASH:
                code = Bytes(b"")
            else:
                code = self._code_store[code_hash]
            existing = self.root.get(addr)
            existing_storage = (
                existing.storage if existing is not None else Storage(root={})
            )
            self.root[addr] = Account(
                nonce=int(spec_account.nonce),
                balance=int(spec_account.balance),
                code=code,
                storage=existing_storage,
            )

        for address, slots in diff.storage_changes.items():
            addr = Address(address)
            account = self.root.get(addr)
            if account is None:
                continue
            merged: Dict[HashInt, HashInt] = dict(account.storage.root)
            for key, value in slots.items():
                key_int = HashInt(int.from_bytes(bytes(key), "big"))
                value_int = int(value)
                if value_int == 0:
                    merged.pop(key_int, None)
                else:
                    merged[key_int] = HashInt(value_int)
            self.root[addr] = account.model_copy(
                update={"storage": Storage(root=merged)}
            )

        # Drop zero-valued storage entries from every account. Ethereum
        # treats an absent slot as zero, so a literal ``{0x00: 0x00}``
        # pair carried over untouched from the pre-state JSON would
        # otherwise survive into the post-state dump and produce noise
        # the spec-state-backed pipeline never had (the spec's
        # ``set_storage`` drops zeros on insert).
        for addr, account in list(self.root.items()):
            if account is None or not account.storage.root:
                continue
            cleaned = {
                key: value
                for key, value in account.storage.root.items()
                if int(value) != 0
            }
            if len(cleaned) != len(account.storage.root):
                self.root[addr] = account.model_copy(
                    update={"storage": Storage(root=cleaned)}
                )

    def freeze(self) -> None:
        """Lock the allocation: no further mutations allowed."""
        self._phase = _Phase.FROZEN

    def state_commitment(self) -> StateCommitment | None:
        """
        Return the commitment scheme this allocation is committed under, or
        `None` if it has not been seeded from a fork yet.
        """
        return self._state_commitment

    def migrate_state_commitment(
        self, commitment: StateCommitment | None
    ) -> None:
        """
        Switch the commitment scheme used to compute the state root.
        """
        if self._phase is _Phase.FROZEN:
            raise RuntimeError(
                "migrate_state_commitment not allowed: Alloc is FROZEN"
            )
        self._state_commitment = commitment

    def deterministic_deploy_contract(
        self,
        *,
        deploy_code: BytesConvertible,
        salt: Hash | int = 0,
        initcode: BytesConvertible | None = None,
        storage: Storage | StorageRootType | None = None,
        label: str | None = None,
    ) -> Address:
        """
        Deploy a contract to the allocation at a deterministic location
        using a deterministic deployment proxy.

        The initcode is not executed during test filling; it is executed only
        when the tests run on live networks. Therefore, if the initcode
        performs modifications to the storage, these must be specified using
        the `storage` parameter.

        Args:
            deploy_code: Contract code to deploy.
            salt: Salt to use for deterministic deployment.
            initcode: Initcode to use for deterministic deployment.
                      If `None`, the initcode is derived from `deploy_code`.
            storage: The expected storage state of the deployed contract after
                     initcode execution.
            label: Label to use for the contract.

        """
        raise NotImplementedError(
            "deterministic_deploy_contract is not implemented in the base "
            "class"
        )

    def deploy_contract(
        self,
        code: BytesConvertible,
        *,
        storage: Storage | StorageRootType | None = None,
        balance: NumberConvertible = 0,
        nonce: NumberConvertible = 1,
        address: Address | None = None,
        label: str | None = None,
        stub: str | None = None,
    ) -> Address:
        """Deploy a contract to the allocation."""
        raise NotImplementedError(
            "deploy_contract is not implemented in the base class"
        )

    def stub_eoa(self, label: str) -> EOA:
        """Return the EOA for a key-bearing stub."""
        raise NotImplementedError(
            "stub_eoa is not implemented in the base class"
        )

    def fund_eoa(
        self,
        amount: NumberConvertible | None = None,
        label: str | None = None,
        storage: Storage | None = None,
        code: BytesConvertible | None = None,
        delegation: Address | Literal["Self"] | None = None,
        nonce: NumberConvertible | None = None,
    ) -> EOA:
        """
        Add a previously unused EOA to the pre-alloc with the balance specified
        by `amount`.
        """
        raise NotImplementedError(
            "fund_eoa is not implemented in the base class"
        )

    def fund_address(
        self,
        address: Address,
        amount: NumberConvertible,
        *,
        minimum_balance: bool = False,
    ) -> None:
        """
        Fund an address with a given amount.

        Add a funded account to the pre-allocation.
        The address must not already exist in the pre-allocation. To set the
        balance of an account, use the `amount` parameter in `fund_eoa()` or
        the `balance` parameter in `deploy_contract()` at creation time.

        Args:
            address: Address to fund
            amount: Amount to fund in Wei
            minimum_balance: If set to True, account will be checked to have a
                minimum balance of `amount` and only fund if the balance is
                insufficient

        """
        raise NotImplementedError(
            "fund_address is not implemented in the base class"
        )

    def nonexistent_account(self) -> Address:
        """
        Return the address of a previously unused nonexistent account.

        The address is guaranteed to not be a precompile or a system contract.
        No account is created — it remains nonexistent in the pre-state.
        """
        raise NotImplementedError(
            "nonexistent_account is not implemented in the base class"
        )

    def expect_account_state(
        self,
        addresses: Address | Sequence[Address],
        *,
        is_existing_account: bool = True,
        is_contract: bool = False,
        min_balance: int | None = None,
        code_prefix: bytes | None = None,
    ) -> None:
        """
        Register start-block expectation(s) for predeployed account(s).

        Accepts a single address or a range; labels ride on the addresses
        themselves. Used only by fill-stateful; ignored by other
        allocations.
        """

    def verify_deployed_accounts(self, block_number: int) -> None:
        """
        Verify predeployed-account expectations at block_number.

        No-op unless fill-stateful allocation.
        """
