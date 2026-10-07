"""
Frame transactions, the transaction type introduced in [EIP-8141].

A frame transaction expresses validity conditions, gas payment, and
execution as an explicit list of [`Frame`]s, each a unit of execution
with its own mode, target, and gas limit. Signatures are carried
alongside the frames in a list of [`FrameSignature`] entries that the
protocol validates before any frame executes.

[EIP-8141]: https://eips.ethereum.org/EIPS/eip-8141
[`Frame`]: ref:ethereum.forks.bogota.transactions.frame_transaction.Frame
[`FrameSignature`]: ref:ethereum.forks.bogota.transactions.frame_transaction.FrameSignature
"""  # noqa: E501

from dataclasses import dataclass, replace
from enum import STRICT
from typing import TYPE_CHECKING, Final, Optional, Tuple, assert_never, final

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes, Bytes0, Bytes32
from ethereum_types.enum import UintEnum, UintFlag
from ethereum_types.frozen import slotted_freezable
from ethereum_types.numeric import U64, U256, Uint, ulen

from ethereum.crypto.elliptic_curve import (
    SECP256K1N,
    SECP256R1N,
    secp256k1_recover,
    secp256r1_verify,
)
from ethereum.crypto.hash import Hash32, keccak256
from ethereum.exceptions import InvalidSignatureError, NonceOverflowError
from ethereum.state import Address

from ..exceptions import (
    BlobCountExceededError,
    FeeOverflowError,
    FrameCountError,
    InvalidBlobVersionedHashError,
    InvalidFrameError,
    InvalidMaxFeePerBlobGasError,
    PriorityFeeGreaterThanMaxFeeError,
    TransactionGasLimitExceededError,
)
from ..fork_types import ExecutionGas, VersionedHash

if TYPE_CHECKING:
    from . import IntrinsicGasCost

MAX_FRAMES_PER_TX: Final[Uint] = Uint(64)
"""
Maximum number of [`Frame`]s allowed per [`FrameTransaction`][ftx].

[`Frame`]: ref:ethereum.forks.bogota.transactions.frame_transaction.Frame
[ftx]: ref:ethereum.forks.bogota.transactions.frame_transaction.FrameTransaction
"""  # noqa: E501

EXPIRY_VERIFIER: Final[Address] = Address(
    bytes.fromhex("81413f0cf12e9b6a49b1d0439e081c577d57ffff")
)
"""
Address of the expiry verifier contract.

The verifier is an ordinary contract, deployed by the pre-signed creation
transaction that [EIP-8141] publishes, from a synthetic sender whose only
transaction it is. The protocol does not install it. The EIP gives its
canonical runtime code, which reverts unless called with exactly
[`EXPIRY_DATA_LENGTH`][edl] bytes of calldata.

A [`VERIFY`][v] frame targeting this address is an _expiry verifier frame_:
its data holds an unsigned big-endian expiry timestamp, and the frame
reverts unless the block timestamp is at or before that expiry. Such frames
are subject to additional validity constraints, checked in
[`validate_frame_transaction`][vft].

[EIP-8141]: https://eips.ethereum.org/EIPS/eip-8141
[edl]: ref:ethereum.forks.bogota.transactions.frame_transaction.EXPIRY_DATA_LENGTH
[v]: ref:ethereum.forks.bogota.transactions.frame_transaction.FrameMode.VERIFY
[vft]: ref:ethereum.forks.bogota.transactions.frame_transaction.validate_frame_transaction
"""  # noqa: E501

EXPIRY_DATA_LENGTH: Final[int] = 8
"""
Exact length, in bytes, of an expiry verifier frame's data: an unsigned
big-endian expiry timestamp.
"""

NONCE_MANAGER: Final[Address] = Address(
    bytes.fromhex("8250968c12e01a19d6f667b9b2f3b3a4d0e51cb7")
)
"""
Address of the nonce manager system contract, whose storage holds the
keyed nonce sequences of every sender (see [`nonce_slot`][ns]).

The nonce manager is an ordinary contract, deployed by the pre-signed
creation transaction that [EIP-8250] publishes, from a synthetic sender
whose only transaction it is. The protocol does not install it, and it
must already be in the state when the fork activates. The EIP gives its
canonical runtime code, which reverts on every ordinary call: only the
protocol writes keyed nonces.

[EIP-8250]: https://eips.ethereum.org/EIPS/eip-8250
[ns]: ref:ethereum.forks.bogota.keyed_nonces.nonce_slot
"""

MAX_NONCE_KEYS: Final[Uint] = Uint(16)
"""
Maximum number of nonce keys a [`FrameTransaction`][ftx] may select.

[ftx]: ref:ethereum.forks.bogota.transactions.frame_transaction.FrameTransaction
"""  # noqa: E501

MAX_NONCE_SEQ: Final[U64] = U64.MAX_VALUE
"""
The exhausted nonce sequence: a key at this sequence cannot advance.
"""

LEGACY_NONCE_KEYS: Final[Tuple[U256, ...]] = (U256(0),)
"""
The nonce key set selecting the sender's account nonce rather than a
keyed nonce sequence held by the nonce manager.
"""


@final
class FrameMode(UintEnum, boundary=STRICT):
    """
    Indicates the purpose of a [`Frame`].

    The members below are the only valid modes. The strict boundary rejects
    any other value as the enum is constructed — notably while decoding a
    transaction — so a frame with an undefined mode never decodes and no
    separate validity check is required. An EIP that extends frame
    transactions with a new mode adds a member here; it does not change how
    the existing members are checked.

    [`Frame`]: ref:ethereum.forks.bogota.transactions.frame_transaction.Frame
    """  # noqa: E501

    DEFAULT = Uint(0)
    """
    Execute frame as [`FRAME_ENTRY_POINT`][fep].

    [fep]: ref:ethereum.forks.bogota.vm.FRAME_ENTRY_POINT
    """

    VERIFY = Uint(1)
    """
    Identify frame as transaction validation.
    """

    SENDER = Uint(2)
    """
    Execute frame as [`sender`][s].

    [s]: ref:ethereum.forks.bogota.transactions.frame_transaction.FrameTransaction.sender
    """  # noqa: E501


@final
class FrameFlag(UintFlag, boundary=STRICT):
    """
    Frame or mode features.

    Each member represents a single bit, and any combination of the bits
    defined here is a valid set of flags. The strict boundary rejects values
    with any other bit set as the flag is constructed — notably while
    decoding a transaction — so a frame carrying a reserved flag bit never
    decodes and no separate validity check is required.
    """

    APPROVE_PAYMENT = Uint(1)
    """
    [`Frame`] has permission to approve payment.

    [`Frame`]: ref:ethereum.forks.bogota.transactions.frame_transaction.Frame
    """  # noqa: E501

    APPROVE_EXECUTION = Uint(2)
    """
    [`Frame`] has permission to approve execution.

    [`Frame`]: ref:ethereum.forks.bogota.transactions.frame_transaction.Frame
    """  # noqa: E501

    ATOMIC_BATCH = Uint(4)
    """
    [`Frame`] belongs to an atomic batch.

    All frames within an atomic batch either all succeed or are all reverted.

    [`Frame`]: ref:ethereum.forks.bogota.transactions.frame_transaction.Frame
    """  # noqa: E501


APPROVE_SCOPE_MASK: Final[FrameFlag] = (
    FrameFlag.APPROVE_PAYMENT | FrameFlag.APPROVE_EXECUTION
)
"""
The flag bits holding a frame's allowed approval scope.
"""


@final
class FrameStatus(UintEnum):
    """
    Outcome of a completed frame, as reported in the frame
    transaction's receipt and exposed by the `FRAMEPARAM` opcode.

    Statuses exist only for completed frames — reading the status of
    the current or a future frame is an exceptional halt — so there is
    no pending member. A frame that executed inside a later-unrolled
    atomic batch keeps its execution status; `SKIPPED` marks only
    frames that never ran.
    """

    FAILURE = Uint(0)
    """
    The frame executed and reverted or exceptionally halted.
    """

    SUCCESS = Uint(1)
    """
    The frame executed and completed successfully.
    """

    SKIPPED = Uint(2)
    """
    The frame never executed because an earlier frame of its atomic
    batch failed.
    """


@final
@slotted_freezable
@dataclass
class GasLimits:
    """
    The gas budgets of a [`Frame`], one per gas dimension.

    The two budgets are independent: neither dimension can fund charges
    of the other, and unused gas in one is not available to the other.

    Corresponds to the `limits` list of the frame object in [EIP-8141].

    [EIP-8141]: https://eips.ethereum.org/EIPS/eip-8141
    [`Frame`]: ref:ethereum.forks.bogota.transactions.frame_transaction.Frame
    """  # noqa: E501

    execution: U64
    """
    Maximum execution gas that can be expended in pursuit of the frame.
    """

    state: U64
    """
    Maximum state gas that can be expended in pursuit of the frame.
    """


@final
@slotted_freezable
@dataclass
class Frame:
    """
    Unit of execution defined in a [`FrameTransaction`][ft].

    [ft]: ref:ethereum.forks.bogota.transactions.frame_transaction.FrameTransaction
    """  # noqa: E501

    mode: FrameMode
    """
    Purpose of this frame.

    Specifies the specific execution semantics this frame will execute with.
    """

    flags: FrameFlag
    """
    Enable optional frame or mode features.
    """

    to: Bytes0 | Address
    """
    Destination or target account for the frame.
    """

    gas_limits: GasLimits
    """
    The frame's gas budgets, one per gas dimension.
    """

    value: U256
    """
    Amount of ether (in wei) to transfer from the [`sender`][s] as part of the
    frame execution.

    [s]: ref:ethereum.forks.bogota.transactions.frame_transaction.FrameTransaction.sender
    """  # noqa: E501

    data: Bytes
    """
    The data payload of the frame, which can be used to call functions on
    contracts.
    """


@final
class FrameSignatureScheme(UintEnum, boundary=STRICT):
    """
    Algorithm used to authenticate [`FrameSignature`][fs]s.

    The strict boundary rejects values other than the schemes defined here
    as the enum is constructed — notably while decoding a transaction — so
    a signature using a reserved scheme never decodes and no separate
    validity check is required.

    [fs]: ref:ethereum.forks.bogota.transactions.frame_transaction.FrameSignature
    """  # noqa: E501

    ARBITRARY = Uint(0)
    """
    Arbitrary bytes that the protocol does not cryptographically validate.
    """

    SECP256K1 = Uint(1)
    """
    ECDSA signature over the secp256k1 curve, as used by other transaction
    types.
    """

    P256 = Uint(2)
    """
    Signature over the NIST P-256 (secp256r1) curve.
    """


@final
@slotted_freezable
@dataclass
class FrameSignature:
    """
    A signature entry available to the transaction's frames.

    Entries are validated before any frame executes and may be
    referenced by [`VERIFY`][v] frames and by ordinary EVM execution,
    through the signature introspection instructions.

    [v]: ref:ethereum.forks.bogota.transactions.frame_transaction.FrameMode.VERIFY
    """  # noqa: E501

    scheme: FrameSignatureScheme
    """
    Algorithm used to construct the signature.
    """

    signer: Bytes
    """
    Scheme-dependent signer metadata.

    For [`SECP256K1`] and [`P256`], this is a 20-byte address.

    [`SECP256K1`]: ref:ethereum.forks.bogota.transactions.frame_transaction.FrameSignatureScheme.SECP256K1
    [`P256`]: ref:ethereum.forks.bogota.transactions.frame_transaction.FrameSignatureScheme.P256
    """  # noqa: E501

    message: Bytes0 | Bytes32
    """
    Either empty, indicating the canonical transaction signature hash, or an
    explicit 32-byte digest.
    """

    signature: Bytes
    """
    Raw signature bytes, to be interpreted according to [`scheme`].

    [`scheme`]: ref:ethereum.forks.bogota.transactions.frame_transaction.FrameSignature.scheme
    """  # noqa: E501


@final
@slotted_freezable
@dataclass
class TransactionFees:
    """
    The fee parameters of a [`FrameTransaction`][ftx].

    Corresponds to the `fees` list of the transaction payload in
    [EIP-8141].

    [EIP-8141]: https://eips.ethereum.org/EIPS/eip-8141
    [ftx]: ref:ethereum.forks.bogota.transactions.frame_transaction.FrameTransaction
    """  # noqa: E501

    max_priority_fee_per_gas: Uint
    """
    The maximum priority fee per gas that the sender is willing to pay.
    """

    max_fee_per_gas: Uint
    """
    The maximum fee per gas that the sender is willing to pay, including the
    base fee and priority fee.
    """

    max_fee_per_blob_gas: U256
    """
    The maximum fee per blob gas that the sender is willing to pay.
    """


@final
@slotted_freezable
@dataclass
class FrameTransaction:
    """
    Transaction type constructed from a series of frames, abstractly defining
    validity conditions and gas payment. Introduced in [EIP-8141].

    [EIP-8141]: https://eips.ethereum.org/EIPS/eip-8141
    """

    chain_id: U64
    """
    The ID of the chain on which this transaction is executed.
    """

    nonce_keys: Tuple[U256, ...]
    """
    The nonce domains the transaction consumes, sharing one
    [`nonce_seq`][ns].

    [`LEGACY_NONCE_KEYS`][lnk] selects the [`sender`][s]'s account nonce;
    any other set selects independent sequences held by the nonce
    manager (see [`current_nonce_seq`][cns]).

    [ns]: ref:ethereum.forks.bogota.transactions.frame_transaction.FrameTransaction.nonce_seq
    [lnk]: ref:ethereum.forks.bogota.transactions.frame_transaction.LEGACY_NONCE_KEYS
    [s]: ref:ethereum.forks.bogota.transactions.frame_transaction.FrameTransaction.sender
    [cns]: ref:ethereum.forks.bogota.keyed_nonces.current_nonce_seq
    """  # noqa: E501

    nonce_seq: U64
    """
    The sequence number every selected nonce key must currently hold.
    """

    sender: Address
    """
    Address of the account intended to be the sender of the transaction.
    """

    frames: Tuple[Frame, ...]
    """
    List of frames to execute.
    """

    signatures: Tuple[FrameSignature, ...]
    """
    Validated signatures available to the transaction.

    The `signatures` list contains signatures that may be referenced by
    [`VERIFY`][v] frames and by ordinary EVM execution. Every signature in the
    list must validate successfully before any [`Frame`] is executed. If any
    signature is malformed or invalid, the whole transaction is invalid.

    [v]: ref:ethereum.forks.bogota.transactions.frame_transaction.FrameMode.VERIFY
    [`Frame`]: ref:ethereum.forks.bogota.transactions.frame_transaction.Frame
    """  # noqa: E501

    fees: TransactionFees
    """
    The transaction's fee parameters.
    """

    blob_versioned_hashes: Tuple[VersionedHash, ...]
    """
    A tuple of objects that represent the versioned hashes of the blobs
    included in the transaction.
    """


def resolve_frame_target(tx: FrameTransaction, frame: Frame) -> Address:
    """
    Resolve the account a frame executes at: an empty `to` resolves to
    the transaction's sender in every mode.
    """
    if isinstance(frame.to, Bytes0):
        return tx.sender
    return frame.to


def compute_frame_signature_hash(tx: FrameTransaction) -> Hash32:
    """
    Compute the canonical signature hash of a frame transaction.

    The raw `signature` bytes of every entry with an empty `msg` are
    elided before hashing, since a signature over the canonical hash
    cannot commit to its own bytes.
    """
    elided_signatures = []
    for signature in tx.signatures:
        if len(signature.message) == 0:
            elided_signatures.append(replace(signature, signature=Bytes(b"")))
        else:
            elided_signatures.append(signature)

    elided_tx = replace(tx, signatures=tuple(elided_signatures))
    return keccak256(b"\x06" + rlp.encode(elided_tx))


def validate_signature(
    frame_signature: FrameSignature, sender: Address, sig_hash: Hash32
) -> Optional[Address]:
    """
    Validate a single [`FrameSignature`] entry and return the signer
    it resolved to.

    The entry's `message` selects what the signature authorizes: empty
    means the canonical signature hash `sig_hash` (see
    [`compute_frame_signature_hash`][csh]), while a 32-byte value is an
    explicit digest. The all-zero digest is invalid, reserving the zero
    stack value as the EVM-visible representation of the canonical-hash
    case.

    An empty `signer` resolves to `sender`. For the protocol-validated
    schemes ([`SECP256K1`][k1] and [`P256`][p256]) the raw signature
    bytes must be canonical — one unique encoding per signature, with
    low-`s` — and must authenticate the resolved signer. The protocol
    does not cryptographically validate [`ARBITRARY`][arb] entries and
    assigns them no resolved signer — `None` is returned — so their
    `signer` must be empty.

    [`FrameSignature`]: ref:ethereum.forks.bogota.transactions.frame_transaction.FrameSignature
    [csh]: ref:ethereum.forks.bogota.transactions.frame_transaction.compute_frame_signature_hash
    [k1]: ref:ethereum.forks.bogota.transactions.frame_transaction.FrameSignatureScheme.SECP256K1
    [p256]: ref:ethereum.forks.bogota.transactions.frame_transaction.FrameSignatureScheme.P256
    [arb]: ref:ethereum.forks.bogota.transactions.frame_transaction.FrameSignatureScheme.ARBITRARY
    """  # noqa: E501
    signature_scheme = frame_signature.scheme
    signer = frame_signature.signer
    signature = frame_signature.signature

    if len(frame_signature.message) == 0:
        message = sig_hash
    elif len(frame_signature.message) == 32:
        if frame_signature.message == b"\0" * 32:
            raise InvalidFrameError(
                "frame signature message cannot be all zeros"
            )
        message = Hash32(frame_signature.message)
    else:
        raise InvalidFrameError("Invalid signature message length")

    if len(signer) not in [0, Address.LENGTH]:
        raise InvalidFrameError("invalid frame signer length")
    resolved_signer: Bytes
    if len(signer) == 0:
        resolved_signer = sender
    else:
        resolved_signer = signer

    match signature_scheme:
        case FrameSignatureScheme.SECP256K1:
            if len(signature) != 65:
                raise InvalidSignatureError(
                    "SECP256K1 signature must be 65 bytes"
                )

            v = U256(signature[0])
            r = U256.from_be_bytes(signature[1:33])
            s = U256.from_be_bytes(signature[33:65])
            if v not in (U256(0), U256(1)):
                raise InvalidSignatureError("bad v in secp256k1 scheme")
            if U256(0) >= r or r >= SECP256K1N:
                raise InvalidSignatureError("bad r in secp256k1 scheme")
            if U256(0) >= s or s > SECP256K1N // U256(2):
                raise InvalidSignatureError("bad s in secp256k1 scheme")

            public_key = secp256k1_recover(r, s, v, message)

            if resolved_signer != keccak256(public_key)[12:]:
                raise InvalidFrameError(
                    "signer does not match in secp256k1 scheme"
                )

            return Address(resolved_signer)

        case FrameSignatureScheme.P256:
            if len(signature) != 128:
                raise InvalidSignatureError("P256 signature must be 128 bytes")

            r = U256.from_be_bytes(signature[0:32])
            s = U256.from_be_bytes(signature[32:64])
            qx = U256.from_be_bytes(signature[64:96])
            qy = U256.from_be_bytes(signature[96:128])

            if U256(0) >= r or r >= SECP256R1N:
                raise InvalidSignatureError("bad r in p256 scheme")
            if U256(0) >= s or s > SECP256R1N // U256(2):
                raise InvalidSignatureError("bad s in p256 scheme")
            if resolved_signer != keccak256(signature[64:128])[12:]:
                raise InvalidFrameError("signer does not match in p256 scheme")
            try:
                secp256r1_verify(r, s, qx, qy, message)
            except ValueError as e:
                raise InvalidSignatureError("invalid p256 public key") from e

            return Address(resolved_signer)

        case FrameSignatureScheme.ARBITRARY:
            if len(signer) != 0:
                raise InvalidFrameError(
                    "signer length should be zero for arbitrary schemes"
                )
            return None
        case _ as unreachable:
            assert_never(unreachable)


@final
@dataclass
class FrameTransactionValidation:
    """
    Everything the static validation of a frame transaction
    establishes: its intrinsic gas cost, its two gas anchors, and the
    signature artifacts retained for execution.
    """

    intrinsic: "IntrinsicGasCost"
    """
    The transaction's intrinsic gas cost.
    """

    standard_gas_limit: Uint
    """
    Settlement anchor: the intrinsic execution gas cost plus the sum
    of the frames' gas budgets in both dimensions.
    """

    max_gas: Uint
    """
    Inclusion anchor: the larger of `standard_gas_limit` and the
    calldata floor plus the frames' total state gas budget.
    """

    signature_hash: Hash32
    """
    The transaction's canonical signature hash.
    """

    resolved_signers: Tuple[Optional[Address], ...]
    """
    The signer each signature entry resolved to; `None` for
    `ARBITRARY` entries, to which the protocol assigns no signer.
    """


def validate_frame_transaction(
    tx: FrameTransaction,
) -> FrameTransactionValidation:
    """
    Check the statically determinable validity constraints of a frame
    transaction and derive its gas anchors.

    Constraints on individual fields — frame modes and flags, signature
    schemes, and field lengths — are mostly enforced by their types
    while the transaction is decoded. Checked here instead are the
    nonce and fee-cap upper bounds, which are tighter than the decoded
    types enforce, and the constraints that span several fields.

    A frame transaction has no gas limit field; its two gas anchors are
    derived instead. The per-transaction gas cap of [EIP-7825] bounds
    the transaction's execution dimension — the larger of its intrinsic
    cost plus the frames' execution gas budgets and its calldata floor —
    while state gas budgets are exempt from the cap.

    [EIP-7825]: https://eips.ethereum.org/EIPS/eip-7825
    """
    from ..vm.gas import GasCosts
    from . import BLOB_COUNT_LIMIT, VERSIONED_HASH_VERSION_KZG

    if tx.nonce_seq >= MAX_NONCE_SEQ:
        raise NonceOverflowError("Nonce too high")
    validate_nonce_keys(tx.nonce_keys)

    if tx.fees.max_fee_per_gas > Uint(U256.MAX_VALUE):
        raise FeeOverflowError("Max fee per gas too high")
    if tx.fees.max_priority_fee_per_gas > Uint(U256.MAX_VALUE):
        raise FeeOverflowError("Max priority fee per gas too high")

    if tx.fees.max_fee_per_gas < tx.fees.max_priority_fee_per_gas:
        raise PriorityFeeGreaterThanMaxFeeError(
            "priority fee greater than max fee"
        )

    blob_count = len(tx.blob_versioned_hashes)
    if blob_count == 0 and tx.fees.max_fee_per_blob_gas != U256(0):
        raise InvalidMaxFeePerBlobGasError(
            "max fee per blob gas must be zero without blobs"
        )
    if blob_count > BLOB_COUNT_LIMIT:
        raise BlobCountExceededError(
            f"Tx has {blob_count} blobs. Max allowed: {BLOB_COUNT_LIMIT}"
        )
    for blob_versioned_hash in tx.blob_versioned_hashes:
        if blob_versioned_hash[0:1] != VERSIONED_HASH_VERSION_KZG:
            raise InvalidBlobVersionedHashError("invalid blob versioned hash")

    frame_count = ulen(tx.frames)
    if frame_count < Uint(1) or frame_count > MAX_FRAMES_PER_TX:
        raise FrameCountError(actual=frame_count, maximum=MAX_FRAMES_PER_TX)

    signature_hash = compute_frame_signature_hash(tx)
    resolved_signers = tuple(
        validate_signature(signature, tx.sender, signature_hash)
        for signature in tx.signatures
    )

    has_expiry_verifier_frame = False
    total_frame_gas = Uint(0)
    total_frame_execution_gas = Uint(0)
    total_frame_state_gas = Uint(0)
    for index, frame in enumerate(tx.frames):
        total_frame_execution_gas += Uint(frame.gas_limits.execution)
        total_frame_state_gas += Uint(frame.gas_limits.state)
        total_frame_gas += Uint(frame.gas_limits.execution) + Uint(
            frame.gas_limits.state
        )
        if total_frame_gas > Uint(U64.MAX_VALUE):
            raise InvalidFrameError("total frame gas overflows")

        if frame.mode != FrameMode.SENDER and frame.value != U256(0):
            raise InvalidFrameError("only sender frames can transfer value")

        if FrameFlag.APPROVE_EXECUTION in frame.flags:
            if isinstance(frame.to, Address) and frame.to != tx.sender:
                raise InvalidFrameError(
                    "approve execution frame must target sender"
                )

        if FrameFlag.ATOMIC_BATCH in frame.flags:
            if frame.mode == FrameMode.VERIFY:
                raise InvalidFrameError(
                    "atomic batches cannot contain verify frames"
                )
            if index + 1 >= len(tx.frames):
                raise InvalidFrameError("last frame cannot have atomic flag")
            if tx.frames[index + 1].mode == FrameMode.VERIFY:
                raise InvalidFrameError(
                    "atomic batches cannot contain verify frames"
                )

        # Approval scope is disallowed on every frame of an atomic
        # batch, including its terminating frame. A frame belongs to a
        # batch when it or its predecessor carries the flag. Keeping the
        # approval context constant across a batch means unrolling one
        # can never withdraw an execution approval that later SENDER
        # frames rely on, and whether the transaction sets a payer never
        # depends on a batch outcome.
        in_batch = FrameFlag.ATOMIC_BATCH in frame.flags or (
            index > 0 and FrameFlag.ATOMIC_BATCH in tx.frames[index - 1].flags
        )
        if in_batch and frame.flags & APPROVE_SCOPE_MASK != FrameFlag(0):
            raise InvalidFrameError(
                "atomic batch frames cannot carry approval scope"
            )

        if frame.mode == FrameMode.VERIFY and frame.to == EXPIRY_VERIFIER:
            if has_expiry_verifier_frame:
                raise InvalidFrameError("multiple expiry verifier frames")
            has_expiry_verifier_frame = True
            if frame.flags != FrameFlag(0):
                raise InvalidFrameError("expiry verifier frame with flags")
            if frame.value != U256(0):
                raise InvalidFrameError("expiry verifier frame with value")
            if frame.gas_limits.state != U64(0):
                raise InvalidFrameError("expiry verifier frame with state gas")
            if len(frame.data) != EXPIRY_DATA_LENGTH:
                raise InvalidFrameError(
                    "expiry verifier frame data must be an expiry timestamp"
                )

    intrinsic = calculate_frame_transaction_intrinsic_cost(tx)
    standard_gas_limit = Uint(intrinsic.execution) + total_frame_gas
    max_gas = max(
        standard_gas_limit,
        Uint(intrinsic.calldata_floor) + total_frame_state_gas,
    )

    # The per-transaction gas cap of EIP-7825 bounds the execution
    # dimension alone: the intrinsic cost plus the frames' execution
    # budgets, with the calldata floor checked against the same cap.
    # State gas is bounded only by the encoding limit and the block's
    # state gas capacity.
    execution_gas_cap_usage = max(
        Uint(intrinsic.execution) + total_frame_execution_gas,
        Uint(intrinsic.calldata_floor),
    )
    if execution_gas_cap_usage > GasCosts.TX_MAX_GAS_LIMIT:
        raise TransactionGasLimitExceededError(
            "Derived execution gas limit exceeds TX_MAX_GAS_LIMIT"
        )

    return FrameTransactionValidation(
        intrinsic=intrinsic,
        standard_gas_limit=standard_gas_limit,
        max_gas=max_gas,
        signature_hash=signature_hash,
        resolved_signers=resolved_signers,
    )


def validate_nonce_keys(nonce_keys: Tuple[U256, ...]) -> None:
    """
    Check that a transaction selects a well-formed set of nonce keys.

    The set holds between one and [`MAX_NONCE_KEYS`][mnk] keys in
    strictly increasing order, so each set has one canonical encoding.
    The zero key aliases the sender's account nonce and may only appear
    alone, as [`LEGACY_NONCE_KEYS`][lnk].

    [mnk]: ref:ethereum.forks.bogota.transactions.frame_transaction.MAX_NONCE_KEYS
    [lnk]: ref:ethereum.forks.bogota.transactions.frame_transaction.LEGACY_NONCE_KEYS
    """  # noqa: E501
    key_count = ulen(nonce_keys)
    if key_count < Uint(1) or key_count > MAX_NONCE_KEYS:
        raise InvalidFrameError("invalid nonce key count")
    for previous, key in zip(nonce_keys, nonce_keys[1:], strict=False):
        if key <= previous:
            raise InvalidFrameError("nonce keys not strictly increasing")
    if U256(0) in nonce_keys and nonce_keys != LEGACY_NONCE_KEYS:
        raise InvalidFrameError("zero nonce key alongside other keys")


def nonce_keys_hash(tx: FrameTransaction) -> Hash32:
    """
    Return the commitment to the transaction's nonce key set exposed to
    the EVM: the hash of the key count followed by every key, each as a
    32-byte big-endian word.
    """
    words = [U256(len(tx.nonce_keys)).to_be_bytes32()]
    words.extend(nonce_key.to_be_bytes32() for nonce_key in tx.nonce_keys)
    return keccak256(b"".join(words))


def nonce_calldata(tx: FrameTransaction) -> Bytes:
    """
    Return the encoding of the transaction's nonce fields, which is
    priced as transaction data.
    """
    return rlp.encode(tx.nonce_keys) + rlp.encode(tx.nonce_seq)


def signature_verification_gas(signature: FrameSignature) -> ExecutionGas:
    """
    Return the gas charged for validating a single signature entry.
    """
    from ..vm.gas import GasCosts

    match signature.scheme:
        case FrameSignatureScheme.SECP256K1:
            return GasCosts.FRAME_SIGNATURE_SCHEME_SECP256K1
        case FrameSignatureScheme.P256:
            return GasCosts.FRAME_SIGNATURE_SCHEME_P256
        case FrameSignatureScheme.ARBITRARY:
            return GasCosts.FRAME_SIGNATURE_SCHEME_ARBITRARY
        case _ as unreachable:
            assert_never(unreachable)


def calculate_frame_transaction_intrinsic_cost(
    tx: FrameTransaction,
) -> "IntrinsicGasCost":
    """
    Calculate the gas that is charged to the payer of a frame transaction
    before execution is started.

    The intrinsic cost is the base cost, the per-frame cost, the calldata
    cost of the byte fields priced as calldata — the `data` of each
    frame, the `signer`, `message`, and `signature` bytes of each
    signature entry, and the encoding of the nonce fields (see
    [`nonce_calldata`][nc]) — the signature verification cost, and the value transfer cost
    of each value-bearing frame with an explicit target other than the
    sender, covering the recipient balance write and transfer log.
    Unlike other transaction types, there is no recipient component:
    target access is paid during frame execution from each frame's own
    execution gas budget.

    The calldata floor of [EIP-7976] counts every charged byte uniformly
    and is anchored on the costs the transaction always pays regardless
    of execution — the base cost, the per-frame cost, the signature
    verification cost, and the value transfer cost — so it never
    undercuts the transaction's own intrinsic base.

    [EIP-7976]: https://eips.ethereum.org/EIPS/eip-7976
    [nc]: ref:ethereum.forks.bogota.transactions.frame_transaction.nonce_calldata
    """  # noqa: E501
    from ..vm.gas import GasCosts
    from . import IntrinsicGasCost, count_tokens_in_data

    nonce_data = nonce_calldata(tx)
    tokens = count_tokens_in_data(nonce_data)
    data_length = ulen(nonce_data)
    value_transfer_gas = Uint(0)
    for frame in tx.frames:
        tokens += count_tokens_in_data(frame.data)
        data_length += ulen(frame.data)
        if (
            frame.value > U256(0)
            and isinstance(frame.to, Address)
            and frame.to != tx.sender
        ):
            value_transfer_gas += GasCosts.TX_VALUE_COST

    signature_gas = Uint(0)
    for signature in tx.signatures:
        signature_gas += signature_verification_gas(signature)
        for data in (
            signature.signer,
            signature.message,
            signature.signature,
        ):
            tokens += count_tokens_in_data(data)
            data_length += ulen(data)

    # EIP-7976 floor tokens: all charged bytes count uniformly.
    floor_tokens = data_length * GasCosts.TX_DATA_TOKEN_STANDARD

    base_execution_gas = (
        GasCosts.TX_FRAME_INTRINSIC
        + ulen(tx.frames) * GasCosts.TX_PER_FRAME
        + signature_gas
        + value_transfer_gas
    )

    return IntrinsicGasCost(
        execution=ExecutionGas(
            base_execution_gas + tokens * GasCosts.TX_DATA_TOKEN_STANDARD
        ),
        calldata_floor=ExecutionGas(
            base_execution_gas + floor_tokens * GasCosts.TX_DATA_TOKEN_FLOOR
        ),
    )
