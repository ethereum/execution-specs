"""
BlockchainTest types
"""

from functools import cached_property
from typing import Annotated, Any, ClassVar, List, Literal, Optional, get_args, get_type_hints

from ethereum import rlp as eth_rlp
from ethereum.base_types import Uint
from ethereum.crypto.hash import keccak256
from pydantic import AliasChoices, Field, PlainSerializer, computed_field

from ethereum_test_base_types import (
    Address,
    Alloc,
    Bloom,
    Bytes,
    CamelModel,
    EmptyOmmersRoot,
    Hash,
    HeaderNonce,
    HexNumber,
    Number,
    ZeroPaddedHexNumber,
)
from ethereum_test_base_types.json import to_json
from ethereum_test_exceptions import EngineAPIError, ExceptionInstanceOrList
from ethereum_test_forks import Fork
from ethereum_test_types.types import (
    DepositRequest,
    DepositRequestGeneric,
    Requests,
    Transaction,
    TransactionFixtureConverter,
    TransactionGeneric,
    Withdrawal,
    WithdrawalGeneric,
    WithdrawalRequest,
    WithdrawalRequestGeneric,
)

from .base import BaseFixture
from .formats import FixtureFormats


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
    fee_recipient: Address = Field(
        ..., alias="coinbase", validation_alias=AliasChoices("coinbase", "miner")
    )
    state_root: Hash
    transactions_trie: Hash = Field(
        validation_alias=AliasChoices("transactionsTrie", "transactionsRoot")
    )
    receipts_root: Hash = Field(
        ..., alias="receiptTrie", validation_alias=AliasChoices("receiptTrie", "receiptsRoot")
    )
    logs_bloom: Bloom = Field(
        ..., alias="bloom", validation_alias=AliasChoices("bloom", "logsBloom")
    )
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
    requests_root: Annotated[Hash, HeaderForkRequirement("requests")] | None = Field(None)

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
    deposit_requests: List[DepositRequest] | None = None
    withdrawal_requests: List[WithdrawalRequest] | None = None

    @classmethod
    def from_fixture_header(
        cls,
        header: FixtureHeader,
        transactions: List[Transaction],
        withdrawals: List[Withdrawal] | None,
        requests: Requests | None,
    ) -> "FixtureExecutionPayload":
        """
        Returns a FixtureExecutionPayload from a FixtureHeader, a list
        of transactions and a list of withdrawals.
        """
        return cls(
            **header.model_dump(exclude={"rlp"}, exclude_none=True),
            transactions=[tx.rlp for tx in transactions],
            withdrawals=withdrawals,
            deposit_requests=requests.deposit_requests() if requests is not None else None,
            withdrawal_requests=requests.withdrawal_requests() if requests is not None else None,
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

    def args(self) -> List[Any]:
        """
        Returns the arguments to be used when calling the Engine API.
        """
        args: List[Any] = [to_json(self.execution_payload)]
        if self.blob_versioned_hashes is not None:
            args.append([str(versioned_hash) for versioned_hash in self.blob_versioned_hashes])
        if self.parent_beacon_block_root is not None:
            args.append(str(self.parent_beacon_block_root))
        return args

    def valid(self) -> bool:
        """
        Returns whether the payload is valid.
        """
        return self.validation_error is None

    @classmethod
    def from_fixture_header(
        cls,
        fork: Fork,
        header: FixtureHeader,
        transactions: List[Transaction],
        withdrawals: List[Withdrawal] | None,
        requests: Requests | None,
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
                requests=requests,
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


class FixtureDepositRequest(DepositRequestGeneric[ZeroPaddedHexNumber]):
    """
    Structure to represent a single deposit request to be processed by the beacon
    chain.
    """

    @classmethod
    def from_deposit_request(cls, d: DepositRequestGeneric) -> "FixtureDepositRequest":
        """
        Returns a FixtureDepositRequest from a DepositRequest.
        """
        return cls(**d.model_dump())


class FixtureWithdrawalRequest(WithdrawalRequestGeneric[ZeroPaddedHexNumber]):
    """
    Structure to represent a single withdrawal request to be processed by the beacon
    chain.
    """

    @classmethod
    def from_withdrawal_request(cls, d: WithdrawalRequestGeneric) -> "FixtureWithdrawalRequest":
        """
        Returns a FixtureWithdrawalRequest from a WithdrawalRequest.
        """
        return cls(**d.model_dump())


class FixtureBlockBase(CamelModel):
    """Representation of an Ethereum block within a test Fixture without RLP bytes."""

    header: FixtureHeader = Field(..., alias="blockHeader")
    txs: List[FixtureTransaction] = Field(default_factory=list, alias="transactions")
    ommers: List[FixtureHeader] = Field(default_factory=list, alias="uncleHeaders")
    withdrawals: List[FixtureWithdrawal] | None = None
    deposit_requests: List[FixtureDepositRequest] | None = None
    withdrawal_requests: List[FixtureWithdrawalRequest] | None = None

    @computed_field(alias="blocknumber")  # type: ignore[misc]
    @cached_property
    def block_number(self) -> Number:
        """
        Get the block number from the header
        """
        return Number(self.header.number)

    def with_rlp(self, txs: List[Transaction], requests: Requests | None) -> "FixtureBlock":
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

        if requests is not None:
            block.append(requests.to_serializable_list())

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
    post_state: Optional[Alloc] = Field(None)
    last_block_hash: Hash = Field(..., alias="lastblockhash")  # FIXME: lastBlockHash

    def get_fork(self) -> str:
        """
        Returns the fork of the fixture as a string.
        """
        return self.fork


class Fixture(FixtureCommon):
    """
    Cross-client specific blockchain test model use in JSON fixtures.
    """

    genesis_rlp: Bytes = Field(..., alias="genesisRLP")
    blocks: List[FixtureBlock | InvalidFixtureBlock]
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
