"""Block-related types for Ethereum tests."""

from dataclasses import dataclass
from functools import cached_property
from typing import Any, Dict, Generic, List, Sequence

import ethereum_rlp as eth_rlp
from ethereum_types.numeric import Uint
from pydantic import Field, computed_field
from trie import HexaryTrie

from ethereum_test_base_types import (
    Address,
    Bytes,
    CamelModel,
    EmptyOmmersRoot,
    Hash,
    HexNumber,
    Number,
    NumberBoundTypeVar,
    ZeroPaddedHexNumber,
)
from ethereum_test_forks import Fork

DEFAULT_BASE_FEE = 7
CURRENT_MAINNET_BLOCK_GAS_LIMIT = 36_000_000
DEFAULT_BLOCK_GAS_LIMIT = CURRENT_MAINNET_BLOCK_GAS_LIMIT * 2


@dataclass
class EnvironmentDefaults:
    """Default environment values."""

    # By default, the constant `DEFAULT_BLOCK_GAS_LIMIT` is used.
    # Other libraries (pytest plugins) may override this value by modifying the
    # `EnvironmentDefaults.gas_limit` class attribute.
    gas_limit: int = DEFAULT_BLOCK_GAS_LIMIT


class WithdrawalGeneric(CamelModel, Generic[NumberBoundTypeVar]):
    """Withdrawal generic type, used as a parent class for `Withdrawal` and `FixtureWithdrawal`."""

    index: NumberBoundTypeVar
    validator_index: NumberBoundTypeVar
    address: Address
    amount: NumberBoundTypeVar

    def to_serializable_list(self) -> List[Any]:
        """
        Return list of the withdrawal's attributes in the order they should
        be serialized.
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
            t.set(eth_rlp.encode(Uint(i)), eth_rlp.encode(w.to_serializable_list()))
        return t.root_hash


class Withdrawal(WithdrawalGeneric[HexNumber]):
    """Withdrawal type."""

    pass


class EnvironmentGeneric(CamelModel, Generic[NumberBoundTypeVar]):
    """Used as a parent class for `Environment` and `FixtureEnvironment`."""

    fee_recipient: Address = Field(
        Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba"),
        alias="currentCoinbase",
    )
    gas_limit: NumberBoundTypeVar = Field(
        default_factory=lambda: EnvironmentDefaults.gas_limit, alias="currentGasLimit"
    )  # type: ignore
    number: NumberBoundTypeVar = Field(1, alias="currentNumber")  # type: ignore
    timestamp: NumberBoundTypeVar = Field(1_000, alias="currentTimestamp")  # type: ignore
    prev_randao: NumberBoundTypeVar | None = Field(None, alias="currentRandom")
    difficulty: NumberBoundTypeVar | None = Field(None, alias="currentDifficulty")
    base_fee_per_gas: NumberBoundTypeVar | None = Field(None, alias="currentBaseFee")
    excess_blob_gas: NumberBoundTypeVar | None = Field(None, alias="currentExcessBlobGas")

    parent_difficulty: NumberBoundTypeVar | None = Field(None)
    parent_timestamp: NumberBoundTypeVar | None = Field(None)
    parent_base_fee_per_gas: NumberBoundTypeVar | None = Field(None, alias="parentBaseFee")
    parent_gas_used: NumberBoundTypeVar | None = Field(None)
    parent_gas_limit: NumberBoundTypeVar | None = Field(None)


class Environment(EnvironmentGeneric[ZeroPaddedHexNumber]):
    """
    Structure used to keep track of the context in which a block
    must be executed.
    """

    blob_gas_used: ZeroPaddedHexNumber | None = Field(None, alias="currentBlobGasUsed")
    parent_ommers_hash: Hash = Field(Hash(EmptyOmmersRoot), alias="parentUncleHash")
    parent_blob_gas_used: ZeroPaddedHexNumber | None = Field(None)
    parent_excess_blob_gas: ZeroPaddedHexNumber | None = Field(None)
    parent_beacon_block_root: Hash | None = Field(None)

    block_hashes: Dict[Number, Hash] = Field(default_factory=dict)
    ommers: List[Hash] = Field(default_factory=list)
    withdrawals: List[Withdrawal] | None = Field(None)
    extra_data: Bytes = Field(Bytes(b"\x00"), exclude=True)

    @computed_field  # type: ignore[misc]
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
        number = self.number
        timestamp = self.timestamp

        updated_values: Dict[str, Any] = {}

        if fork.header_prev_randao_required(number, timestamp) and self.prev_randao is None:
            updated_values["prev_randao"] = 0

        if fork.header_withdrawals_required(number, timestamp) and self.withdrawals is None:
            updated_values["withdrawals"] = []

        if (
            fork.header_base_fee_required(number, timestamp)
            and self.base_fee_per_gas is None
            and self.parent_base_fee_per_gas is None
        ):
            updated_values["base_fee_per_gas"] = DEFAULT_BASE_FEE

        if fork.header_zero_difficulty_required(number, timestamp):
            updated_values["difficulty"] = 0
        elif self.difficulty is None and self.parent_difficulty is None:
            updated_values["difficulty"] = 0x20000

        if (
            fork.header_excess_blob_gas_required(number, timestamp)
            and self.excess_blob_gas is None
            and self.parent_excess_blob_gas is None
        ):
            updated_values["excess_blob_gas"] = 0

        if (
            fork.header_blob_gas_used_required(number, timestamp)
            and self.blob_gas_used is None
            and self.parent_blob_gas_used is None
        ):
            updated_values["blob_gas_used"] = 0

        if (
            fork.header_beacon_root_required(number, timestamp)
            and self.parent_beacon_block_root is None
        ):
            updated_values["parent_beacon_block_root"] = 0

        return self.copy(**updated_values)
