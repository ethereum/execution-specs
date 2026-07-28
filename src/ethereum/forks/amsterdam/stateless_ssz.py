"""
SSZ serialization schema for stateless validation types.

Define ``Container`` subclasses (eth-remerkleable) that mirror the dataclass
types in ``stateless`` and ``execution_engine.types``, plus conversion
functions between the two representations.
"""

from typing import TypeAlias

from ethereum_types.bytes import Bytes, Bytes48, Bytes96
from ethereum_types.numeric import U64, U256, Uint
from remerkleable.basic import boolean, uint64, uint256
from remerkleable.byte_arrays import ByteList, Bytes32, ByteVector
from remerkleable.complex import Container
from remerkleable.complex import List as SszList
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
    ChainConfig,
    ExecutionWitness,
    ForkActivation,
    ForkConfig,
    ProtocolFork,
    StatelessInput,
    StatelessValidationResult,
)

# --- SSZ max-length constants ---


MAX_EXTRA_DATA_BYTES = 32

# Stateless witness resource bounds.  These are local limits chosen for this
# schema, not consensus-spec SSZ constants.

# BAL permits block_gas_limit // 2_000 items. At 500M gas, that is
# 250_000 account accesses; budgeting 16 witness nodes per account gives
# 4_000_000 nodes, rounded up to 2**22. This targets an account-heavy
# witness, since deep storage tries are harder to construct. Depth of
# 16 is around double the depth of mainnet account trie.
MAX_WITNESS_NODES = 2**22

# Enough room for one pre-state bytecode read per BAL item at 500M gas:
# 500_000_000 // 2_000 = 250_000, rounded up to 2**18.
MAX_WITNESS_CODES = 2**18

# Execution only exposes the previous 256 block hashes.
MAX_WITNESS_HEADERS = 256
# As defined in EIP-7954.
MAX_BYTES_PER_CODE = 2**16
MAX_BYTES_PER_HEADER = 2**10
# Full secured-trie branch nodes are 532 bytes when all 16 children are
# represented by hashes, which is the largest normal state witness node.
# 2**10 is the next power of two, with almost twice the needed capacity.
MAX_BYTES_PER_WITNESS_NODE = 2**10

MAX_OPTIONAL_FORK_ACTIVATION_VALUES = 1
# One public key is supplied per transaction. Every valid transaction consumes
# at least 21_000 gas, so a 500M gas block can contain at most
# 500_000_000 // 21_000 = 23_809 transactions, rounded up to next power of 2.
MAX_PUBLIC_KEYS = 2**15
PUBLIC_KEY_BYTES = 65

# Stateless guest input bytes are schema-prefixed:
#   schema_id || encoded_payload
# schema_id is fork_index || schema_revision. Amsterdam is fork 0x15, and
# revision 0x01 uses SSZ encode(SszStatelessInput) for the payload.
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


SszOptionalForkActivationValue: TypeAlias = SszList[
    uint64, MAX_OPTIONAL_FORK_ACTIVATION_VALUES
]


class SszWithdrawal(Container):
    """SSZ container mirroring ``Withdrawal``."""

    index: uint64
    validator_index: uint64
    address: ByteVector[20]
    amount: uint64


class SszExecutionPayload(
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
    withdrawals: ProgressiveList[SszWithdrawal]
    blob_gas_used: uint64
    excess_blob_gas: uint64
    block_access_list: ProgressiveByteList
    slot_number: uint64


class SszDepositRequest(Container):
    """SSZ container mirroring ``DepositRequest``."""

    pubkey: ByteVector[48]
    withdrawal_credentials: Bytes32
    amount: uint64
    signature: ByteVector[96]
    index: uint64


class SszWithdrawalRequest(Container):
    """SSZ container mirroring ``WithdrawalRequest``."""

    source_address: ByteVector[20]
    validator_pubkey: ByteVector[48]
    amount: uint64


class SszConsolidationRequest(Container):
    """SSZ container mirroring ``ConsolidationRequest``."""

    source_address: ByteVector[20]
    source_pubkey: ByteVector[48]
    target_pubkey: ByteVector[48]


class SszBuilderDepositRequest(Container):
    """SSZ container mirroring ``BuilderDepositRequest``."""

    pubkey: ByteVector[48]
    withdrawal_credentials: Bytes32
    amount: uint64
    signature: ByteVector[96]


class SszBuilderExitRequest(Container):
    """SSZ container mirroring ``BuilderExitRequest``."""

    source_address: ByteVector[20]
    pubkey: ByteVector[48]


class SszExecutionRequests(
    ProgressiveContainer(active_fields=[1] * 5)  # type: ignore[misc]
):
    """SSZ container mirroring ``ExecutionRequests``."""

    deposits: ProgressiveList[SszDepositRequest]
    withdrawals: ProgressiveList[SszWithdrawalRequest]
    consolidations: ProgressiveList[SszConsolidationRequest]
    builder_deposits: ProgressiveList[SszBuilderDepositRequest]
    builder_exits: ProgressiveList[SszBuilderExitRequest]


class SszNewPayloadRequest(Container):
    """SSZ container mirroring ``NewPayloadRequest``."""

    execution_payload: SszExecutionPayload
    versioned_hashes: ProgressiveList[Bytes32]
    parent_beacon_block_root: Bytes32
    execution_requests: SszExecutionRequests


class SszExecutionWitness(Container):
    """SSZ container mirroring ``ExecutionWitness``."""

    state: SszList[ByteList[MAX_BYTES_PER_WITNESS_NODE], MAX_WITNESS_NODES]
    codes: SszList[ByteList[MAX_BYTES_PER_CODE], MAX_WITNESS_CODES]
    headers: SszList[ByteList[MAX_BYTES_PER_HEADER], MAX_WITNESS_HEADERS]


class SszForkActivation(Container):
    """SSZ container mirroring ``ForkActivation``."""

    block_number: SszOptionalForkActivationValue
    timestamp: SszOptionalForkActivationValue


class SszForkConfig(Container):
    """SSZ container mirroring ``ForkConfig``."""

    activation: SszForkActivation


class SszChainConfig(Container):
    """SSZ container mirroring ``ChainConfig``."""

    chain_id: uint64
    active_fork: SszForkConfig


class SszStatelessInput(Container):
    """SSZ container mirroring ``StatelessInput``."""

    new_payload_request: SszNewPayloadRequest
    witness: SszExecutionWitness
    chain_config: SszChainConfig
    public_keys: SszList[ByteVector[PUBLIC_KEY_BYTES], MAX_PUBLIC_KEYS]


class SszStatelessValidationResult(Container):
    """SSZ container mirroring ``StatelessValidationResult``."""

    new_payload_request_root: Bytes32
    successful_validation: boolean
    chain_config: SszChainConfig


# --- Conversion helpers ---


def _withdrawal_to_ssz(w: Withdrawal) -> SszWithdrawal:
    """Convert a Withdrawal to its SSZ form."""
    return SszWithdrawal(
        index=uint64(int(w.index)),
        validator_index=uint64(int(w.validator_index)),
        address=ByteVector[20](bytes(w.address)),
        amount=uint64(int(w.amount)),
    )


def _ssz_to_withdrawal(sw: SszWithdrawal) -> Withdrawal:
    """Convert an SSZ withdrawal back to a Withdrawal."""
    return Withdrawal(
        index=U64(sw.index),
        validator_index=U64(sw.validator_index),
        address=Address(bytes(sw.address)),
        amount=U256(sw.amount),
    )


def _payload_to_ssz(
    p: ExecutionPayload,
) -> SszExecutionPayload:
    """Convert an ExecutionPayload to its SSZ form."""
    return SszExecutionPayload(
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
        withdrawals=ProgressiveList[SszWithdrawal](
            _withdrawal_to_ssz(w) for w in p.withdrawals
        ),
        blob_gas_used=uint64(int(p.blob_gas_used)),
        excess_blob_gas=uint64(int(p.excess_blob_gas)),
        block_access_list=ProgressiveByteList(bytes(p.block_access_list)),
        slot_number=uint64(int(p.slot_number)),
    )


def _ssz_to_payload(
    sp: SszExecutionPayload,
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


def _deposit_request_to_ssz(d: DepositRequest) -> SszDepositRequest:
    """Convert a DepositRequest to its SSZ form."""
    return SszDepositRequest(
        pubkey=ByteVector[48](bytes(d.pubkey)),
        withdrawal_credentials=Bytes32(bytes(d.withdrawal_credentials)),
        amount=uint64(int(d.amount)),
        signature=ByteVector[96](bytes(d.signature)),
        index=uint64(int(d.index)),
    )


def _ssz_to_deposit_request(sd: SszDepositRequest) -> DepositRequest:
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
) -> SszWithdrawalRequest:
    """Convert a WithdrawalRequest to its SSZ form."""
    return SszWithdrawalRequest(
        source_address=ByteVector[20](bytes(w.source_address)),
        validator_pubkey=ByteVector[48](bytes(w.validator_pubkey)),
        amount=uint64(int(w.amount)),
    )


def _ssz_to_withdrawal_request(
    sw: SszWithdrawalRequest,
) -> WithdrawalRequest:
    """Convert an SSZ withdrawal request back."""
    return WithdrawalRequest(
        source_address=Address(bytes(sw.source_address)),
        validator_pubkey=Bytes48(bytes(sw.validator_pubkey)),
        amount=U64(sw.amount),
    )


def _consolidation_request_to_ssz(
    c: ConsolidationRequest,
) -> SszConsolidationRequest:
    """Convert a ConsolidationRequest to its SSZ form."""
    return SszConsolidationRequest(
        source_address=ByteVector[20](bytes(c.source_address)),
        source_pubkey=ByteVector[48](bytes(c.source_pubkey)),
        target_pubkey=ByteVector[48](bytes(c.target_pubkey)),
    )


def _ssz_to_consolidation_request(
    sc: SszConsolidationRequest,
) -> ConsolidationRequest:
    """Convert an SSZ consolidation request back."""
    return ConsolidationRequest(
        source_address=Address(bytes(sc.source_address)),
        source_pubkey=Bytes48(bytes(sc.source_pubkey)),
        target_pubkey=Bytes48(bytes(sc.target_pubkey)),
    )


def _builder_deposit_request_to_ssz(
    b: BuilderDepositRequest,
) -> SszBuilderDepositRequest:
    """Convert a BuilderDepositRequest to its SSZ form."""
    return SszBuilderDepositRequest(
        pubkey=ByteVector[48](bytes(b.pubkey)),
        withdrawal_credentials=Bytes32(bytes(b.withdrawal_credentials)),
        amount=uint64(int(b.amount)),
        signature=ByteVector[96](bytes(b.signature)),
    )


def _ssz_to_builder_deposit_request(
    sb: SszBuilderDepositRequest,
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
) -> SszBuilderExitRequest:
    """Convert a BuilderExitRequest to its SSZ form."""
    return SszBuilderExitRequest(
        source_address=ByteVector[20](bytes(b.source_address)),
        pubkey=ByteVector[48](bytes(b.pubkey)),
    )


def _ssz_to_builder_exit_request(
    sb: SszBuilderExitRequest,
) -> BuilderExitRequest:
    """Convert an SSZ builder exit request back."""
    return BuilderExitRequest(
        source_address=Address(bytes(sb.source_address)),
        pubkey=Bytes48(bytes(sb.pubkey)),
    )


def _execution_requests_to_ssz(
    er: ExecutionRequests,
) -> SszExecutionRequests:
    """Convert an ExecutionRequests to its SSZ form."""
    return SszExecutionRequests(
        deposits=ProgressiveList[SszDepositRequest](
            _deposit_request_to_ssz(d) for d in er.deposits
        ),
        withdrawals=ProgressiveList[SszWithdrawalRequest](
            _withdrawal_request_to_ssz(w) for w in er.withdrawals
        ),
        consolidations=ProgressiveList[SszConsolidationRequest](
            _consolidation_request_to_ssz(c) for c in er.consolidations
        ),
        builder_deposits=ProgressiveList[SszBuilderDepositRequest](
            _builder_deposit_request_to_ssz(b) for b in er.builder_deposits
        ),
        builder_exits=ProgressiveList[SszBuilderExitRequest](
            _builder_exit_request_to_ssz(b) for b in er.builder_exits
        ),
    )


def _ssz_to_execution_requests(
    ser: SszExecutionRequests,
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
) -> SszNewPayloadRequest:
    """Convert a NewPayloadRequest to its SSZ form."""
    return SszNewPayloadRequest(
        execution_payload=_payload_to_ssz(npr.execution_payload),
        versioned_hashes=ProgressiveList[Bytes32](
            Bytes32(bytes(vh)) for vh in npr.versioned_hashes
        ),
        parent_beacon_block_root=Bytes32(bytes(npr.parent_beacon_block_root)),
        execution_requests=_execution_requests_to_ssz(npr.execution_requests),
    )


def _ssz_to_new_payload_request(
    snpr: SszNewPayloadRequest,
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
) -> SszExecutionWitness:
    """Convert an ExecutionWitness to its SSZ form."""
    return SszExecutionWitness(
        state=SszList[ByteList[MAX_BYTES_PER_WITNESS_NODE], MAX_WITNESS_NODES](
            ByteList[MAX_BYTES_PER_WITNESS_NODE](bytes(s)) for s in w.state
        ),
        codes=SszList[ByteList[MAX_BYTES_PER_CODE], MAX_WITNESS_CODES](
            ByteList[MAX_BYTES_PER_CODE](bytes(c)) for c in w.codes
        ),
        headers=SszList[ByteList[MAX_BYTES_PER_HEADER], MAX_WITNESS_HEADERS](
            ByteList[MAX_BYTES_PER_HEADER](bytes(h)) for h in w.headers
        ),
    )


def _ssz_to_witness(
    sw: SszExecutionWitness,
) -> ExecutionWitness:
    """Convert an SSZ execution witness back."""
    return ExecutionWitness(
        state=tuple(Bytes(bytes(s)) for s in sw.state),
        codes=tuple(Bytes(bytes(c)) for c in sw.codes),
        headers=tuple(Bytes(bytes(h)) for h in sw.headers),
    )


def _optional_u64_to_ssz(
    value: U64 | None,
) -> SszOptionalForkActivationValue:
    """Convert an optional U64 to a zero-or-one SSZ list."""
    if value is None:
        return SszOptionalForkActivationValue()
    return SszOptionalForkActivationValue(uint64(int(value)))


def _ssz_to_optional_u64(
    ssz_value: SszOptionalForkActivationValue,
) -> U64 | None:
    """Convert a zero-or-one SSZ list back to an optional U64."""
    if ssz_value.length() == 0:
        return None
    return U64(ssz_value.get(0))


def _fork_activation_to_ssz(
    activation: ForkActivation,
) -> SszForkActivation:
    """Convert a ForkActivation to its SSZ form."""
    return SszForkActivation(
        block_number=_optional_u64_to_ssz(activation.block_number),
        timestamp=_optional_u64_to_ssz(activation.timestamp),
    )


def _ssz_to_fork_activation(
    ssz_activation: SszForkActivation,
) -> ForkActivation:
    """Convert an SSZ fork activation back."""
    return ForkActivation(
        block_number=_ssz_to_optional_u64(ssz_activation.block_number),
        timestamp=_ssz_to_optional_u64(ssz_activation.timestamp),
    )


def _fork_config_to_ssz(
    fork_config: ForkConfig,
) -> SszForkConfig:
    """Convert a ForkConfig to its SSZ form."""
    return SszForkConfig(
        activation=_fork_activation_to_ssz(fork_config.activation),
    )


def _ssz_to_fork_config(
    ssz_fork_config: SszForkConfig,
) -> ForkConfig:
    """Convert an SSZ fork config back."""
    return ForkConfig(
        activation=_ssz_to_fork_activation(ssz_fork_config.activation),
    )


def _chain_config_to_ssz(
    cc: ChainConfig,
) -> SszChainConfig:
    """Convert a ChainConfig to its SSZ form."""
    return SszChainConfig(
        chain_id=uint64(int(cc.chain_id)),
        active_fork=_fork_config_to_ssz(cc.active_fork),
    )


def _ssz_to_chain_config(
    scc: SszChainConfig,
) -> ChainConfig:
    """Convert an SSZ chain config back."""
    return ChainConfig(
        chain_id=U64(scc.chain_id),
        active_fork=_ssz_to_fork_config(scc.active_fork),
    )


def stateless_input_to_ssz(
    si: StatelessInput,
) -> SszStatelessInput:
    """Convert a StatelessInput to its SSZ form."""
    for public_key in si.public_keys:
        if len(public_key) != PUBLIC_KEY_BYTES:
            raise ValueError(
                f"Transaction public key must be {PUBLIC_KEY_BYTES} bytes"
            )

    return SszStatelessInput(
        new_payload_request=_new_payload_request_to_ssz(
            si.new_payload_request
        ),
        witness=_witness_to_ssz(si.witness),
        chain_config=_chain_config_to_ssz(si.chain_config),
        public_keys=SszList[ByteVector[PUBLIC_KEY_BYTES], MAX_PUBLIC_KEYS](
            ByteVector[PUBLIC_KEY_BYTES](bytes(pk)) for pk in si.public_keys
        ),
    )


def ssz_to_stateless_input(
    ssz_si: SszStatelessInput,
) -> StatelessInput:
    """Convert an SSZ stateless input back."""
    return StatelessInput(
        new_payload_request=_ssz_to_new_payload_request(
            ssz_si.new_payload_request
        ),
        witness=_ssz_to_witness(ssz_si.witness),
        chain_config=_ssz_to_chain_config(ssz_si.chain_config),
        public_keys=tuple(Bytes(bytes(pk)) for pk in ssz_si.public_keys),
    )


def validation_result_to_ssz(
    vr: StatelessValidationResult,
) -> SszStatelessValidationResult:
    """Convert a StatelessValidationResult to its SSZ form."""
    return SszStatelessValidationResult(
        new_payload_request_root=Bytes32(bytes(vr.new_payload_request_root)),
        successful_validation=boolean(vr.successful_validation),
        chain_config=_chain_config_to_ssz(vr.chain_config),
    )


def ssz_to_validation_result(
    ssz_vr: SszStatelessValidationResult,
) -> StatelessValidationResult:
    """Convert an SSZ validation result back."""
    return StatelessValidationResult(
        new_payload_request_root=Hash32(
            bytes(ssz_vr.new_payload_request_root)
        ),
        successful_validation=bool(ssz_vr.successful_validation),
        chain_config=_ssz_to_chain_config(ssz_vr.chain_config),
    )
