"""
BlockchainTest types
"""

import json
from copy import copy, deepcopy
from dataclasses import dataclass, fields, replace
from pathlib import Path
from typing import Any, Callable, ClassVar, Dict, List, Mapping, Optional, TextIO, Tuple

from ethereum import rlp as eth_rlp
from ethereum.base_types import Uint
from ethereum.crypto.hash import keccak256

from ethereum_test_forks import Fork
from evm_transition_tool import FixtureFormats

from ...common.base_types import (
    Address,
    Bloom,
    Bytes,
    Hash,
    HeaderNonce,
    HexNumber,
    Number,
    ZeroPaddedHexNumber,
)
from ...common.constants import AddrAA, EmptyOmmersRoot, EngineAPIError
from ...common.conversions import BytesConvertible, FixedSizeBytesConvertible, NumberConvertible
from ...common.json import JSONEncoder, field
from ...common.types import (
    Account,
    Alloc,
    Environment,
    Removable,
    Transaction,
    Withdrawal,
    blob_versioned_hashes_from_transactions,
    transaction_list_to_serializable_list,
)
from ...exceptions import BlockException, ExceptionList, TransactionException
from ..base.base_test import BaseFixture


@dataclass(kw_only=True)
class Header:
    """
    Header type used to describe block header properties in test specs.
    """

    parent_hash: Optional[FixedSizeBytesConvertible] = None
    ommers_hash: Optional[FixedSizeBytesConvertible] = None
    coinbase: Optional[FixedSizeBytesConvertible] = None
    state_root: Optional[FixedSizeBytesConvertible] = None
    transactions_root: Optional[FixedSizeBytesConvertible] = None
    receipt_root: Optional[FixedSizeBytesConvertible] = None
    bloom: Optional[FixedSizeBytesConvertible] = None
    difficulty: Optional[NumberConvertible] = None
    number: Optional[NumberConvertible] = None
    gas_limit: Optional[NumberConvertible] = None
    gas_used: Optional[NumberConvertible] = None
    timestamp: Optional[NumberConvertible] = None
    extra_data: Optional[BytesConvertible] = None
    mix_digest: Optional[FixedSizeBytesConvertible] = None
    nonce: Optional[FixedSizeBytesConvertible] = None
    base_fee: Optional[NumberConvertible | Removable] = None
    withdrawals_root: Optional[FixedSizeBytesConvertible | Removable] = None
    blob_gas_used: Optional[NumberConvertible | Removable] = None
    excess_blob_gas: Optional[NumberConvertible | Removable] = None
    beacon_root: Optional[FixedSizeBytesConvertible | Removable] = None
    hash: Optional[FixedSizeBytesConvertible] = None

    REMOVE_FIELD: ClassVar[Removable] = Removable()
    """
    Sentinel object used to specify that a header field should be removed.
    """
    EMPTY_FIELD: ClassVar[Removable] = Removable()
    """
    Sentinel object used to specify that a header field must be empty during verification.
    """


@dataclass(kw_only=True)
class HeaderFieldSource:
    """
    Block header field metadata specifying the source used to populate the field when collecting
    the block header from different sources, and to validate it.
    """

    required: bool = True
    """
    Whether the field is required or not, regardless of the fork.
    """
    fork_requirement_check: Optional[str] = None
    """
    Name of the method to call to check if the field is required for the current fork.
    """
    default: Optional[Any] = None
    """
    Default value for the field if no value was provided by either the transition tool or the
    environment
    """
    parse_type: Optional[Callable] = None
    """
    The type or function to use to parse the field to before initializing the object.
    """
    source_environment: Optional[str] = None
    """
    Name of the field in the environment object, which can be a callable.
    """
    source_transition_tool: Optional[str] = None
    """
    Name of the field in the transition tool result dictionary.
    """

    def collect(
        self,
        *,
        target: Dict[str, Any],
        field_name: str,
        fork: Fork,
        number: int,
        timestamp: int,
        transition_tool_result: Dict[str, Any],
        environment: Environment,
    ) -> None:
        """
        Collects the field from the different sources according to the
        metadata description.
        """
        value = None
        required = self.required
        if self.fork_requirement_check is not None:
            required = getattr(fork, self.fork_requirement_check)(number, timestamp)

        if self.source_transition_tool is not None:
            if self.source_transition_tool in transition_tool_result:
                got_value = transition_tool_result.get(self.source_transition_tool)
                if got_value is not None:
                    value = got_value

        if self.source_environment is not None:
            got_value = getattr(environment, self.source_environment, None)
            if callable(got_value):
                got_value = got_value()
            if got_value is not None:
                value = got_value

        if required:
            if value is None:
                if self.default is not None:
                    value = self.default
                else:
                    raise ValueError(f"missing required field '{field_name}'")

        if value is not None and self.parse_type is not None:
            value = self.parse_type(value)

        target[field_name] = value


def header_field(*args, source: Optional[HeaderFieldSource] = None, **kwargs) -> Any:
    """
    A wrapper around `dataclasses.field` that allows for json configuration info and header
    metadata.
    """
    if "metadata" in kwargs:
        metadata = kwargs["metadata"]
    else:
        metadata = {}
    assert isinstance(metadata, dict)

    if source is not None:
        metadata["source"] = source

    kwargs["metadata"] = metadata
    return field(*args, **kwargs)


@dataclass(kw_only=True)
class FixtureHeader:
    """
    Representation of an Ethereum header within a test Fixture.
    """

    parent_hash: Hash = header_field(
        source=HeaderFieldSource(
            parse_type=Hash,
            source_environment="parent_hash",
        ),
        json_encoder=JSONEncoder.Field(name="parentHash"),
    )
    ommers_hash: Hash = header_field(
        source=HeaderFieldSource(
            parse_type=Hash,
            source_transition_tool="sha3Uncles",
            default=EmptyOmmersRoot,
        ),
        json_encoder=JSONEncoder.Field(name="uncleHash"),
    )
    coinbase: Address = header_field(
        source=HeaderFieldSource(
            parse_type=Address,
            source_environment="coinbase",
        ),
        json_encoder=JSONEncoder.Field(),
    )
    state_root: Hash = header_field(
        source=HeaderFieldSource(
            parse_type=Hash,
            source_transition_tool="stateRoot",
        ),
        json_encoder=JSONEncoder.Field(name="stateRoot"),
    )
    transactions_root: Hash = header_field(
        source=HeaderFieldSource(
            parse_type=Hash,
            source_transition_tool="txRoot",
        ),
        json_encoder=JSONEncoder.Field(name="transactionsTrie"),
    )
    receipt_root: Hash = header_field(
        source=HeaderFieldSource(
            parse_type=Hash,
            source_transition_tool="receiptsRoot",
        ),
        json_encoder=JSONEncoder.Field(name="receiptTrie"),
    )
    bloom: Bloom = header_field(
        source=HeaderFieldSource(
            parse_type=Bloom,
            source_transition_tool="logsBloom",
        ),
        json_encoder=JSONEncoder.Field(),
    )
    difficulty: int = header_field(
        source=HeaderFieldSource(
            parse_type=Number,
            source_transition_tool="currentDifficulty",
            source_environment="difficulty",
            default=0,
        ),
        json_encoder=JSONEncoder.Field(cast_type=ZeroPaddedHexNumber),
    )
    number: int = header_field(
        source=HeaderFieldSource(
            parse_type=Number,
            source_environment="number",
        ),
        json_encoder=JSONEncoder.Field(cast_type=ZeroPaddedHexNumber),
    )
    gas_limit: int = header_field(
        source=HeaderFieldSource(
            parse_type=Number,
            source_environment="gas_limit",
        ),
        json_encoder=JSONEncoder.Field(name="gasLimit", cast_type=ZeroPaddedHexNumber),
    )
    gas_used: int = header_field(
        source=HeaderFieldSource(
            parse_type=Number,
            source_transition_tool="gasUsed",
        ),
        json_encoder=JSONEncoder.Field(name="gasUsed", cast_type=ZeroPaddedHexNumber),
    )
    timestamp: int = header_field(
        source=HeaderFieldSource(
            parse_type=Number,
            source_environment="timestamp",
        ),
        json_encoder=JSONEncoder.Field(cast_type=ZeroPaddedHexNumber),
    )
    extra_data: Bytes = header_field(
        source=HeaderFieldSource(
            parse_type=Bytes,
            source_environment="extra_data",
            default=b"",
        ),
        json_encoder=JSONEncoder.Field(name="extraData"),
    )
    mix_digest: Hash = header_field(
        source=HeaderFieldSource(
            parse_type=Hash,
            source_environment="prev_randao",
            default=b"",
        ),
        json_encoder=JSONEncoder.Field(name="mixHash"),
    )
    nonce: HeaderNonce = header_field(
        source=HeaderFieldSource(
            parse_type=HeaderNonce,
            default=b"",
        ),
        json_encoder=JSONEncoder.Field(),
    )
    base_fee: Optional[int] = header_field(
        default=None,
        source=HeaderFieldSource(
            parse_type=Number,
            fork_requirement_check="header_base_fee_required",
            source_transition_tool="currentBaseFee",
            source_environment="base_fee",
        ),
        json_encoder=JSONEncoder.Field(name="baseFeePerGas", cast_type=ZeroPaddedHexNumber),
    )
    withdrawals_root: Optional[Hash] = header_field(
        default=None,
        source=HeaderFieldSource(
            parse_type=Hash,
            fork_requirement_check="header_withdrawals_required",
            source_transition_tool="withdrawalsRoot",
        ),
        json_encoder=JSONEncoder.Field(name="withdrawalsRoot"),
    )
    blob_gas_used: Optional[int] = header_field(
        default=None,
        source=HeaderFieldSource(
            parse_type=Number,
            fork_requirement_check="header_blob_gas_used_required",
            source_transition_tool="blobGasUsed",
        ),
        json_encoder=JSONEncoder.Field(name="blobGasUsed", cast_type=ZeroPaddedHexNumber),
    )
    excess_blob_gas: Optional[int] = header_field(
        default=None,
        source=HeaderFieldSource(
            parse_type=Number,
            fork_requirement_check="header_excess_blob_gas_required",
            source_transition_tool="currentExcessBlobGas",
        ),
        json_encoder=JSONEncoder.Field(name="excessBlobGas", cast_type=ZeroPaddedHexNumber),
    )
    beacon_root: Optional[Hash] = header_field(
        default=None,
        source=HeaderFieldSource(
            parse_type=Hash,
            fork_requirement_check="header_beacon_root_required",
            source_environment="beacon_root",
        ),
        json_encoder=JSONEncoder.Field(name="parentBeaconBlockRoot"),
    )
    hash: Optional[Hash] = header_field(
        default=None,
        source=HeaderFieldSource(
            required=False,
        ),
        json_encoder=JSONEncoder.Field(),
    )

    @classmethod
    def collect(
        cls,
        *,
        fork: Fork,
        transition_tool_result: Dict[str, Any],
        environment: Environment,
    ) -> "FixtureHeader":
        """
        Collects a FixtureHeader object from multiple sources:
        - The transition tool result
        - The test's current environment
        """
        # We depend on the environment to get the number and timestamp to check the fork
        # requirements
        number, timestamp = Number(environment.number), Number(environment.timestamp)

        # Collect the header fields
        kwargs: Dict[str, Any] = {}
        for header_field in fields(cls):
            field_name = header_field.name
            metadata = header_field.metadata
            assert metadata is not None, f"Field {field_name} has no header field metadata"
            field_metadata = metadata.get("source")
            assert isinstance(field_metadata, HeaderFieldSource), (
                f"Field {field_name} has invalid header_field " f"metadata: {field_metadata}"
            )
            field_metadata.collect(
                target=kwargs,
                field_name=field_name,
                fork=fork,
                number=number,
                timestamp=timestamp,
                transition_tool_result=transition_tool_result,
                environment=environment,
            )

        # Pass the collected fields as keyword arguments to the constructor
        return cls(**kwargs)

    def join(self, modifier: Header) -> "FixtureHeader":
        """
        Produces a fixture header copy with the set values from the modifier.
        """
        new_fixture_header = copy(self)
        for header_field in fields(self):
            field_name = header_field.name
            value = getattr(modifier, field_name)
            if value is not None:
                if value is Header.REMOVE_FIELD:
                    setattr(new_fixture_header, field_name, None)
                else:
                    metadata = header_field.metadata
                    assert metadata is not None, f"Field {field_name} has no header field metadata"
                    field_metadata = metadata.get("source")
                    assert isinstance(field_metadata, HeaderFieldSource), (
                        f"Field {field_name} has invalid header_field "
                        f"metadata: {field_metadata}"
                    )
                    if field_metadata.parse_type is not None:
                        value = field_metadata.parse_type(value)
                    setattr(new_fixture_header, field_name, value)
        return new_fixture_header

    def verify(self, baseline: Header):
        """
        Verifies that the header fields from the baseline are as expected.
        """
        for header_field in fields(self):
            field_name = header_field.name
            baseline_value = getattr(baseline, field_name)
            if baseline_value is not None:
                assert baseline_value is not Header.REMOVE_FIELD, "invalid baseline header"
                value = getattr(self, field_name)
                if baseline_value is Header.EMPTY_FIELD:
                    assert (
                        value is None
                    ), f"invalid header field {field_name}, got {value}, want None"
                    continue
                metadata = header_field.metadata
                field_metadata = metadata.get("source")
                # type check is performed on collect()
                if field_metadata.parse_type is not None:  # type: ignore
                    baseline_value = field_metadata.parse_type(baseline_value)  # type: ignore
                assert value == baseline_value, (
                    f"invalid header field ({field_name}) value, "
                    + f"got {value}, want {baseline_value}"
                )

    def build(
        self,
        *,
        txs: List[Transaction],
        ommers: List[Header],
        withdrawals: List[Withdrawal] | None,
    ) -> Tuple[Bytes, Hash]:
        """
        Returns the serialized version of the block and its hash.
        """
        header = [
            self.parent_hash,
            self.ommers_hash,
            self.coinbase,
            self.state_root,
            self.transactions_root,
            self.receipt_root,
            self.bloom,
            Uint(int(self.difficulty)),
            Uint(int(self.number)),
            Uint(int(self.gas_limit)),
            Uint(int(self.gas_used)),
            Uint(int(self.timestamp)),
            self.extra_data,
            self.mix_digest,
            self.nonce,
        ]
        if self.base_fee is not None:
            header.append(Uint(int(self.base_fee)))
        if self.withdrawals_root is not None:
            header.append(self.withdrawals_root)
        if self.blob_gas_used is not None:
            header.append(Uint(int(self.blob_gas_used)))
        if self.excess_blob_gas is not None:
            header.append(Uint(self.excess_blob_gas))
        if self.beacon_root is not None:
            header.append(self.beacon_root)

        block = [
            header,
            transaction_list_to_serializable_list(txs),
            ommers,  # TODO: This is incorrect, and we probably need to serialize the ommers
        ]

        if withdrawals is not None:
            block.append([w.to_serializable_list() for w in withdrawals])

        serialized_bytes = Bytes(eth_rlp.encode(block))

        return serialized_bytes, Hash(keccak256(eth_rlp.encode(header)))


@dataclass(kw_only=True)
class Block(Header):
    """
    Block type used to describe block properties in test specs
    """

    rlp: Optional[BytesConvertible] = None
    """
    If set, blockchain test will skip generating the block and will pass this value directly to
    the Fixture.

    Only meant to be used to simulate blocks with bad formats, and therefore
    requires the block to produce an exception.
    """
    header_verify: Optional[Header] = None
    """
    If set, the block header will be verified against the specified values.
    """
    rlp_modifier: Optional[Header] = None
    """
    An RLP modifying header which values would be used to override the ones
    returned by the  `evm_transition_tool`.
    """
    exception: Optional[BlockException | TransactionException | ExceptionList] = None
    """
    If set, the block is expected to be rejected by the client.
    """
    engine_api_error_code: Optional[EngineAPIError] = None
    """
    If set, the block is expected to produce an error response from the Engine API.
    """
    txs: Optional[List[Transaction]] = None
    """
    List of transactions included in the block.
    """
    ommers: Optional[List[Header]] = None
    """
    List of ommer headers included in the block.
    """
    withdrawals: Optional[List[Withdrawal]] = None
    """
    List of withdrawals to perform for this block.
    """

    def set_environment(self, env: Environment) -> Environment:
        """
        Creates a copy of the environment with the characteristics of this
        specific block.
        """
        new_env = copy(env)

        """
        Values that need to be set in the environment and are `None` for
        this block need to be set to their defaults.
        """
        environment_default = Environment()
        new_env.difficulty = self.difficulty
        new_env.coinbase = (
            self.coinbase if self.coinbase is not None else environment_default.coinbase
        )
        new_env.gas_limit = self.gas_limit or env.parent_gas_limit or environment_default.gas_limit
        if not isinstance(self.base_fee, Removable):
            new_env.base_fee = self.base_fee
        new_env.withdrawals = self.withdrawals
        if not isinstance(self.excess_blob_gas, Removable):
            new_env.excess_blob_gas = self.excess_blob_gas
        if not isinstance(self.blob_gas_used, Removable):
            new_env.blob_gas_used = self.blob_gas_used
        if not isinstance(self.beacon_root, Removable):
            new_env.beacon_root = self.beacon_root
        """
        These values are required, but they depend on the previous environment,
        so they can be calculated here.
        """
        if self.number is not None:
            new_env.number = self.number
        else:
            # calculate the next block number for the environment
            if len(new_env.block_hashes) == 0:
                new_env.number = 0
            else:
                new_env.number = max([Number(n) for n in new_env.block_hashes.keys()]) + 1

        if self.timestamp is not None:
            new_env.timestamp = self.timestamp
        else:
            assert new_env.parent_timestamp is not None
            new_env.timestamp = int(Number(new_env.parent_timestamp) + 12)

        return new_env

    def copy_with_rlp(self, rlp: Bytes | BytesConvertible | None) -> "Block":
        """
        Creates a copy of the block and adds the specified RLP.
        """
        new_block = deepcopy(self)
        new_block.rlp = Bytes.or_none(rlp)
        return new_block


@dataclass(kw_only=True)
class FixtureExecutionPayload(FixtureHeader):
    """
    Representation of the execution payload of a block within a test fixture.
    """

    # Skipped fields in the Engine API
    ommers_hash: Hash = field(
        json_encoder=JSONEncoder.Field(
            skip=True,
        ),
    )
    transactions_root: Hash = field(
        json_encoder=JSONEncoder.Field(
            skip=True,
        ),
    )
    difficulty: int = field(
        json_encoder=JSONEncoder.Field(
            skip=True,
        )
    )
    nonce: HeaderNonce = field(
        json_encoder=JSONEncoder.Field(
            skip=True,
        )
    )
    withdrawals_root: Optional[Hash] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            skip=True,
        ),
    )

    # Fields with different names
    coinbase: Address = field(
        json_encoder=JSONEncoder.Field(
            name="feeRecipient",
        )
    )
    receipt_root: Hash = field(
        json_encoder=JSONEncoder.Field(
            name="receiptsRoot",
        ),
    )
    bloom: Bloom = field(
        json_encoder=JSONEncoder.Field(
            name="logsBloom",
        )
    )
    mix_digest: Hash = field(
        json_encoder=JSONEncoder.Field(
            name="prevRandao",
        ),
    )
    hash: Optional[Hash] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="blockHash",
        ),
    )

    # Fields with different formatting
    number: int = field(
        json_encoder=JSONEncoder.Field(
            name="blockNumber",
            cast_type=HexNumber,
        )
    )
    gas_limit: int = field(json_encoder=JSONEncoder.Field(name="gasLimit", cast_type=HexNumber))
    gas_used: int = field(json_encoder=JSONEncoder.Field(name="gasUsed", cast_type=HexNumber))
    timestamp: int = field(json_encoder=JSONEncoder.Field(cast_type=HexNumber))
    base_fee: Optional[int] = field(
        default=None,
        json_encoder=JSONEncoder.Field(name="baseFeePerGas", cast_type=HexNumber),
    )
    blob_gas_used: Optional[int] = field(
        default=None,
        json_encoder=JSONEncoder.Field(name="blobGasUsed", cast_type=HexNumber),
    )
    excess_blob_gas: Optional[int] = field(
        default=None,
        json_encoder=JSONEncoder.Field(name="excessBlobGas", cast_type=HexNumber),
    )

    # Fields only used in the Engine API
    transactions: Optional[List[Transaction]] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            cast_type=lambda txs: [Bytes(tx.serialized_bytes()) for tx in txs],
            to_json=True,
        ),
    )
    withdrawals: Optional[List[Withdrawal]] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            to_json=True,
        ),
    )

    @classmethod
    def from_fixture_header(
        cls,
        header: FixtureHeader,
        transactions: Optional[List[Transaction]] = None,
        withdrawals: Optional[List[Withdrawal]] = None,
    ) -> "FixtureExecutionPayload":
        """
        Returns a FixtureExecutionPayload from a FixtureHeader, a list
        of transactions and a list of withdrawals.
        """
        kwargs = {field.name: getattr(header, field.name) for field in fields(header)}
        return cls(**kwargs, transactions=transactions, withdrawals=withdrawals)


@dataclass(kw_only=True)
class FixtureEngineNewPayload:
    """
    Representation of the `engine_newPayloadVX` information to be
    sent using the block information.
    """

    payload: FixtureExecutionPayload = field(
        json_encoder=JSONEncoder.Field(
            name="executionPayload",
            to_json=True,
        )
    )
    blob_versioned_hashes: Optional[List[FixedSizeBytesConvertible]] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="expectedBlobVersionedHashes",
            cast_type=lambda hashes: [Hash(hash) for hash in hashes],
            to_json=True,
        ),
    )
    beacon_root: Optional[FixedSizeBytesConvertible] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="parentBeaconBlockRoot",
            cast_type=Hash,
        ),
    )
    validation_error: Optional[TransactionException | BlockException | ExceptionList] = field(
        json_encoder=JSONEncoder.Field(
            name="validationError",
        ),
    )
    version: int = field(
        json_encoder=JSONEncoder.Field(),
    )
    error_code: Optional[EngineAPIError] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="errorCode",
            cast_type=int,
        ),
    )

    @classmethod
    def from_fixture_header(
        cls,
        fork: Fork,
        header: FixtureHeader,
        transactions: List[Transaction],
        withdrawals: Optional[List[Withdrawal]],
        validation_error: Optional[TransactionException | BlockException | ExceptionList],
        error_code: Optional[EngineAPIError],
    ) -> "FixtureEngineNewPayload":
        """
        Creates a `FixtureEngineNewPayload` from a `FixtureHeader`.
        """
        new_payload_version = fork.engine_new_payload_version(header.number, header.timestamp)

        assert new_payload_version is not None, "Invalid header for engine_newPayload"

        new_payload = cls(
            payload=FixtureExecutionPayload.from_fixture_header(
                header=replace(header, beacon_root=None),
                transactions=transactions,
                withdrawals=withdrawals,
            ),
            version=new_payload_version,
            validation_error=validation_error,
            error_code=error_code,
        )

        if fork.engine_new_payload_blob_hashes(header.number, header.timestamp):
            new_payload.blob_versioned_hashes = blob_versioned_hashes_from_transactions(
                transactions
            )

        if fork.engine_new_payload_beacon_root(header.number, header.timestamp):
            new_payload.beacon_root = header.beacon_root

        return new_payload


@dataclass
class FixtureTransaction(Transaction):
    """
    Representation of an Ethereum transaction within a test Fixture.
    """

    ty: Optional[int] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="type",
            cast_type=ZeroPaddedHexNumber,
        ),
    )
    """
    Transaction type value.
    """
    chain_id: int = field(
        default=1,
        json_encoder=JSONEncoder.Field(
            name="chainId",
            cast_type=ZeroPaddedHexNumber,
        ),
    )
    nonce: int = field(
        default=0,
        json_encoder=JSONEncoder.Field(
            cast_type=ZeroPaddedHexNumber,
        ),
    )
    gas_price: Optional[int] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="gasPrice",
            cast_type=ZeroPaddedHexNumber,
        ),
    )
    max_priority_fee_per_gas: Optional[int] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="maxPriorityFeePerGas",
            cast_type=ZeroPaddedHexNumber,
        ),
    )
    max_fee_per_gas: Optional[int] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="maxFeePerGas",
            cast_type=ZeroPaddedHexNumber,
        ),
    )
    gas_limit: int = field(
        default=21000,
        json_encoder=JSONEncoder.Field(
            name="gasLimit",
            cast_type=ZeroPaddedHexNumber,
        ),
    )
    to: Optional[FixedSizeBytesConvertible] = field(
        default=AddrAA,
        json_encoder=JSONEncoder.Field(
            cast_type=Address,
            default_value_skip_cast="",
        ),
    )
    value: int = field(
        default=0,
        json_encoder=JSONEncoder.Field(
            cast_type=ZeroPaddedHexNumber,
        ),
    )
    data: BytesConvertible = field(
        default_factory=bytes,
        json_encoder=JSONEncoder.Field(
            cast_type=Bytes,
        ),
    )
    max_fee_per_blob_gas: Optional[int] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="maxFeePerBlobGas",
            cast_type=ZeroPaddedHexNumber,
        ),
    )
    v: Optional[int] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            cast_type=ZeroPaddedHexNumber,
        ),
    )
    r: Optional[int] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            cast_type=ZeroPaddedHexNumber,
        ),
    )
    s: Optional[int] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            cast_type=ZeroPaddedHexNumber,
        ),
    )

    @classmethod
    def from_transaction(cls, tx: Transaction) -> "FixtureTransaction":
        """
        Returns a FixtureTransaction from a Transaction.
        """
        kwargs = {field.name: getattr(tx, field.name) for field in fields(tx)}
        return cls(**kwargs)


@dataclass(kw_only=True)
class FixtureWithdrawal(Withdrawal):
    """
    Structure to represent a single withdrawal of a validator's balance from
    the beacon chain in the output fixture.
    """

    index: NumberConvertible = field(
        json_encoder=JSONEncoder.Field(
            cast_type=ZeroPaddedHexNumber,
        ),
    )
    validator: NumberConvertible = field(
        json_encoder=JSONEncoder.Field(
            name="validatorIndex",
            cast_type=ZeroPaddedHexNumber,
        ),
    )
    amount: NumberConvertible = field(
        json_encoder=JSONEncoder.Field(
            cast_type=ZeroPaddedHexNumber,
        ),
    )

    @classmethod
    def from_withdrawal(cls, w: Withdrawal) -> "FixtureWithdrawal":
        """
        Returns a FixtureWithdrawal from a Withdrawal.
        """
        kwargs = {field.name: getattr(w, field.name) for field in fields(w)}
        return cls(**kwargs)


@dataclass(kw_only=True)
class FixtureBlock:
    """
    Representation of an Ethereum block within a test Fixture.
    """

    rlp: Optional[Bytes] = field(
        json_encoder=JSONEncoder.Field(),
    )
    block_header: FixtureHeader = field(
        json_encoder=JSONEncoder.Field(
            name="blockHeader",
            to_json=True,
        ),
    )
    block_number: NumberConvertible = field(
        json_encoder=JSONEncoder.Field(
            name="blocknumber",
            cast_type=Number,
        ),
    )
    txs: List[Transaction] = field(
        json_encoder=JSONEncoder.Field(
            name="transactions",
            cast_type=lambda txs: [FixtureTransaction.from_transaction(tx) for tx in txs],
            to_json=True,
        ),
    )
    ommers: List[FixtureHeader] = field(
        json_encoder=JSONEncoder.Field(
            name="uncleHeaders",
            to_json=True,
        ),
    )
    withdrawals: Optional[List[Withdrawal]] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="withdrawals",
            cast_type=lambda withdrawals: [
                FixtureWithdrawal.from_withdrawal(w) for w in withdrawals
            ],
            to_json=True,
        ),
    )


@dataclass(kw_only=True)
class InvalidFixtureBlock:
    """
    Representation of an invalid Ethereum block within a test Fixture.
    """

    rlp: Bytes = field(
        json_encoder=JSONEncoder.Field(),
    )
    expected_exception: TransactionException | BlockException | ExceptionList = field(
        json_encoder=JSONEncoder.Field(
            name="expectException",
        ),
    )
    rlp_decoded: Optional[FixtureBlock] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="rlp_decoded",
            to_json=True,
        ),
    )


@dataclass(kw_only=True)
class FixtureCommon(BaseFixture):
    """
    Base Ethereum test fixture fields class.
    """

    name: str = field(
        default="",
        json_encoder=JSONEncoder.Field(
            skip=True,
        ),
    )
    fork: str = field(
        json_encoder=JSONEncoder.Field(
            name="network",
        ),
    )

    @classmethod
    def collect_into_file(cls, fd: TextIO, fixtures: Dict[str, "BaseFixture"]):
        """
        For BlockchainTest format, we simply join the json fixtures into a single file.
        """
        json_fixtures: Dict[str, Dict[str, Any]] = {}
        for name, fixture in fixtures.items():
            assert isinstance(fixture, FixtureCommon), f"Invalid fixture type: {type(fixture)}"
            json_fixtures[name] = fixture.to_json()
        json.dump(json_fixtures, fd, indent=4)


@dataclass(kw_only=True)
class Fixture(FixtureCommon):
    """
    Cross-client specific test fixture information.
    """

    genesis_rlp: Bytes = field(
        json_encoder=JSONEncoder.Field(
            name="genesisRLP",
        ),
    )
    genesis: FixtureHeader = field(
        json_encoder=JSONEncoder.Field(
            name="genesisBlockHeader",
            to_json=True,
        ),
    )
    blocks: List[FixtureBlock | InvalidFixtureBlock] = field(
        json_encoder=JSONEncoder.Field(
            name="blocks",
            to_json=True,
        ),
    )
    last_block_hash: Hash = field(
        json_encoder=JSONEncoder.Field(
            name="lastblockhash",
        ),
    )
    pre_state: Mapping[str, Account] = field(
        json_encoder=JSONEncoder.Field(
            name="pre",
            cast_type=Alloc,
            to_json=True,
        ),
    )
    post_state: Optional[Mapping[str, Account]] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="postState",
            cast_type=Alloc,
            to_json=True,
        ),
    )
    seal_engine: str = field(
        default="NoProof",
        json_encoder=JSONEncoder.Field(
            name="sealEngine",
        ),
    )

    @classmethod
    def output_base_dir_name(cls) -> Path:
        """
        Returns the name of the subdirectory where this type of fixture should be dumped to.
        """
        return Path("blockchain_tests")

    @classmethod
    def format(cls) -> FixtureFormats:
        """
        Returns the fixture format which the evm tool can use to determine how to verify the
        fixture.
        """
        return FixtureFormats.BLOCKCHAIN_TEST


@dataclass(kw_only=True)
class HiveFixture(FixtureCommon):
    """
    Hive specific test fixture information.
    """

    genesis: FixtureHeader = field(
        json_encoder=JSONEncoder.Field(
            name="genesisBlockHeader",
            to_json=True,
        ),
    )
    payloads: List[FixtureEngineNewPayload] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="engineNewPayloads",
            to_json=True,
        ),
    )
    fcu_version: int = field(
        default=1,
        json_encoder=JSONEncoder.Field(
            name="engineFcuVersion",
        ),
    )
    sync_payload: Optional[FixtureEngineNewPayload] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="syncPayload",
            to_json=True,
        ),
    )
    pre_state: Mapping[str, Account] = field(
        json_encoder=JSONEncoder.Field(
            name="pre",
            cast_type=Alloc,
            to_json=True,
        ),
    )
    post_state: Optional[Mapping[str, Account]] = field(
        default=None,
        json_encoder=JSONEncoder.Field(
            name="postState",
            cast_type=Alloc,
            to_json=True,
        ),
    )

    @classmethod
    def output_base_dir_name(cls) -> Path:
        """
        Returns the name of the subdirectory where this type of fixture should be dumped to.
        """
        return Path("blockchain_tests_hive")

    @classmethod
    def format(cls) -> FixtureFormats:
        """
        Returns the fixture format which the evm tool can use to determine how to verify the
        fixture.
        """
        return FixtureFormats.BLOCKCHAIN_TEST_HIVE
