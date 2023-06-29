"""
Useful types for generating Ethereum tests.
"""
import json
from copy import copy, deepcopy
from dataclasses import dataclass, field
from typing import Any, ClassVar, Dict, List, Mapping, Optional, Sequence, Tuple, Type, TypeAlias

from coincurve.keys import PrivateKey, PublicKey
from ethereum import rlp as eth_rlp
from ethereum.base_types import Uint
from ethereum.crypto.hash import keccak256

from ethereum_test_forks import Fork
from evm_transition_tool import TransitionTool

from ..code import Code, code_to_bytes, code_to_hex
from ..reference_spec.reference_spec import ReferenceSpec
from .constants import AddrAA, EmptyOmmersRoot, TestPrivateKey, ZeroAddress
from .conversions import (
    address_or_none,
    address_to_bytes,
    bytes_or_none,
    code_or_none,
    even_padding,
    hash_string,
    hash_to_bytes,
    hash_to_int,
    hex_or_none,
    int_or_none,
    str_or_none,
)


def to_json_or_none(input: Any, default=None) -> Dict[str, Any] | None:
    """
    Converts a value to its json representation or returns a default (None).
    """
    if input is None:
        return default
    return json.loads(json.dumps(input, cls=JSONEncoder))


def to_json(input: Any, remove_none: bool = False) -> Dict[str, Any]:
    """
    Converts a value to its json representation or returns a default (None).
    """
    j = json.loads(json.dumps(input, cls=JSONEncoder))
    if remove_none:
        j = {k: v for (k, v) in j.items() if v is not None}
    return j


MAX_STORAGE_KEY_VALUE = 2**256 - 1
MIN_STORAGE_KEY_VALUE = -(2**255)


# Sentinel classes
class Removable:
    """
    Sentinel class to detect if a parameter should be removed.
    (`None` normally means "do not modify")
    """

    pass


class Auto:
    """
    Class to use as a sentinel value for parameters that should be
    automatically calculated.
    """

    def __repr__(self) -> str:
        """Print the correct test id."""
        return "auto"


# Common Types
class Storage:
    """
    Definition of a storage in pre or post state of a test
    """

    data: Dict[int, int]

    StorageDictType: ClassVar[TypeAlias] = Dict[str | int | bytes, str | int | bytes]
    """
    Dictionary type to be used when defining an input to initialize a storage.
    """

    class InvalidType(Exception):
        """
        Invalid type used when describing test's expected storage key or value.
        """

        key_or_value: Any

        def __init__(self, key_or_value: Any, *args):
            super().__init__(args)
            self.key_or_value = key_or_value

        def __str__(self):
            """Print exception string"""
            return f"invalid type for key/value: {self.key_or_value}"

    class InvalidValue(Exception):
        """
        Invalid value used when describing test's expected storage key or
        value.
        """

        key_or_value: Any

        def __init__(self, key_or_value: Any, *args):
            super().__init__(args)
            self.key_or_value = key_or_value

        def __str__(self):
            """Print exception string"""
            return f"invalid value for key/value: {self.key_or_value}"

    class AmbiguousKeyValue(Exception):
        """
        Key is represented twice in the storage.
        """

        key_1: str | int
        val_1: str | int
        key_2: str | int
        val_2: str | int

        def __init__(
            self,
            key_1: str | int,
            val_1: str | int,
            key_2: str | int,
            val_2: str | int,
            *args,
        ):
            super().__init__(args)
            self.key_1 = key_1
            self.val_1 = val_1
            self.key_2 = key_2
            self.val_2 = val_2

        def __str__(self):
            """Print exception string"""
            return f"""
            Key is represented twice (due to negative numbers) with different
            values in storage:
            s[{self.key_1}] = {self.val_1} and s[{self.key_2}] = {self.val_2}
            """

    class MissingKey(Exception):
        """
        Test expected to find a storage key set but key was missing.
        """

        key: int

        def __init__(self, key: int, *args):
            super().__init__(args)
            self.key = key

        def __str__(self):
            """Print exception string"""
            return "key {0} not found in storage".format(Storage.key_value_to_string(self.key))

    class KeyValueMismatch(Exception):
        """
        Test expected a certain value in a storage key but value found
        was different.
        """

        key: int
        want: int
        got: int

        def __init__(self, key: int, want: int, got: int, *args):
            super().__init__(args)
            self.key = key
            self.want = want
            self.got = got

        def __str__(self):
            """Print exception string"""
            return (
                "incorrect value for key {0}: want {1} (dec:{2})," + " got {3} (dec:{4})"
            ).format(
                Storage.key_value_to_string(self.key),
                Storage.key_value_to_string(self.want),
                self.want,
                Storage.key_value_to_string(self.got),
                self.got,
            )

    @staticmethod
    def parse_key_value(input: str | int | bytes) -> int:
        """
        Parses a key or value to a valid int key for storage.
        """
        if type(input) is str:
            input = int(input, 0)
        elif type(input) is int:
            pass
        elif type(input) is bytes:
            input = int.from_bytes(input, "big")
        else:
            raise Storage.InvalidType(input)

        if input > MAX_STORAGE_KEY_VALUE or input < MIN_STORAGE_KEY_VALUE:
            raise Storage.InvalidValue(input)
        return input

    @staticmethod
    def key_value_to_string(value: int) -> str:
        """
        Transforms a key or value into an hex string.
        """
        hex_str = value.to_bytes(32, "big", signed=(value < 0)).hex().lstrip("0")
        if hex_str == "":
            hex_str = "00"
        if len(hex_str) % 2 != 0:
            hex_str = "0" + hex_str
        return "0x" + hex_str

    def __init__(self, input: StorageDictType):
        """
        Initializes the storage using a given mapping which can have
        keys and values either as string or int.
        Strings must be valid decimal or hexadecimal (starting with 0x)
        numbers.
        """
        self.data = {}
        for key in input:
            value = Storage.parse_key_value(input[key])
            key = Storage.parse_key_value(key)
            self.data[key] = value
        pass

    def __len__(self) -> int:
        """Returns number of elements in the storage"""
        return len(self.data)

    def __contains__(self, key: str | int) -> bool:
        """Checks for an item in the storage"""
        key = Storage.parse_key_value(key)
        return key in self.data

    def __getitem__(self, key: str | int) -> int:
        """Returns an item from the storage"""
        key = Storage.parse_key_value(key)
        if key not in self.data:
            raise KeyError()
        return self.data[key]

    def __setitem__(self, key: str | int, value: str | int):  # noqa: SC200
        """Sets an item in the storage"""
        self.data[Storage.parse_key_value(key)] = Storage.parse_key_value(value)

    def __delitem__(self, key: str | int):
        """Deletes an item from the storage"""
        del self.data[Storage.parse_key_value(key)]

    def to_dict(self) -> Mapping[str, str]:
        """
        Converts the storage into a string dict with appropriate 32-byte
        hex string formatting.
        """
        res: Dict[str, str] = {}
        for key in self.data:
            key_repr = Storage.key_value_to_string(key)
            val_repr = Storage.key_value_to_string(self.data[key])
            if key_repr in res and val_repr != res[key_repr]:
                raise Storage.AmbiguousKeyValue(key_repr, res[key_repr], key, val_repr)
            res[key_repr] = val_repr
        return res

    def contains(self, other: "Storage") -> bool:
        """
        Returns True if self contains all keys with equal value as
        contained by second storage.
        Used for comparison with test expected post state and alloc returned
        by the transition tool.
        """
        for key in other.data:
            if key not in self.data:
                return False
            if self.data[key] != other.data[key]:
                return False
        return True

    def must_contain(self, other: "Storage"):
        """
        Succeeds only if self contains all keys with equal value as
        contained by second storage.
        Used for comparison with test expected post state and alloc returned
        by the transition tool.
        Raises detailed exception when a difference is found.
        """
        for key in other.data:
            if key not in self.data:
                # storage[key]==0 is equal to missing storage
                if other[key] != 0:
                    raise Storage.MissingKey(key)
            elif self.data[key] != other.data[key]:
                raise Storage.KeyValueMismatch(key, self.data[key], other.data[key])

    def must_be_equal(self, other: "Storage"):
        """
        Succeeds only if "self" is equal to "other" storage.
        """
        # Test keys contained in both storage objects
        for key in self.data.keys() & other.data.keys():
            if self.data[key] != other.data[key]:
                raise Storage.KeyValueMismatch(key, self.data[key], other.data[key])

        # Test keys contained in either one of the storage objects
        for key in self.data.keys() ^ other.data.keys():
            if key in self.data:
                if self.data[key] != 0:
                    raise Storage.KeyValueMismatch(key, self.data[key], 0)

            elif other.data[key] != 0:
                raise Storage.KeyValueMismatch(key, 0, other.data[key])


class Account:
    """
    State associated with an address.
    """

    nonce: int | None = None
    """
    The scalar value equal to a) the number of transactions sent by
    an Externally Owned Account, b) the amount of contracts created by a
    contract.
    """
    balance: int | None = None
    """
    The amount of Wei (10<sup>-18</sup> Eth) the account has.
    """
    code: str | bytes | Code | None = None
    """
    Bytecode contained by the account.
    """
    storage: Storage | None = None
    """
    Storage within a contract.
    """

    NONEXISTENT: ClassVar[object] = object()
    """
    Sentinel object used to specify when an account should not exist in the
    state.
    """

    class NonceMismatch(Exception):
        """
        Test expected a certain nonce value for an account but a different
        value was found.
        """

        address: str
        want: int | None
        got: int | None

        def __init__(self, address: str, want: int | None, got: int | None, *args):
            super().__init__(args)
            self.address = address
            self.want = want
            self.got = got

        def __str__(self):
            """Print exception string"""
            return (
                f"unexpected nonce for account {self.address}: "
                + f"want {self.want}, got {self.got}"
            )

    class BalanceMismatch(Exception):
        """
        Test expected a certain balance for an account but a different
        value was found.
        """

        address: str
        want: int | None
        got: int | None

        def __init__(self, address: str, want: int | None, got: int | None, *args):
            super().__init__(args)
            self.address = address
            self.want = want
            self.got = got

        def __str__(self):
            """Print exception string"""
            return (
                f"unexpected balance for account {self.address}: "
                + f"want {self.want}, got {self.got}"
            )

    class CodeMismatch(Exception):
        """
        Test expected a certain bytecode for an account but a different
        one was found.
        """

        address: str
        want: str | None
        got: str | None

        def __init__(self, address: str, want: str | None, got: str | None, *args):
            super().__init__(args)
            self.address = address
            self.want = want
            self.got = got

        def __str__(self):
            """Print exception string"""
            return (
                f"unexpected code for account {self.address}: "
                + f"want {self.want}, got {self.got}"
            )

    def __init__(
        self,
        *,
        nonce: int | None = None,
        balance: int | None = None,
        code: str | bytes | Code | None = None,
        storage: Storage | Dict[str | int | bytes, str | int | bytes] | None = None,
    ) -> None:
        """Init account members"""
        self.nonce = nonce
        self.balance = balance
        self.code = code
        if storage is not None and type(storage) is dict:
            self.storage = Storage(storage)

    def check_alloc(self: "Account", address: str, alloc: dict):
        """
        Checks the returned alloc against an expected account in post state.
        Raises exception on failure.
        """
        if self.nonce is not None:
            actual_nonce = int_or_none(alloc.get("nonce"), 0)
            if self.nonce != actual_nonce:
                raise Account.NonceMismatch(
                    address=address,
                    want=self.nonce,
                    got=actual_nonce,
                )

        if self.balance is not None:
            actual_balance = int_or_none(alloc.get("balance"), 0)
            if self.balance != actual_balance:
                raise Account.BalanceMismatch(
                    address=address,
                    want=self.balance,
                    got=actual_balance,
                )

        if self.code is not None:
            expected_code = code_to_hex(self.code)
            actual_code = str_or_none(alloc.get("code"), "0x")
            if expected_code != actual_code:
                raise Account.CodeMismatch(
                    address=address,
                    want=expected_code,
                    got=actual_code,
                )

        if self.storage is not None:
            expected_storage = (
                self.storage if isinstance(self.storage, Storage) else Storage(self.storage)
            )
            actual_storage = Storage(alloc["storage"]) if "storage" in alloc else Storage({})
            expected_storage.must_be_equal(actual_storage)

    @classmethod
    def with_code(cls: Type, code: bytes | str | Code) -> "Account":
        """
        Create account with provided `code` and nonce of `1`.
        """
        return Account(nonce=1, code=code)


def alloc_to_accounts(got_alloc: Dict[str, Any]) -> Mapping[str, Account]:
    """
    Converts the post state alloc returned from t8n to a mapping of accounts.
    """
    accounts = {}
    for address, value in got_alloc.items():
        account = Account(
            nonce=int_or_none(value.get("nonce", None)),
            balance=int_or_none(value.get("balance", None)),
            code=value.get("code", None),
            storage=value.get("storage", None),
        )
        accounts[address] = account
    return accounts


@dataclass(kw_only=True)
class Withdrawal:
    """
    Structure to represent a single withdrawal of a validator's balance from
    the beacon chain.
    """

    index: int
    validator: int
    address: str
    amount: int

    def to_serializable_list(self) -> List[Any]:
        """
        Returns a list of the withdrawal's attributes in the order they should
        be serialized.
        """
        return [
            Uint(self.index),
            Uint(self.validator),
            bytes.fromhex(self.address[2:]),
            Uint(self.amount),
        ]


DEFAULT_BASE_FEE = 7


@dataclass(kw_only=True)
class Environment:
    """
    Structure used to keep track of the context in which a block
    must be executed.
    """

    coinbase: str | bytes = "0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba"
    gas_limit: int = 100000000000000000
    number: int = 1
    timestamp: int = 1000
    difficulty: Optional[int] = None
    prev_randao: Optional[int] = None
    block_hashes: Dict[int, bytes] = field(default_factory=dict)
    base_fee: Optional[int] = None
    parent_difficulty: Optional[int] = None
    parent_timestamp: Optional[int] = None
    parent_base_fee: Optional[int] = None
    parent_gas_used: Optional[int] = None
    parent_gas_limit: Optional[int] = None
    parent_ommers_hash: Optional[str | bytes] = None
    withdrawals: Optional[List[Withdrawal]] = None
    parent_data_gas_used: Optional[int] = None
    parent_excess_data_gas: Optional[int] = None
    excess_data_gas: Optional[int] = None
    data_gas_used: Optional[int] = None

    @staticmethod
    def from_parent_header(parent: "FixtureHeader") -> "Environment":
        """
        Instantiates a new environment with the provided header as parent.
        """
        return Environment(
            parent_difficulty=parent.difficulty,
            parent_timestamp=parent.timestamp,
            parent_base_fee=parent.base_fee,
            parent_data_gas_used=parent.data_gas_used,
            parent_excess_data_gas=parent.excess_data_gas,
            parent_gas_used=parent.gas_used,
            parent_gas_limit=parent.gas_limit,
            parent_ommers_hash=parent.ommers_hash,
            block_hashes={
                parent.number: parent.hash if parent.hash is not None else bytes([0] * 32)
            },
        )

    def parent_hash(self) -> bytes:
        """
        Obtjains the latest hash according to the highest block number in
        `block_hashes`.
        """
        if len(self.block_hashes) == 0:
            return bytes([0] * 32)

        last_index = max(self.block_hashes.keys())
        return self.block_hashes[last_index]

    def apply_new_parent(self, new_parent: "FixtureHeader") -> "Environment":
        """
        Applies a header as parent to a copy of this environment.
        """
        env = copy(self)
        env.parent_difficulty = new_parent.difficulty
        env.parent_timestamp = new_parent.timestamp
        env.parent_base_fee = new_parent.base_fee
        env.parent_data_gas_used = new_parent.data_gas_used
        env.parent_excess_data_gas = new_parent.excess_data_gas
        env.parent_gas_used = new_parent.gas_used
        env.parent_gas_limit = new_parent.gas_limit
        env.parent_ommers_hash = new_parent.ommers_hash
        env.block_hashes[new_parent.number] = (
            new_parent.hash if new_parent.hash is not None else bytes([0] * 32)
        )
        return env

    def set_fork_requirements(self, fork: Fork) -> "Environment":
        """
        Fills the required fields in an environment depending on the fork.
        """
        res = copy(self)

        if (
            fork.header_prev_randao_required(self.number, self.timestamp)
            and res.prev_randao is None
        ):
            res.prev_randao = 0

        if (
            fork.header_withdrawals_required(self.number, self.timestamp)
            and res.withdrawals is None
        ):
            res.withdrawals = []

        if (
            fork.header_base_fee_required(self.number, self.timestamp)
            and res.base_fee is None
            and res.parent_base_fee is None
        ):
            res.base_fee = DEFAULT_BASE_FEE

        if fork.header_zero_difficulty_required(self.number, self.timestamp):
            res.difficulty = 0

        if (
            fork.header_excess_data_gas_required(self.number, self.timestamp)
            and res.excess_data_gas is None
            and res.parent_excess_data_gas is None
        ):
            res.excess_data_gas = 0

        if (
            fork.header_data_gas_used_required(self.number, self.timestamp)
            and res.data_gas_used is None
            and res.parent_data_gas_used is None
        ):
            res.data_gas_used = 0

        return res


class AccessList:
    """
    Access List for transactions.
    """

    address: bytes
    storage_keys: List[bytes]

    def __init__(
        self,
        *,
        address: str | int | bytes,
        storage_keys: List[str | int | bytes],
    ) -> None:
        """
        Ensures the access list has the correct byte length for each field.
        """
        self.address = address_to_bytes(address)
        self.storage_keys = [hash_to_bytes(key) for key in storage_keys]

    def to_list(self) -> List[bytes | List[bytes]]:
        """
        Returns the access list as a list of serializable elements.
        """
        return [self.address, self.storage_keys]


@dataclass(kw_only=True)
class Transaction:
    """
    Generic object that can represent all Ethereum transaction types.
    """

    ty: Optional[int] = None
    """
    Transaction type value.
    """
    chain_id: int = 1
    nonce: int = 0
    to: Optional[str | int] = AddrAA
    value: int = 0
    data: bytes | str | Code = bytes()
    gas_limit: int = 21000
    access_list: Optional[List[AccessList]] = None

    gas_price: Optional[int] = None
    max_fee_per_gas: Optional[int] = None
    max_priority_fee_per_gas: Optional[int] = None

    max_fee_per_data_gas: Optional[int] = None
    blob_versioned_hashes: Optional[Sequence[str | bytes]] = None

    wrapped_blob_transaction: bool = False
    blobs: Optional[Sequence[bytes]] = None
    blob_kzg_commitments: Optional[Sequence[bytes]] = None
    blob_kzg_proofs: Optional[Sequence[bytes]] = None

    signature: Optional[Tuple[int, int, int]] = None
    secret_key: Optional[str] = None
    sender: Optional[str | bytes] = None
    protected: bool = True
    error: Optional[str] = None

    class InvalidFeePayment(Exception):
        """
        Transaction described more than one fee payment type.
        """

        def __str__(self):
            """Print exception string"""
            return "only one type of fee payment field can be used in a single tx"

    class InvalidSignaturePrivateKey(Exception):
        """
        Transaction describes both the signature and private key of
        source account.
        """

        def __str__(self):
            """Print exception string"""
            return "can't define both 'signature' and 'private_key'"

    def __post_init__(self) -> None:
        """
        Ensures the transaction has no conflicting properties.
        """
        if (
            self.gas_price is not None
            and self.max_fee_per_gas is not None
            and self.max_priority_fee_per_gas is not None
        ):
            raise Transaction.InvalidFeePayment()

        if (
            self.gas_price is None
            and self.max_fee_per_gas is None
            and self.max_priority_fee_per_gas is None
        ):
            self.gas_price = 10

        if self.signature is not None and self.secret_key is not None:
            raise Transaction.InvalidSignaturePrivateKey()

        if self.signature is None and self.secret_key is None:
            self.secret_key = TestPrivateKey

        if self.ty is None:
            # Try to deduce transaction type from included fields
            if self.max_fee_per_data_gas is not None:
                self.ty = 3
            elif self.max_fee_per_gas is not None:
                self.ty = 2
            elif self.access_list is not None:
                self.ty = 1
            else:
                self.ty = 0

    def with_error(self, error: str) -> "Transaction":
        """
        Create a copy of the transaction with an added error.
        """
        tx = copy(self)
        tx.error = error
        return tx

    def with_nonce(self, nonce: int) -> "Transaction":
        """
        Create a copy of the transaction with a modified nonce.
        """
        tx = copy(self)
        tx.nonce = nonce
        return tx

    def with_fields(self, **kwargs) -> "Transaction":
        """
        Create a deepcopy of the transaction with modified fields.
        """
        tx = deepcopy(self)
        for key, value in kwargs.items():
            if hasattr(tx, key):
                setattr(tx, key, value)
            else:
                raise ValueError(f"Invalid field '{key}' for Transaction")
        return tx

    def payload_body(self) -> List[Any]:
        """
        Returns the list of values included in the transaction body.
        """
        if self.signature is None:
            raise ValueError("signature must be set before serializing any tx type")

        if self.gas_limit is None:
            raise ValueError("gas_limit must be set for all tx types")
        to = address_to_bytes(self.to)

        if self.ty == 3:
            # EIP-4844: https://eips.ethereum.org/EIPS/eip-4844
            if self.max_priority_fee_per_gas is None:
                raise ValueError("max_priority_fee_per_gas must be set for type 3 tx")
            if self.max_fee_per_gas is None:
                raise ValueError("max_fee_per_gas must be set for type 3 tx")
            if self.max_fee_per_data_gas is None:
                raise ValueError("max_fee_per_data_gas must be set for type 3 tx")
            if self.blob_versioned_hashes is None:
                raise ValueError("blob_versioned_hashes must be set for type 3 tx")

            if self.wrapped_blob_transaction:
                if self.blobs is None:
                    raise ValueError("blobs must be set for network version of type 3 tx")
                if self.blob_kzg_commitments is None:
                    raise ValueError(
                        "blob_kzg_commitments must be set for network version of type 3 tx"
                    )
                if self.blob_kzg_proofs is None:
                    raise ValueError(
                        "blob_kzg_proofs must be set for network version of type 3 tx"
                    )

                return [
                    [
                        Uint(self.chain_id),
                        Uint(self.nonce),
                        Uint(self.max_priority_fee_per_gas),
                        Uint(self.max_fee_per_gas),
                        Uint(self.gas_limit),
                        to,
                        Uint(self.value),
                        code_to_bytes(self.data),
                        [a.to_list() for a in self.access_list]
                        if self.access_list is not None
                        else [],
                        Uint(self.max_fee_per_data_gas),
                        [hash_to_bytes(h) for h in self.blob_versioned_hashes],
                        Uint(self.signature[0]),
                        Uint(self.signature[1]),
                        Uint(self.signature[2]),
                    ],
                    self.blobs,
                    self.blob_kzg_commitments,
                    self.blob_kzg_proofs,
                ]
            else:
                return [
                    Uint(self.chain_id),
                    Uint(self.nonce),
                    Uint(self.max_priority_fee_per_gas),
                    Uint(self.max_fee_per_gas),
                    Uint(self.gas_limit),
                    to,
                    Uint(self.value),
                    code_to_bytes(self.data),
                    [a.to_list() for a in self.access_list]
                    if self.access_list is not None
                    else [],
                    Uint(self.max_fee_per_data_gas),
                    [hash_to_bytes(h) for h in self.blob_versioned_hashes],
                    Uint(self.signature[0]),
                    Uint(self.signature[1]),
                    Uint(self.signature[2]),
                ]
        elif self.ty == 2:
            # EIP-1559: https://eips.ethereum.org/EIPS/eip-1559
            if self.max_priority_fee_per_gas is None:
                raise ValueError("max_priority_fee_per_gas must be set for type 3 tx")
            if self.max_fee_per_gas is None:
                raise ValueError("max_fee_per_gas must be set for type 3 tx")
            return [
                Uint(self.chain_id),
                Uint(self.nonce),
                Uint(self.max_priority_fee_per_gas),
                Uint(self.max_fee_per_gas),
                Uint(self.gas_limit),
                to,
                Uint(self.value),
                code_to_bytes(self.data),
                [a.to_list() for a in self.access_list] if self.access_list is not None else [],
                Uint(self.signature[0]),
                Uint(self.signature[1]),
                Uint(self.signature[2]),
            ]
        elif self.ty == 1:
            # EIP-2930: https://eips.ethereum.org/EIPS/eip-2930
            if self.gas_price is None:
                raise ValueError("gas_price must be set for type 1 tx")

            return [
                Uint(self.chain_id),
                Uint(self.nonce),
                Uint(self.gas_price),
                Uint(self.gas_limit),
                to,
                Uint(self.value),
                code_to_bytes(self.data),
                [a.to_list() for a in self.access_list] if self.access_list is not None else [],
                Uint(self.signature[0]),
                Uint(self.signature[1]),
                Uint(self.signature[2]),
            ]
        elif self.ty == 0:
            if self.gas_price is None:
                raise ValueError("gas_price must be set for type 0 tx")
            # EIP-155: https://eips.ethereum.org/EIPS/eip-155
            return [
                Uint(self.nonce),
                Uint(self.gas_price),
                Uint(self.gas_limit),
                to,
                Uint(self.value),
                code_to_bytes(self.data),
                Uint(self.signature[0]),
                Uint(self.signature[1]),
                Uint(self.signature[2]),
            ]

        raise NotImplementedError(f"serialized_bytes not implemented for tx type {self.ty}")

    def serialized_bytes(self) -> bytes:
        """
        Returns bytes of the serialized representation of the transaction,
        which is almost always RLP encoding.
        """
        if self.ty is None:
            raise ValueError("ty must be set for all tx types")

        if self.ty > 0:
            return bytes([self.ty]) + eth_rlp.encode(self.payload_body())
        else:
            return eth_rlp.encode(self.payload_body())

    def signing_envelope(self) -> List[Any]:
        """
        Returns the list of values included in the envelope used for signing.
        """
        if self.gas_limit is None:
            raise ValueError("gas_limit must be set for all tx types")
        to = address_to_bytes(self.to)

        if self.ty == 3:
            # EIP-4844: https://eips.ethereum.org/EIPS/eip-4844
            if self.max_priority_fee_per_gas is None:
                raise ValueError("max_priority_fee_per_gas must be set for type 3 tx")
            if self.max_fee_per_gas is None:
                raise ValueError("max_fee_per_gas must be set for type 3 tx")
            if self.max_fee_per_data_gas is None:
                raise ValueError("max_fee_per_data_gas must be set for type 3 tx")
            if self.blob_versioned_hashes is None:
                raise ValueError("blob_versioned_hashes must be set for type 3 tx")
            return [
                Uint(self.chain_id),
                Uint(self.nonce),
                Uint(self.max_priority_fee_per_gas),
                Uint(self.max_fee_per_gas),
                Uint(self.gas_limit),
                to,
                Uint(self.value),
                code_to_bytes(self.data),
                [a.to_list() for a in self.access_list] if self.access_list is not None else [],
                Uint(self.max_fee_per_data_gas),
                [hash_to_bytes(h) for h in self.blob_versioned_hashes],
            ]
        elif self.ty == 2:
            # EIP-1559: https://eips.ethereum.org/EIPS/eip-1559
            if self.max_priority_fee_per_gas is None:
                raise ValueError("max_priority_fee_per_gas must be set for type 3 tx")
            if self.max_fee_per_gas is None:
                raise ValueError("max_fee_per_gas must be set for type 3 tx")
            return [
                Uint(self.chain_id),
                Uint(self.nonce),
                Uint(self.max_priority_fee_per_gas),
                Uint(self.max_fee_per_gas),
                Uint(self.gas_limit),
                to,
                Uint(self.value),
                code_to_bytes(self.data),
                [a.to_list() for a in self.access_list] if self.access_list is not None else [],
            ]
        elif self.ty == 1:
            # EIP-2930: https://eips.ethereum.org/EIPS/eip-2930
            if self.gas_price is None:
                raise ValueError("gas_price must be set for type 1 tx")

            return [
                Uint(self.chain_id),
                Uint(self.nonce),
                Uint(self.gas_price),
                Uint(self.gas_limit),
                to,
                Uint(self.value),
                code_to_bytes(self.data),
                [a.to_list() for a in self.access_list] if self.access_list is not None else [],
            ]
        elif self.ty == 0:
            if self.gas_price is None:
                raise ValueError("gas_price must be set for type 0 tx")

            if self.protected:
                # EIP-155: https://eips.ethereum.org/EIPS/eip-155
                return [
                    Uint(self.nonce),
                    Uint(self.gas_price),
                    Uint(self.gas_limit),
                    to,
                    Uint(self.value),
                    code_to_bytes(self.data),
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
                    code_to_bytes(self.data),
                ]
        raise NotImplementedError("sigining for transaction type {self.ty} not implemented")

    def signing_bytes(self) -> bytes:
        """
        Returns the serialized bytes of the transaction used for signing.
        """
        if self.ty is None:
            raise ValueError("ty must be set for all tx types")

        if self.ty > 0:
            return bytes([self.ty]) + eth_rlp.encode(self.signing_envelope())
        else:
            return eth_rlp.encode(self.signing_envelope())

    def with_signature_and_sender(self) -> "Transaction":
        """
        Returns a signed version of the transaction using the private key.
        """
        tx = copy(self)

        if tx.signature is not None:
            # Transaction already signed
            if tx.sender is None:
                # TODO: We need to recover the sender from the signature
                raise NotImplementedError("recovering sender from signature not implemented")
            return tx

        if tx.secret_key is None:
            raise ValueError("secret_key must be set to sign a transaction")

        # Get the signing bytes
        signing_hash = keccak256(tx.signing_bytes())

        # Sign the bytes
        private_key = PrivateKey.from_int(hash_to_int(tx.secret_key))
        signature_bytes = private_key.sign_recoverable(signing_hash, hasher=None)
        public_key = PublicKey.from_signature_and_message(
            signature_bytes, signing_hash, hasher=None
        )
        tx.sender = keccak256(public_key.format(compressed=False)[1:])[32 - 20 :]

        v, r, s = (
            signature_bytes[64],
            int.from_bytes(signature_bytes[0:32], byteorder="big"),
            int.from_bytes(signature_bytes[32:64], byteorder="big"),
        )
        if tx.ty == 0:
            if tx.protected:
                v += 35 + (tx.chain_id * 2)
            else:  # not protected
                v += 27

        tx.signature = (v, r, s)

        # Remove the secret key because otherwise we might attempt to sign again (?)
        tx.secret_key = None
        return tx


def transaction_list_to_serializable_list(input_txs: List[Transaction] | None) -> List[Any]:
    """
    Returns the transaction list as a list of serializable objects.
    """
    if input_txs is None:
        return []

    txs: List[Any] = []
    for tx in input_txs:
        if tx.ty is None:
            raise ValueError("ty must be set for all tx types")

        if tx.ty > 0:
            txs.append(tx.serialized_bytes())
        else:
            txs.append(tx.payload_body())
    return txs


def serialize_transactions(input_txs: List[Transaction] | None) -> bytes:
    """
    Serialize a list of transactions into a single byte string, usually RLP encoded.
    """
    return eth_rlp.encode(transaction_list_to_serializable_list(input_txs))


@dataclass
class FixtureTransaction:
    """
    Representation of an Ethereum transaction within a test Fixture.
    """

    tx: Transaction


@dataclass(kw_only=True)
class Header:
    """
    Header type used to describe block header properties in test specs.
    """

    parent_hash: Optional[bytes] = None
    ommers_hash: Optional[bytes] = None
    coinbase: Optional[bytes | str] = None
    state_root: Optional[bytes] = None
    transactions_root: Optional[bytes] = None
    receipt_root: Optional[bytes] = None
    bloom: Optional[bytes] = None
    difficulty: Optional[int] = None
    number: Optional[int] = None
    gas_limit: Optional[int] = None
    gas_used: Optional[int] = None
    timestamp: Optional[int] = None
    extra_data: Optional[bytes] = None
    mix_digest: Optional[bytes] = None
    nonce: Optional[bytes] = None
    base_fee: Optional[int | Removable] = None
    withdrawals_root: Optional[bytes | Removable] = None
    data_gas_used: Optional[int | Removable] = None
    excess_data_gas: Optional[int | Removable] = None
    hash: Optional[bytes] = None

    REMOVE_FIELD: ClassVar[Removable] = Removable()
    """
    Sentinel object used to specify that a header field should be removed.
    """


@dataclass(kw_only=True)
class FixtureHeader:
    """
    Representation of an Ethereum header within a test Fixture.
    """

    parent_hash: bytes
    ommers_hash: bytes
    coinbase: bytes
    state_root: bytes
    transactions_root: bytes
    receipt_root: bytes
    bloom: bytes
    difficulty: int
    number: int
    gas_limit: int
    gas_used: int
    timestamp: int
    extra_data: bytes
    mix_digest: bytes
    nonce: bytes
    base_fee: Optional[int] = None
    withdrawals_root: Optional[bytes] = None
    data_gas_used: Optional[int] = None
    excess_data_gas: Optional[int] = None
    hash: Optional[bytes] = None

    @staticmethod
    def from_dict(source: Dict[str, Any]) -> "FixtureHeader":
        """
        Creates a FixedHeader object from a Dict.
        """
        ommers_hash = bytes_or_none(source.get("sha3Uncles"))
        if ommers_hash is None:
            ommers_hash = EmptyOmmersRoot

        parent_hash = bytes_or_none(source.get("parentHash"))
        assert parent_hash is not None, "parentHash is required"

        state_root = bytes_or_none(source["stateRoot"])
        assert state_root is not None, "stateRoot is required"

        transactions_root = bytes_or_none(source["transactionsRoot"])
        assert transactions_root is not None, "transactionsRoot is required"

        receipt_root = bytes_or_none(source["receiptsRoot"])
        assert receipt_root is not None, "receiptsRoot is required"

        bloom = bytes_or_none(source["logsBloom"])
        assert bloom is not None, "logsBloom is required"

        extra_data = bytes_or_none(source["extraData"])
        assert extra_data is not None, "extraData is required"

        mix_digest = bytes_or_none(source["mixHash"])
        assert mix_digest is not None, "mixHash is required"

        nonce = bytes_or_none(source["nonce"])
        assert nonce is not None, "nonce is required"

        return FixtureHeader(
            parent_hash=parent_hash,
            ommers_hash=ommers_hash,
            coinbase=address_to_bytes(source["miner"]),
            state_root=state_root,
            transactions_root=transactions_root,
            receipt_root=receipt_root,
            bloom=bloom,
            difficulty=int(source["difficulty"], 0),
            number=int(source["number"], 0),
            gas_limit=int(source["gasLimit"], 0),
            gas_used=int(source["gasUsed"], 0),
            timestamp=int(source["timestamp"], 0),
            extra_data=extra_data,
            mix_digest=mix_digest,
            nonce=nonce,
            base_fee=int_or_none(source.get("baseFeePerGas")),
            withdrawals_root=bytes_or_none(source.get("withdrawalsRoot")),
            data_gas_used=int_or_none(source.get("dataGasUsed")),
            excess_data_gas=int_or_none(source.get("excessDataGas")),
            hash=bytes_or_none(source.get("hash")),
        )

    def join(self, modifier: Header) -> "FixtureHeader":
        """
        Produces a fixture header copy with the set values from the modifier.
        """
        new_fixture_header = copy(self)
        for header_field in self.__dataclass_fields__:
            value = getattr(modifier, header_field)
            if value is not None:
                if value is Header.REMOVE_FIELD:
                    setattr(new_fixture_header, header_field, None)
                else:
                    if header_field == "coinbase":
                        value = bytes_or_none(value)
                    setattr(new_fixture_header, header_field, value)
        return new_fixture_header

    def build(
        self,
        *,
        txs: List[Transaction],
        ommers: List[Header],
        withdrawals: List[Withdrawal] | None,
    ) -> Tuple[bytes, bytes]:
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
            Uint(self.difficulty),
            Uint(self.number),
            Uint(self.gas_limit),
            Uint(self.gas_used),
            Uint(self.timestamp),
            self.extra_data,
            self.mix_digest,
            self.nonce,
        ]
        if self.base_fee is not None:
            header.append(Uint(self.base_fee))
        if self.withdrawals_root is not None:
            header.append(self.withdrawals_root)
        if self.data_gas_used is not None:
            header.append(Uint(self.data_gas_used))
        if self.excess_data_gas is not None:
            header.append(Uint(self.excess_data_gas))

        block = [
            header,
            transaction_list_to_serializable_list(txs),
            ommers,  # TODO: This is incorrect, and we probably need to serialize the ommers
        ]

        if withdrawals is not None:
            block.append([w.to_serializable_list() for w in withdrawals])

        serialized_bytes = eth_rlp.encode(block)

        return serialized_bytes, keccak256(eth_rlp.encode(header))


@dataclass(kw_only=True)
class Block(Header):
    """
    Block type used to describe block properties in test specs
    """

    rlp: Optional[bytes] = None
    """
    If set, blockchain test will skip generating the block and will pass this value directly to
    the Fixture.

    Only meant to be used to simulate blocks with bad formats, and therefore
    requires the block to produce an exception.
    """
    rlp_modifier: Optional[Header] = None
    """
    An RLP modifying header which values would be used to override the ones
    returned by the  `evm_transition_tool`.
    """
    exception: Optional[str] = None
    """
    If set, the block is expected to be rejected by the client.
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
        new_env.gas_limit = (
            self.gas_limit if self.gas_limit is not None else environment_default.gas_limit
        )
        if not isinstance(self.base_fee, Removable):
            new_env.base_fee = self.base_fee
        new_env.withdrawals = self.withdrawals
        if not isinstance(self.excess_data_gas, Removable):
            new_env.excess_data_gas = self.excess_data_gas
        if not isinstance(self.data_gas_used, Removable):
            new_env.data_gas_used = self.data_gas_used
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
                new_env.number = max(new_env.block_hashes.keys()) + 1

        if self.timestamp is not None:
            new_env.timestamp = self.timestamp
        else:
            assert new_env.parent_timestamp is not None
            new_env.timestamp = new_env.parent_timestamp + 12

        return new_env

    def copy_with_rlp(self, rlp: bytes) -> "Block":
        """
        Creates a copy of the block and adds the specified RLP.
        """
        new_block = deepcopy(self)
        new_block.rlp = rlp
        return new_block


@dataclass(kw_only=True)
class FixtureExecutionPayload:
    """
    Representation of the execution payload of a block within a test fixture.
    """

    header: FixtureHeader
    transactions: Optional[List[Transaction]]
    withdrawals: Optional[List[Withdrawal]]


@dataclass(kw_only=True)
class FixtureBlock:
    """
    Representation of an Ethereum block within a test Fixture.
    """

    rlp: bytes
    block_header: Optional[FixtureHeader] = None
    execution_payload: Optional[FixtureExecutionPayload] = None
    expected_exception: Optional[str] = None
    block_number: Optional[int] = None
    txs: Optional[List[Transaction]] = None
    ommers: Optional[List[Header]] = None
    withdrawals: Optional[List[Withdrawal]] = None


@dataclass(kw_only=True)
class Fixture:
    """
    Cross-client compatible Ethereum test fixture.
    """

    blocks: List[FixtureBlock]
    genesis: FixtureHeader
    genesis_rlp: bytes
    head: bytes
    fork: str
    pre_state: Mapping[str, Account]
    post_state: Optional[Mapping[str, Account]]
    seal_engine: str
    info: Dict[str, str] = field(default_factory=dict)
    name: str = ""

    _json: Dict[str, Any] | None = None

    def __post_init__(self):
        """
        Post init hook to convert to JSON after instantiation.
        """
        self._json = to_json(self)

    def fill_info(
        self,
        t8n: TransitionTool,
        ref_spec: ReferenceSpec | None,
    ):
        """
        Fill the info field for this fixture
        """
        self.info["filling-transition-tool"] = t8n.version()
        if ref_spec is not None:
            ref_spec.write_info(self.info)


JSONEncoderSupportedType: TypeAlias = (
    AccessList
    | Account
    | Environment
    | Fixture
    | FixtureBlock
    | FixtureHeader
    | FixtureTransaction
    | Storage
    | Transaction
    | Withdrawal
)


class JSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder for `ethereum_test` types.
    """

    def default(self, obj: JSONEncoderSupportedType) -> Any:
        """
        Enocdes types defined in this module using basic python facilities.
        """
        if isinstance(obj, Storage):
            return obj.to_dict()
        elif isinstance(obj, Account):
            account = {
                "nonce": hex_or_none(obj.nonce, hex(0)),
                "balance": hex_or_none(obj.balance, hex(0)),
                "code": code_or_none(obj.code, "0x"),
                "storage": to_json_or_none(obj.storage, {}),
            }
            return even_padding(account, excluded=["storage"])
        elif isinstance(obj, AccessList):
            access_list: Dict[str, Any] = {
                "address": address_or_none(obj.address, "0x" + ZeroAddress.hex())
            }
            if obj.storage_keys is not None:
                access_list["storageKeys"] = [hex_or_none(k) for k in obj.storage_keys]
            return access_list
        elif isinstance(obj, Transaction):
            assert obj.ty is not None, "Transaction type must be set"
            tx: Dict[str, Any] = {
                "type": hex(obj.ty),
                "chainId": hex(obj.chain_id),
                "nonce": hex(obj.nonce),
                "gasPrice": hex_or_none(obj.gas_price),
                "maxPriorityFeePerGas": hex_or_none(obj.max_priority_fee_per_gas),
                "maxFeePerGas": hex_or_none(obj.max_fee_per_gas),
                "gas": hex(obj.gas_limit),
                "value": hex(obj.value),
                "input": code_to_hex(obj.data),
                "to": address_or_none(obj.to),
                "accessList": obj.access_list,
                "protected": obj.protected,
                "secretKey": obj.secret_key,
                "maxFeePerDataGas": hex_or_none(obj.max_fee_per_data_gas),
                "sender": address_or_none(obj.sender),
            }

            if obj.blob_versioned_hashes is not None:
                tx["blobVersionedHashes"] = [hash_string(h) for h in obj.blob_versioned_hashes]

            if obj.secret_key is None:
                assert obj.signature is not None
                assert len(obj.signature) == 3
                tx["v"] = hex(obj.signature[0])
                tx["r"] = hex(obj.signature[1])
                tx["s"] = hex(obj.signature[2])
            else:
                tx["v"] = ""
                tx["r"] = ""
                tx["s"] = ""

            return {k: v for (k, v) in tx.items() if v is not None}
        elif isinstance(obj, Withdrawal):
            withdrawal = {
                "index": hex(obj.index),
                "validatorIndex": hex(obj.validator),
                "address": obj.address,
                "amount": hex(obj.amount),
            }
            return withdrawal
        elif isinstance(obj, Environment):
            env: Dict[str, Any] = {
                "currentCoinbase": address_or_none(obj.coinbase, "0x" + ZeroAddress.hex()),
                "currentGasLimit": str_or_none(obj.gas_limit),
                "currentNumber": str_or_none(obj.number),
                "currentTimestamp": str_or_none(obj.timestamp),
                "currentRandom": str_or_none(obj.prev_randao),
                "currentDifficulty": str_or_none(obj.difficulty),
                "parentDifficulty": str_or_none(obj.parent_difficulty),
                "parentBaseFee": str_or_none(obj.parent_base_fee),
                "parentGasUsed": str_or_none(obj.parent_gas_used),
                "parentGasLimit": str_or_none(obj.parent_gas_limit),
                "parentTimestamp": str_or_none(obj.parent_timestamp),
                "blockHashes": {str(k): hex_or_none(v) for (k, v) in obj.block_hashes.items()},
                "ommers": [],
                "withdrawals": to_json_or_none(obj.withdrawals),
                "parentUncleHash": hash_string(obj.parent_ommers_hash),
                "currentBaseFee": str_or_none(obj.base_fee),
                "parentDataGasUsed": str_or_none(obj.parent_data_gas_used),
                "parentExcessDataGas": str_or_none(obj.parent_excess_data_gas),
                "currentExcessDataGas": str_or_none(obj.excess_data_gas),
                "currentDataGasUsed": str_or_none(obj.data_gas_used),
            }

            return {k: v for (k, v) in env.items() if v is not None}
        elif isinstance(obj, FixtureHeader):
            header = {
                "parentHash": hex_or_none(obj.parent_hash),
                "uncleHash": hex_or_none(obj.ommers_hash),
                "coinbase": hex_or_none(obj.coinbase),
                "stateRoot": hex_or_none(obj.state_root),
                "transactionsTrie": hex_or_none(obj.transactions_root),
                "receiptTrie": hex_or_none(obj.receipt_root),
                "bloom": hex_or_none(obj.bloom),
                "difficulty": hex(obj.difficulty),
                "number": hex(obj.number),
                "gasLimit": hex(obj.gas_limit),
                "gasUsed": hex(obj.gas_used),
                "timestamp": hex(obj.timestamp),
                "extraData": hex_or_none(obj.extra_data),
                "mixHash": hex_or_none(obj.mix_digest),
                "nonce": hex_or_none(obj.nonce),
            }
            if obj.base_fee is not None:
                header["baseFeePerGas"] = hex(obj.base_fee)
            if obj.hash is not None:
                header["hash"] = "0x" + obj.hash.hex()
            if obj.withdrawals_root is not None:
                header["withdrawalsRoot"] = hex_or_none(obj.withdrawals_root)
            if obj.data_gas_used is not None:
                header["dataGasUsed"] = hex(obj.data_gas_used)
            if obj.excess_data_gas is not None:
                header["excessDataGas"] = hex(obj.excess_data_gas)
            return even_padding(
                header,
                excluded=[
                    "parentHash",
                    "uncleHash",
                    "stateRoot",
                    "coinbase",
                    "transactionsTrie",
                    "receiptTrie",
                    "bloom",
                    "nonce",
                    "mixHash",
                    "hash",
                    "withdrawalsRoot",
                    "extraData",
                ],
            )
        elif isinstance(obj, FixtureTransaction):
            json_tx = to_json(obj.tx)
            if json_tx["v"] == "":
                del json_tx["v"]
                del json_tx["r"]
                del json_tx["s"]
            if "input" in json_tx:
                json_tx["data"] = json_tx["input"]
                del json_tx["input"]
            if "gas" in json_tx:
                json_tx["gasLimit"] = json_tx["gas"]
                del json_tx["gas"]
            if "to" not in json_tx:
                json_tx["to"] = ""
            return even_padding(
                json_tx,
                excluded=["data", "to", "accessList"],
            )
        elif isinstance(obj, FixtureBlock):
            b: Dict[str, Any] = {"rlp": hex_or_none(obj.rlp)}
            if obj.block_header is not None:
                b["blockHeader"] = json.loads(json.dumps(obj.block_header, cls=JSONEncoder))
            if obj.expected_exception is not None:
                b["expectException"] = obj.expected_exception
            if obj.block_number is not None:
                b["blocknumber"] = str(obj.block_number)
            if obj.txs is not None:
                b["transactions"] = [FixtureTransaction(tx=tx) for tx in obj.txs]
            if obj.ommers is not None:
                b["uncleHeaders"] = obj.ommers
            if obj.withdrawals is not None:
                b["withdrawals"] = [
                    even_padding(to_json(wd), excluded=["address"]) for wd in obj.withdrawals
                ]
            return b
        elif isinstance(obj, FixtureExecutionPayload):
            payload: Dict[str, Any] = {
                "parentHash": hex_or_none(obj.header.parent_hash),
                "feeRecipient": hex_or_none(obj.header.coinbase),
                "stateRoot": hex_or_none(obj.header.state_root),
                "receiptsRoot": hex_or_none(obj.header.receipt_root),
                "logsBloom": hex_or_none(obj.header.bloom),
                "prevRandao": hex_or_none(obj.header.mix_digest),
                "blockNumber": hex(obj.header.number),
                "gasLimit": hex(obj.header.gas_limit),
                "gasUsed": hex(obj.header.gas_used),
                "timestamp": hex(obj.header.timestamp),
                "extraData": hex_or_none(obj.header.extra_data),
            }
            if obj.header.base_fee is not None:
                payload["baseFeePerGas"] = hex(obj.header.base_fee)
            if obj.header.hash is not None:
                payload["blockHash"] = "0x" + obj.header.hash.hex()

            if obj.transactions is not None:
                payload["transactions"] = [
                    hex_or_none(tx.serialized_bytes()) for tx in obj.transactions
                ]
            if obj.withdrawals is not None:
                payload["withdrawals"] = obj.withdrawals

            if obj.header.data_gas_used is not None:
                payload["dataGasUsed"] = hex(obj.header.data_gas_used)
            if obj.header.excess_data_gas is not None:
                payload["excessDataGas"] = hex(obj.header.excess_data_gas)

            return payload
        elif isinstance(obj, Fixture):
            if obj._json is not None:
                obj._json["_info"] = obj.info
                return obj._json

            f = {
                "_info": obj.info,
                "blocks": [json.loads(json.dumps(b, cls=JSONEncoder)) for b in obj.blocks],
                "genesisBlockHeader": self.default(obj.genesis),
                "genesisRLP": hex_or_none(obj.genesis_rlp),
                "lastblockhash": hex_or_none(obj.head),
                "network": obj.fork,
                "pre": json.loads(json.dumps(obj.pre_state, cls=JSONEncoder)),
                "postState": json.loads(json.dumps(obj.post_state, cls=JSONEncoder)),
                "sealEngine": obj.seal_engine,
            }
            if f["postState"] is None:
                del f["postState"]
            return f
        else:
            return super().default(obj)
