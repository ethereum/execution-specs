"""
StateTest types
"""
import json
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, TextIO

from evm_transition_tool import FixtureFormats

from ...common.conversions import BytesConvertible, FixedSizeBytesConvertible
from ...common.json import JSONEncoder, field, to_json
from ...common.types import (
    AccessList,
    Address,
    Alloc,
    Bytes,
    Environment,
    Hash,
    HexNumber,
    NumberConvertible,
    Transaction,
    ZeroPaddedHexNumber,
)
from ..base.base_test import BaseFixture


@dataclass(kw_only=True)
class FixtureEnvironment:
    """
    Type used to describe the environment of a state test.
    """

    coinbase: FixedSizeBytesConvertible = field(
        default="0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba",
        json_encoder=JSONEncoder.Field(
            name="currentCoinbase",
            cast_type=Address,
        ),
    )
    gas_limit: NumberConvertible = field(
        default=100000000000000000,
        json_encoder=JSONEncoder.Field(
            name="currentGasLimit",
            cast_type=ZeroPaddedHexNumber,
        ),
    )
    number: NumberConvertible = field(
        default=1,
        json_encoder=JSONEncoder.Field(
            name="currentNumber",
            cast_type=ZeroPaddedHexNumber,
        ),
    )
    timestamp: NumberConvertible = field(
        default=1000,
        json_encoder=JSONEncoder.Field(
            name="currentTimestamp",
            cast_type=ZeroPaddedHexNumber,
        ),
    )
    prev_randao: Optional[NumberConvertible] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="currentRandom",
            cast_type=Hash,
        ),
    )
    difficulty: Optional[NumberConvertible] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="currentDifficulty",
            cast_type=ZeroPaddedHexNumber,
        ),
    )
    base_fee: Optional[NumberConvertible] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="currentBaseFee",
            cast_type=ZeroPaddedHexNumber,
        ),
    )
    excess_blob_gas: Optional[NumberConvertible] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="currentExcessBlobGas",
            cast_type=ZeroPaddedHexNumber,
        ),
    )
    previous_hash: Optional[FixedSizeBytesConvertible] = field(
        default="0x5e20a0453cecd065ea59c37ac63e079ee08998b6045136a8ce6635c7912ec0b6",
        json_encoder=JSONEncoder.Field(
            name="previousHash",
            cast_type=Hash,
        ),
    )

    @classmethod
    def from_env(cls, env: Environment) -> "FixtureEnvironment":
        """
        Returns a FixtureEnvironment from an Environment.
        """
        kwargs = {
            field.name: getattr(env, field.name)
            for field in fields(cls)
            if field.name != "previous_hash"  # define this field for state tests only
        }
        return cls(**kwargs)


@dataclass(kw_only=True)
class FixtureTransaction:
    """
    Type used to describe a transaction in a state test.
    """

    nonce: int = field(
        json_encoder=JSONEncoder.Field(
            cast_type=ZeroPaddedHexNumber,
        ),
    )
    gas_price: Optional[int] = field(
        json_encoder=JSONEncoder.Field(
            name="gasPrice",
            cast_type=ZeroPaddedHexNumber,
        ),
    )
    max_priority_fee_per_gas: Optional[int] = field(
        json_encoder=JSONEncoder.Field(
            name="maxPriorityFeePerGas",
            cast_type=HexNumber,
        ),
    )
    max_fee_per_gas: Optional[int] = field(
        json_encoder=JSONEncoder.Field(
            name="maxFeePerGas",
            cast_type=HexNumber,
        ),
    )
    gas_limit: int = field(
        json_encoder=JSONEncoder.Field(
            name="gasLimit",
            cast_type=lambda x: [ZeroPaddedHexNumber(x)],  # Converted to list
            to_json=True,
        ),
    )
    to: Optional[FixedSizeBytesConvertible] = field(
        json_encoder=JSONEncoder.Field(
            default_value_skip_cast="",  # Empty string for None
            cast_type=Address,
        ),
    )
    value: int = field(
        json_encoder=JSONEncoder.Field(
            cast_type=lambda x: [ZeroPaddedHexNumber(x)],  # Converted to list
            to_json=True,
        ),
    )
    data: BytesConvertible = field(
        json_encoder=JSONEncoder.Field(
            cast_type=lambda x: [Bytes(x)],
            to_json=True,
        ),
    )
    access_list: Optional[List[AccessList]] = field(
        json_encoder=JSONEncoder.Field(
            name="accessLists",
            cast_type=lambda x: [x],  # Converted to list of lists
            to_json=True,
        ),
    )
    max_fee_per_blob_gas: Optional[int] = field(
        json_encoder=JSONEncoder.Field(
            name="maxFeePerBlobGas",
            cast_type=HexNumber,
        ),
    )
    blob_versioned_hashes: Optional[Sequence[FixedSizeBytesConvertible]] = field(
        json_encoder=JSONEncoder.Field(
            name="blobVersionedHashes",
            cast_type=lambda x: [Hash(k) for k in x],
            to_json=True,
        ),
    )

    sender: FixedSizeBytesConvertible = field(
        json_encoder=JSONEncoder.Field(
            cast_type=Address,
        ),
    )
    secret_key: Optional[FixedSizeBytesConvertible] = field(
        json_encoder=JSONEncoder.Field(
            name="secretKey",
            cast_type=Hash,
        ),
    )

    @classmethod
    def from_transaction(cls, tx: Transaction) -> "FixtureTransaction":
        """
        Returns a FixtureTransaction from a Transaction.
        """
        kwargs = {field.name: getattr(tx, field.name) for field in fields(cls)}
        return cls(**kwargs)


@dataclass(kw_only=True)
class FixtureForkPostIndexes:
    """
    Type used to describe the indexes of a single post state of a single Fork.
    """

    data: int = field(default=0, json_encoder=JSONEncoder.Field(skip_string_convert=True))
    gas: int = field(default=0, json_encoder=JSONEncoder.Field(skip_string_convert=True))
    value: int = field(default=0, json_encoder=JSONEncoder.Field(skip_string_convert=True))


@dataclass(kw_only=True)
class FixtureForkPost:
    """
    Type used to describe the post state of a single Fork.
    """

    state_root: Hash = field(
        json_encoder=JSONEncoder.Field(
            name="hash",
        ),
    )
    logs_hash: Hash = field(
        json_encoder=JSONEncoder.Field(
            name="logs",
        ),
    )
    tx_bytes: BytesConvertible = field(
        json_encoder=JSONEncoder.Field(
            name="txbytes",
            cast_type=Bytes,
        ),
    )
    expected_exception: Optional[str] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="expectException",
        ),
    )
    indexes: FixtureForkPostIndexes = field(
        json_encoder=JSONEncoder.Field(
            to_json=True,
        ),
    )

    @classmethod
    def collect(
        cls,
        *,
        transition_tool_result: Dict[str, Any],
        transaction: Transaction,
    ) -> "FixtureForkPost":
        """
        Collects the post state of a single Fork from the transition tool result.
        """
        state_root = Hash(transition_tool_result["stateRoot"])
        logs_hash = Hash(transition_tool_result["logsHash"])
        indexes = FixtureForkPostIndexes()
        return cls(
            state_root=state_root,
            logs_hash=logs_hash,
            tx_bytes=transaction.serialized_bytes(),
            expected_exception=transaction.error,
            indexes=indexes,
        )


@dataclass(kw_only=True)
class Fixture(BaseFixture):
    """
    Fixture for a single StateTest.
    """

    env: Environment = field(
        json_encoder=JSONEncoder.Field(
            cast_type=FixtureEnvironment.from_env,
            to_json=True,
        ),
    )

    pre_state: Alloc = field(
        json_encoder=JSONEncoder.Field(
            name="pre",
            cast_type=Alloc,
            to_json=True,
        ),
    )

    transaction: Transaction = field(
        json_encoder=JSONEncoder.Field(
            to_json=True,
            cast_type=FixtureTransaction.from_transaction,
        ),
    )

    post: Mapping[str, List[FixtureForkPost]] = field(
        default_factory=dict,
        json_encoder=JSONEncoder.Field(
            name="post",
            to_json=True,
        ),
    )

    _json: Dict[str, Any] | None = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            skip=True,
        ),
    )

    def __post_init__(self):
        """
        Post init hook to convert to JSON after instantiation.
        """
        self._json = to_json(self)

    def to_json(self) -> Dict[str, Any]:
        """
        Convert to JSON.
        """
        assert self._json is not None, "Fixture not initialized"
        self._json["_info"] = self.info
        return self._json

    @classmethod
    def collect_into_file(cls, fd: TextIO, fixtures: Dict[str, "BaseFixture"]):
        """
        For StateTest format, we simply join the json fixtures into a single file.

        We could do extra processing like combining tests that use the same pre-state,
        and similar transaction, but this is not done for now.
        """
        json_fixtures: Dict[str, Dict[str, Any]] = {}
        for name, fixture in fixtures.items():
            assert isinstance(fixture, Fixture), f"Invalid fixture type: {type(fixture)}"
            json_fixtures[name] = fixture.to_json()
        json.dump(json_fixtures, fd, indent=4)

    @classmethod
    def output_base_dir_name(cls) -> Path:
        """
        Returns the name of the subdirectory where this type of fixture should be dumped to.
        """
        return Path("state_tests")

    @classmethod
    def format(cls) -> FixtureFormats:
        """
        Returns the fixture format which the evm tool can use to determine how to verify the
        fixture.
        """
        return FixtureFormats.STATE_TEST
