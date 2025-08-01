"""Expect section structure of ethereum/tests fillers."""

import re
from enum import StrEnum
from typing import Annotated, Any, Dict, Iterator, List, Mapping, Set, Union

from pydantic import (
    BaseModel,
    BeforeValidator,
    Field,
    ValidatorFunctionWrapHandler,
    field_validator,
    model_validator,
)

from ethereum_test_base_types import (
    Account,
    Address,
    CamelModel,
    EthereumTestRootModel,
    HexNumber,
    Storage,
)
from ethereum_test_exceptions import TransactionExceptionInstanceOrList
from ethereum_test_forks import Fork, get_forks
from ethereum_test_types import Alloc

from .common import (
    AddressOrCreateTagInFiller,
    CodeInFiller,
    Tag,
    TagDependentData,
    TagDict,
    ValueInFiller,
    ValueOrCreateTagInFiller,
)


class Indexes(BaseModel):
    """Class that represents an index filler."""

    data: int | List[Union[int, str]] | List[int] | str = Field(-1)
    gas: int | List[Union[int, str]] | List[int] | str = Field(-1)
    value: int | List[Union[int, str]] | List[int] | str = Field(-1)


def validate_any_string_as_none(v: Any) -> Any:
    """Validate "ANY" as None."""
    if type(v) is str and v == "ANY":
        return None
    return v


class StorageInExpectSection(EthereumTestRootModel, TagDependentData):
    """Class that represents a storage in expect section filler."""

    root: Dict[
        ValueOrCreateTagInFiller,
        Annotated[ValueOrCreateTagInFiller | None, BeforeValidator(validate_any_string_as_none)],
    ]

    def tag_dependencies(self) -> Mapping[str, Tag]:
        """Get storage dependencies."""
        tag_dependencies = {}
        for key, value in self.root.items():
            if isinstance(key, Tag):
                tag_dependencies[key.name] = key
            if isinstance(value, Tag):
                tag_dependencies[value.name] = value
        return tag_dependencies

    def resolve(self, tags: TagDict) -> Storage:
        """Resolve the account with the given tags."""
        storage = Storage()
        for key, value in self.root.items():
            resolved_key: HexNumber | Address
            if isinstance(key, Tag):
                resolved_key = key.resolve(tags)
            else:
                resolved_key = key
            if value is None:
                storage.set_expect_any(resolved_key)
            elif isinstance(value, Tag):
                storage[resolved_key] = value.resolve(tags)
            else:
                storage[resolved_key] = value
        return storage

    def __contains__(self, key: Address) -> bool:
        """Check if the storage contains a key."""
        return key in self.root

    def __iter__(self) -> Iterator[ValueOrCreateTagInFiller]:  # type: ignore[override]
        """Iterate over the storage."""
        return iter(self.root)


class AccountInExpectSection(BaseModel, TagDependentData):
    """Class that represents an account in expect section filler."""

    balance: ValueInFiller | None = None
    code: CodeInFiller | None = None
    nonce: ValueInFiller | None = None
    storage: StorageInExpectSection | None = None

    @model_validator(mode="wrap")
    @classmethod
    def validate_should_not_exist(cls, v: Any, handler: ValidatorFunctionWrapHandler):
        """Validate the "shouldnotexist" field, which makes this validator return `None`."""
        if isinstance(v, dict):
            if "shouldnotexist" in v:
                return None
        return handler(v)

    def tag_dependencies(self) -> Mapping[str, Tag]:
        """Get tag dependencies."""
        tag_dependencies: Dict[str, Tag] = {}
        if self.code is not None:
            tag_dependencies.update(self.code.tag_dependencies())
        if self.storage is not None:
            tag_dependencies.update(self.storage.tag_dependencies())
        return tag_dependencies

    def resolve(self, tags: TagDict) -> Account:
        """Resolve the account with the given tags."""
        account_kwargs: Dict[str, Any] = {}
        if self.storage is not None:
            account_kwargs["storage"] = self.storage.resolve(tags)
        if self.code is not None:
            account_kwargs["code"] = self.code.compiled(tags)
        if self.balance is not None:
            account_kwargs["balance"] = self.balance
        if self.nonce is not None:
            account_kwargs["nonce"] = self.nonce
        return Account(**account_kwargs)


class CMP(StrEnum):
    """Comparison action."""

    LE = "<="
    GE = ">="
    LT = "<"
    GT = ">"
    EQ = "="


class ForkConstraint(BaseModel):
    """Single fork with an operand."""

    operand: CMP
    fork: Fork

    @field_validator("fork", mode="before")
    @classmethod
    def parse_fork_synonyms(cls, value: Any):
        """Resolve fork synonyms."""
        if value == "EIP158":
            value = "Byzantium"
        return value

    @model_validator(mode="before")
    @classmethod
    def parse_from_string(cls, data: Any) -> Any:
        """Parse a fork with operand from a string."""
        if isinstance(data, str):
            for cmp in CMP:
                if data.startswith(cmp):
                    fork = data.removeprefix(cmp)
                    return {
                        "operand": cmp,
                        "fork": fork,
                    }
            return {
                "operand": CMP.EQ,
                "fork": data,
            }
        return data

    def match(self, fork: Fork) -> bool:
        """Return whether the fork satisfies the operand evaluation."""
        match self.operand:
            case CMP.LE:
                return fork <= self.fork
            case CMP.GE:
                return fork >= self.fork
            case CMP.LT:
                return fork < self.fork
            case CMP.GT:
                return fork > self.fork
            case CMP.EQ:
                return fork == self.fork
            case _:
                raise ValueError(f"Invalid operand: {self.operand}")


class ForkSet(EthereumTestRootModel):
    """Set of forks."""

    root: Set[Fork]

    @model_validator(mode="before")
    @classmethod
    def parse_from_list_or_string(cls, value: Any) -> Set[Fork]:
        """Parse fork_with_operand `>=Cancun` into {Cancun, Prague, ...}."""
        fork_set: Set[Fork] = set()
        if not isinstance(value, list):
            value = [value]

        for fork_with_operand in value:
            matches = re.findall(r"(<=|<|>=|>|=)([^<>=]+)", fork_with_operand)
            if matches:
                all_fork_constraints = [
                    ForkConstraint.model_validate(f"{op}{fork.strip()}") for op, fork in matches
                ]
            else:
                all_fork_constraints = [ForkConstraint.model_validate(fork_with_operand.strip())]

            for fork in get_forks():
                for f in all_fork_constraints:
                    if not f.match(fork):
                        # If any constraint does not match, skip adding
                        break
                else:
                    # All constraints match, add the fork to the set
                    fork_set.add(fork)

        return fork_set

    def __hash__(self) -> int:
        """Return the hash of the fork set."""
        h = hash(None)
        for fork in sorted([str(f) for f in self]):
            h ^= hash(fork)
        return h

    def __contains__(self, fork: Fork) -> bool:
        """Check if the fork set contains a fork."""
        return fork in self.root

    def __iter__(self) -> Iterator[Fork]:  # type: ignore[override]
        """Iterate over the fork set."""
        return iter(self.root)

    def __len__(self) -> int:
        """Return the length of the fork set."""
        return len(self.root)


class ResultInFiller(EthereumTestRootModel, TagDependentData):
    """
    Post section in state test filler.

    A value of `None` for an address means that the account should not be in the state trie
    at the end of the test.
    """

    root: Dict[AddressOrCreateTagInFiller, AccountInExpectSection | None]

    def tag_dependencies(self) -> Mapping[str, Tag]:
        """Return all tags used in the result."""
        tag_dependencies: Dict[str, Tag] = {}
        for address, account in self.root.items():
            if isinstance(address, Tag):
                tag_dependencies[address.name] = address

            if account is None:
                continue

            tag_dependencies.update(account.tag_dependencies())

        return tag_dependencies

    def resolve(self, tags: TagDict) -> Alloc:
        """Resolve the post section."""
        post = Alloc()
        for address, account in self.root.items():
            if isinstance(address, Tag):
                resolved_address = address.resolve(tags)
            else:
                resolved_address = Address(address)

            if account is None:
                continue

            post[resolved_address] = account.resolve(tags)
        return post

    def __contains__(self, address: Address) -> bool:
        """Check if the result contains an address."""
        return address in self.root

    def __iter__(self) -> Iterator[AddressOrCreateTagInFiller]:  # type: ignore[override]
        """Iterate over the result."""
        return iter(self.root)

    def __len__(self) -> int:
        """Return the length of the result."""
        return len(self.root)


class ExpectException(EthereumTestRootModel):
    """Expect exception model."""

    root: Dict[ForkSet, TransactionExceptionInstanceOrList]

    def __getitem__(self, fork: Fork) -> TransactionExceptionInstanceOrList:
        """Get an expectation for a given fork."""
        for k in self.root:
            if fork in k:
                return self.root[k]
        raise KeyError(f"Fork {fork} not found in expectations.")

    def __contains__(self, fork: Fork) -> bool:
        """Check if the expect exception contains a fork."""
        return fork in self.root

    def __iter__(self) -> Iterator[ForkSet]:  # type: ignore[override]
        """Iterate over the expect exception."""
        return iter(self.root)

    def __len__(self) -> int:
        """Return the length of the expect exception."""
        return len(self.root)


class ExpectSectionInStateTestFiller(CamelModel):
    """Expect section in state test filler."""

    indexes: Indexes = Field(default_factory=Indexes)
    network: ForkSet
    result: ResultInFiller
    expect_exception: ExpectException | None = None

    def model_post_init(self, __context):
        """Validate that the expectation is coherent."""
        if self.expect_exception is None:
            return
        all_forks: Set[Fork] = set()
        for current_fork_set in self.expect_exception:
            for fork in current_fork_set:
                assert fork not in all_forks
                all_forks.add(fork)

    def has_index(self, d: int, g: int, v: int) -> bool:
        """Check if there is index set in indexes."""
        d_match: bool = False
        g_match: bool = False
        v_match: bool = False

        # Check if data index match
        if isinstance(self.indexes.data, int):
            d_match = True if self.indexes.data == -1 or self.indexes.data == d else False
        elif isinstance(self.indexes.data, list):
            d_match = True if self.indexes.data.count(d) else False

        # Check if gas index match
        if isinstance(self.indexes.gas, int):
            g_match = True if self.indexes.gas == -1 or self.indexes.gas == g else False
        elif isinstance(self.indexes.gas, list):
            g_match = True if self.indexes.gas.count(g) else False

        # Check if value index match
        if isinstance(self.indexes.value, int):
            v_match = True if self.indexes.value == -1 or self.indexes.value == v else False
        elif isinstance(self.indexes.value, list):
            v_match = True if self.indexes.value.count(v) else False

        return d_match and g_match and v_match
