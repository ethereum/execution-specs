"""
Pydantic stub-account templates for the fill-stateful hive genesis.

Each template is a validated model carrying a ``template`` discriminator
and a polymorphic :meth:`expand` that yields the ``{Address: Account}`` it
contributes to the genesis pre-state. New patterns subclass
:class:`StubAccount` and join :data:`AnyStubAccount`. These mirror the
account/contract templates in ethereum/state-actor; keep parameters modest
— this genesis' state root is built by a pure-Python trie, so bloatnet-
scale state belongs in a state-actor snapshot instead.
"""

from abc import abstractmethod
from typing import Annotated, Dict, Literal, Optional, Union

from pydantic import BaseModel, Field, model_validator

from execution_testing.base_types import (
    Account,
    Address,
    Bytes,
    HexNumber,
)
from execution_testing.test_types import (
    DETERMINISTIC_FACTORY_ADDRESS,
    DETERMINISTIC_FACTORY_BYTECODE,
    compute_create2_address,
    compute_create_address,
)

StubAlloc = Dict[Address, Account]


def _dense_storage(final: int) -> Dict[int, int]:
    """Build the dense counter layout: slot 0 = final+1, slot k = k."""
    storage: Dict[int, int] = {0: final + 1}
    storage.update({k: k for k in range(1, final + 1)})
    return storage


class StoragePatternSpec(BaseModel):
    """Reusable dense-storage descriptor (slot 0 = ``final + 1``)."""

    final: int = Field(ge=0)


class StubAccount(BaseModel):
    """Base class for a parameterized genesis stub-account template."""

    @abstractmethod
    def expand(self) -> StubAlloc:
        """Return the ``{address: account}`` entries this template adds."""


class FundedEOA(StubAccount):
    """A single plain EOA funded with ``balance``."""

    template: Literal["funded_eoa"] = "funded_eoa"
    address: Address
    balance: HexNumber

    def expand(self) -> StubAlloc:
        """Fund ``address`` with ``balance``."""
        return {self.address: Account(balance=self.balance)}


class Create2Factory(StubAccount):
    """The canonical Arachnid CREATE2 deterministic-deployment proxy."""

    template: Literal["create2_factory"] = "create2_factory"

    def expand(self) -> StubAlloc:
        """Pre-deploy the factory at its canonical address."""
        return {
            DETERMINISTIC_FACTORY_ADDRESS: Account(
                nonce=1, code=DETERMINISTIC_FACTORY_BYTECODE
            )
        }


class SequentialBalanceOnlyAccount(StubAccount):
    """
    ``count`` balance-only accounts at ``anchor + i``, each funded with
    ``balance`` (nonce 0, no code).
    """

    template: Literal["sequential_balance_only_account"] = (
        "sequential_balance_only_account"
    )
    anchor: HexNumber
    count: int = Field(ge=0)
    balance: HexNumber

    @model_validator(mode="after")
    def _check_range(self) -> "SequentialBalanceOnlyAccount":
        """Reject ranges that overflow the 20-byte address space."""
        if self.count and self.anchor + self.count - 1 >= 2**160:
            raise ValueError(
                "sequential_balance_only_account: address range "
                "overflows 20 bytes"
            )
        return self

    def expand(self) -> StubAlloc:
        """Fund ``count`` accounts starting at ``anchor`` (no code)."""
        return {
            Address(self.anchor + i): Account(balance=self.balance)
            for i in range(self.count)
        }


class StoragePattern(StubAccount):
    """
    Dense counter storage: slot 0 = ``final + 1`` and slot ``k`` = ``k``
    for ``k`` in ``1..final``. No code (stays EIP-7702-delegatable); nonce
    is forced to 1 so EIP-161 empty-account pruning can't wipe it.
    """

    template: Literal["storage_pattern"] = "storage_pattern"
    address: Address
    final: int = Field(ge=0)
    balance: HexNumber = HexNumber(0)

    def expand(self) -> StubAlloc:
        """Plant the counter storage layout at ``address``."""
        return {
            self.address: Account(
                nonce=1,
                balance=self.balance,
                storage=_dense_storage(self.final),
            )
        }


class Erc20(StubAccount):
    """
    Pre-deployed ERC-20 contract at ``address`` with runtime ``code``.

    For bloated-state tests, set ``storage_pattern`` to plant the dense
    counter layout at the same address (composes code + storage in one
    entry). For ad-hoc state, use ``storage`` directly.
    """

    template: Literal["erc20"] = "erc20"
    address: Address
    code: Optional[Bytes] = None
    storage: Dict[HexNumber, HexNumber] = Field(default_factory=dict)
    storage_pattern: Optional[StoragePatternSpec] = None
    nonce: int = Field(default=1, ge=1)
    balance: HexNumber = HexNumber(0)

    @model_validator(mode="after")
    def _require_code(self) -> "Erc20":
        """Require runtime code (inline ``code`` is mandatory)."""
        if not self.code:
            raise ValueError("erc20: 'code' is required (hex runtime bytes)")
        return self

    def expand(self) -> StubAlloc:
        """Plant the ERC-20 runtime at ``address`` with merged storage."""
        merged: Dict[int, int] = {
            int(k): int(v) for k, v in self.storage.items()
        }
        if self.storage_pattern is not None:
            merged.update(_dense_storage(self.storage_pattern.final))
        return {
            self.address: Account(
                nonce=self.nonce,
                balance=self.balance,
                code=self.code,
                storage=merged,
            )
        }


class Create2Deploys(StubAccount):
    """
    Plant ``code`` at every address derived from
    ``CREATE2(deployer, salt, initcode)`` for ``salt`` in
    ``[start, start + count)``. The deployer defaults to the canonical
    Arachnid factory. Constructors never run — ``code`` may differ from
    what ``initcode`` would have returned.
    """

    template: Literal["create2_deploys"] = "create2_deploys"
    deployer: Address = DETERMINISTIC_FACTORY_ADDRESS
    initcode: Bytes
    code: Bytes
    count: int = Field(ge=0)
    start: int = Field(default=0, ge=0)

    def expand(self) -> StubAlloc:
        """Derive ``count`` CREATE2 addresses and plant ``code`` at each."""
        result: StubAlloc = {}
        for i in range(self.count):
            addr = compute_create2_address(
                address=self.deployer,
                salt=self.start + i,
                initcode=self.initcode,
            )
            result[addr] = Account(nonce=1, code=self.code)
        return result


class CreatePreimageDeploys(StubAccount):
    """
    Plant ``code`` at every address derived from
    ``CREATE(deployer, nonce)`` for ``nonce`` in
    ``[start, start + count)``. The deployer is *not* implicitly funded —
    declare a separate ``funded_eoa`` if you need it.
    """

    template: Literal["create_preimage_deploys"] = "create_preimage_deploys"
    deployer: Address
    code: Bytes
    count: int = Field(ge=0)
    start: int = Field(default=0, ge=0)

    def expand(self) -> StubAlloc:
        """Derive ``count`` CREATE addresses and plant ``code`` at each."""
        result: StubAlloc = {}
        for i in range(self.count):
            addr = compute_create_address(
                address=self.deployer, nonce=self.start + i
            )
            result[addr] = Account(nonce=1, code=self.code)
        return result


# Discriminated union of every concrete template, keyed on ``template``.
# Lets a chainspec hold a heterogeneous, validated (and JSON-parseable)
# list of stub accounts.
AnyStubAccount = Annotated[
    Union[
        FundedEOA,
        Create2Factory,
        SequentialBalanceOnlyAccount,
        StoragePattern,
        Erc20,
        Create2Deploys,
        CreatePreimageDeploys,
    ],
    Field(discriminator="template"),
]
