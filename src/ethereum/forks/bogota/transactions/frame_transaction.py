"""
Frame transactions, the transaction type introduced in [EIP-8141].

A frame transaction expresses validity conditions, gas payment, and
execution as an explicit list of [`Frame`]s, each a unit of execution
with its own mode, target, and gas limit. Next to the frames, a list of
declarative [`Claim`]s names what must have been verified before any
frame executes. The witnesses that satisfy the claims are segregated:
they are not part of the transaction, but travel in the block's
dependency proof.

[EIP-8141]: https://eips.ethereum.org/EIPS/eip-8141
[`Frame`]: ref:ethereum.forks.bogota.transactions.frame_transaction.Frame
[`Claim`]: ref:ethereum.forks.bogota.transactions.frame_transaction.Claim
"""  # noqa: E501

from dataclasses import dataclass
from enum import STRICT
from typing import TYPE_CHECKING, Final, Optional, Tuple, final

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes, Bytes0, Bytes32
from ethereum_types.enum import UintEnum, UintFlag
from ethereum_types.frozen import slotted_freezable
from ethereum_types.numeric import U64, U256, Uint, ulen

from ethereum.crypto.hash import Hash32, keccak256
from ethereum.exceptions import NonceOverflowError
from ethereum.state import Address

from ..exceptions import (
    BlobCountExceededError,
    FeeOverflowError,
    FrameCountError,
    InvalidBlobVersionedHashError,
    InvalidFrameError,
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

MAX_CLAIMS_PER_TX: Final[Uint] = Uint(64)
"""
Maximum number of [`Claim`]s allowed per [`FrameTransaction`][ftx].

[`Claim`]: ref:ethereum.forks.bogota.transactions.frame_transaction.Claim
[ftx]: ref:ethereum.forks.bogota.transactions.frame_transaction.FrameTransaction
"""  # noqa: E501

MAX_CLAIM_WITNESS_BYTES: Final[Uint] = Uint(1048576)
"""
Maximum `witness_len` of a [`Claim`] verified by a custom contract
verifier.

[`Claim`]: ref:ethereum.forks.bogota.transactions.frame_transaction.Claim
"""  # noqa: E501

SECP256K1_VERIFIER: Final[Address] = Address(
    bytes.fromhex("00000000000000000000000000000000000081a1")
)
"""
Reserved address of the claim-only protocol verifier of secp256k1
signatures. Its witness is `v || r || s`.

The address is not a callable precompile: calling it from EVM code
behaves as calling an account without code. [EIP-8141] leaves it to be
assigned; this placeholder lies outside the active precompile range
and the range reserved for RIPs.

[EIP-8141]: https://eips.ethereum.org/EIPS/eip-8141
"""

P256_VERIFIER: Final[Address] = Address(
    bytes.fromhex("00000000000000000000000000000000000081a2")
)
"""
Reserved address of the claim-only protocol verifier of NIST P-256
signatures. Its witness is `r || s || qx || qy`. Placeholder address,
as for [`SECP256K1_VERIFIER`][k1].

[k1]: ref:ethereum.forks.bogota.transactions.frame_transaction.SECP256K1_VERIFIER
"""  # noqa: E501

LEANSPHINCS_VERIFIER: Final[Address] = Address(
    bytes.fromhex("00000000000000000000000000000000000081a3")
)
"""
Reserved address of the claim-only protocol verifier of leanSPHINCS
signatures. Its witness is the signature itself. Placeholder address,
as for [`SECP256K1_VERIFIER`][k1].

[k1]: ref:ethereum.forks.bogota.transactions.frame_transaction.SECP256K1_VERIFIER
"""  # noqa: E501

SECP256K1_WITNESS_LENGTH: Final[Uint] = Uint(65)
"""
Length of a [`SECP256K1_VERIFIER`][k1] witness: `v || r || s`.

[k1]: ref:ethereum.forks.bogota.transactions.frame_transaction.SECP256K1_VERIFIER
"""  # noqa: E501

P256_WITNESS_LENGTH: Final[Uint] = Uint(128)
"""
Length of a [`P256_VERIFIER`][p] witness: `r || s || qx || qy`.

[p]: ref:ethereum.forks.bogota.transactions.frame_transaction.P256_VERIFIER
"""  # noqa: E501

LEANSPHINCS_SIGNATURE_SIZE: Final[Uint] = Uint(7740)
"""
Length of a leanSPHINCS signature, the
[`LEANSPHINCS_VERIFIER`][l] witness.

[l]: ref:ethereum.forks.bogota.transactions.frame_transaction.LEANSPHINCS_VERIFIER
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
@slotted_freezable
@dataclass
class Claim:
    """
    A declarative claim of a [`FrameTransaction`][ftx]: the verifier at
    `verifier` attests that the resolved key authorizes the resolved
    message.

    Every claim must be satisfied by its segregated witness before any
    frame executes. Frames test for a claim with the `HASCLAIM`
    instruction; the witness bytes are never readable by EVM code.

    [ftx]: ref:ethereum.forks.bogota.transactions.frame_transaction.FrameTransaction
    """  # noqa: E501

    verifier: Address
    """
    The verifier that checks the claim's witness: a reserved protocol
    verifier, an active precompile, or a deployed non-delegated
    contract.
    """

    key: Bytes
    """
    The signing key or proven program. Empty resolves to the
    transaction's sender; a non-zero 20-byte value is left-padded to 32
    bytes; a non-zero 32-byte value is used directly.
    """

    msg: Bytes0 | Bytes32
    """
    Either empty, indicating the canonical transaction signature hash, or
    an explicit non-zero 32-byte digest.
    """

    gas_limit: U64
    """
    Execution gas a custom contract verifier is given, charged in full.
    Zero for protocol verifiers, whose gas is fixed.
    """

    witness_len: U64
    """
    Exact length of the witness of a custom contract verifier. Zero for
    protocol verifiers, whose witness length is fixed.
    """


@final
@dataclass(frozen=True, order=True)
class Dependency:
    """
    A [`Claim`] resolved against its transaction: the tuple a witness
    must satisfy.

    Dependencies are what a block's dependency proof carries witnesses
    for. They are compared as tuples, so two claims with the same
    resolved fields share one witness.

    [`Claim`]: ref:ethereum.forks.bogota.transactions.frame_transaction.Claim
    """  # noqa: E501

    verifier: Address
    """
    The verifier that checks the witness.
    """

    key: Bytes32
    """
    The resolved key.
    """

    msg: Hash32
    """
    The resolved message: the explicit digest, or the transaction's
    canonical signature hash.
    """

    gas_limit: Uint
    """
    The resolved verification gas.
    """

    witness_len: Uint
    """
    The resolved witness length.
    """


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

    max_fee: Uint
    """
    The maximum total fee, in wei, that the sender is willing to pay for
    all of the transaction's execution, state, and blob gas.
    """

    max_priority_fee_per_gas: Uint
    """
    The priority fee per gas that the sender is willing to pay.
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

    nonce: U256
    """
    A scalar value equal to the number of transactions sent by the
    [`sender`][s].

    [s]: ref:ethereum.forks.bogota.transactions.frame_transaction.FrameTransaction.sender
    """  # noqa: E501

    sender: Address
    """
    Address of the account intended to be the sender of the transaction.
    """

    claims: Tuple[Claim, ...]
    """
    Declarative claims whose segregated witnesses must verify before any
    [`Frame`] executes.

    [`Frame`]: ref:ethereum.forks.bogota.transactions.frame_transaction.Frame
    """  # noqa: E501

    frames: Tuple[Frame, ...]
    """
    List of frames to execute.
    """

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

    The transaction carries no witness bytes, so the hash covers it
    whole. The `0x00` byte after the type separates it from the
    transaction hash, so a signature over the transaction hash cannot be
    replayed as an authorization of the transaction.
    """
    return keccak256(b"\x06\x00" + rlp.encode(tx))


def protocol_verifier_parameters(
    verifier: Address,
) -> Optional[Tuple[ExecutionGas, Uint]]:
    """
    Return the fixed verification gas and witness length of a protocol
    verifier, or `None` when `verifier` is not one.
    """
    from ..vm.gas import GasCosts

    if verifier == SECP256K1_VERIFIER:
        return GasCosts.SECP256K1_VERIFICATION, SECP256K1_WITNESS_LENGTH
    if verifier == P256_VERIFIER:
        return GasCosts.P256_VERIFICATION, P256_WITNESS_LENGTH
    if verifier == LEANSPHINCS_VERIFIER:
        return GasCosts.LEANSPHINCS_VERIFICATION, LEANSPHINCS_SIGNATURE_SIZE
    return None


def resolve_claim_key(claim: Claim, sender: Address) -> Bytes32:
    """
    Resolve a claim's `key` to 32 bytes: empty resolves to `sender`, a
    20-byte key is left-padded, and a 32-byte key is used directly. A
    zero key, or a key of any other length, is invalid.
    """
    if len(claim.key) == 0:
        return Bytes32(sender.rjust(32, b"\x00"))
    if len(claim.key) == Address.LENGTH:
        if claim.key == b"\x00" * Address.LENGTH:
            raise InvalidFrameError("claim key cannot be zero")
        return Bytes32(claim.key.rjust(32, b"\x00"))
    if len(claim.key) == 32:
        if claim.key == b"\x00" * 32:
            raise InvalidFrameError("claim key cannot be zero")
        return Bytes32(claim.key)
    raise InvalidFrameError("invalid claim key length")


def resolve_claim_gas(claim: Claim) -> ExecutionGas:
    """
    Return the gas charged for verifying a claim: fixed for a protocol
    verifier, the claim's `gas_limit` for a custom one.
    """
    parameters = protocol_verifier_parameters(claim.verifier)
    if parameters is not None:
        return parameters[0]
    return ExecutionGas(Uint(claim.gas_limit))


def resolve_witness_length(claim: Claim) -> Uint:
    """
    Return the length of a claim's witness: fixed for a protocol
    verifier, the claim's `witness_len` for a custom one.
    """
    parameters = protocol_verifier_parameters(claim.verifier)
    if parameters is not None:
        return parameters[1]
    return Uint(claim.witness_len)


def resolve_dependency(
    claim: Claim, sender: Address, sig_hash: Hash32
) -> Dependency:
    """
    Resolve a claim into the [`Dependency`] its witness must satisfy. An
    empty `msg` resolves to the canonical signature hash `sig_hash`.

    [`Dependency`]: ref:ethereum.forks.bogota.transactions.frame_transaction.Dependency
    """  # noqa: E501
    if len(claim.msg) == 0:
        msg = sig_hash
    elif len(claim.msg) == 32:
        msg = Hash32(claim.msg)
    else:
        raise InvalidFrameError("invalid claim msg length")
    return Dependency(
        verifier=claim.verifier,
        key=resolve_claim_key(claim, sender),
        msg=msg,
        gas_limit=Uint(resolve_claim_gas(claim)),
        witness_len=resolve_witness_length(claim),
    )


def has_claim(
    tx: FrameTransaction, verifier: Address, key: Bytes32, msg: Bytes32
) -> bool:
    """
    Check whether the transaction declares a claim by `verifier` whose
    resolved key is `key` and whose message is `msg`, where a zero `msg`
    stands for the canonical signature hash, i.e. an empty claim `msg`.
    """
    for claim in tx.claims:
        if claim.verifier != verifier:
            continue
        if resolve_claim_key(claim, tx.sender) != key:
            continue
        if msg == b"\x00" * 32:
            if len(claim.msg) == 0:
                return True
        elif claim.msg == msg:
            return True
    return False


@final
@dataclass
class FrameTransactionValidation:
    """
    Everything the static validation of a frame transaction
    establishes: its intrinsic gas cost, its two gas anchors, its
    canonical signature hash, and the dependencies its claims resolve
    to.
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

    dependencies: Tuple[Dependency, ...]
    """
    The dependency each claim resolved to, in claim order.
    """


def validate_frame_transaction(
    tx: FrameTransaction,
) -> FrameTransactionValidation:
    """
    Check the statically determinable validity constraints of a frame
    transaction and derive its gas anchors.

    Constraints on individual fields — frame modes and flags, and
    field lengths — are mostly enforced by their types
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

    if tx.nonce >= U256(U64.MAX_VALUE):
        raise NonceOverflowError("Nonce too high")

    if tx.fees.max_fee > Uint(U256.MAX_VALUE):
        raise FeeOverflowError("Max fee too high")
    if tx.fees.max_priority_fee_per_gas > Uint(U256.MAX_VALUE):
        raise FeeOverflowError("Max priority fee per gas too high")

    blob_count = len(tx.blob_versioned_hashes)
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

    if ulen(tx.claims) > MAX_CLAIMS_PER_TX:
        raise InvalidFrameError("too many claims")

    signature_hash = compute_frame_signature_hash(tx)
    total_claim_gas = Uint(0)
    for claim in tx.claims:
        resolved_key = resolve_claim_key(claim, tx.sender)
        if claim.verifier in (SECP256K1_VERIFIER, P256_VERIFIER):
            if resolved_key[:12] != b"\x00" * 12:
                raise InvalidFrameError("claim key must be an address")
        if len(claim.msg) == 32:
            if claim.msg == b"\x00" * 32:
                raise InvalidFrameError("claim msg cannot be zero")
        elif len(claim.msg) != 0:
            raise InvalidFrameError("invalid claim msg length")

        if protocol_verifier_parameters(claim.verifier) is not None:
            if claim.gas_limit != U64(0) or claim.witness_len != U64(0):
                raise InvalidFrameError(
                    "protocol verifier claim with gas limit or witness length"
                )
        else:
            if claim.gas_limit == U64(0):
                raise InvalidFrameError("custom verifier claim without gas")
            if Uint(claim.witness_len) > MAX_CLAIM_WITNESS_BYTES:
                raise InvalidFrameError("claim witness too long")

        total_claim_gas += Uint(resolve_claim_gas(claim))
        if total_claim_gas > Uint(U64.MAX_VALUE):
            raise InvalidFrameError("total claim gas overflows")

    dependencies = tuple(
        resolve_dependency(claim, tx.sender, signature_hash)
        for claim in tx.claims
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
        dependencies=dependencies,
    )


def calculate_frame_transaction_intrinsic_cost(
    tx: FrameTransaction,
) -> "IntrinsicGasCost":
    """
    Calculate the gas that is charged to the payer of a frame transaction
    before execution is started.

    The intrinsic cost is the base cost, the per-frame cost, the calldata
    cost of the byte fields priced as calldata — the `data` of each frame
    and the `verifier`, `key`, and `msg` bytes of each claim — the claim
    verification cost, the witness cost, and the value transfer cost of
    each value-bearing frame with an explicit target other than the
    sender, covering the recipient balance write and transfer log.
    Witnesses are not part of the transaction, so they are priced by
    their resolved length, as calldata whose bytes are all non-zero.
    Unlike other transaction types, there is no recipient component:
    target access is paid during frame execution from each frame's own
    execution gas budget.

    The calldata floor of [EIP-7976] counts every charged byte uniformly
    and is anchored on the costs the transaction always pays regardless
    of execution — the base cost, the per-frame cost, the claim
    verification cost, and the value transfer cost — so it never
    undercuts the transaction's own intrinsic base.

    [EIP-7976]: https://eips.ethereum.org/EIPS/eip-7976
    """
    from ..vm.gas import GasCosts
    from . import IntrinsicGasCost, count_tokens_in_data

    tokens = Uint(0)
    data_length = Uint(0)
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

    claim_gas = Uint(0)
    for claim in tx.claims:
        claim_gas += resolve_claim_gas(claim)
        for data in (claim.verifier, claim.key, claim.msg):
            tokens += count_tokens_in_data(data)
            data_length += ulen(data)
        witness_length = resolve_witness_length(claim)
        tokens += witness_length * Uint(4)
        data_length += witness_length

    # EIP-7976 floor tokens: all charged bytes count uniformly.
    floor_tokens = data_length * Uint(4)

    base_execution_gas = (
        GasCosts.TX_FRAME_INTRINSIC
        + ulen(tx.frames) * GasCosts.TX_PER_FRAME
        + claim_gas
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
