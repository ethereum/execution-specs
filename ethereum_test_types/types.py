"""Useful types for generating Ethereum tests."""

from abc import abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from functools import cached_property
from typing import Any, ClassVar, Dict, Generic, List, Literal, Sequence, SupportsBytes, Tuple

from coincurve.keys import PrivateKey, PublicKey
from ethereum import rlp as eth_rlp
from ethereum.frontier.fork_types import Account as FrontierAccount
from ethereum.frontier.fork_types import Address as FrontierAddress
from ethereum.frontier.state import State, set_account, set_storage, state_root
from ethereum_types.numeric import U256, Uint
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PrivateAttr,
    computed_field,
    model_serializer,
    model_validator,
)
from trie import HexaryTrie

from ethereum_test_base_types import (
    AccessList,
    Account,
    Address,
    Bloom,
    BLSPublicKey,
    BLSSignature,
    Bytes,
    CamelModel,
    EmptyOmmersRoot,
    Hash,
    HexNumber,
    Number,
    NumberBoundTypeVar,
    Storage,
    StorageRootType,
    TestAddress,
    TestPrivateKey,
)
from ethereum_test_base_types import Alloc as BaseAlloc
from ethereum_test_base_types.conversions import (
    BytesConvertible,
    FixedSizeBytesConvertible,
    NumberConvertible,
)
from ethereum_test_exceptions import TransactionException
from ethereum_test_forks import Fork
from ethereum_test_vm import EVMCodeType


def keccak256(data: bytes) -> Hash:
    """Calculate keccak256 hash of the given data."""
    return Bytes(data).keccak256()


def int_to_bytes(value: int) -> bytes:
    """Convert integer to its big-endian representation."""
    if value == 0:
        return b""

    return int_to_bytes(value // 256) + bytes([value % 256])


# Sentinel classes
class Removable:
    """
    Sentinel class to detect if a parameter should be removed.
    (`None` normally means "do not modify").
    """

    pass


class EOA(Address):
    """
    An Externally Owned Account (EOA) is an account controlled by a private key.

    The EOA is defined by its address and (optionally) by its corresponding private key.
    """

    key: Hash | None
    nonce: Number

    def __new__(
        cls,
        address: "FixedSizeBytesConvertible | Address | EOA | None" = None,
        *,
        key: FixedSizeBytesConvertible | None = None,
        nonce: NumberConvertible = 0,
    ):
        """Init the EOA."""
        if address is None:
            if key is None:
                raise ValueError("impossible to initialize EOA without address")
            private_key = PrivateKey(Hash(key))
            public_key = private_key.public_key
            address = Address(keccak256(public_key.format(compressed=False)[1:])[32 - 20 :])
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

    def copy(self) -> "EOA":
        """Return copy of the EOA."""
        return EOA(Address(self), key=self.key, nonce=self.nonce)


class Alloc(BaseAlloc):
    """Allocation of accounts in the state, pre and post test execution."""

    _eoa_fund_amount_default: int = PrivateAttr(10**21)

    @dataclass(kw_only=True)
    class UnexpectedAccountError(Exception):
        """Unexpected account found in the allocation."""

        address: Address
        account: Account | None

        def __init__(self, address: Address, account: Account | None, *args):
            """Initialize the exception."""
            super().__init__(args)
            self.address = address
            self.account = account

        def __str__(self):
            """Print exception string."""
            return f"unexpected account in allocation {self.address}: {self.account}"

    @dataclass(kw_only=True)
    class MissingAccountError(Exception):
        """Expected account not found in the allocation."""

        address: Address

        def __init__(self, address: Address, *args):
            """Initialize the exception."""
            super().__init__(args)
            self.address = address

        def __str__(self):
            """Print exception string."""
            return f"Account missing from allocation {self.address}"

    @classmethod
    def merge(cls, alloc_1: "Alloc", alloc_2: "Alloc") -> "Alloc":
        """Return merged allocation of two sources."""
        merged = alloc_1.model_dump()

        for address, other_account in alloc_2.root.items():
            merged_account = Account.merge(merged.get(address, None), other_account)
            if merged_account:
                merged[address] = merged_account
            elif address in merged:
                merged.pop(address, None)

        return Alloc(merged)

    def __iter__(self):
        """Return iterator over the allocation."""
        return iter(self.root)

    def items(self):
        """Return iterator over the allocation items."""
        return self.root.items()

    def __getitem__(self, address: Address | FixedSizeBytesConvertible) -> Account | None:
        """Return account associated with an address."""
        if not isinstance(address, Address):
            address = Address(address)
        return self.root[address]

    def __setitem__(self, address: Address | FixedSizeBytesConvertible, account: Account | None):
        """Set account associated with an address."""
        if not isinstance(address, Address):
            address = Address(address)
        self.root[address] = account

    def __delitem__(self, address: Address | FixedSizeBytesConvertible):
        """Delete account associated with an address."""
        if not isinstance(address, Address):
            address = Address(address)
        self.root.pop(address, None)

    def __eq__(self, other) -> bool:
        """Return True if both allocations are equal."""
        if not isinstance(other, Alloc):
            return False
        return self.root == other.root

    def __contains__(self, address: Address | FixedSizeBytesConvertible) -> bool:
        """Check if an account is in the allocation."""
        if not isinstance(address, Address):
            address = Address(address)
        return address in self.root

    def empty_accounts(self) -> List[Address]:
        """Return list of addresses of empty accounts."""
        return [address for address, account in self.root.items() if not account]

    def state_root(self) -> bytes:
        """Return state root of the allocation."""
        state = State()
        for address, account in self.root.items():
            if account is None:
                continue
            set_account(
                state=state,
                address=FrontierAddress(address),
                account=FrontierAccount(
                    nonce=Uint(account.nonce) if account.nonce is not None else Uint(0),
                    balance=(U256(account.balance) if account.balance is not None else U256(0)),
                    code=account.code if account.code is not None else b"",
                ),
            )
            if account.storage is not None:
                for key, value in account.storage.root.items():
                    set_storage(
                        state=state,
                        address=FrontierAddress(address),
                        key=Hash(key),
                        value=U256(value),
                    )
        return state_root(state)

    def verify_post_alloc(self, got_alloc: "Alloc"):
        """
        Verify that the allocation matches the expected post in the test.
        Raises exception on unexpected values.
        """
        assert isinstance(got_alloc, Alloc), f"got_alloc is not an Alloc: {got_alloc}"
        for address, account in self.root.items():
            if account is None:
                # Account must not exist
                if address in got_alloc.root and got_alloc.root[address] is not None:
                    raise Alloc.UnexpectedAccountError(address, got_alloc.root[address])
            else:
                if address in got_alloc.root:
                    got_account = got_alloc.root[address]
                    assert isinstance(got_account, Account)
                    assert isinstance(account, Account)
                    account.check_alloc(address, got_account)
                else:
                    raise Alloc.MissingAccountError(address)

    def deploy_contract(
        self,
        code: BytesConvertible,
        *,
        storage: Storage | StorageRootType | None = None,
        balance: NumberConvertible = 0,
        nonce: NumberConvertible = 1,
        address: Address | None = None,
        evm_code_type: EVMCodeType | None = None,
        label: str | None = None,
    ) -> Address:
        """Deploy a contract to the allocation."""
        raise NotImplementedError("deploy_contract is not implemented in the base class")

    def fund_eoa(
        self,
        amount: NumberConvertible | None = None,
        label: str | None = None,
        storage: Storage | None = None,
        delegation: Address | Literal["Self"] | None = None,
        nonce: NumberConvertible | None = None,
    ) -> EOA:
        """Add a previously unused EOA to the pre-alloc with the balance specified by `amount`."""
        raise NotImplementedError("fund_eoa is not implemented in the base class")

    def fund_address(self, address: Address, amount: NumberConvertible):
        """
        Fund an address with a given amount.

        If the address is already present in the pre-alloc the amount will be
        added to its existing balance.
        """
        raise NotImplementedError("fund_address is not implemented in the base class")


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


DEFAULT_BASE_FEE = 7


class EnvironmentGeneric(CamelModel, Generic[NumberBoundTypeVar]):
    """Used as a parent class for `Environment` and `FixtureEnvironment`."""

    fee_recipient: Address = Field(
        Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba"),
        alias="currentCoinbase",
    )
    gas_limit: NumberBoundTypeVar = Field(100_000_000_000_000_000, alias="currentGasLimit")  # type: ignore
    number: NumberBoundTypeVar = Field(1, alias="currentNumber")  # type: ignore
    timestamp: NumberBoundTypeVar = Field(1_000, alias="currentTimestamp")  # type: ignore
    prev_randao: NumberBoundTypeVar | None = Field(None, alias="currentRandom")
    difficulty: NumberBoundTypeVar | None = Field(None, alias="currentDifficulty")
    base_fee_per_gas: NumberBoundTypeVar | None = Field(None, alias="currentBaseFee")
    excess_blob_gas: NumberBoundTypeVar | None = Field(None, alias="currentExcessBlobGas")
    target_blobs_per_block: NumberBoundTypeVar | None = Field(
        None,
        alias="currentTargetBlobsPerBlock",
    )

    parent_difficulty: NumberBoundTypeVar | None = Field(None)
    parent_timestamp: NumberBoundTypeVar | None = Field(None)
    parent_base_fee_per_gas: NumberBoundTypeVar | None = Field(None, alias="parentBaseFee")
    parent_gas_used: NumberBoundTypeVar | None = Field(None)
    parent_gas_limit: NumberBoundTypeVar | None = Field(None)


class Environment(EnvironmentGeneric[Number]):
    """
    Structure used to keep track of the context in which a block
    must be executed.
    """

    blob_gas_used: Number | None = Field(None, alias="currentBlobGasUsed")
    parent_ommers_hash: Hash = Field(Hash(EmptyOmmersRoot), alias="parentUncleHash")
    parent_blob_gas_used: Number | None = Field(None)
    parent_excess_blob_gas: Number | None = Field(None)
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

        if (
            fork.header_target_blobs_per_block_required(number, timestamp)
            and self.target_blobs_per_block is None
        ):
            updated_values["target_blobs_per_block"] = fork.target_blobs_per_block(
                number, timestamp
            )

        return self.copy(**updated_values)


class AuthorizationTupleGeneric(CamelModel, Generic[NumberBoundTypeVar]):
    """Authorization tuple for transactions."""

    chain_id: NumberBoundTypeVar = Field(0)  # type: ignore
    address: Address
    nonce: List[NumberBoundTypeVar] | NumberBoundTypeVar = Field(0)  # type: ignore

    v: NumberBoundTypeVar = Field(0)  # type: ignore
    r: NumberBoundTypeVar = Field(0)  # type: ignore
    s: NumberBoundTypeVar = Field(0)  # type: ignore

    magic: ClassVar[int] = 0x05

    def to_list(self) -> List[Any]:
        """Return authorization tuple as a list of serializable elements."""
        if isinstance(self.nonce, list):
            # Nonce list for testing purposes only
            return [
                Uint(self.chain_id),
                self.address,
                [Uint(nonce) for nonce in self.nonce],
                Uint(self.v),
                Uint(self.r),
                Uint(self.s),
            ]
        return [
            Uint(self.chain_id),
            self.address,
            Uint(self.nonce),
            Uint(self.v),
            Uint(self.r),
            Uint(self.s),
        ]

    @cached_property
    def signing_bytes(self) -> Bytes:
        """Returns the data to be signed."""
        if isinstance(self.nonce, list):
            # Nonce list for testing purposes only
            return Bytes(
                int.to_bytes(self.magic, length=1, byteorder="big")
                + eth_rlp.encode(
                    [
                        Uint(self.chain_id),
                        self.address,
                        [Uint(nonce) for nonce in self.nonce],
                    ]
                )
            )
        return Bytes(
            int.to_bytes(self.magic, length=1, byteorder="big")
            + eth_rlp.encode(
                [
                    Uint(self.chain_id),
                    self.address,
                    Uint(self.nonce),
                ]
            )
        )

    def signature(self, private_key: Hash) -> Tuple[int, int, int]:
        """Return signature of the authorization tuple."""
        signature_bytes = PrivateKey(secret=private_key).sign_recoverable(
            self.signing_bytes, hasher=keccak256
        )
        return (
            signature_bytes[64],
            int.from_bytes(signature_bytes[0:32], byteorder="big"),
            int.from_bytes(signature_bytes[32:64], byteorder="big"),
        )


class AuthorizationTuple(AuthorizationTupleGeneric[HexNumber]):
    """Authorization tuple for transactions."""

    signer: EOA | None = None
    secret_key: Hash | None = None

    def model_post_init(self, __context: Any) -> None:
        """Automatically signs the authorization tuple if a secret key or sender are provided."""
        super().model_post_init(__context)

        if self.secret_key is not None:
            self.sign(self.secret_key)
        elif self.signer is not None:
            assert self.signer.key is not None, "signer must have a key"
            self.sign(self.signer.key)
        else:
            assert self.v is not None, "v must be set"
            assert self.r is not None, "r must be set"
            assert self.s is not None, "s must be set"

            # Calculate the address from the signature
            try:
                signature_bytes = (
                    int(self.r).to_bytes(32, byteorder="big")
                    + int(self.s).to_bytes(32, byteorder="big")
                    + bytes([self.v])
                )
                public_key = PublicKey.from_signature_and_message(
                    signature_bytes, self.signing_bytes.keccak256(), hasher=None
                )
                self.signer = EOA(
                    address=Address(keccak256(public_key.format(compressed=False)[1:])[32 - 20 :])
                )
            except Exception:
                # Signer remains `None` in this case
                pass

    def sign(self, private_key: Hash) -> None:
        """Signs the authorization tuple with a private key."""
        signature = self.signature(private_key)

        self.v = HexNumber(signature[0])
        self.r = HexNumber(signature[1])
        self.s = HexNumber(signature[2])


class TransactionLog(CamelModel):
    """Transaction log."""

    address: Address
    topics: List[Hash]
    data: Bytes
    block_number: HexNumber
    transaction_hash: Hash
    transaction_index: HexNumber
    block_hash: Hash
    log_index: HexNumber
    removed: bool


class ReceiptDelegation(CamelModel):
    """Transaction receipt set-code delegation."""

    from_address: Address = Field(..., alias="from")
    nonce: HexNumber
    target: Address


class TransactionReceipt(CamelModel):
    """Transaction receipt."""

    transaction_hash: Hash | None = None
    gas_used: HexNumber | None = None
    root: Bytes | None = None
    status: HexNumber | None = None
    cumulative_gas_used: HexNumber | None = None
    logs_bloom: Bloom | None = None
    logs: List[TransactionLog] | None = None
    contract_address: Address | None = None
    effective_gas_price: HexNumber | None = None
    block_hash: Hash | None = None
    transaction_index: HexNumber | None = None
    blob_gas_used: HexNumber | None = None
    blob_gas_price: HexNumber | None = None
    delegations: List[ReceiptDelegation] | None = None


@dataclass
class TransactionDefaults:
    """Default values for transactions."""

    chain_id: int = 1
    gas_price = 10
    max_fee_per_gas = 7
    max_priority_fee_per_gas: int = 0


class TransactionGeneric(BaseModel, Generic[NumberBoundTypeVar]):
    """
    Generic transaction type used as a parent for Transaction and
    FixtureTransaction (blockchain).
    """

    ty: NumberBoundTypeVar = Field(0, alias="type")  # type: ignore
    chain_id: NumberBoundTypeVar = Field(default_factory=lambda: TransactionDefaults.chain_id)  # type: ignore
    nonce: NumberBoundTypeVar = Field(0)  # type: ignore
    gas_price: NumberBoundTypeVar | None = None
    max_priority_fee_per_gas: NumberBoundTypeVar | None = None
    max_fee_per_gas: NumberBoundTypeVar | None = None
    gas_limit: NumberBoundTypeVar = Field(21_000)  # type: ignore
    to: Address | None = None
    value: NumberBoundTypeVar = Field(0)  # type: ignore
    data: Bytes = Field(Bytes(b""))
    access_list: List[AccessList] | None = None
    max_fee_per_blob_gas: NumberBoundTypeVar | None = None
    blob_versioned_hashes: Sequence[Hash] | None = None

    v: NumberBoundTypeVar | None = None
    r: NumberBoundTypeVar | None = None
    s: NumberBoundTypeVar | None = None
    sender: EOA | None = None


class TransactionValidateToAsEmptyString(CamelModel):
    """Handler to validate the `to` field from an empty string."""

    @model_validator(mode="before")
    @classmethod
    def validate_to_as_empty_string(cls, data: Any) -> Any:
        """If the `to` field is an empty string, set the model value to None."""
        if (
            isinstance(data, dict)
            and "to" in data
            and isinstance(data["to"], str)
            and data["to"] == ""
        ):
            data["to"] = None
        return data


class TransactionFixtureConverter(TransactionValidateToAsEmptyString):
    """Handler for serializing and validating the `to` field as an empty string."""

    @model_serializer(mode="wrap", when_used="json-unless-none")
    def serialize_to_as_empty_string(self, serializer):
        """Serialize the `to` field as the empty string if the model value is None."""
        default = serializer(self)
        if default is not None and "to" not in default:
            default["to"] = ""
        return default


class TransactionTransitionToolConverter(TransactionValidateToAsEmptyString):
    """Handler for serializing and validating the `to` field as an empty string."""

    @model_serializer(mode="wrap", when_used="json-unless-none")
    def serialize_to_as_none(self, serializer):
        """
        Serialize the `to` field as `None` if the model value is None.

        This is required as we use `exclude_none=True` when serializing, but the
        t8n tool explicitly requires a value of `None` (respectively null), for
        if the `to` field should be unset (contract creation).
        """
        default = serializer(self)
        if default is not None and "to" not in default:
            default["to"] = None
        return default


class Transaction(TransactionGeneric[HexNumber], TransactionTransitionToolConverter):
    """Generic object that can represent all Ethereum transaction types."""

    gas_limit: HexNumber = Field(HexNumber(21_000), serialization_alias="gas")
    to: Address | None = Field(Address(0xAA))
    data: Bytes = Field(Bytes(b""), alias="input")

    authorization_list: List[AuthorizationTuple] | None = None

    secret_key: Hash | None = None
    error: List[TransactionException] | TransactionException | None = Field(None, exclude=True)

    protected: bool = Field(True, exclude=True)
    rlp_override: Bytes | None = Field(None, exclude=True)

    expected_receipt: TransactionReceipt | None = Field(None, exclude=True)

    wrapped_blob_transaction: bool = Field(False, exclude=True)
    blobs: Sequence[Bytes] | None = Field(None, exclude=True)
    blob_kzg_commitments: Sequence[Bytes] | None = Field(None, exclude=True)
    blob_kzg_proofs: Sequence[Bytes] | None = Field(None, exclude=True)

    model_config = ConfigDict(validate_assignment=True)

    class InvalidFeePaymentError(Exception):
        """Transaction described more than one fee payment type."""

        def __str__(self):
            """Print exception string."""
            return "only one type of fee payment field can be used in a single tx"

    class InvalidSignaturePrivateKeyError(Exception):
        """
        Transaction describes both the signature and private key of
        source account.
        """

        def __str__(self):
            """Print exception string."""
            return "can't define both 'signature' and 'private_key'"

    def model_post_init(self, __context):
        """Ensure transaction has no conflicting properties."""
        super().model_post_init(__context)

        if self.gas_price is not None and (
            self.max_fee_per_gas is not None
            or self.max_priority_fee_per_gas is not None
            or self.max_fee_per_blob_gas is not None
        ):
            raise Transaction.InvalidFeePaymentError()

        if "ty" not in self.model_fields_set:
            # Try to deduce transaction type from included fields
            if self.authorization_list is not None:
                self.ty = 4
            elif self.max_fee_per_blob_gas is not None or self.blob_kzg_commitments is not None:
                self.ty = 3
            elif self.max_fee_per_gas is not None or self.max_priority_fee_per_gas is not None:
                self.ty = 2
            elif self.access_list is not None:
                self.ty = 1
            else:
                self.ty = 0

        if self.v is not None and self.secret_key is not None:
            raise Transaction.InvalidSignaturePrivateKeyError()

        if self.v is None and self.secret_key is None:
            if self.sender is not None:
                self.secret_key = self.sender.key
            else:
                self.secret_key = Hash(TestPrivateKey)
                self.sender = EOA(address=TestAddress, key=self.secret_key, nonce=0)

        # Set default values for fields that are required for certain tx types
        if self.ty <= 1 and self.gas_price is None:
            self.gas_price = TransactionDefaults.gas_price
        if self.ty >= 1 and self.access_list is None:
            self.access_list = []
        if self.ty < 1:
            assert self.access_list is None, "access_list must be None"

        if self.ty >= 2 and self.max_fee_per_gas is None:
            self.max_fee_per_gas = TransactionDefaults.max_fee_per_gas
        if self.ty >= 2 and self.max_priority_fee_per_gas is None:
            self.max_priority_fee_per_gas = TransactionDefaults.max_priority_fee_per_gas
        if self.ty < 2:
            assert self.max_fee_per_gas is None, "max_fee_per_gas must be None"
            assert self.max_priority_fee_per_gas is None, "max_priority_fee_per_gas must be None"

        if self.ty == 3 and self.max_fee_per_blob_gas is None:
            self.max_fee_per_blob_gas = 1
        if self.ty != 3:
            assert self.blob_versioned_hashes is None, "blob_versioned_hashes must be None"
            assert self.max_fee_per_blob_gas is None, "max_fee_per_blob_gas must be None"

        if self.ty == 4 and self.authorization_list is None:
            self.authorization_list = []
        if self.ty != 4:
            assert self.authorization_list is None, "authorization_list must be None"

        if "nonce" not in self.model_fields_set and self.sender is not None:
            self.nonce = HexNumber(self.sender.get_nonce())

    def with_error(
        self, error: List[TransactionException] | TransactionException
    ) -> "Transaction":
        """Create a copy of the transaction with an added error."""
        return self.copy(error=error)

    def with_nonce(self, nonce: int) -> "Transaction":
        """Create a copy of the transaction with a modified nonce."""
        return self.copy(nonce=nonce)

    def with_signature_and_sender(self, *, keep_secret_key: bool = False) -> "Transaction":
        """Return signed version of the transaction using the private key."""
        updated_values: Dict[str, Any] = {}

        if self.v is not None:
            # Transaction already signed
            if self.sender is not None:
                return self

            public_key = PublicKey.from_signature_and_message(
                self.signature_bytes, self.signing_bytes.keccak256(), hasher=None
            )
            updated_values["sender"] = Address(
                keccak256(public_key.format(compressed=False)[1:])[32 - 20 :]
            )
            return self.copy(**updated_values)

        if self.secret_key is None:
            raise ValueError("secret_key must be set to sign a transaction")

        # Get the signing bytes
        signing_hash = self.signing_bytes.keccak256()

        # Sign the bytes
        signature_bytes = PrivateKey(secret=self.secret_key).sign_recoverable(
            signing_hash, hasher=None
        )
        public_key = PublicKey.from_signature_and_message(
            signature_bytes, signing_hash, hasher=None
        )

        sender = keccak256(public_key.format(compressed=False)[1:])[32 - 20 :]
        updated_values["sender"] = Address(sender)

        v, r, s = (
            signature_bytes[64],
            int.from_bytes(signature_bytes[0:32], byteorder="big"),
            int.from_bytes(signature_bytes[32:64], byteorder="big"),
        )
        if self.ty == 0:
            if self.protected:
                v += 35 + (self.chain_id * 2)
            else:  # not protected
                v += 27

        updated_values["v"] = HexNumber(v)
        updated_values["r"] = HexNumber(r)
        updated_values["s"] = HexNumber(s)

        updated_values["secret_key"] = None

        updated_tx: "Transaction" = self.model_copy(update=updated_values)

        # Remove the secret key if requested
        if keep_secret_key:
            updated_tx.secret_key = self.secret_key
        return updated_tx

    @cached_property
    def signing_envelope(self) -> List[Any]:
        """Returns the list of values included in the envelope used for signing."""
        to = self.to if self.to else bytes()
        if self.ty == 4:
            # EIP-7702: https://eips.ethereum.org/EIPS/eip-7702
            if self.max_priority_fee_per_gas is None:
                raise ValueError(f"max_priority_fee_per_gas must be set for type {self.ty} tx")
            if self.max_fee_per_gas is None:
                raise ValueError(f"max_fee_per_gas must be set for type {self.ty} tx")
            if self.access_list is None:
                raise ValueError(f"access_list must be set for type {self.ty} tx")
            if self.authorization_list is None:
                raise ValueError(f"authorization_tuples must be set for type {self.ty} tx")
            return [
                Uint(self.chain_id),
                Uint(self.nonce),
                Uint(self.max_priority_fee_per_gas),
                Uint(self.max_fee_per_gas),
                Uint(self.gas_limit),
                to,
                Uint(self.value),
                self.data,
                [a.to_list() for a in self.access_list],
                [a.to_list() for a in self.authorization_list],
            ]
        elif self.ty == 3:
            # EIP-4844: https://eips.ethereum.org/EIPS/eip-4844
            if self.max_priority_fee_per_gas is None:
                raise ValueError(f"max_priority_fee_per_gas must be set for type {self.ty} tx")
            if self.max_fee_per_gas is None:
                raise ValueError(f"max_fee_per_gas must be set for type {self.ty} tx")
            if self.max_fee_per_blob_gas is None:
                raise ValueError(f"max_fee_per_blob_gas must be set for type {self.ty} tx")
            if self.blob_versioned_hashes is None:
                raise ValueError(f"blob_versioned_hashes must be set for type {self.ty} tx")
            if self.access_list is None:
                raise ValueError(f"access_list must be set for type {self.ty} tx")
            return [
                Uint(self.chain_id),
                Uint(self.nonce),
                Uint(self.max_priority_fee_per_gas),
                Uint(self.max_fee_per_gas),
                Uint(self.gas_limit),
                to,
                Uint(self.value),
                self.data,
                [a.to_list() for a in self.access_list],
                Uint(self.max_fee_per_blob_gas),
                list(self.blob_versioned_hashes),
            ]
        elif self.ty == 2:
            # EIP-1559: https://eips.ethereum.org/EIPS/eip-1559
            if self.max_priority_fee_per_gas is None:
                raise ValueError(f"max_priority_fee_per_gas must be set for type {self.ty} tx")
            if self.max_fee_per_gas is None:
                raise ValueError(f"max_fee_per_gas must be set for type {self.ty} tx")
            if self.access_list is None:
                raise ValueError(f"access_list must be set for type {self.ty} tx")
            return [
                Uint(self.chain_id),
                Uint(self.nonce),
                Uint(self.max_priority_fee_per_gas),
                Uint(self.max_fee_per_gas),
                Uint(self.gas_limit),
                to,
                Uint(self.value),
                self.data,
                [a.to_list() for a in self.access_list],
            ]
        elif self.ty == 1:
            # EIP-2930: https://eips.ethereum.org/EIPS/eip-2930
            if self.gas_price is None:
                raise ValueError(f"gas_price must be set for type {self.ty} tx")
            if self.access_list is None:
                raise ValueError(f"access_list must be set for type {self.ty} tx")

            return [
                Uint(self.chain_id),
                Uint(self.nonce),
                Uint(self.gas_price),
                Uint(self.gas_limit),
                to,
                Uint(self.value),
                self.data,
                [a.to_list() for a in self.access_list],
            ]
        elif self.ty == 0:
            if self.gas_price is None:
                raise ValueError(f"gas_price must be set for type {self.ty} tx")

            if self.protected:
                # EIP-155: https://eips.ethereum.org/EIPS/eip-155
                return [
                    Uint(self.nonce),
                    Uint(self.gas_price),
                    Uint(self.gas_limit),
                    to,
                    Uint(self.value),
                    self.data,
                    Uint(self.chain_id),
                    Uint(0),
                    Uint(0),
                ]
            else:
                return [
                    Uint(self.nonce),
                    Uint(self.gas_price),
                    Uint(self.gas_limit),
                    to,
                    Uint(self.value),
                    self.data,
                ]
        raise NotImplementedError("signing for transaction type {self.ty} not implemented")

    @cached_property
    def payload_body(self) -> List[Any]:
        """Returns the list of values included in the transaction body."""
        if self.v is None or self.r is None or self.s is None:
            raise ValueError("signature must be set before serializing any tx type")

        signing_envelope = self.signing_envelope

        if self.ty == 0 and self.protected:
            # Remove the chain_id and the two zeros from the signing envelope
            signing_envelope = signing_envelope[:-3]
        elif self.ty == 3 and self.wrapped_blob_transaction:
            # EIP-4844: https://eips.ethereum.org/EIPS/eip-4844
            if self.blobs is None:
                raise ValueError(f"blobs must be set for type {self.ty} tx")
            if self.blob_kzg_commitments is None:
                raise ValueError(f"blob_kzg_commitments must be set for type {self.ty} tx")
            if self.blob_kzg_proofs is None:
                raise ValueError(f"blob_kzg_proofs must be set for type {self.ty} tx")
            return [
                signing_envelope + [Uint(self.v), Uint(self.r), Uint(self.s)],
                list(self.blobs),
                list(self.blob_kzg_commitments),
                list(self.blob_kzg_proofs),
            ]

        return signing_envelope + [Uint(self.v), Uint(self.r), Uint(self.s)]

    @cached_property
    def rlp(self) -> Bytes:
        """
        Returns bytes of the serialized representation of the transaction,
        which is almost always RLP encoding.
        """
        if self.rlp_override is not None:
            return self.rlp_override
        if self.ty > 0:
            return Bytes(bytes([self.ty]) + eth_rlp.encode(self.payload_body))
        else:
            return Bytes(eth_rlp.encode(self.payload_body))

    @cached_property
    def hash(self) -> Hash:
        """Returns hash of the transaction."""
        return self.rlp.keccak256()

    @cached_property
    def signing_bytes(self) -> Bytes:
        """Returns the serialized bytes of the transaction used for signing."""
        return Bytes(
            bytes([self.ty]) + eth_rlp.encode(self.signing_envelope)
            if self.ty > 0
            else eth_rlp.encode(self.signing_envelope)
        )

    @cached_property
    def signature_bytes(self) -> Bytes:
        """Returns the serialized bytes of the transaction signature."""
        assert self.v is not None and self.r is not None and self.s is not None
        v = int(self.v)
        if self.ty == 0:
            if self.protected:
                assert self.chain_id is not None
                v -= 35 + (self.chain_id * 2)
            else:
                v -= 27
        return Bytes(
            self.r.to_bytes(32, byteorder="big")
            + self.s.to_bytes(32, byteorder="big")
            + bytes([v])
        )

    @cached_property
    def serializable_list(self) -> Any:
        """Return list of values included in the transaction as a serializable object."""
        return self.rlp if self.ty > 0 else self.payload_body

    @staticmethod
    def list_root(input_txs: List["Transaction"]) -> Hash:
        """Return transactions root of a list of transactions."""
        t = HexaryTrie(db={})
        for i, tx in enumerate(input_txs):
            t.set(eth_rlp.encode(Uint(i)), tx.rlp)
        return Hash(t.root_hash)

    @staticmethod
    def list_blob_versioned_hashes(input_txs: List["Transaction"]) -> List[Hash]:
        """Get list of ordered blob versioned hashes from a list of transactions."""
        return [
            blob_versioned_hash
            for tx in input_txs
            if tx.blob_versioned_hashes is not None
            for blob_versioned_hash in tx.blob_versioned_hashes
        ]

    @cached_property
    def created_contract(self) -> Address:
        """Return address of the contract created by the transaction."""
        if self.to is not None:
            raise ValueError("transaction is not a contract creation")
        if self.sender is None:
            raise ValueError("sender address is None")
        hash_bytes = Bytes(eth_rlp.encode([self.sender, int_to_bytes(self.nonce)])).keccak256()
        return Address(hash_bytes[-20:])


class RequestBase:
    """Base class for requests."""

    type: ClassVar[int]

    @abstractmethod
    def __bytes__(self) -> bytes:
        """Return request's attributes as bytes."""
        ...


class DepositRequest(RequestBase, CamelModel):
    """Deposit Request type."""

    pubkey: BLSPublicKey
    withdrawal_credentials: Hash
    amount: HexNumber
    signature: BLSSignature
    index: HexNumber

    type: ClassVar[int] = 0

    def __bytes__(self) -> bytes:
        """Return deposit's attributes as bytes."""
        return (
            bytes(self.pubkey)
            + bytes(self.withdrawal_credentials)
            + self.amount.to_bytes(8, "little")
            + bytes(self.signature)
            + self.index.to_bytes(8, "little")
        )


class WithdrawalRequest(RequestBase, CamelModel):
    """Withdrawal Request type."""

    source_address: Address = Address(0)
    validator_pubkey: BLSPublicKey
    amount: HexNumber

    type: ClassVar[int] = 1

    def __bytes__(self) -> bytes:
        """Return withdrawal's attributes as bytes."""
        return (
            bytes(self.source_address)
            + bytes(self.validator_pubkey)
            + self.amount.to_bytes(8, "little")
        )


class ConsolidationRequest(RequestBase, CamelModel):
    """Consolidation Request type."""

    source_address: Address = Address(0)
    source_pubkey: BLSPublicKey
    target_pubkey: BLSPublicKey

    type: ClassVar[int] = 2

    def __bytes__(self) -> bytes:
        """Return consolidation's attributes as bytes."""
        return bytes(self.source_address) + bytes(self.source_pubkey) + bytes(self.target_pubkey)


def requests_list_to_bytes(requests_list: List[RequestBase] | Bytes | SupportsBytes) -> Bytes:
    """Convert list of requests to bytes."""
    if not isinstance(requests_list, list):
        return Bytes(requests_list)
    return Bytes(b"".join([bytes(r) for r in requests_list]))


class Requests:
    """Requests for the transition tool."""

    requests_list: List[Bytes]

    def __init__(
        self,
        *requests: RequestBase,
        requests_lists: List[List[RequestBase] | Bytes] | None = None,
    ):
        """Initialize requests object."""
        if requests_lists is not None:
            assert len(requests) == 0, "requests must be empty if list is provided"
            self.requests_list = []
            for requests_list in requests_lists:
                self.requests_list.append(requests_list_to_bytes(requests_list))
            return
        else:
            lists: Dict[int, List[RequestBase]] = defaultdict(list)
            for r in requests:
                lists[r.type].append(r)

            self.requests_list = [
                Bytes(bytes([request_type]) + requests_list_to_bytes(lists[request_type]))
                for request_type in sorted(lists.keys())
            ]

    def __bytes__(self) -> bytes:
        """Return requests hash."""
        s: bytes = b""
        for r in self.requests_list:
            # Append the index of the request type to the request data before hashing
            s = s + r.sha256()
        return Bytes(s).sha256()
