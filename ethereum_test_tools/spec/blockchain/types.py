"""
BlockchainTest types
"""

from functools import cached_property
from typing import Annotated, Any, ClassVar, Dict, List, Literal, get_args, get_type_hints

from ethereum import rlp as eth_rlp
from ethereum.base_types import Uint
from ethereum.crypto.hash import keccak256
from pydantic import ConfigDict, Field, PlainSerializer, computed_field

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
from ...common.constants import EmptyOmmersRoot, EngineAPIError
from ...common.types import (
    Alloc,
    CamelModel,
    Environment,
    Removable,
    Transaction,
    TransactionFixtureConverter,
    TransactionGeneric,
    Withdrawal,
    WithdrawalGeneric,
)
from ...exceptions import BlockException, ExceptionInstanceOrList, TransactionException
from ..base.base_test import BaseFixture


class Header(CamelModel):
    """
    Header type used to describe block header properties in test specs.
    """

    parent_hash: Hash | None = None
    ommers_hash: Hash | None = None
    fee_recipient: Address | None = None
    state_root: Hash | None = None
    transactions_trie: Hash | None = None
    receipts_root: Hash | None = None
    logs_bloom: Bloom | None = None
    difficulty: HexNumber | None = None
    number: HexNumber | None = None
    gas_limit: HexNumber | None = None
    gas_used: HexNumber | None = None
    timestamp: HexNumber | None = None
    extra_data: Bytes | None = None
    prev_randao: Hash | None = None
    nonce: HeaderNonce | None = None
    base_fee_per_gas: Removable | HexNumber | None = None
    withdrawals_root: Removable | Hash | None = None
    blob_gas_used: Removable | HexNumber | None = None
    excess_blob_gas: Removable | HexNumber | None = None
    parent_beacon_block_root: Removable | Hash | None = None

    REMOVE_FIELD: ClassVar[Removable] = Removable()
    """
    Sentinel object used to specify that a header field should be removed.
    """
    EMPTY_FIELD: ClassVar[Removable] = Removable()
    """
    Sentinel object used to specify that a header field must be empty during verification.

    This can be used in a test to explicitly skip a field in a block's RLP encoding.
    included in the (json) output when the model is serialized. For example:
    ```
    header_modifier = Header(
        excess_blob_gas=Header.REMOVE_FIELD,
    )
    block = Block(
        timestamp=TIMESTAMP,
        rlp_modifier=header_modifier,
        exception=BlockException.INCORRECT_BLOCK_FORMAT,
        engine_api_error_code=EngineAPIError.InvalidParams,
    )
    ```
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        # explicitly set Removable items to None so they are not included in the serialization
        # (in combination with exclude_None=True in model.dump()).
        json_encoders={
            Removable: lambda x: None,
        },
    )


class HeaderForkRequirement(str):
    """
    Fork requirement class that specifies the name of the method that should be called
    to check if the field is required.
    """

    def __new__(cls, value: str) -> "HeaderForkRequirement":
        """
        Create a new instance of the class
        """
        return super().__new__(cls, value)

    def required(self, fork: Fork, block_number: int, timestamp: int) -> bool:
        """
        Check if the field is required for the given fork.
        """
        return getattr(fork, f"header_{self}_required")(block_number, timestamp)

    @classmethod
    def get_from_annotation(cls, field_hints: Any) -> "HeaderForkRequirement | None":
        """
        Find the annotation in the field args
        """
        if isinstance(field_hints, cls):
            return field_hints
        for hint in get_args(field_hints):
            if res := cls.get_from_annotation(hint):
                return res
        return None


class FixtureHeader(CamelModel):
    """
    Representation of an Ethereum header within a test Fixture.

    We combine the `Environment` and `Result` contents to create this model.
    """

    parent_hash: Hash
    ommers_hash: Hash = Field(Hash(EmptyOmmersRoot), alias="uncleHash")
    fee_recipient: Address = Field(..., alias="coinbase")
    state_root: Hash
    transactions_trie: Hash
    receipts_root: Hash = Field(..., alias="receiptTrie")
    logs_bloom: Bloom = Field(..., alias="bloom")
    difficulty: ZeroPaddedHexNumber = ZeroPaddedHexNumber(0)
    number: ZeroPaddedHexNumber
    gas_limit: ZeroPaddedHexNumber
    gas_used: ZeroPaddedHexNumber
    timestamp: ZeroPaddedHexNumber
    extra_data: Bytes
    prev_randao: Hash = Field(Hash(0), alias="mixHash")
    nonce: HeaderNonce = Field(HeaderNonce(0), validate_default=True)
    base_fee_per_gas: Annotated[
        ZeroPaddedHexNumber, HeaderForkRequirement("base_fee")
    ] | None = Field(None)
    withdrawals_root: Annotated[Hash, HeaderForkRequirement("withdrawals")] | None = Field(None)
    blob_gas_used: (
        Annotated[ZeroPaddedHexNumber, HeaderForkRequirement("blob_gas_used")] | None
    ) = Field(None)
    excess_blob_gas: (
        Annotated[ZeroPaddedHexNumber, HeaderForkRequirement("excess_blob_gas")] | None
    ) = Field(None)
    parent_beacon_block_root: Annotated[Hash, HeaderForkRequirement("beacon_root")] | None = Field(
        None
    )

    fork: Fork | None = Field(None, exclude=True)

    def model_post_init(self, __context):
        """
        Model post init method used to check for required fields of a given fork.
        """
        super().model_post_init(__context)

        if self.fork is None:
            # No validation done when we are importing the fixture from file
            return

        # Get the timestamp and block number
        block_number = self.number
        timestamp = self.timestamp

        # For each field, check if any of the annotations are of type HeaderForkRequirement and
        # if so, check if the field is required for the given fork.
        annotated_hints = get_type_hints(self, include_extras=True)

        for field in self.model_fields:
            if field == "fork":
                continue

            header_fork_requirement = HeaderForkRequirement.get_from_annotation(
                annotated_hints[field]
            )
            if header_fork_requirement is not None:
                if (
                    header_fork_requirement.required(self.fork, block_number, timestamp)
                    and getattr(self, field) is None
                ):
                    raise ValueError(f"Field {field} is required for fork {self.fork}")

    @cached_property
    def rlp_encode_list(self) -> List:
        """
        Compute the RLP of the header
        """
        header_list = []
        for field in self.model_fields:
            if field == "fork":
                continue
            value = getattr(self, field)
            if value is not None:
                header_list.append(value if isinstance(value, bytes) else Uint(value))
        return header_list

    @cached_property
    def rlp(self) -> Bytes:
        """
        Compute the RLP of the header
        """
        return Bytes(eth_rlp.encode(self.rlp_encode_list))

    @computed_field(alias="hash")  # type: ignore[misc]
    @cached_property
    def block_hash(self) -> Hash:
        """
        Compute the RLP of the header
        """
        return Hash(keccak256(self.rlp))

    def join(self, modifier: Header) -> "FixtureHeader":
        """
        Produces a fixture header copy with the set values from the modifier.
        """
        return self.copy(
            **{
                k: (v if v is not Header.REMOVE_FIELD else None)
                for k, v in modifier.model_dump(exclude_none=True).items()
            }
        )

    def verify(self, baseline: Header):
        """
        Verifies that the header fields from the baseline are as expected.
        """
        for field_name in baseline.model_fields:
            baseline_value = getattr(baseline, field_name)
            if baseline_value is not None:
                assert baseline_value is not Header.REMOVE_FIELD, "invalid baseline header"
                value = getattr(self, field_name)
                if baseline_value is Header.EMPTY_FIELD:
                    assert (
                        value is None
                    ), f"invalid header field {field_name}, got {value}, want None"
                    continue
                assert value == baseline_value, (
                    f"invalid header field ({field_name}) value, "
                    + f"got {value}, want {baseline_value}"
                )


class Block(Header):
    """
    Block type used to describe block properties in test specs
    """

    rlp: Bytes | None = None
    """
    If set, blockchain test will skip generating the block and will pass this value directly to
    the Fixture.

    Only meant to be used to simulate blocks with bad formats, and therefore
    requires the block to produce an exception.
    """
    header_verify: Header | None = None
    """
    If set, the block header will be verified against the specified values.
    """
    rlp_modifier: Header | None = None
    """
    An RLP modifying header which values would be used to override the ones
    returned by the  `evm_transition_tool`.
    """
    exception: List[
        TransactionException | BlockException
    ] | TransactionException | BlockException | None = None
    """
    If set, the block is expected to be rejected by the client.
    """
    engine_api_error_code: EngineAPIError | None = None
    """
    If set, the block is expected to produce an error response from the Engine API.
    """
    txs: List[Transaction] = Field(default_factory=list)
    """
    List of transactions included in the block.
    """
    ommers: List[Header] | None = None
    """
    List of ommer headers included in the block.
    """
    withdrawals: List[Withdrawal] | None = None
    """
    List of withdrawals to perform for this block.
    """

    def set_environment(self, env: Environment) -> Environment:
        """
        Creates a copy of the environment with the characteristics of this
        specific block.
        """
        new_env_values: Dict[str, Any] = {}

        """
        Values that need to be set in the environment and are `None` for
        this block need to be set to their defaults.
        """
        new_env_values["difficulty"] = self.difficulty
        new_env_values["fee_recipient"] = (
            self.fee_recipient if self.fee_recipient is not None else Environment().fee_recipient
        )
        new_env_values["gas_limit"] = (
            self.gas_limit or env.parent_gas_limit or Environment().gas_limit
        )
        if not isinstance(self.base_fee_per_gas, Removable):
            new_env_values["base_fee_per_gas"] = self.base_fee_per_gas
        new_env_values["withdrawals"] = self.withdrawals
        if not isinstance(self.excess_blob_gas, Removable):
            new_env_values["excess_blob_gas"] = self.excess_blob_gas
        if not isinstance(self.blob_gas_used, Removable):
            new_env_values["blob_gas_used"] = self.blob_gas_used
        if not isinstance(self.parent_beacon_block_root, Removable):
            new_env_values["parent_beacon_block_root"] = self.parent_beacon_block_root
        """
        These values are required, but they depend on the previous environment,
        so they can be calculated here.
        """
        if self.number is not None:
            new_env_values["number"] = self.number
        else:
            # calculate the next block number for the environment
            if len(env.block_hashes) == 0:
                new_env_values["number"] = 0
            else:
                new_env_values["number"] = max([Number(n) for n in env.block_hashes.keys()]) + 1

        if self.timestamp is not None:
            new_env_values["timestamp"] = self.timestamp
        else:
            assert env.parent_timestamp is not None
            new_env_values["timestamp"] = int(Number(env.parent_timestamp) + 12)

        return env.copy(**new_env_values)


class FixtureExecutionPayload(CamelModel):
    """
    Representation of an Ethereum execution payload within a test Fixture.
    """

    parent_hash: Hash
    fee_recipient: Address
    state_root: Hash

    receipts_root: Hash
    logs_bloom: Bloom

    number: HexNumber = Field(..., alias="blockNumber")
    gas_limit: HexNumber
    gas_used: HexNumber
    timestamp: HexNumber
    extra_data: Bytes
    prev_randao: Hash

    base_fee_per_gas: HexNumber
    blob_gas_used: HexNumber | None = Field(None)
    excess_blob_gas: HexNumber | None = Field(None)

    block_hash: Hash

    transactions: List[Bytes]
    withdrawals: List[Withdrawal] | None = None

    @classmethod
    def from_fixture_header(
        cls,
        header: FixtureHeader,
        transactions: List[Transaction],
        withdrawals: List[Withdrawal] | None = None,
    ) -> "FixtureExecutionPayload":
        """
        Returns a FixtureExecutionPayload from a FixtureHeader, a list
        of transactions and a list of withdrawals.
        """
        return cls(
            **header.model_dump(exclude={"rlp"}, exclude_none=True),
            transactions=[tx.rlp for tx in transactions],
            withdrawals=withdrawals,
        )


class FixtureEngineNewPayload(CamelModel):
    """
    Representation of the `engine_newPayloadVX` information to be
    sent using the block information.
    """

    execution_payload: FixtureExecutionPayload
    version: Number
    blob_versioned_hashes: List[Hash] | None = Field(None, alias="expectedBlobVersionedHashes")
    parent_beacon_block_root: Hash | None = Field(None, alias="parentBeaconBlockRoot")
    validation_error: ExceptionInstanceOrList | None = None
    error_code: (
        Annotated[
            EngineAPIError,
            PlainSerializer(
                lambda x: str(x.value),
                return_type=str,
            ),
        ]
        | None
    ) = None

    @classmethod
    def from_fixture_header(
        cls,
        fork: Fork,
        header: FixtureHeader,
        transactions: List[Transaction],
        withdrawals: List[Withdrawal] | None,
        **kwargs,
    ) -> "FixtureEngineNewPayload":
        """
        Creates a `FixtureEngineNewPayload` from a `FixtureHeader`.
        """
        new_payload_version = fork.engine_new_payload_version(header.number, header.timestamp)

        assert new_payload_version is not None, "Invalid header for engine_newPayload"

        new_payload = cls(
            execution_payload=FixtureExecutionPayload.from_fixture_header(
                header=header,
                transactions=transactions,
                withdrawals=withdrawals,
            ),
            version=new_payload_version,
            blob_versioned_hashes=(
                Transaction.list_blob_versioned_hashes(transactions)
                if fork.engine_new_payload_blob_hashes(header.number, header.timestamp)
                else None
            ),
            parent_beacon_block_root=header.parent_beacon_block_root,
            **kwargs,
        )

        return new_payload


class FixtureTransaction(TransactionFixtureConverter, TransactionGeneric[ZeroPaddedHexNumber]):
    """
    Representation of an Ethereum transaction within a test Fixture.
    """

    @classmethod
    def from_transaction(cls, tx: Transaction) -> "FixtureTransaction":
        """
        Returns a FixtureTransaction from a Transaction.
        """
        return cls(**tx.model_dump())


class FixtureWithdrawal(WithdrawalGeneric[ZeroPaddedHexNumber]):
    """
    Structure to represent a single withdrawal of a validator's balance from
    the beacon chain in the output fixture.
    """

    @classmethod
    def from_withdrawal(cls, w: WithdrawalGeneric) -> "FixtureWithdrawal":
        """
        Returns a FixtureWithdrawal from a Withdrawal.
        """
        return cls(**w.model_dump())


class FixtureBlockBase(CamelModel):
    """Representation of an Ethereum block within a test Fixture without RLP bytes."""

    header: FixtureHeader = Field(..., alias="blockHeader")
    txs: List[FixtureTransaction] = Field(default_factory=list, alias="transactions")
    ommers: List[FixtureHeader] = Field(default_factory=list, alias="uncleHeaders")
    withdrawals: List[FixtureWithdrawal] | None = None

    @computed_field(alias="blocknumber")  # type: ignore[misc]
    @cached_property
    def block_number(self) -> Number:
        """
        Get the block number from the header
        """
        return Number(self.header.number)

    def with_rlp(self, txs: List[Transaction]) -> "FixtureBlock":
        """
        Returns a FixtureBlock with the RLP bytes set.
        """
        block = [
            self.header.rlp_encode_list,
            [tx.serializable_list for tx in txs],
            self.ommers,  # TODO: This is incorrect, and we probably need to serialize the ommers
        ]

        if self.withdrawals is not None:
            block.append([w.to_serializable_list() for w in self.withdrawals])

        return FixtureBlock(
            **self.model_dump(),
            rlp=eth_rlp.encode(block),
        )


class FixtureBlock(FixtureBlockBase):
    """Representation of an Ethereum block within a test Fixture."""

    rlp: Bytes

    def without_rlp(self) -> FixtureBlockBase:
        """
        Returns a FixtureBlockBase without the RLP bytes set.
        """
        return FixtureBlockBase(
            **self.model_dump(exclude={"rlp"}),
        )


class InvalidFixtureBlock(CamelModel):
    """
    Representation of an invalid Ethereum block within a test Fixture.
    """

    rlp: Bytes
    expect_exception: ExceptionInstanceOrList
    rlp_decoded: FixtureBlockBase | None = Field(None, alias="rlp_decoded")


class FixtureCommon(BaseFixture):
    """
    Base blockchain test fixture model.
    """

    fork: str = Field(..., alias="network")
    genesis: FixtureHeader = Field(..., alias="genesisBlockHeader")
    pre: Alloc
    post_state: Alloc


class Fixture(FixtureCommon):
    """
    Cross-client specific blockchain test model use in JSON fixtures.
    """

    genesis_rlp: Bytes = Field(..., alias="genesisRLP")
    blocks: List[FixtureBlock | InvalidFixtureBlock]
    last_block_hash: Hash = Field(..., alias="lastblockhash")
    seal_engine: Literal["NoProof"] = Field("NoProof")

    format: ClassVar[FixtureFormats] = FixtureFormats.BLOCKCHAIN_TEST


class HiveFixture(FixtureCommon):
    """
    Hive specific test fixture information.
    """

    payloads: List[FixtureEngineNewPayload] = Field(..., alias="engineNewPayloads")
    fcu_version: Number = Field(..., alias="engineFcuVersion")
    sync_payload: FixtureEngineNewPayload | None = None

    format: ClassVar[FixtureFormats] = FixtureFormats.BLOCKCHAIN_TEST_HIVE
