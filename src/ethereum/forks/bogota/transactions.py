"""
Transactions are atomic units of work created externally to Ethereum and
submitted to be executed. If Ethereum is viewed as a state machine,
transactions are the events that move between states.
"""

from dataclasses import dataclass, replace
from typing import Tuple, TypeGuard, final

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes, Bytes0, Bytes32
from ethereum_types.frozen import slotted_freezable
from ethereum_types.numeric import U64, U256, Uint, ulen

from ethereum.crypto.elliptic_curve import (
    SECP256K1N,
    secp256k1_recover,
    secp256r1_verify,
)
from ethereum.crypto.hash import Hash32, keccak256
from ethereum.exceptions import (
    InsufficientTransactionGasError,
    InvalidSignatureError,
    NonceOverflowError,
)
from ethereum.state import Address

from .exceptions import (
    FrameTransactionFormatError,
    InitCodeTooLargeError,
    TransactionTypeError,
)
from .fork_types import (
    Authorization,
    RegularGas,
    StateGas,
    VersionedHash,
)


@final
@dataclass
class IntrinsicGasCost:
    """Intrinsic gas costs for a transaction, split by gas type."""

    regular: RegularGas
    """Regular execution gas (calldata, base cost, access list, etc.)."""

    state: StateGas
    """
    State growth gas (account creation, storage set, authorization) per
    [EIP-8037].

    [EIP-8037]: https://eips.ethereum.org/EIPS/eip-8037
    """

    calldata_floor: RegularGas
    """
    Minimum gas cost based on calldata size per [EIP-7623].

    [EIP-7623]: https://eips.ethereum.org/EIPS/eip-7623
    """


TX_MAX_GAS_LIMIT = Uint(16_777_216)

ACCESS_LIST_ADDRESS_FLOOR_TOKENS = Uint(80)
"""
Floor data tokens contributed by a single access list address per
[EIP-7981].

[EIP-7981]: https://eips.ethereum.org/EIPS/eip-7981
"""

ACCESS_LIST_STORAGE_KEY_FLOOR_TOKENS = Uint(128)
"""
Floor data tokens contributed by a single access list storage key per
[EIP-7981].

[EIP-7981]: https://eips.ethereum.org/EIPS/eip-7981
"""

FRAME_TX_INTRINSIC_COST = Uint(15000)
"""
Base intrinsic cost of a frame transaction per [EIP-8141].

[EIP-8141]: https://eips.ethereum.org/EIPS/eip-8141
"""

FRAME_TX_PER_FRAME_COST = Uint(475)
"""
Fixed cost charged for each frame in a frame transaction per [EIP-8141].
It covers the call-context overhead of the frame boundary and the
per-frame receipt entry.

[EIP-8141]: https://eips.ethereum.org/EIPS/eip-8141
"""

ENTRY_POINT = Address(b"\x00" * 19 + b"\xaa")
"""
Address used as the caller of `DEFAULT` and `VERIFY` mode frames per
[EIP-8141].

[EIP-8141]: https://eips.ethereum.org/EIPS/eip-8141
"""

EXPIRY_VERIFIER = Address(b"\x00" * 18 + b"\x81\x41")
"""
Address of the expiry verifier contract per [EIP-8141]. A `VERIFY` frame
targeting this address checks that the transaction has not expired.

[EIP-8141]: https://eips.ethereum.org/EIPS/eip-8141
"""

EXPIRY_VERIFIER_CODE = Bytes(
    bytes.fromhex("60083614600a575f5ffd5b5f3560c01c4211601657005b5f5ffd")
)
"""
Runtime code installed at [`EXPIRY_VERIFIER`] per [EIP-8141]. It reverts
unless the calldata is an 8-byte big-endian timestamp that is greater
than or equal to the block timestamp.

[`EXPIRY_VERIFIER`]: ref:ethereum.forks.bogota.transactions.EXPIRY_VERIFIER
[EIP-8141]: https://eips.ethereum.org/EIPS/eip-8141
"""

EXPIRY_DATA_LENGTH = 8
"""
Required length of the calldata of an expiry verifier frame per
[EIP-8141].

[EIP-8141]: https://eips.ethereum.org/EIPS/eip-8141
"""

MAX_FRAMES = 64
"""
Maximum number of frames in a frame transaction per [EIP-8141].

[EIP-8141]: https://eips.ethereum.org/EIPS/eip-8141
"""

FRAME_MODE_DEFAULT = Uint(0)
"""
Frame mode executing the frame as a call from [`ENTRY_POINT`].

[`ENTRY_POINT`]: ref:ethereum.forks.bogota.transactions.ENTRY_POINT
"""

FRAME_MODE_VERIFY = Uint(1)
"""
Frame mode identifying the frame as transaction validation. The frame
executes with static-call semantics; only `APPROVE` may modify state.
A reverting `VERIFY` frame invalidates the whole transaction.
"""

FRAME_MODE_SENDER = Uint(2)
"""
Frame mode executing the frame as a call from the transaction sender.
Requires prior execution approval.
"""

FRAME_MODE_COUNT = Uint(3)
"""
Number of defined frame modes. `frame.mode` must be strictly less than
this value.
"""

ATOMIC_BATCH_FLAG = Uint(0x4)
"""
Bit 2 of `frame.flags`: the frame forms an atomic batch with the frames
that follow it, up to and including the first frame without this flag.
"""

FRAME_FLAGS_LIMIT = Uint(8)
"""
Exclusive upper bound of the `frame.flags` field. Higher bits are
reserved.
"""

APPROVE_NONE = Uint(0x0)
"""
Approval scope permitting no approval at all.
"""

APPROVE_PAYMENT = Uint(0x1)
"""
Approval scope where the approving contract pays the total gas cost of
the transaction.
"""

APPROVE_EXECUTION = Uint(0x2)
"""
Approval scope where the sender contract approves future frames calling
on its behalf. Only valid when the frame's resolved target equals the
transaction sender.
"""

APPROVE_EXECUTION_AND_PAYMENT = Uint(0x3)
"""
Approval scope combining [`APPROVE_PAYMENT`] and [`APPROVE_EXECUTION`].

[`APPROVE_PAYMENT`]: ref:ethereum.forks.bogota.transactions.APPROVE_PAYMENT
[`APPROVE_EXECUTION`]: ref:ethereum.forks.bogota.transactions.APPROVE_EXECUTION
"""

APPROVE_SCOPE_MASK = APPROVE_EXECUTION_AND_PAYMENT
"""
Mask extracting the approval scope from `frame.flags` (bits 0-1).
"""

SIGNATURE_SCHEME_ARBITRARY = Uint(0x0)
"""
Signature scheme carrying arbitrary witness bytes that are not validated
by the protocol.
"""

SIGNATURE_SCHEME_SECP256K1 = Uint(0x1)
"""
Signature scheme for secp256k1 signatures encoded as
`v (1 byte) || r (32 bytes) || s (32 bytes)`.
"""

SIGNATURE_SCHEME_P256 = Uint(0x2)
"""
Signature scheme for P-256 signatures encoded as
`r || s || qx || qy` (each 32 bytes).
"""

SECP256K1_SIGNATURE_VERIFICATION_GAS = Uint(2800)
"""
Gas charged for protocol validation of a secp256k1 signature entry.
"""

P256_SIGNATURE_VERIFICATION_GAS = Uint(6700)
"""
Gas charged for protocol validation of a P-256 signature entry.
"""

FRAME_STATUS_FAILURE = Uint(0)
"""
Frame receipt status of a frame whose execution reverted or was rolled
back as part of a failed atomic batch.
"""

FRAME_STATUS_SUCCESS = Uint(1)
"""
Frame receipt status of a frame that executed successfully.
"""

FRAME_STATUS_SKIPPED = Uint(3)
"""
Frame receipt status of a frame that was skipped because an earlier
frame of its atomic batch failed.
"""


@final
@slotted_freezable
@dataclass
class LegacyTransaction:
    """
    Atomic operation performed on the block chain. This represents the original
    transaction format used before [EIP-1559], [EIP-2930], [EIP-4844],
    and [EIP-7702].

    [EIP-1559]: https://eips.ethereum.org/EIPS/eip-1559
    [EIP-2930]: https://eips.ethereum.org/EIPS/eip-2930
    [EIP-4844]: https://eips.ethereum.org/EIPS/eip-4844
    [EIP-7702]: https://eips.ethereum.org/EIPS/eip-7702
    """

    nonce: U256
    """
    A scalar value equal to the number of transactions sent by the sender.
    """

    gas_price: Uint
    """
    The price of gas for this transaction, in wei.
    """

    gas: Uint
    """
    The maximum amount of gas that can be used by this transaction.
    """

    to: Bytes0 | Address
    """
    The address of the recipient. If empty, the transaction is a contract
    creation.
    """

    value: U256
    """
    The amount of ether (in wei) to send with this transaction.
    """

    data: Bytes
    """
    The data payload of the transaction, which can be used to call functions
    on contracts or to create new contracts.
    """

    v: U256
    """
    The recovery id of the signature.
    """

    r: U256
    """
    The first part of the signature.
    """

    s: U256
    """
    The second part of the signature.
    """


@final
@slotted_freezable
@dataclass
class Access:
    """
    A mapping from account address to storage slots that are pre-warmed as part
    of a transaction.
    """

    account: Address
    """
    The address of the account that is accessed.
    """

    slots: Tuple[Bytes32, ...]
    """
    A tuple of storage slots that are accessed in the account.
    """


@final
@slotted_freezable
@dataclass
class AccessListTransaction:
    """
    The transaction type added in [EIP-2930] to support access lists.

    This transaction type extends the legacy transaction with an access list
    and chain ID. The access list specifies which addresses and storage slots
    the transaction will access.

    [EIP-2930]: https://eips.ethereum.org/EIPS/eip-2930
    """

    chain_id: U64
    """
    The ID of the chain on which this transaction is executed.
    """

    nonce: U256
    """
    A scalar value equal to the number of transactions sent by the sender.
    """

    gas_price: Uint
    """
    The price of gas for this transaction.
    """

    gas: Uint
    """
    The maximum amount of gas that can be used by this transaction.
    """

    to: Bytes0 | Address
    """
    The address of the recipient. If empty, the transaction is a contract
    creation.
    """

    value: U256
    """
    The amount of ether (in wei) to send with this transaction.
    """

    data: Bytes
    """
    The data payload of the transaction, which can be used to call functions
    on contracts or to create new contracts.
    """

    access_list: Tuple[Access, ...]
    """
    A tuple of `Access` objects that specify which addresses and storage slots
    are accessed in the transaction.
    """

    y_parity: U256
    """
    The recovery id of the signature.
    """

    r: U256
    """
    The first part of the signature.
    """

    s: U256
    """
    The second part of the signature.
    """


@final
@slotted_freezable
@dataclass
class FeeMarketTransaction:
    """
    The transaction type added in [EIP-1559].

    This transaction type introduces a new fee market mechanism with two gas
    price parameters: max_priority_fee_per_gas and max_fee_per_gas.

    [EIP-1559]: https://eips.ethereum.org/EIPS/eip-1559
    """

    chain_id: U64
    """
    The ID of the chain on which this transaction is executed.
    """

    nonce: U256
    """
    A scalar value equal to the number of transactions sent by the sender.
    """

    max_priority_fee_per_gas: Uint
    """
    The maximum priority fee per gas that the sender is willing to pay.
    """

    max_fee_per_gas: Uint
    """
    The maximum fee per gas that the sender is willing to pay, including the
    base fee and priority fee.
    """

    gas: Uint
    """
    The maximum amount of gas that can be used by this transaction.
    """

    to: Bytes0 | Address
    """
    The address of the recipient. If empty, the transaction is a contract
    creation.
    """

    value: U256
    """
    The amount of ether (in wei) to send with this transaction.
    """

    data: Bytes
    """
    The data payload of the transaction, which can be used to call functions
    on contracts or to create new contracts.
    """

    access_list: Tuple[Access, ...]
    """
    A tuple of `Access` objects that specify which addresses and storage slots
    are accessed in the transaction.
    """

    y_parity: U256
    """
    The recovery id of the signature.
    """

    r: U256
    """
    The first part of the signature.
    """

    s: U256
    """
    The second part of the signature.
    """


@final
@slotted_freezable
@dataclass
class BlobTransaction:
    """
    The transaction type added in [EIP-4844].

    This transaction type extends the fee market transaction to support
    blob-carrying transactions.

    [EIP-4844]: https://eips.ethereum.org/EIPS/eip-4844
    """

    chain_id: U64
    """
    The ID of the chain on which this transaction is executed.
    """

    nonce: U256
    """
    A scalar value equal to the number of transactions sent by the sender.
    """

    max_priority_fee_per_gas: Uint
    """
    The maximum priority fee per gas that the sender is willing to pay.
    """

    max_fee_per_gas: Uint
    """
    The maximum fee per gas that the sender is willing to pay, including the
    base fee and priority fee.
    """

    gas: Uint
    """
    The maximum amount of gas that can be used by this transaction.
    """

    to: Address
    """
    The address of the recipient. If empty, the transaction is a contract
    creation.
    """

    value: U256
    """
    The amount of ether (in wei) to send with this transaction.
    """

    data: Bytes
    """
    The data payload of the transaction, which can be used to call functions
    on contracts or to create new contracts.
    """

    access_list: Tuple[Access, ...]
    """
    A tuple of `Access` objects that specify which addresses and storage slots
    are accessed in the transaction.
    """

    max_fee_per_blob_gas: U256
    """
    The maximum fee per blob gas that the sender is willing to pay.
    """

    blob_versioned_hashes: Tuple[VersionedHash, ...]
    """
    A tuple of objects that represent the versioned hashes of the blobs
    included in the transaction.
    """

    y_parity: U256
    """
    The recovery id of the signature.
    """

    r: U256
    """
    The first part of the signature.
    """

    s: U256
    """
    The second part of the signature.
    """


@final
@slotted_freezable
@dataclass
class SetCodeTransaction:
    """
    The transaction type added in [EIP-7702].

    This transaction type allows Ethereum Externally Owned Accounts (EOAs)
    to set code on their account, enabling them to act as smart contracts.

    [EIP-7702]: https://eips.ethereum.org/EIPS/eip-7702
    """

    chain_id: U64
    """
    The ID of the chain on which this transaction is executed.
    """

    nonce: U64
    """
    A scalar value equal to the number of transactions sent by the sender.
    """

    max_priority_fee_per_gas: Uint
    """
    The maximum priority fee per gas that the sender is willing to pay.
    """

    max_fee_per_gas: Uint
    """
    The maximum fee per gas that the sender is willing to pay, including the
    base fee and priority fee.
    """

    gas: Uint
    """
    The maximum amount of gas that can be used by this transaction.
    """

    to: Address
    """
    The address of the recipient. If empty, the transaction is a contract
    creation.
    """

    value: U256
    """
    The amount of ether (in wei) to send with this transaction.
    """

    data: Bytes
    """
    The data payload of the transaction, which can be used to call functions
    on contracts or to create new contracts.
    """

    access_list: Tuple[Access, ...]
    """
    A tuple of `Access` objects that specify which addresses and storage slots
    are accessed in the transaction.
    """

    authorizations: Tuple[Authorization, ...]
    """
    A tuple of `Authorization` objects that specify what code the signer
    desires to execute in the context of their EOA.
    """

    y_parity: U256
    """
    The recovery id of the signature.
    """

    r: U256
    """
    The first part of the signature.
    """

    s: U256
    """
    The second part of the signature.
    """


@final
@slotted_freezable
@dataclass
class Frame:
    """
    A single execution frame of a [`FrameTransaction`][ft], as defined
    in [EIP-8141]. A frame is a contract call that validates the
    transaction, approves gas payment, or executes a user operation.

    [ft]: ref:ethereum.forks.bogota.transactions.FrameTransaction
    [EIP-8141]: https://eips.ethereum.org/EIPS/eip-8141
    """

    mode: Uint
    """
    The execution semantics of the frame: 0 = `DEFAULT`, 1 = `VERIFY`,
    2 = `SENDER`.
    """

    flags: Uint
    """
    Optional frame features. Bits 0-1 are the allowed approval scope and
    bit 2 marks the frame as part of an atomic batch.
    """

    target: Bytes0 | Address
    """
    The destination address of the frame. If empty, the frame targets
    the transaction sender.
    """

    gas_limit: Uint
    """
    The maximum gas allowed to be used by the frame.
    """

    value: U256
    """
    The amount in wei transferred from the sender as part of the frame
    execution. Must be zero unless the frame mode is `SENDER`.
    """

    data: Bytes
    """
    The calldata provided to the top level call of the frame.
    """


@final
@slotted_freezable
@dataclass
class TransactionSignature:
    """
    A signature entry of a [`FrameTransaction`][ft], as defined in
    [EIP-8141]. Signature entries are validated by the protocol before
    any frame executes and may be referenced by `VERIFY` frames and by
    ordinary EVM execution through the `SIGPARAM` instruction.

    [ft]: ref:ethereum.forks.bogota.transactions.FrameTransaction
    [EIP-8141]: https://eips.ethereum.org/EIPS/eip-8141
    """

    scheme: Uint
    """
    The verification scheme used to interpret the raw signature bytes:
    0 = `ARBITRARY`, 1 = `SECP256K1`, 2 = `P256`.
    """

    signer: Bytes
    """
    Scheme-dependent signer metadata. A 20-byte address for `SECP256K1`
    and `P256`; empty for `ARBITRARY`.
    """

    msg: Bytes
    """
    Either empty, indicating the canonical transaction signature hash,
    or an explicit 32-byte digest. The explicit 32-byte zero digest is
    invalid.
    """

    signature: Bytes
    """
    Raw signature bytes interpreted according to `scheme`.
    """


@final
@slotted_freezable
@dataclass
class FrameTransaction:
    """
    The transaction type added in [EIP-8141].

    A frame transaction decomposes into a sequence of frames — contract
    calls that validate the transaction, approve gas payment, and
    execute user operations — allowing validity and gas payment to be
    defined abstractly by account code.

    [EIP-8141]: https://eips.ethereum.org/EIPS/eip-8141
    """

    chain_id: U64
    """
    The ID of the chain on which this transaction is executed.
    """

    nonce: U64
    """
    A scalar value equal to the number of transactions sent by the
    sender.
    """

    sender: Address
    """
    The address of the intended sender of the transaction.
    """

    frames: Tuple[Frame, ...]
    """
    The ordered list of frames to execute.
    """

    signatures: Tuple[TransactionSignature, ...]
    """
    The list of validated signatures available to the transaction.
    """

    max_priority_fee_per_gas: Uint
    """
    The maximum priority fee per gas that the sender is willing to pay.
    """

    max_fee_per_gas: Uint
    """
    The maximum fee per gas that the sender is willing to pay, including
    the base fee and priority fee.
    """

    max_fee_per_blob_gas: U256
    """
    The maximum fee per blob gas that the sender is willing to pay. Must
    be zero if `blob_versioned_hashes` is empty.
    """

    blob_versioned_hashes: Tuple[VersionedHash, ...]
    """
    A tuple of objects that represent the versioned hashes of the blobs
    included in the transaction.
    """


Transaction = (
    LegacyTransaction
    | AccessListTransaction
    | FeeMarketTransaction
    | BlobTransaction
    | SetCodeTransaction
    | FrameTransaction
)
"""
Union type representing any valid transaction type.
"""


AccessListCapableTransaction = (
    AccessListTransaction
    | FeeMarketTransaction
    | BlobTransaction
    | SetCodeTransaction
)
"""
Transaction types that include an [EIP-2930]-style access list.

See [`has_access_list`][hal] and [`Access`][a] for more details.

[EIP-2930]: https://eips.ethereum.org/EIPS/eip-2930
[hal]: ref:ethereum.forks.bogota.transactions.has_access_list
[a]: ref:ethereum.forks.bogota.transactions.Access
"""


FeeMarketCapableTransaction = (
    FeeMarketTransaction | BlobTransaction | SetCodeTransaction
)
"""
Transaction types that include the [EIP-1559]-style fee structure.

See [`FeeMarketTransaction`][fmt] for more details.

[EIP-1559]: https://eips.ethereum.org/EIPS/eip-1559
[fmt]: ref:ethereum.forks.bogota.transactions.FeeMarketTransaction
"""


def encode_transaction(tx: Transaction) -> LegacyTransaction | Bytes:
    """
    Encode a transaction into its RLP or typed transaction format.
    Needed because non-legacy transactions aren't RLP.

    Legacy transactions are returned as-is, while other transaction types
    are prefixed with their type identifier and RLP encoded.
    """
    if isinstance(tx, LegacyTransaction):
        return tx
    elif isinstance(tx, AccessListTransaction):
        return b"\x01" + rlp.encode(tx)
    elif isinstance(tx, FeeMarketTransaction):
        return b"\x02" + rlp.encode(tx)
    elif isinstance(tx, BlobTransaction):
        return b"\x03" + rlp.encode(tx)
    elif isinstance(tx, SetCodeTransaction):
        return b"\x04" + rlp.encode(tx)
    elif isinstance(tx, FrameTransaction):
        return b"\x06" + rlp.encode(tx)
    else:
        raise Exception(f"Unable to encode transaction of type {type(tx)}")


def decode_transaction(tx: LegacyTransaction | Bytes) -> Transaction:
    """
    Decode a transaction from its RLP or typed transaction format.
    Needed because non-legacy transactions aren't RLP.

    Accept a ``LegacyTransaction`` object (returned as-is) or raw
    bytes.

    EIP-2718 states that the first byte distinguishes the format:
    [0x00, 0x7f] is a typed transaction, [0xc0, 0xfe] is a legacy
    transaction (RLP list prefix).
    """
    if isinstance(tx, Bytes):
        if tx[0] == 1:
            return rlp.decode_to(AccessListTransaction, tx[1:])
        elif tx[0] == 2:
            return rlp.decode_to(FeeMarketTransaction, tx[1:])
        elif tx[0] == 3:
            return rlp.decode_to(BlobTransaction, tx[1:])
        elif tx[0] == 4:
            return rlp.decode_to(SetCodeTransaction, tx[1:])
        elif tx[0] == 6:
            return rlp.decode_to(FrameTransaction, tx[1:])
        elif tx[0] >= 0xC0:
            assert tx[0] <= 0xFE
            return rlp.decode_to(LegacyTransaction, tx)
        else:
            raise TransactionTypeError(tx[0])
    else:
        return tx


def validate_transaction(tx: Transaction, sender: Address) -> IntrinsicGasCost:
    """
    Verifies a transaction.

    The gas in a transaction gets used to pay for the intrinsic cost of
    operations, therefore if there is insufficient gas then it would not
    be possible to execute a transaction and it will be declared invalid.

    Additionally, the nonce of a transaction must not equal or exceed the
    limit defined in [EIP-2681].
    In practice, defining the limit as ``2**64-1`` has no impact because
    sending ``2**64-1`` transactions is improbable. It's not strictly
    impossible though, ``2**64-1`` transactions is the entire capacity of the
    Ethereum blockchain at 2022 gas limits for a little over 22 years.

    Also, the code size of a contract creation transaction must be within
    limits of the protocol.

    Frame transactions have no gas limit field: their gas limit is derived
    from the transaction contents, so the intrinsic cost is covered by
    construction. Their structure is checked by
    [`validate_frame_transaction`][vft] and their calldata floor is
    validated against the derived gas limit.

    This function takes a transaction and gas_limit as parameters and
    returns the intrinsic gas costs for the transaction after validation.
    It throws an `InsufficientTransactionGasError` exception if the
    transaction does not provide enough gas to cover the intrinsic cost,
    and a `NonceOverflowError` exception if the nonce overflows.
    It also raises an `InitCodeTooLargeError` if the code
    size of a contract creation transaction exceeds the maximum allowed
    size.

    [EIP-2681]: https://eips.ethereum.org/EIPS/eip-2681
    [EIP-7623]: https://eips.ethereum.org/EIPS/eip-7623
    [vft]: ref:ethereum.forks.bogota.transactions.validate_frame_transaction
    """
    from .vm.interpreter import MAX_INIT_CODE_SIZE

    intrinsic = calculate_intrinsic_cost(tx, sender)
    if isinstance(tx, FrameTransaction):
        validate_frame_transaction(tx)
        if intrinsic.calldata_floor > calculate_frame_transaction_gas_limit(
            tx
        ):
            raise InsufficientTransactionGasError(
                "Insufficient calldata floor"
            )
    else:
        intrinsic_gas = Uint(intrinsic.regular) + Uint(intrinsic.state)
        if intrinsic_gas > tx.gas:
            raise InsufficientTransactionGasError("Insufficient intrinsic gas")
        if intrinsic.calldata_floor > tx.gas:
            raise InsufficientTransactionGasError(
                "Insufficient calldata floor"
            )
        if tx.to == Bytes0(b"") and len(tx.data) > MAX_INIT_CODE_SIZE:
            raise InitCodeTooLargeError("Code size too large")
        if intrinsic.regular > TX_MAX_GAS_LIMIT:
            raise InsufficientTransactionGasError(
                "Intrinsic regular gas exceeds TX_MAX_GAS_LIMIT"
            )
        if intrinsic.calldata_floor > TX_MAX_GAS_LIMIT:
            raise InsufficientTransactionGasError(
                "Intrinsic calldata floor exceeds TX_MAX_GAS_LIMIT"
            )
    if U256(tx.nonce) >= U256(U64.MAX_VALUE):
        raise NonceOverflowError("Nonce too high")

    return intrinsic


def calculate_intrinsic_cost(
    tx: Transaction, sender: Address
) -> IntrinsicGasCost:
    """
    Calculates the gas that is charged before execution is started.

    The intrinsic cost of the transaction is charged before execution has
    begun. Functions/operations in the EVM cost money to execute so this
    intrinsic cost is for the operations that need to be paid for as part of
    the transaction. Data transfer, for example, is part of this intrinsic
    cost. It costs ether to send data over the wire and that ether is
    accounted for in the intrinsic cost calculated in this function. This
    intrinsic cost must be calculated and paid for before execution in order
    for all operations to be implemented.

    The intrinsic cost includes:
    1. Sender cost (`TX_BASE`).
    2. Recipient cost (`COLD_ACCOUNT_ACCESS` for a non-self-transfer
       call, or `CREATE_ACCESS` plus `NEW_ACCOUNT` state gas for a
       contract creation).
    3. Value cost (`TRANSFER_LOG_COST`, plus `TX_VALUE_COST` for a
       non-self-transfer call) when ``tx.value > 0``.
    4. Calldata cost (zero and non-zero bytes).
    5. Access list entries (if applicable).
    6. Authorizations (if applicable).

    Self-transfers (``sender == tx.to``) skip the recipient and value
    charges.

    The intrinsic cost of a frame transaction is instead the base cost, the
    per-frame cost, the calldata cost of the frame and signature byte
    fields, and the signature verification cost.

    This function takes a transaction and gas_limit as parameters and
    returns the intrinsic regular gas cost, intrinsic state gas cost, and the
    minimum gas cost used by the transaction based on the calldata size.
    """
    from .vm.gas import (
        GasCosts,
        StateGasCosts,
        init_code_cost,
    )

    if isinstance(tx, FrameTransaction):
        signature_gas = Uint(0)
        for sig in tx.signatures:
            signature_gas += signature_verification_gas(sig)

        calldata_tokens = Uint(0)
        for charged_data in frame_transaction_charged_data(tx):
            calldata_tokens += count_tokens_in_data(charged_data)

        regular_gas = (
            FRAME_TX_INTRINSIC_COST
            + ulen(tx.frames) * FRAME_TX_PER_FRAME_COST
            + calldata_tokens * GasCosts.TX_DATA_TOKEN_STANDARD
            + signature_gas
        )
        return IntrinsicGasCost(
            regular=RegularGas(regular_gas),
            state=StateGas(Uint(0)),
            calldata_floor=RegularGas(
                calculate_frame_transaction_calldata_floor(tx)
            ),
        )

    tokens_in_calldata = count_tokens_in_data(tx.data)

    data_cost = tokens_in_calldata * GasCosts.TX_DATA_TOKEN_STANDARD

    is_create = tx.to == Bytes0(b"")
    is_self_transfer = tx.to == sender

    recipient_regular_gas = Uint(0)
    recipient_state_gas = Uint(0)
    if is_create:
        recipient_regular_gas = GasCosts.CREATE_ACCESS + init_code_cost(
            ulen(tx.data)
        )
        recipient_state_gas = StateGasCosts.NEW_ACCOUNT
        if tx.value > U256(0):
            recipient_regular_gas += GasCosts.TRANSFER_LOG_COST
    elif not is_self_transfer:
        recipient_regular_gas = GasCosts.COLD_ACCOUNT_ACCESS
        if tx.value > U256(0):
            recipient_regular_gas += (
                GasCosts.TRANSFER_LOG_COST + GasCosts.TX_VALUE_COST
            )

    access_list_cost = Uint(0)
    tokens_in_access_list = Uint(0)
    if has_access_list(tx):
        for access in tx.access_list:
            access_list_cost += GasCosts.TX_ACCESS_LIST_ADDRESS
            access_list_cost += (
                ulen(access.slots) * GasCosts.TX_ACCESS_LIST_STORAGE_KEY
            )
            tokens_in_access_list += ACCESS_LIST_ADDRESS_FLOOR_TOKENS
            tokens_in_access_list += (
                ulen(access.slots) * ACCESS_LIST_STORAGE_KEY_FLOOR_TOKENS
            )

    # Data token floor cost for access list bytes.
    access_list_cost += tokens_in_access_list * GasCosts.TX_DATA_TOKEN_FLOOR

    auth_regular_gas = Uint(0)
    auth_state_gas = Uint(0)
    if isinstance(tx, SetCodeTransaction):
        auth_regular_gas = (
            GasCosts.ACCOUNT_WRITE + GasCosts.REGULAR_PER_AUTH_BASE_COST
        ) * ulen(tx.authorizations)
        auth_state_gas = (
            StateGasCosts.NEW_ACCOUNT + StateGasCosts.AUTH_BASE
        ) * ulen(tx.authorizations)

    # EIP-7976 floor tokens: all calldata bytes count uniformly.
    floor_tokens_in_calldata = ulen(tx.data) * GasCosts.TX_DATA_TOKEN_STANDARD

    # Total floor tokens.
    total_floor_tokens = floor_tokens_in_calldata + tokens_in_access_list

    # Floor gas cost (EIP-7623: minimum gas for data-heavy transactions).
    data_floor_gas_cost = (
        total_floor_tokens * GasCosts.TX_DATA_TOKEN_FLOOR + GasCosts.TX_BASE
    )

    intrinsic_regular_gas = (
        GasCosts.TX_BASE
        + data_cost
        + recipient_regular_gas
        + access_list_cost
        + auth_regular_gas
    )

    intrinsic_state_gas = recipient_state_gas + auth_state_gas

    return IntrinsicGasCost(
        regular=RegularGas(intrinsic_regular_gas),
        state=StateGas(intrinsic_state_gas),
        calldata_floor=RegularGas(data_floor_gas_cost),
    )


def count_tokens_in_data(data: bytes) -> Uint:
    """
    Count the data tokens in arbitrary input bytes.

    Zero bytes count as 1 token; non-zero bytes count as 4 tokens.
    """
    num_zeros = Uint(data.count(0))
    num_non_zeros = ulen(data) - num_zeros

    return num_zeros + num_non_zeros * Uint(4)


def chain_id(tx: Transaction) -> None | U64:
    """
    Extract the chain identifier from a transaction. See [EIP-155].

    [EIP-155]: https://eips.ethereum.org/EIPS/eip-155
    """
    if isinstance(tx, LegacyTransaction):
        if tx.v == 27 or tx.v == 28:
            return None

        if tx.v < U256(35):
            raise InvalidSignatureError("bad v")

        return U64((tx.v - U256(35)) >> U256(1))
    else:
        return tx.chain_id


def recover_sender(tx: Transaction) -> Address:
    """
    Extracts the sender address from a transaction.

    The v, r, and s values are the three parts that make up the signature
    of a transaction. In order to recover the sender of a transaction the two
    components needed are the signature (``v``, ``r``, and ``s``) and the
    signing hash of the transaction. The sender's public key can be obtained
    with these two values and therefore the sender address can be retrieved.

    Frame transactions declare their sender explicitly and are
    authenticated by their signature list, so they never reach this
    function.

    This function takes chain_id and a transaction as parameters and returns
    the address of the sender of the transaction. It raises an
    `InvalidSignatureError` if the signature values (r, s, v) are invalid.
    """
    assert not isinstance(tx, FrameTransaction)
    r, s = tx.r, tx.s
    if U256(0) >= r or r >= SECP256K1N:
        raise InvalidSignatureError("bad r")
    if U256(0) >= s or s > SECP256K1N // U256(2):
        raise InvalidSignatureError("bad s")

    if isinstance(tx, LegacyTransaction):
        v = tx.v
        if v == 27 or v == 28:
            public_key = secp256k1_recover(
                r, s, v - U256(27), signing_hash_pre155(tx)
            )
        else:
            assert v >= U256(35), "call chain_id before recover_sender"
            tx_chain_id = U64((v - U256(35)) >> U256(1))
            v = (v - U256(35)) & U256(1)
            public_key = secp256k1_recover(
                r,
                s,
                v,
                signing_hash_155(tx, tx_chain_id),
            )
    elif isinstance(tx, AccessListTransaction):
        if tx.y_parity not in (U256(0), U256(1)):
            raise InvalidSignatureError("bad y_parity")
        public_key = secp256k1_recover(
            r, s, tx.y_parity, signing_hash_2930(tx)
        )
    elif isinstance(tx, FeeMarketTransaction):
        if tx.y_parity not in (U256(0), U256(1)):
            raise InvalidSignatureError("bad y_parity")
        public_key = secp256k1_recover(
            r, s, tx.y_parity, signing_hash_1559(tx)
        )
    elif isinstance(tx, BlobTransaction):
        if tx.y_parity not in (U256(0), U256(1)):
            raise InvalidSignatureError("bad y_parity")
        public_key = secp256k1_recover(
            r, s, tx.y_parity, signing_hash_4844(tx)
        )
    elif isinstance(tx, SetCodeTransaction):
        if tx.y_parity not in (U256(0), U256(1)):
            raise InvalidSignatureError("bad y_parity")
        public_key = secp256k1_recover(
            r, s, tx.y_parity, signing_hash_7702(tx)
        )

    return Address(keccak256(public_key)[12:32])


def signing_hash_pre155(tx: LegacyTransaction) -> Hash32:
    """
    Compute the hash of a transaction used in a legacy (pre [EIP-155])
    signature.

    This function takes a legacy transaction as a parameter and returns the
    signing hash of the transaction.

    [EIP-155]: https://eips.ethereum.org/EIPS/eip-155
    """
    return keccak256(
        rlp.encode(
            (
                tx.nonce,
                tx.gas_price,
                tx.gas,
                tx.to,
                tx.value,
                tx.data,
            )
        )
    )


def signing_hash_155(tx: LegacyTransaction, chain_id: U64) -> Hash32:
    """
    Compute the hash of a transaction used in a [EIP-155] signature.

    This function takes a legacy transaction and a chain ID as parameters
    and returns the hash of the transaction used in an [EIP-155] signature.

    [EIP-155]: https://eips.ethereum.org/EIPS/eip-155
    """
    return keccak256(
        rlp.encode(
            (
                tx.nonce,
                tx.gas_price,
                tx.gas,
                tx.to,
                tx.value,
                tx.data,
                chain_id,
                Uint(0),
                Uint(0),
            )
        )
    )


def signing_hash_2930(tx: AccessListTransaction) -> Hash32:
    """
    Compute the hash of a transaction used in a [EIP-2930] signature.

    This function takes an access list transaction as a parameter
    and returns the hash of the transaction used in an [EIP-2930] signature.

    [EIP-2930]: https://eips.ethereum.org/EIPS/eip-2930
    """
    return keccak256(
        b"\x01"
        + rlp.encode(
            (
                tx.chain_id,
                tx.nonce,
                tx.gas_price,
                tx.gas,
                tx.to,
                tx.value,
                tx.data,
                tx.access_list,
            )
        )
    )


def signing_hash_1559(tx: FeeMarketTransaction) -> Hash32:
    """
    Compute the hash of a transaction used in an [EIP-1559] signature.

    This function takes a fee market transaction as a parameter
    and returns the hash of the transaction used in an [EIP-1559] signature.

    [EIP-1559]: https://eips.ethereum.org/EIPS/eip-1559
    """
    return keccak256(
        b"\x02"
        + rlp.encode(
            (
                tx.chain_id,
                tx.nonce,
                tx.max_priority_fee_per_gas,
                tx.max_fee_per_gas,
                tx.gas,
                tx.to,
                tx.value,
                tx.data,
                tx.access_list,
            )
        )
    )


def signing_hash_4844(tx: BlobTransaction) -> Hash32:
    """
    Compute the hash of a transaction used in an [EIP-4844] signature.

    This function takes a transaction as a parameter and returns the
    signing hash of the transaction used in an [EIP-4844] signature.

    [EIP-4844]: https://eips.ethereum.org/EIPS/eip-4844
    """
    return keccak256(
        b"\x03"
        + rlp.encode(
            (
                tx.chain_id,
                tx.nonce,
                tx.max_priority_fee_per_gas,
                tx.max_fee_per_gas,
                tx.gas,
                tx.to,
                tx.value,
                tx.data,
                tx.access_list,
                tx.max_fee_per_blob_gas,
                tx.blob_versioned_hashes,
            )
        )
    )


def signing_hash_7702(tx: SetCodeTransaction) -> Hash32:
    """
    Compute the hash of a transaction used in a [EIP-7702] signature.

    This function takes a transaction as a parameter and returns the
    signing hash of the transaction used in a [EIP-7702] signature.

    [EIP-7702]: https://eips.ethereum.org/EIPS/eip-7702
    """
    return keccak256(
        b"\x04"
        + rlp.encode(
            (
                tx.chain_id,
                tx.nonce,
                tx.max_priority_fee_per_gas,
                tx.max_fee_per_gas,
                tx.gas,
                tx.to,
                tx.value,
                tx.data,
                tx.access_list,
                tx.authorizations,
            )
        )
    )


def get_transaction_hash(tx: Bytes | LegacyTransaction) -> Hash32:
    """
    Compute the hash of a transaction.

    This function takes a transaction as a parameter and returns the
    keccak256 hash of the transaction. It can handle both legacy transactions
    and typed transactions (`AccessListTransaction`, `FeeMarketTransaction`,
    etc.).
    """
    assert isinstance(tx, (LegacyTransaction, Bytes))
    if isinstance(tx, LegacyTransaction):
        return keccak256(rlp.encode(tx))
    else:
        return keccak256(tx)


def has_access_list(
    tx: Transaction,
) -> TypeGuard[AccessListCapableTransaction]:
    """
    Return whether the transaction has an [EIP-2930]-style access list.

    [EIP-2930]: https://eips.ethereum.org/EIPS/eip-2930
    """
    return isinstance(
        tx,
        AccessListCapableTransaction,
    )


def resolve_frame_target(tx: FrameTransaction, frame: Frame) -> Address:
    """
    Return the resolved target address of a frame.

    An empty frame target resolves to the transaction sender.
    """
    if isinstance(frame.target, Bytes0):
        return tx.sender
    return frame.target


def is_expiry_verifier_frame(frame: Frame) -> bool:
    """
    Return whether the frame is an expiry verifier frame, i.e. a
    `VERIFY` frame targeting the [`EXPIRY_VERIFIER`] contract.

    [`EXPIRY_VERIFIER`]: ref:ethereum.forks.bogota.transactions.EXPIRY_VERIFIER
    """
    return frame.mode == FRAME_MODE_VERIFY and frame.target == EXPIRY_VERIFIER


def validate_frame_transaction(tx: FrameTransaction) -> None:
    """
    Verify the static constraints of a frame transaction.

    The frame count, frame fields, and signature entry structure are
    checked against the limits defined in [EIP-8141]. A
    `FrameTransactionFormatError` is raised for any violation.

    [EIP-8141]: https://eips.ethereum.org/EIPS/eip-8141
    """
    if len(tx.frames) == 0 or len(tx.frames) > MAX_FRAMES:
        raise FrameTransactionFormatError(
            "frame count must be greater than 0 and at most MAX_FRAMES"
        )

    for sig in tx.signatures:
        if tx_signature_scheme_is_protocol_validated(sig):
            if len(sig.signer) != 20:
                raise FrameTransactionFormatError(
                    "signer must be a 20-byte address"
                )
        elif sig.scheme == SIGNATURE_SCHEME_ARBITRARY:
            if len(sig.signer) != 0:
                raise FrameTransactionFormatError(
                    "arbitrary signature signer must be empty"
                )
        else:
            raise FrameTransactionFormatError("unknown signature scheme")
        if len(sig.msg) == 32:
            if sig.msg == b"\x00" * 32:
                raise FrameTransactionFormatError(
                    "explicit zero digest is invalid"
                )
        elif len(sig.msg) != 0:
            raise FrameTransactionFormatError(
                "signature msg must be empty or 32 bytes"
            )

    total_frame_gas = Uint(0)
    expiry_verifier_frames = 0
    for i, frame in enumerate(tx.frames):
        if frame.mode >= FRAME_MODE_COUNT:
            raise FrameTransactionFormatError("unknown frame mode")
        if frame.flags >= FRAME_FLAGS_LIMIT:
            raise FrameTransactionFormatError("reserved frame flags set")
        if frame.gas_limit > Uint(U64.MAX_VALUE):
            raise FrameTransactionFormatError("frame gas limit too high")
        if frame.mode != FRAME_MODE_SENDER and frame.value != 0:
            raise FrameTransactionFormatError(
                "non-zero value outside SENDER mode"
            )
        total_frame_gas += frame.gas_limit
        if total_frame_gas > Uint(U64.MAX_VALUE):
            raise FrameTransactionFormatError("total frame gas too high")

        # An atomic batch must be terminated by a subsequent frame.
        if frame.flags & ATOMIC_BATCH_FLAG and i + 1 >= len(tx.frames):
            raise FrameTransactionFormatError(
                "atomic batch flag set on last frame"
            )

        if is_expiry_verifier_frame(frame):
            expiry_verifier_frames += 1
            if frame.flags != 0:
                raise FrameTransactionFormatError(
                    "expiry verifier frame flags must be zero"
                )
            if len(frame.data) != EXPIRY_DATA_LENGTH:
                raise FrameTransactionFormatError(
                    "expiry verifier frame data must be 8 bytes"
                )

    if expiry_verifier_frames > 1:
        raise FrameTransactionFormatError("multiple expiry verifier frames")

    if len(tx.blob_versioned_hashes) == 0 and tx.max_fee_per_blob_gas != 0:
        raise FrameTransactionFormatError(
            "max_fee_per_blob_gas must be zero without blobs"
        )


def tx_signature_scheme_is_protocol_validated(
    sig: TransactionSignature,
) -> bool:
    """
    Return whether the signature entry uses a scheme that is
    cryptographically validated by the protocol.
    """
    return sig.scheme in (
        SIGNATURE_SCHEME_SECP256K1,
        SIGNATURE_SCHEME_P256,
    )


def signature_verification_gas(sig: TransactionSignature) -> Uint:
    """
    Return the gas charged for validating a single signature entry.
    """
    if sig.scheme == SIGNATURE_SCHEME_SECP256K1:
        return SECP256K1_SIGNATURE_VERIFICATION_GAS
    if sig.scheme == SIGNATURE_SCHEME_P256:
        return P256_SIGNATURE_VERIFICATION_GAS
    assert sig.scheme == SIGNATURE_SCHEME_ARBITRARY
    return Uint(0)


def frame_transaction_charged_data(tx: FrameTransaction) -> Tuple[Bytes, ...]:
    """
    Return the byte fields of a frame transaction that are priced as
    calldata: the `data` of each frame and the `signer`, `msg`, and
    `signature` bytes of each signature entry. The fixed-size fields
    are covered by the intrinsic and per-frame costs.
    """
    charged: Tuple[Bytes, ...] = ()
    for frame in tx.frames:
        charged += (frame.data,)
    for sig in tx.signatures:
        charged += (sig.signer, sig.msg, sig.signature)
    return charged


def calculate_frame_transaction_gas_limit(tx: FrameTransaction) -> Uint:
    """
    Calculate the total gas limit of a frame transaction.

    The gas limit is the sum of the transaction's intrinsic cost — see
    [`calculate_intrinsic_cost`][cic] — and the gas limits of all frames.

    [cic]: ref:ethereum.forks.bogota.transactions.calculate_intrinsic_cost
    """
    intrinsic = calculate_intrinsic_cost(tx, tx.sender)

    total_frame_gas = Uint(0)
    for frame in tx.frames:
        total_frame_gas += frame.gas_limit

    return Uint(intrinsic.regular) + total_frame_gas


def calculate_frame_transaction_calldata_floor(tx: FrameTransaction) -> Uint:
    """
    Calculate the minimum gas cost of a frame transaction based on the
    size of the frame and signature byte fields, per [EIP-7623] and
    [EIP-7976]. Like ordinary calldata, every charged byte counts as a
    standard token and is priced at the floor token cost.

    [EIP-7623]: https://eips.ethereum.org/EIPS/eip-7623
    [EIP-7976]: https://eips.ethereum.org/EIPS/eip-7976
    """
    from .vm.gas import GasCosts

    data_length = Uint(0)
    for data in frame_transaction_charged_data(tx):
        data_length += ulen(data)
    floor_tokens = data_length * GasCosts.TX_DATA_TOKEN_STANDARD

    return (
        floor_tokens * GasCosts.TX_DATA_TOKEN_FLOOR + FRAME_TX_INTRINSIC_COST
    )


def compute_frame_signature_hash(tx: FrameTransaction) -> Hash32:
    """
    Compute the canonical signature hash of a frame transaction.

    The raw `signature` bytes of every entry with an empty `msg` are
    elided before hashing, since a signature over the canonical hash
    cannot commit to its own bytes.
    """
    elided_signatures = []
    for sig in tx.signatures:
        if len(sig.msg) == 0:
            elided_signatures.append(replace(sig, signature=Bytes(b"")))
        else:
            elided_signatures.append(sig)

    elided_tx = replace(tx, signatures=tuple(elided_signatures))
    return keccak256(b"\x06" + rlp.encode(elided_tx))


def validate_frame_signature(
    sig: TransactionSignature, sig_hash: Hash32
) -> bool:
    """
    Validate a single signature entry of a frame transaction.

    An empty `msg` authorizes the canonical signature hash; a 32-byte
    `msg` authorizes that explicit digest. `SECP256K1` and `P256`
    entries are cryptographically verified against their `signer`
    address, while `ARBITRARY` entries are only structurally checked.
    """
    if len(sig.msg) == 0:
        msg = sig_hash
    elif len(sig.msg) == 32:
        if sig.msg == b"\x00" * 32:
            return False
        msg = Hash32(sig.msg)
    else:
        return False

    if sig.scheme == SIGNATURE_SCHEME_SECP256K1:
        if len(sig.signature) != 65:
            return False
        v = U256(sig.signature[0])
        r = U256.from_be_bytes(sig.signature[1:33])
        s = U256.from_be_bytes(sig.signature[33:65])
        if v not in (U256(0), U256(1)):
            return False
        if U256(0) >= r or r >= SECP256K1N:
            return False
        if U256(0) >= s or s > SECP256K1N // U256(2):
            return False
        try:
            public_key = secp256k1_recover(r, s, v, msg)
        except InvalidSignatureError:
            return False
        return Bytes(sig.signer) == keccak256(public_key)[12:32]

    elif sig.scheme == SIGNATURE_SCHEME_P256:
        if len(sig.signature) != 128:
            return False
        r = U256.from_be_bytes(sig.signature[0:32])
        s = U256.from_be_bytes(sig.signature[32:64])
        qx = U256.from_be_bytes(sig.signature[64:96])
        qy = U256.from_be_bytes(sig.signature[96:128])
        if Bytes(sig.signer) != keccak256(sig.signature[64:128])[12:32]:
            return False
        try:
            secp256r1_verify(r, s, qx, qy, msg)
        except (InvalidSignatureError, ValueError):
            return False
        return True

    elif sig.scheme == SIGNATURE_SCHEME_ARBITRARY:
        return len(sig.signer) == 0

    else:
        return False
