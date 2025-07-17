"""BlockchainTest types."""

from functools import cached_property
from typing import (
    Annotated,
    Any,
    ClassVar,
    List,
    Literal,
    Tuple,
    Union,
    cast,
    get_args,
    get_type_hints,
)

import ethereum_rlp as eth_rlp
from ethereum_types.numeric import Uint
from pydantic import AliasChoices, Field, PlainSerializer, computed_field, model_validator

from ethereum_test_base_types import (
    Address,
    Alloc,
    Bloom,
    Bytes,
    CamelModel,
    EmptyOmmersRoot,
    EmptyTrieRoot,
    Hash,
    HeaderNonce,
    HexNumber,
    Number,
    ZeroPaddedHexNumber,
)
from ethereum_test_exceptions import EngineAPIError, ExceptionInstanceOrList
from ethereum_test_forks import Fork, Paris
from ethereum_test_types import (
    Environment,
    Requests,
    Transaction,
    Withdrawal,
)
from ethereum_test_types.block_types import WithdrawalGeneric
from ethereum_test_types.transaction_types import TransactionFixtureConverter, TransactionGeneric

from .base import BaseFixture
from .common import FixtureAuthorizationTuple, FixtureBlobSchedule


def post_state_validator(alternate_field: str | None = None, mode: str = "after"):
    """
    Create a validator to ensure exactly one post-state field is provided.

    Args:
        alternate_field: Alternative field name to post_state_hash (e.g., 'post_state_diff').
        mode: Pydantic validation mode.

    """

    def decorator(cls):
        @model_validator(mode=mode)
        def validate_post_state_fields(self):
            """Ensure exactly one post-state field is provided."""
            if mode == "after":
                # Determine which fields to check
                if alternate_field:
                    # For engine x fixtures: check post_state vs post_state_diff
                    field1_name, field2_name = "post_state", alternate_field
                else:
                    # For standard fixtures: check post_state vs post_state_hash
                    field1_name, field2_name = "post_state", "post_state_hash"

                field1_value = getattr(self, field1_name, None)
                field2_value = getattr(self, field2_name, None)

                if field1_value is None and field2_value is None:
                    raise ValueError(f"Either {field1_name} or {field2_name} must be provided.")
                if field1_value is not None and field2_value is not None:
                    raise ValueError(
                        f"Only one of {field1_name} or {field2_name} must be provided."
                    )
            return self

        # Apply the validator to the class
        return cls

    return decorator


class HeaderForkRequirement(str):
    """
    Fork requirement class that specifies the name of the method that should be called
    to check if the field is required.
    """

    def __new__(cls, value: str) -> "HeaderForkRequirement":
        """Create a new instance of the class."""
        return super().__new__(cls, value)

    def required(self, fork: Fork, block_number: int, timestamp: int) -> bool:
        """Check if the field is required for the given fork."""
        return getattr(fork, f"header_{self}_required")(block_number, timestamp)

    @classmethod
    def get_from_annotation(cls, field_hints: Any) -> "HeaderForkRequirement | None":
        """Find the annotation in the field args."""
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

    parent_hash: Hash = Hash(0)
    ommers_hash: Hash = Field(Hash(EmptyOmmersRoot), alias="uncleHash")
    fee_recipient: Address = Field(
        ..., alias="coinbase", validation_alias=AliasChoices("coinbase", "miner")
    )
    state_root: Hash
    transactions_trie: Hash = Field(
        Hash(EmptyTrieRoot), validation_alias=AliasChoices("transactionsTrie", "transactionsRoot")
    )
    receipts_root: Hash = Field(
        Hash(EmptyTrieRoot),
        alias="receiptTrie",
        validation_alias=AliasChoices("receiptTrie", "receiptsRoot"),
    )
    logs_bloom: Bloom = Field(
        Bloom(0), alias="bloom", validation_alias=AliasChoices("bloom", "logsBloom")
    )
    difficulty: ZeroPaddedHexNumber = ZeroPaddedHexNumber(0)
    number: ZeroPaddedHexNumber
    gas_limit: ZeroPaddedHexNumber
    gas_used: ZeroPaddedHexNumber = ZeroPaddedHexNumber(0)
    timestamp: ZeroPaddedHexNumber
    extra_data: Bytes
    prev_randao: Hash = Field(Hash(0), alias="mixHash")
    nonce: HeaderNonce = Field(HeaderNonce(0), validate_default=True)
    base_fee_per_gas: (
        Annotated[
            ZeroPaddedHexNumber,
            HeaderForkRequirement("base_fee"),
        ]
        | None
    ) = Field(None)
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
    requests_hash: Annotated[Hash, HeaderForkRequirement("requests")] | None = Field(None)

    fork: Fork | None = Field(None, exclude=True)

    def model_post_init(self, __context):
        """Model post init method used to check for required fields of a given fork."""
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
        """Compute the RLP of the header."""
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
        """Compute the RLP of the header."""
        return Bytes(eth_rlp.encode(self.rlp_encode_list))

    @computed_field(alias="hash")  # type: ignore[misc]
    @cached_property
    def block_hash(self) -> Hash:
        """Compute the RLP of the header."""
        return self.rlp.keccak256()

    @classmethod
    def genesis(cls, fork: Fork, env: Environment, state_root: Hash) -> "FixtureHeader":
        """Get the genesis header for the given fork."""
        environment_values = env.model_dump(exclude_none=True, exclude={"withdrawals"})
        if env.withdrawals is not None:
            environment_values["withdrawals_root"] = Withdrawal.list_root(env.withdrawals)
        environment_values["extra_data"] = env.extra_data
        extras = {
            "state_root": state_root,
            "requests_hash": Requests() if fork.header_requests_required(0, 0) else None,
            "fork": fork,
        }
        return FixtureHeader(**environment_values, **extras)


class FixtureExecutionPayload(CamelModel):
    """Representation of an Ethereum execution payload within a test Fixture."""

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
        withdrawals: List[Withdrawal] | None,
    ) -> "FixtureExecutionPayload":
        """
        Return FixtureExecutionPayload from a FixtureHeader, a list
        of transactions and a list of withdrawals.
        """
        return cls(
            **header.model_dump(exclude={"rlp"}, exclude_none=True),
            transactions=[tx.rlp() for tx in transactions],
            withdrawals=withdrawals,
        )


EngineNewPayloadV1Parameters = Tuple[FixtureExecutionPayload]
EngineNewPayloadV3Parameters = Tuple[FixtureExecutionPayload, List[Hash], Hash]
EngineNewPayloadV4Parameters = Tuple[
    FixtureExecutionPayload,
    List[Hash],
    Hash,
    List[Bytes],
]

# Important: We check EngineNewPayloadV3Parameters first as it has more fields, and pydantic
# has a weird behavior when the smaller tuple is checked first.
EngineNewPayloadParameters = Union[
    EngineNewPayloadV4Parameters,
    EngineNewPayloadV3Parameters,
    EngineNewPayloadV1Parameters,
]


class FixtureEngineNewPayload(CamelModel):
    """
    Representation of the `engine_newPayloadVX` information to be
    sent using the block information.
    """

    params: EngineNewPayloadParameters
    new_payload_version: Number
    forkchoice_updated_version: Number
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

    def valid(self) -> bool:
        """Return whether the payload is valid."""
        return self.validation_error is None

    @classmethod
    def from_fixture_header(
        cls,
        fork: Fork,
        header: FixtureHeader,
        transactions: List[Transaction],
        withdrawals: List[Withdrawal] | None,
        requests: List[Bytes] | None,
        **kwargs,
    ) -> "FixtureEngineNewPayload":
        """Create `FixtureEngineNewPayload` from a `FixtureHeader`."""
        new_payload_version = fork.engine_new_payload_version(header.number, header.timestamp)
        forkchoice_updated_version = fork.engine_forkchoice_updated_version(
            header.number, header.timestamp
        )

        assert new_payload_version is not None, "Invalid header for engine_newPayload"
        execution_payload = FixtureExecutionPayload.from_fixture_header(
            header=header,
            transactions=transactions,
            withdrawals=withdrawals,
        )

        params: List[Any] = [execution_payload]
        if fork.engine_new_payload_blob_hashes(header.number, header.timestamp):
            blob_hashes = Transaction.list_blob_versioned_hashes(transactions)
            if blob_hashes is None:
                raise ValueError(f"Blob hashes are required for ${fork}.")
            params.append(blob_hashes)

        if fork.engine_new_payload_beacon_root(header.number, header.timestamp):
            parent_beacon_block_root = header.parent_beacon_block_root
            if parent_beacon_block_root is None:
                raise ValueError(f"Parent beacon block root is required for ${fork}.")
            params.append(parent_beacon_block_root)

        if fork.engine_new_payload_requests(header.number, header.timestamp):
            if requests is None:
                raise ValueError(f"Requests are required for ${fork}.")
            params.append(requests)

        payload_params: EngineNewPayloadParameters = cast(
            EngineNewPayloadParameters,
            tuple(params),
        )
        new_payload = cls(
            params=payload_params,
            new_payload_version=new_payload_version,
            forkchoice_updated_version=forkchoice_updated_version,
            **kwargs,
        )

        return new_payload


class FixtureTransaction(TransactionFixtureConverter, TransactionGeneric[ZeroPaddedHexNumber]):
    """Representation of an Ethereum transaction within a test Fixture."""

    authorization_list: List[FixtureAuthorizationTuple] | None = None
    initcodes: List[Bytes] | None = None

    @classmethod
    def from_transaction(cls, tx: Transaction) -> "FixtureTransaction":
        """Return FixtureTransaction from a Transaction."""
        return cls(**tx.model_dump())


class FixtureWithdrawal(WithdrawalGeneric[ZeroPaddedHexNumber]):
    """
    Structure to represent a single withdrawal of a validator's balance from
    the beacon chain in the output fixture.
    """

    @classmethod
    def from_withdrawal(cls, w: WithdrawalGeneric) -> "FixtureWithdrawal":
        """Return FixtureWithdrawal from a Withdrawal."""
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
        """Get the block number from the header."""
        return Number(self.header.number)

    def with_rlp(self, txs: List[Transaction]) -> "FixtureBlock":
        """Return FixtureBlock with the RLP bytes set."""
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
        """Return FixtureBlockBase without the RLP bytes set."""
        return FixtureBlockBase(
            **self.model_dump(exclude={"rlp"}),
        )


class FixtureConfig(CamelModel):
    """Chain configuration for a fixture."""

    fork: Fork = Field(..., alias="network")
    chain_id: ZeroPaddedHexNumber = Field(ZeroPaddedHexNumber(1), alias="chainid")
    blob_schedule: FixtureBlobSchedule | None = None


class InvalidFixtureBlock(CamelModel):
    """Representation of an invalid Ethereum block within a test Fixture."""

    rlp: Bytes
    expect_exception: ExceptionInstanceOrList
    rlp_decoded: FixtureBlockBase | None = Field(None, alias="rlp_decoded")


@post_state_validator()
class BlockchainFixtureCommon(BaseFixture):
    """Base blockchain test fixture model."""

    fork: Fork = Field(..., alias="network")
    genesis: FixtureHeader = Field(..., alias="genesisBlockHeader")
    pre: Alloc
    post_state: Alloc | None = Field(None)
    post_state_hash: Hash | None = Field(None)
    last_block_hash: Hash = Field(..., alias="lastblockhash")  # FIXME: lastBlockHash
    config: FixtureConfig

    @model_validator(mode="before")
    @classmethod
    def config_defaults_for_backwards_compatibility(cls, data: Any) -> Any:
        """
        Check if the config field is populated, otherwise use the root-level field values for
        backwards compatibility.
        """
        if isinstance(data, dict):
            if "config" not in data:
                data["config"] = {}
            if isinstance(data["config"], dict):
                if "network" not in data["config"]:
                    data["config"]["network"] = data["network"]
                if "chainid" not in data["config"]:
                    data["config"]["chainid"] = "0x01"
        return data

    def get_fork(self) -> Fork | None:
        """Return fork of the fixture as a string."""
        return self.fork


class BlockchainFixture(BlockchainFixtureCommon):
    """Cross-client specific blockchain test model use in JSON fixtures."""

    format_name: ClassVar[str] = "blockchain_test"
    description: ClassVar[str] = "Tests that generate a blockchain test fixture."

    genesis_rlp: Bytes = Field(..., alias="genesisRLP")
    blocks: List[FixtureBlock | InvalidFixtureBlock]
    seal_engine: Literal["NoProof"] = Field("NoProof")


@post_state_validator()
class BlockchainEngineFixtureCommon(BaseFixture):
    """
    Base blockchain test fixture model for Engine API based execution.

    Similar to BlockchainFixtureCommon but excludes the 'pre' field to avoid
    duplicating large pre-allocations.
    """

    fork: Fork = Field(..., alias="network")
    post_state_hash: Hash | None = Field(None)
    last_block_hash: Hash = Field(..., alias="lastblockhash")  # FIXME: lastBlockHash
    config: FixtureConfig

    def get_fork(self) -> Fork | None:
        """Return fixture's `Fork`."""
        return self.fork

    @classmethod
    def supports_fork(cls, fork: Fork) -> bool:
        """
        Return whether the fixture can be generated for the given fork.

        The Engine API is available only on Paris and afterwards.
        """
        return fork >= Paris


class BlockchainEngineFixture(BlockchainEngineFixtureCommon):
    """Engine specific test fixture information."""

    format_name: ClassVar[str] = "blockchain_test_engine"
    description: ClassVar[str] = (
        "Tests that generate a blockchain test fixture in Engine API format."
    )
    pre: Alloc
    genesis: FixtureHeader = Field(..., alias="genesisBlockHeader")
    post_state: Alloc | None = Field(None)
    payloads: List[FixtureEngineNewPayload] = Field(..., alias="engineNewPayloads")
    sync_payload: FixtureEngineNewPayload | None = None


@post_state_validator(alternate_field="post_state_diff")
class BlockchainEngineXFixture(BlockchainEngineFixtureCommon):
    """
    Engine X specific test fixture information.

    Uses pre-allocation groups (and a single client instance) for efficient
    test execution without client restarts.
    """

    format_name: ClassVar[str] = "blockchain_test_engine_x"
    description: ClassVar[str] = "Tests that generate a Blockchain Test Engine X fixture."

    pre_hash: str
    """Hash of the pre-allocation group this test belongs to."""

    post_state_diff: Alloc | None = None
    """State difference from genesis after test execution (efficiency optimization)."""

    payloads: List[FixtureEngineNewPayload] = Field(..., alias="engineNewPayloads")
    """Engine API payloads for blockchain execution."""

    sync_payload: FixtureEngineNewPayload | None = None
    """Optional sync payload for blockchain synchronization."""
