"""
SSZ serialization schema for stateless validation types.

Define ``Container`` subclasses (eth-remerkleable) that mirror the dataclass
types in ``stateless`` and ``execution_engine.types``, plus conversion
functions between the two representations.
"""

from ethereum_types.bytes import Bytes, Bytes48, Bytes96
from ethereum_types.numeric import U16, U64, U256, Uint
from remerkleable.basic import boolean, uint16, uint64, uint256
from remerkleable.byte_arrays import ByteList, Bytes32, ByteVector
from remerkleable.complex import Container
from remerkleable.complex import List as SSZList
from remerkleable.progressive import (
    ProgressiveByteList,
    ProgressiveContainer,
    ProgressiveList,
)

from ethereum.crypto.hash import Hash32
from ethereum.state import Address, Root

from .blocks import Withdrawal
from .execution_engine.requests import (
    BuilderDepositRequest,
    BuilderExitRequest,
    ConsolidationRequest,
    DepositRequest,
    ExecutionRequests,
    WithdrawalRequest,
)
from .execution_engine.types import ExecutionPayload, NewPayloadRequest
from .fork_types import Bloom, VersionedHash
from .stateless import (
    ExecutionWitness,
    ProtocolFork,
    StatelessInput,
    StatelessValidationResult,
)

# --- SSZ max-length constants ---


MAX_EXTRA_DATA_BYTES = 32

# Execution only exposes the previous 256 block hashes.
MAX_WITNESS_HEADERS = 256
# As defined in EIP-7954.
MAX_BYTES_PER_CODE = 2**16
MAX_BYTES_PER_HEADER = 2**10
# Full secured-trie branch nodes are 532 bytes when all 16 children are
# represented by hashes, which is the largest normal state witness node.
# 2**10 is the next power of two, with almost twice the needed capacity.
MAX_BYTES_PER_WITNESS_NODE = 2**10

PUBLIC_KEY_BYTES = 65

# Stateless guest input bytes are schema-prefixed:
#   schema_id || encoded_payload
# schema_id is fork_index || schema_revision. Amsterdam is fork 0x15, and
# revision 0x01 uses SSZ encode(SSZStatelessInput) for the payload.
STATELESS_INPUT_SCHEMA_FORK_INDEX = ProtocolFork.Amsterdam
STATELESS_INPUT_SCHEMA_REVISION = 0x01
STATELESS_INPUT_SCHEMA_ID = (
    STATELESS_INPUT_SCHEMA_FORK_INDEX << 8
) | STATELESS_INPUT_SCHEMA_REVISION
STATELESS_INPUT_SCHEMA_ID_SIZE = 2
STATELESS_INPUT_SCHEMA_ID_BYTES = STATELESS_INPUT_SCHEMA_ID.to_bytes(
    STATELESS_INPUT_SCHEMA_ID_SIZE,
    "big",
)


# --- SSZ Container types ---


class SSZWithdrawal(Container):
    """SSZ container mirroring ``Withdrawal``."""

    index: uint64
    validator_index: uint64
    address: ByteVector[20]
    amount: uint64


class SSZExecutionPayload(
    ProgressiveContainer(active_fields=[1] * 19)  # type: ignore[misc]
):
    """SSZ container mirroring ``ExecutionPayload``."""

    parent_hash: Bytes32
    fee_recipient: ByteVector[20]
    state_root: Bytes32
    receipts_root: Bytes32
    logs_bloom: ByteVector[256]
    prev_randao: Bytes32
    block_number: uint64
    gas_limit: uint64
    gas_used: uint64
    timestamp: uint64
    extra_data: ByteList[MAX_EXTRA_DATA_BYTES]
    base_fee_per_gas: uint256
    block_hash: Bytes32
    transactions: ProgressiveList[ProgressiveByteList]
    withdrawals: ProgressiveList[SSZWithdrawal]
    blob_gas_used: uint64
    excess_blob_gas: uint64
    block_access_list: ProgressiveByteList
    slot_number: uint64


class SSZDepositRequest(Container):
    """SSZ container mirroring ``DepositRequest``."""

    pubkey: ByteVector[48]
    withdrawal_credentials: Bytes32
    amount: uint64
    signature: ByteVector[96]
    index: uint64


class SSZWithdrawalRequest(Container):
    """SSZ container mirroring ``WithdrawalRequest``."""

    source_address: ByteVector[20]
    validator_pubkey: ByteVector[48]
    amount: uint64


class SSZConsolidationRequest(Container):
    """SSZ container mirroring ``ConsolidationRequest``."""

    source_address: ByteVector[20]
    source_pubkey: ByteVector[48]
    target_pubkey: ByteVector[48]


class SSZBuilderDepositRequest(Container):
    """SSZ container mirroring ``BuilderDepositRequest``."""

    pubkey: ByteVector[48]
    withdrawal_credentials: Bytes32
    amount: uint64
    signature: ByteVector[96]


class SSZBuilderExitRequest(Container):
    """SSZ container mirroring ``BuilderExitRequest``."""

    source_address: ByteVector[20]
    pubkey: ByteVector[48]


class SSZExecutionRequests(
    ProgressiveContainer(active_fields=[1] * 5)  # type: ignore[misc]
):
    """SSZ container mirroring ``ExecutionRequests``."""

    deposits: ProgressiveList[SSZDepositRequest]
    withdrawals: ProgressiveList[SSZWithdrawalRequest]
    consolidations: ProgressiveList[SSZConsolidationRequest]
    builder_deposits: ProgressiveList[SSZBuilderDepositRequest]
    builder_exits: ProgressiveList[SSZBuilderExitRequest]


class SSZNewPayloadRequest(Container):
    """SSZ container mirroring ``NewPayloadRequest``."""

    execution_payload: SSZExecutionPayload
    versioned_hashes: ProgressiveList[Bytes32]
    parent_beacon_block_root: Bytes32
    execution_requests: SSZExecutionRequests


class SSZExecutionWitness(Container):
    """SSZ container mirroring ``ExecutionWitness``."""

    state: ProgressiveList[ByteList[MAX_BYTES_PER_WITNESS_NODE]]
    codes: ProgressiveList[ByteList[MAX_BYTES_PER_CODE]]
    headers: SSZList[ByteList[MAX_BYTES_PER_HEADER], MAX_WITNESS_HEADERS]


class SSZStatelessInput(Container):
    """SSZ container mirroring ``StatelessInput``."""

    new_payload_request: SSZNewPayloadRequest
    witness: SSZExecutionWitness
    chain_id: uint64
    public_keys: ProgressiveList[ByteVector[PUBLIC_KEY_BYTES]]


class SSZStatelessValidationResult(Container):
    """SSZ container mirroring ``StatelessValidationResult``."""

    new_payload_request_root: Bytes32
    successful_validation: boolean
    chain_id: uint64
    schema_id: uint16


# --- Conversion helpers ---


def _withdrawal_to_ssz(w: Withdrawal) -> SSZWithdrawal:
    """Convert a Withdrawal to its SSZ form."""
    return SSZWithdrawal(
        index=uint64(int(w.index)),
        validator_index=uint64(int(w.validator_index)),
        address=ByteVector[20](bytes(w.address)),
        amount=uint64(int(w.amount)),
    )


def _ssz_to_withdrawal(sw: SSZWithdrawal) -> Withdrawal:
    """Convert an SSZ withdrawal back to a Withdrawal."""
    return Withdrawal(
        index=U64(sw.index),
        validator_index=U64(sw.validator_index),
        address=Address(bytes(sw.address)),
        amount=U64(sw.amount),
    )


def _payload_to_ssz(
    p: ExecutionPayload,
) -> SSZExecutionPayload:
    """Convert an ExecutionPayload to its SSZ form."""
    return SSZExecutionPayload(
        parent_hash=Bytes32(bytes(p.parent_hash)),
        fee_recipient=ByteVector[20](bytes(p.fee_recipient)),
        state_root=Bytes32(bytes(p.state_root)),
        receipts_root=Bytes32(bytes(p.receipts_root)),
        logs_bloom=ByteVector[256](bytes(p.logs_bloom)),
        prev_randao=Bytes32(bytes(p.prev_randao)),
        block_number=uint64(int(p.block_number)),
        gas_limit=uint64(int(p.gas_limit)),
        gas_used=uint64(int(p.gas_used)),
        timestamp=uint64(int(p.timestamp)),
        extra_data=ByteList[MAX_EXTRA_DATA_BYTES](bytes(p.extra_data)),
        base_fee_per_gas=uint256(int(p.base_fee_per_gas)),
        block_hash=Bytes32(bytes(p.block_hash)),
        transactions=ProgressiveList[ProgressiveByteList](
            ProgressiveByteList(bytes(tx)) for tx in p.transactions
        ),
        withdrawals=ProgressiveList[SSZWithdrawal](
            _withdrawal_to_ssz(w) for w in p.withdrawals
        ),
        blob_gas_used=uint64(int(p.blob_gas_used)),
        excess_blob_gas=uint64(int(p.excess_blob_gas)),
        block_access_list=ProgressiveByteList(bytes(p.block_access_list)),
        slot_number=uint64(int(p.slot_number)),
    )


def _ssz_to_payload(
    sp: SSZExecutionPayload,
) -> ExecutionPayload:
    """Convert an SSZ execution payload back to ExecutionPayload."""
    return ExecutionPayload(
        parent_hash=Hash32(bytes(sp.parent_hash)),
        fee_recipient=Address(bytes(sp.fee_recipient)),
        state_root=Root(bytes(sp.state_root)),
        receipts_root=Root(bytes(sp.receipts_root)),
        logs_bloom=Bloom(bytes(sp.logs_bloom)),
        prev_randao=Bytes32(bytes(sp.prev_randao)),
        block_number=Uint(sp.block_number),
        gas_limit=Uint(sp.gas_limit),
        gas_used=Uint(sp.gas_used),
        timestamp=U256(sp.timestamp),
        extra_data=Bytes(bytes(sp.extra_data)),
        base_fee_per_gas=Uint(sp.base_fee_per_gas),
        block_hash=Hash32(bytes(sp.block_hash)),
        transactions=tuple(Bytes(bytes(tx)) for tx in sp.transactions),
        withdrawals=tuple(_ssz_to_withdrawal(sw) for sw in sp.withdrawals),
        blob_gas_used=U64(sp.blob_gas_used),
        excess_blob_gas=U64(sp.excess_blob_gas),
        block_access_list=Bytes(bytes(sp.block_access_list)),
        slot_number=U64(sp.slot_number),
    )


def _deposit_request_to_ssz(d: DepositRequest) -> SSZDepositRequest:
    """Convert a DepositRequest to its SSZ form."""
    return SSZDepositRequest(
        pubkey=ByteVector[48](bytes(d.pubkey)),
        withdrawal_credentials=Bytes32(bytes(d.withdrawal_credentials)),
        amount=uint64(int(d.amount)),
        signature=ByteVector[96](bytes(d.signature)),
        index=uint64(int(d.index)),
    )


def _ssz_to_deposit_request(sd: SSZDepositRequest) -> DepositRequest:
    """Convert an SSZ deposit request back."""
    return DepositRequest(
        pubkey=Bytes48(bytes(sd.pubkey)),
        withdrawal_credentials=Bytes32(bytes(sd.withdrawal_credentials)),
        amount=U64(sd.amount),
        signature=Bytes96(bytes(sd.signature)),
        index=U64(sd.index),
    )


def _withdrawal_request_to_ssz(
    w: WithdrawalRequest,
) -> SSZWithdrawalRequest:
    """Convert a WithdrawalRequest to its SSZ form."""
    return SSZWithdrawalRequest(
        source_address=ByteVector[20](bytes(w.source_address)),
        validator_pubkey=ByteVector[48](bytes(w.validator_pubkey)),
        amount=uint64(int(w.amount)),
    )


def _ssz_to_withdrawal_request(
    sw: SSZWithdrawalRequest,
) -> WithdrawalRequest:
    """Convert an SSZ withdrawal request back."""
    return WithdrawalRequest(
        source_address=Address(bytes(sw.source_address)),
        validator_pubkey=Bytes48(bytes(sw.validator_pubkey)),
        amount=U64(sw.amount),
    )


def _consolidation_request_to_ssz(
    c: ConsolidationRequest,
) -> SSZConsolidationRequest:
    """Convert a ConsolidationRequest to its SSZ form."""
    return SSZConsolidationRequest(
        source_address=ByteVector[20](bytes(c.source_address)),
        source_pubkey=ByteVector[48](bytes(c.source_pubkey)),
        target_pubkey=ByteVector[48](bytes(c.target_pubkey)),
    )


def _ssz_to_consolidation_request(
    sc: SSZConsolidationRequest,
) -> ConsolidationRequest:
    """Convert an SSZ consolidation request back."""
    return ConsolidationRequest(
        source_address=Address(bytes(sc.source_address)),
        source_pubkey=Bytes48(bytes(sc.source_pubkey)),
        target_pubkey=Bytes48(bytes(sc.target_pubkey)),
    )


def _builder_deposit_request_to_ssz(
    b: BuilderDepositRequest,
) -> SSZBuilderDepositRequest:
    """Convert a BuilderDepositRequest to its SSZ form."""
    return SSZBuilderDepositRequest(
        pubkey=ByteVector[48](bytes(b.pubkey)),
        withdrawal_credentials=Bytes32(bytes(b.withdrawal_credentials)),
        amount=uint64(int(b.amount)),
        signature=ByteVector[96](bytes(b.signature)),
    )


def _ssz_to_builder_deposit_request(
    sb: SSZBuilderDepositRequest,
) -> BuilderDepositRequest:
    """Convert an SSZ builder deposit request back."""
    return BuilderDepositRequest(
        pubkey=Bytes48(bytes(sb.pubkey)),
        withdrawal_credentials=Bytes32(bytes(sb.withdrawal_credentials)),
        amount=U64(sb.amount),
        signature=Bytes96(bytes(sb.signature)),
    )


def _builder_exit_request_to_ssz(
    b: BuilderExitRequest,
) -> SSZBuilderExitRequest:
    """Convert a BuilderExitRequest to its SSZ form."""
    return SSZBuilderExitRequest(
        source_address=ByteVector[20](bytes(b.source_address)),
        pubkey=ByteVector[48](bytes(b.pubkey)),
    )


def _ssz_to_builder_exit_request(
    sb: SSZBuilderExitRequest,
) -> BuilderExitRequest:
    """Convert an SSZ builder exit request back."""
    return BuilderExitRequest(
        source_address=Address(bytes(sb.source_address)),
        pubkey=Bytes48(bytes(sb.pubkey)),
    )


def _execution_requests_to_ssz(
    er: ExecutionRequests,
) -> SSZExecutionRequests:
    """Convert an ExecutionRequests to its SSZ form."""
    return SSZExecutionRequests(
        deposits=ProgressiveList[SSZDepositRequest](
            _deposit_request_to_ssz(d) for d in er.deposits
        ),
        withdrawals=ProgressiveList[SSZWithdrawalRequest](
            _withdrawal_request_to_ssz(w) for w in er.withdrawals
        ),
        consolidations=ProgressiveList[SSZConsolidationRequest](
            _consolidation_request_to_ssz(c) for c in er.consolidations
        ),
        builder_deposits=ProgressiveList[SSZBuilderDepositRequest](
            _builder_deposit_request_to_ssz(b) for b in er.builder_deposits
        ),
        builder_exits=ProgressiveList[SSZBuilderExitRequest](
            _builder_exit_request_to_ssz(b) for b in er.builder_exits
        ),
    )


def _ssz_to_execution_requests(
    ser: SSZExecutionRequests,
) -> ExecutionRequests:
    """Convert an SSZ execution requests back."""
    return ExecutionRequests(
        deposits=tuple(_ssz_to_deposit_request(sd) for sd in ser.deposits),
        withdrawals=tuple(
            _ssz_to_withdrawal_request(sw) for sw in ser.withdrawals
        ),
        consolidations=tuple(
            _ssz_to_consolidation_request(sc) for sc in ser.consolidations
        ),
        builder_deposits=tuple(
            _ssz_to_builder_deposit_request(sb) for sb in ser.builder_deposits
        ),
        builder_exits=tuple(
            _ssz_to_builder_exit_request(sb) for sb in ser.builder_exits
        ),
    )


def _new_payload_request_to_ssz(
    npr: NewPayloadRequest,
) -> SSZNewPayloadRequest:
    """Convert a NewPayloadRequest to its SSZ form."""
    return SSZNewPayloadRequest(
        execution_payload=_payload_to_ssz(npr.execution_payload),
        versioned_hashes=ProgressiveList[Bytes32](
            Bytes32(bytes(vh)) for vh in npr.versioned_hashes
        ),
        parent_beacon_block_root=Bytes32(bytes(npr.parent_beacon_block_root)),
        execution_requests=_execution_requests_to_ssz(npr.execution_requests),
    )


def _ssz_to_new_payload_request(
    snpr: SSZNewPayloadRequest,
) -> NewPayloadRequest:
    """Convert an SSZ new payload request back."""
    return NewPayloadRequest(
        execution_payload=_ssz_to_payload(snpr.execution_payload),
        versioned_hashes=tuple(
            VersionedHash(bytes(vh)) for vh in snpr.versioned_hashes
        ),
        parent_beacon_block_root=Root(bytes(snpr.parent_beacon_block_root)),
        execution_requests=_ssz_to_execution_requests(snpr.execution_requests),
    )


def _witness_to_ssz(
    w: ExecutionWitness,
) -> SSZExecutionWitness:
    """Convert an ExecutionWitness to its SSZ form."""
    return SSZExecutionWitness(
        state=ProgressiveList[ByteList[MAX_BYTES_PER_WITNESS_NODE]](
            ByteList[MAX_BYTES_PER_WITNESS_NODE](bytes(s)) for s in w.state
        ),
        codes=ProgressiveList[ByteList[MAX_BYTES_PER_CODE]](
            ByteList[MAX_BYTES_PER_CODE](bytes(c)) for c in w.codes
        ),
        headers=SSZList[ByteList[MAX_BYTES_PER_HEADER], MAX_WITNESS_HEADERS](
            ByteList[MAX_BYTES_PER_HEADER](bytes(h)) for h in w.headers
        ),
    )


def _ssz_to_witness(
    sw: SSZExecutionWitness,
) -> ExecutionWitness:
    """Convert an SSZ execution witness back."""
    return ExecutionWitness(
        state=tuple(Bytes(bytes(s)) for s in sw.state),
        codes=tuple(Bytes(bytes(c)) for c in sw.codes),
        headers=tuple(Bytes(bytes(h)) for h in sw.headers),
    )


def stateless_input_to_ssz(
    si: StatelessInput,
) -> SSZStatelessInput:
    """Convert a StatelessInput to its SSZ form."""
    for public_key in si.public_keys:
        if len(public_key) != PUBLIC_KEY_BYTES:
            raise ValueError(
                f"Transaction public key must be {PUBLIC_KEY_BYTES} bytes"
            )

    return SSZStatelessInput(
        new_payload_request=_new_payload_request_to_ssz(
            si.new_payload_request
        ),
        witness=_witness_to_ssz(si.witness),
        chain_id=uint64(int(si.chain_id)),
        public_keys=ProgressiveList[ByteVector[PUBLIC_KEY_BYTES]](
            ByteVector[PUBLIC_KEY_BYTES](bytes(pk)) for pk in si.public_keys
        ),
    )


def ssz_to_stateless_input(
    ssz_si: SSZStatelessInput,
) -> StatelessInput:
    """Convert an SSZ stateless input back."""
    return StatelessInput(
        new_payload_request=_ssz_to_new_payload_request(
            ssz_si.new_payload_request
        ),
        witness=_ssz_to_witness(ssz_si.witness),
        chain_id=U64(ssz_si.chain_id),
        public_keys=tuple(Bytes(bytes(pk)) for pk in ssz_si.public_keys),
    )


def validation_result_to_ssz(
    vr: StatelessValidationResult,
) -> SSZStatelessValidationResult:
    """Convert a StatelessValidationResult to its SSZ form."""
    return SSZStatelessValidationResult(
        new_payload_request_root=Bytes32(bytes(vr.new_payload_request_root)),
        successful_validation=boolean(vr.successful_validation),
        chain_id=uint64(int(vr.chain_id)),
        schema_id=uint16(int(vr.schema_id)),
    )


def ssz_to_validation_result(
    ssz_vr: SSZStatelessValidationResult,
) -> StatelessValidationResult:
    """Convert an SSZ validation result back."""
    return StatelessValidationResult(
        new_payload_request_root=Hash32(
            bytes(ssz_vr.new_payload_request_root)
        ),
        successful_validation=bool(ssz_vr.successful_validation),
        chain_id=U64(ssz_vr.chain_id),
        schema_id=U16(ssz_vr.schema_id),
    )
