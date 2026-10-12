"""
Classify and replay frame transactions for inclusion-list eligibility.

Candidate classification and protocol signatures are separate so an inclusion
list charges its signature budget before cryptographic verification. Replay
uses an isolated insertion state, executes complete validation frames, and
never incorporates their effects into the payload.
"""

from dataclasses import dataclass, field, replace
from typing import Dict, Optional, Set, final

from ethereum_types.bytes import Bytes, Bytes32
from ethereum_types.numeric import U256, Uint

from ethereum.crypto.hash import Hash32, keccak256
from ethereum.exceptions import EthereumException
from ethereum.state import EMPTY_CODE_HASH, Address

from .exceptions import InvalidFrameError
from .frame_processing import check_frame_transaction
from .state_tracker import get_account, get_code
from .transactions.frame_transaction import (
    APPROVE_SCOPE_MASK,
    EXPIRY_VERIFIER,
    RECENT_ROOT_ADDRESS,
    FrameFlag,
    FrameMode,
    FrameStatus,
    FrameTransaction,
    FrameTransactionValidation,
    resolve_frame_target,
    signature_verification_gas,
    validate_frame_transaction,
    validate_signature,
)
from .vm import BlockEnvironment, BlockOutput, Evm
from .vm.frame_interpreter import process_frames
from .vm.instructions import Ops
from .vm.precompiled_contracts.mapping import PRE_COMPILED_CONTRACTS

MAX_VERIFY_GAS_PER_TX = Uint(2**18)
"""Maximum declared validation work for a frame candidate."""
AA_VOPS_SLOT_COUNT = U256(4)
"""Ordinary validation storage surface of each sender and payer."""
RECENT_ROOT_LENGTH = 8192
"""Number of recent-root entries per source."""
RECENT_ROOT_TUPLE_BYTES = 72
"""Encoded size of one recent-root reference."""
MAX_RECENT_ROOT_REFERENCES = 16
"""Maximum references in the canonical recent-root verifier frame."""
RECENT_ROOT_STORAGE_DOMAIN = keccak256(b"RECENT_ROOT_STORAGE")
"""Domain separating recent-root storage keys."""
EXPIRY_VERIFIER_CODE = bytes.fromhex(
    "60083614600a575f5ffd5b5f3560c01c4211601657005b5f5ffd"
)
"""Canonical expiry-verifier runtime specified by EIP-8141."""
RECENT_ROOT_CODE = bytes.fromhex(
    "346100ba57366040146100c05736604836066100ba5780156100ba57610480"
    "81116100ba574b60005b602081013560c01c828110156100ba578083036120"
    "0011156100ba577f8f42481679c8e6fefa040974b3c905e0ce3f2e464ba93a"
    "cdb074a41181617efc60005260488260203760686000207fbdc897da2177d2"
    "60ff5f4be5d4b2aad43f89c3347a305b584fa5a2546d053daa60005290611f"
    "ff1660c01b60405260486000205414156100ba5760480182811061002857005b"
    "60006000fd5b33600052602060006020376034600c20807f8f42481679c8e6"
    "fefa040974b3c905e0ce3f2e464ba93acdb074a41181617efc6040524b6068"
    "52606052602060206088376068604020817fbdc897da2177d260ff5f4be5d4"
    "b2aad43f89c3347a305b584fa5a2546d053daa60a852611fff4b1660d05260"
    "c852604860a8205500"
)
"""Canonical recent-root runtime specified by EIP-8272."""


@final
@dataclass(frozen=True)
class ReplayLimits:
    """
    Supply the enforcing fork's explicit code-loading limits.

    No consensus defaults are selected here: activation requires benchmarked
    bounds on both distinct code bodies and their combined encoded size.
    """

    max_code_bodies: int
    max_code_bytes: int

    def __post_init__(self) -> None:
        """
        Require an explicit positive bound in each code dimension.
        """
        if self.max_code_bodies <= 0 or self.max_code_bytes <= 0:
            raise ValueError("replay code limits must be positive")


@final
@dataclass
class FrameCandidate:
    """
    Retain a declared validation prefix and its separately verified signatures.
    """

    tx: FrameTransaction
    prefix_length: int
    signature_cost: Uint
    execution_cost: Uint
    validation: FrameTransactionValidation
    payer: Address
    deploy_index: Optional[int] = None
    expiry_index: Optional[int] = None
    recent_root_index: Optional[int] = None
    signatures_valid: Optional[bool] = None


def classify_frame_candidate(tx: FrameTransaction) -> Optional[FrameCandidate]:
    """
    Classify a canonically decoded frame transaction without signature checks.
    """
    try:
        validation = validate_frame_transaction(tx, verify_signatures=False)
    except EthereumException:
        return None
    if tx.blob_versioned_hashes:
        return None

    index = 0
    expiry_index = None
    recent_root_index = None
    deploy_index = None
    if tx.frames[index].to == EXPIRY_VERIFIER:
        frame = tx.frames[index]
        if frame.mode != FrameMode.VERIFY or frame.flags != FrameFlag(0):
            return None
        expiry_index = index
        index += 1
    if index < len(tx.frames) and tx.frames[index].to == RECENT_ROOT_ADDRESS:
        frame = tx.frames[index]
        if (
            frame.mode != FrameMode.VERIFY
            or frame.flags != FrameFlag(0)
            or frame.gas_limits.state != 0
            or not 1
            <= len(frame.data) // RECENT_ROOT_TUPLE_BYTES
            <= MAX_RECENT_ROOT_REFERENCES
            or len(frame.data) % RECENT_ROOT_TUPLE_BYTES != 0
        ):
            return None
        recent_root_index = index
        index += 1
    if index < len(tx.frames) and tx.frames[index].mode == FrameMode.DEFAULT:
        if tx.frames[index].flags != FrameFlag(0):
            return None
        deploy_index = index
        index += 1
    if index >= len(tx.frames):
        return None
    frame = tx.frames[index]
    if (
        frame.mode != FrameMode.VERIFY
        or resolve_frame_target(tx, frame) != tx.sender
    ):
        return None
    if frame.flags == APPROVE_SCOPE_MASK:
        payer = tx.sender
        index += 1
    elif frame.flags == FrameFlag.APPROVE_EXECUTION:
        index += 1
        if index >= len(tx.frames):
            return None
        frame = tx.frames[index]
        if (
            frame.mode != FrameMode.VERIFY
            or frame.flags != FrameFlag.APPROVE_PAYMENT
        ):
            return None
        payer = resolve_frame_target(tx, frame)
        index += 1
    else:
        return None
    if any(frame.mode == FrameMode.VERIFY for frame in tx.frames[index:]):
        return None
    signature_cost = Uint(
        sum(int(signature_verification_gas(sig)) for sig in tx.signatures)
    )
    execution_cost = Uint(
        sum(int(frame.gas_limits.execution) for frame in tx.frames[:index])
    )
    if signature_cost + execution_cost > MAX_VERIFY_GAS_PER_TX:
        return None
    return FrameCandidate(
        tx=tx,
        prefix_length=index,
        signature_cost=signature_cost,
        execution_cost=execution_cost,
        validation=validation,
        payer=payer,
        deploy_index=deploy_index,
        expiry_index=expiry_index,
        recent_root_index=recent_root_index,
    )


def verify_candidate_signatures(candidate: FrameCandidate) -> bool:
    """
    Verify protocol signatures once and retain the signers required by replay.
    """
    if candidate.signatures_valid is None:
        tx = candidate.tx
        try:
            signers = tuple(
                validate_signature(
                    sig, tx.sender, candidate.validation.signature_hash
                )
                for sig in tx.signatures
            )
        except EthereumException:
            candidate.signatures_valid = False
        else:
            candidate.validation = replace(
                candidate.validation, resolved_signers=signers
            )
            candidate.signatures_valid = True
    return candidate.signatures_valid


@final
@dataclass
class ValidationAccessTrace:
    """
    Enforce access restrictions independently of EVM state rollback.

    A violation aborts replay rather than raising an EVM exceptional halt that
    a calling contract could swallow. Missing state or code remains an external
    data error and is not converted into an eligibility failure.
    """

    candidate: FrameCandidate
    limits: ReplayLimits
    code_sizes: Dict[Hash32, int] = field(default_factory=dict)
    recent_root_slots: Set[Bytes32] = field(default_factory=set)

    def code_read(self, code_hash: Hash32, code: Optional[Bytes]) -> None:
        """
        Bound distinct code loads and require their authenticated contents.
        """
        if code_hash in self.code_sizes:
            return
        if len(self.code_sizes) >= self.limits.max_code_bodies:
            raise InvalidFrameError("validation code body count exceeded")
        if code is not None:
            if keccak256(code) != code_hash:
                raise ValueError("code does not match authenticated code hash")
            if (
                sum(self.code_sizes.values()) + len(code)
                > self.limits.max_code_bytes
            ):
                raise InvalidFrameError("validation code byte limit exceeded")
            self.code_sizes[code_hash] = len(code)

    def create(self, address: Address) -> None:
        """
        Permit deployment bookkeeping only for the transaction's sender.
        """
        if address != self.candidate.tx.sender:
            raise InvalidFrameError("validation deployment outside sender")

    def opcode(self, evm: Evm, opcode: int) -> None:
        """
        Check the attempted operation before it can read or modify state.
        """
        try:
            op = Ops(opcode)
        except ValueError as error:
            raise InvalidFrameError("invalid validation opcode") from error
        context = evm.tx_env.frame_context
        assert context is not None
        candidate = self.candidate
        index = int(context.current_frame_index)
        is_deploy = index == candidate.deploy_index
        is_expiry = (
            index == candidate.expiry_index
            and evm.depth == 0
            and evm.current_target == EXPIRY_VERIFIER
            and evm.code == EXPIRY_VERIFIER_CODE
        )
        is_recent_root = (
            index == candidate.recent_root_index
            and evm.depth == 0
            and evm.current_target == RECENT_ROOT_ADDRESS
            and evm.code == RECENT_ROOT_CODE
        )
        banned = {
            Ops.GASPRICE,
            Ops.BLOCKHASH,
            Ops.COINBASE,
            Ops.NUMBER,
            Ops.PREVRANDAO,
            Ops.GASLIMIT,
            Ops.BASEFEE,
            Ops.BLOBBASEFEE,
            Ops.SELFDESTRUCT,
            Ops.BALANCE,
            Ops.SELFBALANCE,
            Ops.TSTORE,
        }
        if op in banned:
            raise InvalidFrameError("banned validation opcode")
        if op == Ops.TIMESTAMP and not is_expiry:
            raise InvalidFrameError("timestamp outside canonical expiry")
        if op == Ops.SLOTNUM and not is_recent_root:
            raise InvalidFrameError("slot outside canonical recent root")
        calls = {Ops.CALL, Ops.CALLCODE, Ops.DELEGATECALL, Ops.STATICCALL}
        if op == Ops.GAS and (
            int(evm.pc) + 1 >= len(evm.code)
            or evm.code[int(evm.pc) + 1] not in {call.value for call in calls}
        ):
            raise InvalidFrameError("validation GAS not followed by a call")
        if op in (Ops.CREATE, Ops.CREATE2) and not is_deploy:
            raise InvalidFrameError("creation outside deploy frame")
        if op in (Ops.SLOAD, Ops.SSTORE) and evm.stack:
            slot = evm.stack[-1]
            ordinary = (
                evm.current_target in (candidate.tx.sender, candidate.payer)
                and slot < AA_VOPS_SLOT_COUNT
            )
            recent_root = (
                is_recent_root
                and slot.to_be_bytes32() in self.recent_root_slots
            )
            if op == Ops.SLOAD and not (ordinary or recent_root):
                raise InvalidFrameError(
                    "validation storage read outside surface"
                )
            if op == Ops.SSTORE and not (
                is_deploy
                and evm.current_target == candidate.tx.sender
                and slot < AA_VOPS_SLOT_COUNT
            ):
                raise InvalidFrameError(
                    "validation storage write outside sender"
                )
        if op in (Ops.CALL, Ops.CALLCODE) and len(evm.stack) >= 3:
            if evm.stack[-3] != 0:
                raise InvalidFrameError("validation call transfers value")
        target_word = None
        if op in calls and len(evm.stack) >= 2:
            target_word = evm.stack[-2]
        elif (
            op in (Ops.EXTCODESIZE, Ops.EXTCODECOPY, Ops.EXTCODEHASH)
            and evm.stack
        ):
            target_word = evm.stack[-1]
        if target_word is not None:
            target = Address((int(target_word) % 2**160).to_bytes(20, "big"))
            if (
                target not in PRE_COMPILED_CONTRACTS
                and target != candidate.tx.sender
                and get_account(evm.tx_env.state, target).code_hash
                == EMPTY_CODE_HASH
            ):
                raise InvalidFrameError("validation target has no code")


def replay_frame_candidate(
    block_env: BlockEnvironment,
    block_output: BlockOutput,
    candidate: FrameCandidate,
    index: Uint,
    limits: ReplayLimits,
) -> bool:
    """
    Execute a candidate's complete prefix on a disposable insertion state.

    The caller supplies the reconstructed state and cumulative dimensional gas
    before `index`. Only the transaction overlay changes; no receipt, gas total
    or state update is incorporated into the supplied block.
    """
    if candidate.signatures_valid is not True:
        return False
    tx = candidate.tx
    if tx.chain_id != block_env.chain_id:
        return False
    try:
        tx_env = check_frame_transaction(
            block_env, block_output, tx, index, candidate.validation
        )
        trace = ValidationAccessTrace(candidate, limits)
        tx_env.validation_opcode_hook = trace.opcode
        tx_env.validation_create_hook = trace.create
        tx_env.state.code_read_hook = trace.code_read
        for verifier_index, address, code in (
            (candidate.expiry_index, EXPIRY_VERIFIER, EXPIRY_VERIFIER_CODE),
            (
                candidate.recent_root_index,
                RECENT_ROOT_ADDRESS,
                RECENT_ROOT_CODE,
            ),
        ):
            if verifier_index is not None:
                actual_code = get_code(
                    tx_env.state, get_account(tx_env.state, address).code_hash
                )
                if actual_code != code:
                    return False
        if candidate.recent_root_index is not None:
            data = tx.frames[candidate.recent_root_index].data
            for offset in range(0, len(data), RECENT_ROOT_TUPLE_BYTES):
                source = data[offset : offset + 32]
                slot = int.from_bytes(data[offset + 32 : offset + 40], "big")
                trace.recent_root_slots.add(
                    keccak256(
                        RECENT_ROOT_STORAGE_DOMAIN
                        + source
                        + (slot % RECENT_ROOT_LENGTH).to_bytes(8, "big")
                    )
                )
        process_frames(block_env, tx_env, candidate.prefix_length)
        context = tx_env.frame_context
        assert context is not None
        if context.payer != candidate.payer or not context.sender_approved:
            return False
        if any(
            receipt.status != FrameStatus.SUCCESS
            for receipt in context.frame_receipts
        ):
            return False
        if candidate.deploy_index is not None:
            if (
                tx.sender not in tx_env.state.created_accounts
                or get_account(tx_env.state, tx.sender).code_hash
                == EMPTY_CODE_HASH
            ):
                return False
    except EthereumException:
        return False
    return True
