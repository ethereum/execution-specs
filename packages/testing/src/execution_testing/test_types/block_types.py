"""Block-related types for Ethereum tests."""

import json
from dataclasses import dataclass
from functools import cached_property
from typing import Any, Callable, Dict, Generic, List, Sequence

import ethereum_rlp as eth_rlp
from ethereum_types.numeric import Uint
from pydantic import Field, computed_field, model_validator
from trie import HexaryTrie

from execution_testing.base_types import (
    Address,
    Bytes,
    CamelModel,
    EmptyOmmersRoot,
    Hash,
    HexNumber,
    NumberBoundTypeVar,
    ZeroPaddedHexNumber,
)
from execution_testing.base_types.ssz import SSZModel, Uint64
from execution_testing.forks import Fork

DEFAULT_BASE_FEE = 7
CURRENT_MAINNET_BLOCK_GAS_LIMIT = 60_000_000
DEFAULT_BLOCK_GAS_LIMIT = CURRENT_MAINNET_BLOCK_GAS_LIMIT * 2

FORK_GATED_FIELDS: Dict[str, Callable[[Fork], bool]] = {
    "prev_randao": lambda fork: fork.header_prev_randao_required(),
    "base_fee_per_gas": lambda fork: fork.header_base_fee_required(),
    "parent_base_fee_per_gas": lambda fork: fork.header_base_fee_required(),
    "withdrawals": lambda fork: fork.header_withdrawals_required(),
    "excess_blob_gas": lambda fork: fork.header_excess_blob_gas_required(),
    "parent_excess_blob_gas": (
        lambda fork: fork.header_excess_blob_gas_required()
    ),
    "blob_gas_used": lambda fork: fork.header_blob_gas_used_required(),
    "parent_blob_gas_used": lambda fork: fork.header_blob_gas_used_required(),
    "parent_beacon_block_root": (
        lambda fork: fork.header_beacon_root_required()
    ),
    "slot_number": lambda fork: fork.header_slot_number_required(),
    "parent_slot_number": lambda fork: fork.header_slot_number_required(),
}
"""
Environment fields, current and parent, that only some block headers
carry, keyed by the fork predicate that admits each one.
"""


@dataclass
class EnvironmentDefaults:
    """Default environment values."""

    # By default, the constant `DEFAULT_BLOCK_GAS_LIMIT` is used.
    # Other libraries (pytest plugins) may override this value by modifying the
    # `EnvironmentDefaults.gas_limit` class attribute.
    gas_limit: int = DEFAULT_BLOCK_GAS_LIMIT


class WithdrawalGeneric(CamelModel, Generic[NumberBoundTypeVar]):
    """
    Withdrawal generic type, used as a parent class for `Withdrawal` and
    `FixtureWithdrawal`.
    """

    index: NumberBoundTypeVar
    validator_index: NumberBoundTypeVar
    address: Address
    amount: NumberBoundTypeVar

    def to_serializable_list(self) -> List[Any]:
        """
        Return list of the withdrawal's attributes in the order they should be
        serialized.
        """
        return [
            Uint(self.index),
            Uint(self.validator_index),
            self.address,
            Uint(self.amount),
        ]

    @staticmethod
    def list_root(withdrawals: Sequence["WithdrawalGeneric"]) -> bytes:
        """Return withdrawals root of a list of withdrawals."""
        t = HexaryTrie(db={})
        for i, w in enumerate(withdrawals):
            t.set(
                eth_rlp.encode(Uint(i)),
                eth_rlp.encode(w.to_serializable_list()),
            )
        return t.root_hash


class Withdrawal(WithdrawalGeneric[HexNumber], SSZModel):
    """Withdrawal type; also the consensus-layer SSZ container."""

    index: Uint64
    validator_index: Uint64
    amount: Uint64


class EnvironmentGeneric(CamelModel, Generic[NumberBoundTypeVar]):
    """Used as a parent class for `Environment` and `FixtureEnvironment`."""

    fee_recipient: Address = Field(
        Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba"),
        alias="currentCoinbase",
    )
    gas_limit: NumberBoundTypeVar = Field(
        default_factory=lambda: EnvironmentDefaults.gas_limit,
        alias="currentGasLimit",
    )  # type: ignore
    number: NumberBoundTypeVar = Field(1, alias="currentNumber")  # type: ignore
    timestamp: NumberBoundTypeVar = Field(1_000, alias="currentTimestamp")  # type: ignore
    prev_randao: NumberBoundTypeVar | None = Field(None, alias="currentRandom")
    difficulty: NumberBoundTypeVar | None = Field(
        None, alias="currentDifficulty"
    )
    base_fee_per_gas: NumberBoundTypeVar | None = Field(
        None, alias="currentBaseFee"
    )
    excess_blob_gas: NumberBoundTypeVar | None = Field(
        None, alias="currentExcessBlobGas"
    )
    slot_number: NumberBoundTypeVar | None = Field(None, alias="slotNumber")

    parent_difficulty: NumberBoundTypeVar | None = Field(None)
    parent_timestamp: NumberBoundTypeVar | None = Field(None)
    parent_base_fee_per_gas: NumberBoundTypeVar | None = Field(
        None, alias="parentBaseFee"
    )
    parent_gas_used: NumberBoundTypeVar | None = Field(None)
    parent_gas_limit: NumberBoundTypeVar | None = Field(None)


class Environment(EnvironmentGeneric[ZeroPaddedHexNumber]):
    """
    Structure used to keep track of the context in which a block must be
    executed.
    """

    @model_validator(mode="before")
    @classmethod
    def strip_computed_fields(cls, data: Any) -> Any:
        """Strip computed fields that are not valid input fields."""
        if isinstance(data, dict):
            data.pop("parent_hash", None)
            data.pop("parentHash", None)
        return data

    blob_gas_used: ZeroPaddedHexNumber | None = Field(
        None, alias="currentBlobGasUsed"
    )
    parent_ommers_hash: Hash = Field(
        Hash(EmptyOmmersRoot), alias="parentUncleHash"
    )
    parent_blob_gas_used: ZeroPaddedHexNumber | None = Field(None)
    parent_excess_blob_gas: ZeroPaddedHexNumber | None = Field(None)
    parent_slot_number: ZeroPaddedHexNumber | None = Field(None)
    parent_beacon_block_root: Hash | None = Field(None)

    block_hashes: Dict[ZeroPaddedHexNumber, Hash] = Field(default_factory=dict)
    ommers: List[Hash] = Field(default_factory=list)
    withdrawals: List[Withdrawal] | None = Field(None)
    extra_data: Bytes = Field(Bytes(b"\x00"), exclude=True)

    # EIP-7928: Block-level access lists
    block_access_list_hash: Hash | None = Field(None)
    block_access_lists: Bytes | None = Field(None)

    @computed_field  # type: ignore[prop-decorator]
    @cached_property
    def parent_hash(self) -> Hash | None:
        """
        Obtains the latest hash according to the highest block number in
        `block_hashes`.
        """
        if len(self.block_hashes) == 0:
            return None

        last_index = max(self.block_hashes.keys())
        return Hash(self.block_hashes[last_index])

    def set_fork_requirements(self, fork: Fork) -> "Environment":
        """Fill required fields in an environment depending on the fork."""
        updated_values: Dict[str, Any] = {}

        if fork.header_prev_randao_required() and self.prev_randao is None:
            updated_values["prev_randao"] = 0

        if fork.header_withdrawals_required() and self.withdrawals is None:
            updated_values["withdrawals"] = []

        if (
            fork.header_base_fee_required()
            and self.base_fee_per_gas is None
            and self.parent_base_fee_per_gas is None
        ):
            updated_values["base_fee_per_gas"] = DEFAULT_BASE_FEE

        if fork.header_zero_difficulty_required():
            updated_values["difficulty"] = 0
        elif self.difficulty is None and self.parent_difficulty is None:
            updated_values["difficulty"] = 0x20000

        if (
            fork.header_excess_blob_gas_required()
            and self.excess_blob_gas is None
            and self.parent_excess_blob_gas is None
        ):
            updated_values["excess_blob_gas"] = 0

        if (
            fork.header_blob_gas_used_required()
            and self.blob_gas_used is None
            and self.parent_blob_gas_used is None
        ):
            updated_values["blob_gas_used"] = 0

        if (
            fork.header_beacon_root_required()
            and self.parent_beacon_block_root is None
        ):
            updated_values["parent_beacon_block_root"] = 0

        if fork.header_slot_number_required() and self.slot_number is None:
            updated_values["slot_number"] = (
                int(self.parent_slot_number) + 1
                if self.parent_slot_number is not None
                else 0
            )

        return self.copy(**updated_values)

    @classmethod
    def for_fork(cls, fork: Fork, **kwargs: Any) -> "Environment":
        """
        Build an environment from only the fields the fork's header has.

        Use it when one pinned context spans forks whose headers differ:
        the pins the fork lacks are dropped instead of raising in
        `check_fork_fields`.
        """
        return cls(
            **{
                name: value
                for name, value in kwargs.items()
                if name not in FORK_GATED_FIELDS
                or FORK_GATED_FIELDS[name](fork)
            }
        )

    def check_fork_fields(self, fork: Fork) -> None:
        """
        Raise if a set field is one the fork's block header lacks.

        Serializing such a field into a fixture would misstate the block
        context, so the test has to state its intent instead.
        """
        unsupported = [
            name
            for name, required in FORK_GATED_FIELDS.items()
            if getattr(self, name) is not None and not required(fork)
        ]
        if not unsupported:
            return
        raise ValueError(
            f"{', '.join(unsupported)} set for {fork.name()}, whose block "
            "header has no such field. Remove the field from the test, "
            "build the environment with Environment.for_fork(fork, ...) "
            "to keep only the fields the fork has, or, to check that "
            "clients reject the field, set it on the block through "
            "Block(rlp_modifier=Header(...))."
        )

    def canonical_json(self) -> str:
        """
        Return the canonical JSON encoding of this model.

        Keys are alias-cased and sorted, and unset fields are excluded, so
        two equal models encode identically and the encoding is stable
        across processes: usable as a grouping key or a hash pre-image.
        """
        return json.dumps(
            self.model_dump(mode="json", by_alias=True, exclude_none=True),
            sort_keys=True,
        )

    def __eq__(self, other: object) -> bool:
        """Check if two environment objects are equal."""
        if not isinstance(other, Environment):
            return False

        self_dict = self.model_dump(exclude_none=True, by_alias=True)
        self_dict["extra_data"] = self.extra_data.hex()

        other_dict = other.model_dump(exclude_none=True, by_alias=True)
        other_dict["extra_data"] = other.extra_data.hex()

        return self_dict == other_dict
