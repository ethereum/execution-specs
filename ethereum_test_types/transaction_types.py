"""Transaction-related types for Ethereum tests."""

from dataclasses import dataclass
from enum import IntEnum
from functools import cached_property
from typing import Any, ClassVar, Dict, Generic, List, Literal, Sequence

import ethereum_rlp as eth_rlp
from coincurve.keys import PrivateKey, PublicKey
from ethereum_types.numeric import Uint
from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    model_serializer,
    model_validator,
)
from trie import HexaryTrie

from ethereum_test_base_types import (
    AccessList,
    Address,
    Bytes,
    CamelModel,
    Hash,
    HexNumber,
    NumberBoundTypeVar,
    RLPSerializable,
    SignableRLPSerializable,
    TestAddress,
    TestPrivateKey,
)
from ethereum_test_exceptions import TransactionException

from .account_types import EOA
from .blob_types import Blob
from .receipt_types import TransactionReceipt
from .utils import int_to_bytes, keccak256


class TransactionType(IntEnum):
    """Transaction types."""

    LEGACY = 0
    ACCESS_LIST = 1
    BASE_FEE = 2
    BLOB_TRANSACTION = 3
    SET_CODE = 4


@dataclass
class TransactionDefaults:
    """Default values for transactions."""

    chain_id: int = 1
    gas_price = 10
    max_fee_per_gas = 7
    max_priority_fee_per_gas: int = 0


class AuthorizationTupleGeneric(CamelModel, Generic[NumberBoundTypeVar], SignableRLPSerializable):
    """Authorization tuple for transactions."""

    chain_id: NumberBoundTypeVar = Field(0)  # type: ignore
    address: Address
    nonce: NumberBoundTypeVar = Field(0)  # type: ignore

    v: NumberBoundTypeVar = Field(default=0, validation_alias=AliasChoices("v", "yParity"))  # type: ignore
    r: NumberBoundTypeVar = Field(0)  # type: ignore
    s: NumberBoundTypeVar = Field(0)  # type: ignore

    magic: ClassVar[int] = 0x05

    rlp_fields: ClassVar[List[str]] = ["chain_id", "address", "nonce", "v", "r", "s"]
    rlp_signing_fields: ClassVar[List[str]] = ["chain_id", "address", "nonce"]

    def get_rlp_signing_prefix(self) -> bytes:
        """
        Return a prefix that has to be appended to the serialized signing object.

        By default, an empty string is returned.
        """
        return self.magic.to_bytes(1, byteorder="big")

    @model_serializer(mode="wrap", when_used="json-unless-none")
    def duplicate_v_as_y_parity(self, serializer):
        """
        Add a duplicate 'yParity' field (same as `v`) in JSON fixtures.

        Background: https://github.com/erigontech/erigon/issues/14073
        """
        data = serializer(self)
        if "v" in data and data["v"] is not None:
            data["yParity"] = data["v"]
        return data


class AuthorizationTuple(AuthorizationTupleGeneric[HexNumber]):
    """Authorization tuple for transactions."""

    signer: EOA | None = None
    secret_key: Hash | None = None

    def model_post_init(self, __context: Any) -> None:
        """Automatically signs the authorization tuple if a secret key or sender are provided."""
        super().model_post_init(__context)
        self.sign()

    def sign(self: "AuthorizationTuple"):
        """Signs the authorization tuple with a private key."""
        signature_bytes: bytes | None = None
        rlp_signing_bytes = self.rlp_signing_bytes()
        if (
            "v" not in self.model_fields_set
            and "r" not in self.model_fields_set
            and "s" not in self.model_fields_set
        ):
            signing_key: Hash | None = None
            if self.secret_key is not None:
                signing_key = self.secret_key
            elif self.signer is not None:
                eoa = self.signer
                assert eoa is not None, "signer must be set"
                signing_key = eoa.key
            assert signing_key is not None, "secret_key or signer must be set"

            signature_bytes = PrivateKey(secret=signing_key).sign_recoverable(
                rlp_signing_bytes, hasher=keccak256
            )
            self.v, self.r, self.s = (
                HexNumber(signature_bytes[64]),
                HexNumber(int.from_bytes(signature_bytes[0:32], byteorder="big")),
                HexNumber(int.from_bytes(signature_bytes[32:64], byteorder="big")),
            )
            self.model_fields_set.add("v")
            self.model_fields_set.add("r")
            self.model_fields_set.add("s")

        if self.signer is None:
            try:
                if not signature_bytes:
                    signature_bytes = (
                        int(self.r).to_bytes(32, byteorder="big")
                        + int(self.s).to_bytes(32, byteorder="big")
                        + bytes([self.v])
                    )
                public_key = PublicKey.from_signature_and_message(
                    signature_bytes, rlp_signing_bytes.keccak256(), hasher=None
                )
                self.signer = EOA(
                    address=Address(keccak256(public_key.format(compressed=False)[1:])[32 - 20 :])
                )
            except Exception:
                # Signer remains `None` in this case
                pass


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

    v: NumberBoundTypeVar = Field(0)  # type: ignore
    r: NumberBoundTypeVar = Field(0)  # type: ignore
    s: NumberBoundTypeVar = Field(0)  # type: ignore
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


class Transaction(
    TransactionGeneric[HexNumber], TransactionTransitionToolConverter, SignableRLPSerializable
):
    """Generic object that can represent all Ethereum transaction types."""

    gas_limit: HexNumber = Field(HexNumber(21_000), serialization_alias="gas")
    to: Address | None = Field(Address(0xAA))
    data: Bytes = Field(Bytes(b""), alias="input")

    authorization_list: List[AuthorizationTuple] | None = None

    initcodes: List[Bytes] | None = None

    secret_key: Hash | None = None
    error: List[TransactionException] | TransactionException | None = Field(None, exclude=True)

    protected: bool = Field(True, exclude=True)

    expected_receipt: TransactionReceipt | None = Field(None, exclude=True)

    zero: ClassVar[Literal[0]] = 0

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
            if self.initcodes is not None:
                self.ty = 6
            elif self.authorization_list is not None:
                self.ty = 4
            elif self.max_fee_per_blob_gas is not None or self.blob_versioned_hashes is not None:
                self.ty = 3
            elif self.max_fee_per_gas is not None or self.max_priority_fee_per_gas is not None:
                self.ty = 2
            elif self.access_list is not None:
                self.ty = 1
            else:
                self.ty = 0

        if "v" in self.model_fields_set and self.secret_key is not None:
            raise Transaction.InvalidSignaturePrivateKeyError()

        if "v" not in self.model_fields_set and self.secret_key is None:
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

        if self.ty == 6 and self.initcodes is None:
            self.initcodes = []
        if self.ty != 6:
            assert self.initcodes is None, "initcodes must be None"

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

    @cached_property
    def signature_bytes(self) -> Bytes:
        """Returns the serialized bytes of the transaction signature."""
        assert "v" in self.model_fields_set, "transaction must be signed"
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

    def sign(self: "Transaction"):
        """Signs the authorization tuple with a private key."""
        signature_bytes: bytes | None = None
        rlp_signing_bytes = self.rlp_signing_bytes()
        if (
            "v" not in self.model_fields_set
            and "r" not in self.model_fields_set
            and "s" not in self.model_fields_set
        ):
            signing_key: Hash | None = None
            if self.secret_key is not None:
                signing_key = self.secret_key
                self.secret_key = None
            elif self.sender is not None:
                eoa = self.sender
                assert eoa is not None, "signer must be set"
                signing_key = eoa.key
            assert signing_key is not None, "secret_key or signer must be set"

            signature_bytes = PrivateKey(secret=signing_key).sign_recoverable(
                rlp_signing_bytes, hasher=keccak256
            )
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
            self.v, self.r, self.s = (HexNumber(v), HexNumber(r), HexNumber(s))
            self.model_fields_set.add("v")
            self.model_fields_set.add("r")
            self.model_fields_set.add("s")

        if self.sender is None:
            try:
                if not signature_bytes:
                    v = self.v
                    if self.ty == 0:
                        if v > 28:
                            v -= 35 + (self.chain_id * 2)
                        else:  # not protected
                            v -= 27
                    signature_bytes = (
                        int(self.r).to_bytes(32, byteorder="big")
                        + int(self.s).to_bytes(32, byteorder="big")
                        + bytes([v])
                    )
                public_key = PublicKey.from_signature_and_message(
                    signature_bytes, rlp_signing_bytes.keccak256(), hasher=None
                )
                self.sender = EOA(
                    address=Address(keccak256(public_key.format(compressed=False)[1:])[32 - 20 :])
                )
            except Exception:
                # Signer remains `None` in this case
                pass

    def with_signature_and_sender(self, *, keep_secret_key: bool = False) -> "Transaction":
        """Return signed version of the transaction using the private key."""
        updated_values: Dict[str, Any] = {}

        if (
            "v" in self.model_fields_set
            or "r" in self.model_fields_set
            or "s" in self.model_fields_set
        ):
            # Transaction already signed
            if self.sender is not None:
                return self

            public_key = PublicKey.from_signature_and_message(
                self.signature_bytes, self.rlp_signing_bytes().keccak256(), hasher=None
            )
            updated_values["sender"] = Address(
                keccak256(public_key.format(compressed=False)[1:])[32 - 20 :]
            )
            return self.copy(**updated_values)

        if self.secret_key is None:
            raise ValueError("secret_key must be set to sign a transaction")

        # Get the signing bytes
        signing_hash = self.rlp_signing_bytes().keccak256()

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

    def get_rlp_signing_fields(self) -> List[str]:
        """
        Return the list of values included in the envelope used for signing depending on
        the transaction type.
        """
        field_list: List[str]
        if self.ty == 6:
            # EIP-7873: https://eips.ethereum.org/EIPS/eip-7873
            field_list = [
                "chain_id",
                "nonce",
                "max_priority_fee_per_gas",
                "max_fee_per_gas",
                "gas_limit",
                "to",
                "value",
                "data",
                "access_list",
                "initcodes",
            ]
        elif self.ty == 4:
            # EIP-7702: https://eips.ethereum.org/EIPS/eip-7702
            field_list = [
                "chain_id",
                "nonce",
                "max_priority_fee_per_gas",
                "max_fee_per_gas",
                "gas_limit",
                "to",
                "value",
                "data",
                "access_list",
                "authorization_list",
            ]
        elif self.ty == 3:
            # EIP-4844: https://eips.ethereum.org/EIPS/eip-4844
            field_list = [
                "chain_id",
                "nonce",
                "max_priority_fee_per_gas",
                "max_fee_per_gas",
                "gas_limit",
                "to",
                "value",
                "data",
                "access_list",
                "max_fee_per_blob_gas",
                "blob_versioned_hashes",
            ]
        elif self.ty == 2:
            # EIP-1559: https://eips.ethereum.org/EIPS/eip-1559
            field_list = [
                "chain_id",
                "nonce",
                "max_priority_fee_per_gas",
                "max_fee_per_gas",
                "gas_limit",
                "to",
                "value",
                "data",
                "access_list",
            ]
        elif self.ty == 1:
            # EIP-2930: https://eips.ethereum.org/EIPS/eip-2930
            field_list = [
                "chain_id",
                "nonce",
                "gas_price",
                "gas_limit",
                "to",
                "value",
                "data",
                "access_list",
            ]
        elif self.ty == 0:
            field_list = ["nonce", "gas_price", "gas_limit", "to", "value", "data"]
            if self.protected:
                # EIP-155: https://eips.ethereum.org/EIPS/eip-155
                field_list.extend(["chain_id", "zero", "zero"])
        else:
            raise NotImplementedError(f"signing for transaction type {self.ty} not implemented")

        for field in field_list:
            if field != "to":
                assert getattr(self, field) is not None, (
                    f"{field} must be set for type {self.ty} tx"
                )
        return field_list

    def get_rlp_fields(self) -> List[str]:
        """
        Return the list of values included in the list used for rlp encoding depending on
        the transaction type.
        """
        fields = self.get_rlp_signing_fields()
        if self.ty == 0 and self.protected:
            fields = fields[:-3]
        return fields + ["v", "r", "s"]

    def get_rlp_prefix(self) -> bytes:
        """
        Return the transaction type as bytes to be appended at the beginning of the
        serialized transaction if type is not 0.
        """
        if self.ty > 0:
            return bytes([self.ty])
        return b""

    def get_rlp_signing_prefix(self) -> bytes:
        """
        Return the transaction type as bytes to be appended at the beginning of the
        serialized transaction signing envelope if type is not 0.
        """
        if self.ty > 0:
            return bytes([self.ty])
        return b""

    @cached_property
    def hash(self) -> Hash:
        """Returns hash of the transaction."""
        return self.rlp().keccak256()

    @cached_property
    def serializable_list(self) -> Any:
        """Return list of values included in the transaction as a serializable object."""
        return self.rlp() if self.ty > 0 else self.to_list(signing=False)

    @staticmethod
    def list_root(input_txs: List["Transaction"]) -> Hash:
        """Return transactions root of a list of transactions."""
        t = HexaryTrie(db={})
        for i, tx in enumerate(input_txs):
            t.set(eth_rlp.encode(Uint(i)), tx.rlp())
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


class NetworkWrappedTransaction(CamelModel, RLPSerializable):
    """
    Network wrapped transaction as defined in
    [EIP-4844](https://eips.ethereum.org/EIPS/eip-4844#networking).
    """

    tx: Transaction
    wrapper_version: Literal[1] | None = None
    blobs: Sequence[Blob]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def blob_data(self) -> Sequence[Bytes]:
        """Return a list of blobs as bytes."""
        return [blob.data for blob in self.blobs]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def blob_kzg_commitments(self) -> Sequence[Bytes]:
        """Return a list of kzg commitments."""
        return [blob.kzg_commitment for blob in self.blobs]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def blob_kzg_proofs(self) -> Sequence[Bytes]:
        """Return a list of kzg proofs."""
        proofs: List[Bytes] = []
        for blob in self.blobs:
            if blob.kzg_proof is not None:
                proofs.append(blob.kzg_proof)
            elif blob.kzg_cell_proofs is not None:
                proofs.extend(blob.kzg_cell_proofs)
        return proofs

    def get_rlp_fields(self) -> List[str]:
        """
        Return an ordered list of field names to be included in RLP serialization.

        Function can be overridden to customize the logic to return the fields.

        By default, rlp_fields class variable is used.

        The list can be nested list up to one extra level to represent nested fields.
        """
        wrapper = []
        if self.wrapper_version is not None:
            wrapper = ["wrapper_version"]
        return ["tx", *wrapper, "blob_data", "blob_kzg_commitments", "blob_kzg_proofs"]

    def get_rlp_prefix(self) -> bytes:
        """
        Return the transaction type as bytes to be appended at the beginning of the
        serialized transaction if type is not 0.
        """
        if self.tx.ty > 0:
            return bytes([self.tx.ty])
        return b""
