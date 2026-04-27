"""
SSZ serialization schema for stateless validation types.

Define ``Container`` subclasses (eth-remerkleable) that mirror the dataclass
types in ``stateless`` and ``execution_engine.types``, plus conversion
functions between the two representations.
"""

from ethereum_types.bytes import Bytes, Bytes48, Bytes96
from ethereum_types.numeric import U64, U256, Uint
from remerkleable.basic import boolean, uint64, uint256
from remerkleable.byte_arrays import ByteList, Bytes32, ByteVector
from remerkleable.complex import Container
from remerkleable.complex import List as SszList

from ethereum.crypto.hash import Hash32
from ethereum.state import Address, Root

from .blocks import Withdrawal
from .execution_engine.requests import (
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
    StatelessInput,
    StatelessValidationResult,
)

# --- SSZ max-length constants ---

MAX_EXTRA_DATA_BYTES = 32
MAX_BYTES_PER_TRANSACTION = 2**30
MAX_TRANSACTIONS_PER_PAYLOAD = 2**20
# TODO: CL spec defines MAX_WITHDRAWALS_PER_PAYLOAD as 2**4 (16).
# Some fill tests exceed this; raised to 2**16 until those tests are
# capped or skipped for Amsterdam.
MAX_WITHDRAWALS_PER_PAYLOAD = 2**16
MAX_BLOB_COMMITMENTS_PER_BLOCK = 4096
MAX_DEPOSIT_REQUESTS_PER_PAYLOAD = 2**13
MAX_WITHDRAWAL_REQUESTS_PER_PAYLOAD = 2**4
MAX_CONSOLIDATION_REQUESTS_PER_PAYLOAD = 2**1
MAX_BLOCK_ACCESS_LIST_BYTES = 2**24
MAX_WITNESS_NODES = 2**20
MAX_WITNESS_CODES = 2**16
MAX_WITNESS_HEADERS = 256
MAX_BYTES_PER_WITNESS_NODE = 2**20
MAX_BYTES_PER_CODE = 2**24
MAX_BYTES_PER_HEADER = 2**10
MAX_PUBLIC_KEYS = 2**20
MAX_BYTES_PER_PUBLIC_KEY = 65


# --- SSZ Container types ---


class SszWithdrawal(Container):
    """SSZ container mirroring ``Withdrawal``."""

    index: uint64
    validator_index: uint64
    address: ByteVector[20]
    amount: uint64


class SszExecutionPayload(Container):
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
    transactions: SszList[
        ByteList[MAX_BYTES_PER_TRANSACTION], MAX_TRANSACTIONS_PER_PAYLOAD
    ]  # noqa: E501
    withdrawals: SszList[SszWithdrawal, MAX_WITHDRAWALS_PER_PAYLOAD]
    blob_gas_used: uint64
    excess_blob_gas: uint64
    block_access_list: ByteList[MAX_BLOCK_ACCESS_LIST_BYTES]


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


class SszExecutionRequests(Container):
    """SSZ container mirroring ``ExecutionRequests``."""

    deposits: SszList[SszDepositRequest, MAX_DEPOSIT_REQUESTS_PER_PAYLOAD]
    withdrawals: SszList[
        SszWithdrawalRequest, MAX_WITHDRAWAL_REQUESTS_PER_PAYLOAD
    ]
    consolidations: SszList[
        SszConsolidationRequest, MAX_CONSOLIDATION_REQUESTS_PER_PAYLOAD
    ]


class SszNewPayloadRequest(Container):
    """SSZ container mirroring ``NewPayloadRequest``."""

    execution_payload: SszExecutionPayload
    versioned_hashes: SszList[Bytes32, MAX_BLOB_COMMITMENTS_PER_BLOCK]
    parent_beacon_block_root: Bytes32
    execution_requests: SszExecutionRequests


class SszExecutionWitness(Container):
    """SSZ container mirroring ``ExecutionWitness``."""

    state: SszList[ByteList[MAX_BYTES_PER_WITNESS_NODE], MAX_WITNESS_NODES]
    codes: SszList[ByteList[MAX_BYTES_PER_CODE], MAX_WITNESS_CODES]
    headers: SszList[ByteList[MAX_BYTES_PER_HEADER], MAX_WITNESS_HEADERS]


class SszChainConfig(Container):
    """SSZ container mirroring ``ChainConfig``."""

    chain_id: uint64


class SszStatelessInput(Container):
    """SSZ container mirroring ``StatelessInput``."""

    new_payload_request: SszNewPayloadRequest
    witness: SszExecutionWitness
    chain_config: SszChainConfig
    public_keys: SszList[ByteList[MAX_BYTES_PER_PUBLIC_KEY], MAX_PUBLIC_KEYS]


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
        transactions=SszList[
            ByteList[MAX_BYTES_PER_TRANSACTION],
            MAX_TRANSACTIONS_PER_PAYLOAD,
        ](
            ByteList[MAX_BYTES_PER_TRANSACTION](bytes(tx))
            for tx in p.transactions
        ),
        withdrawals=SszList[SszWithdrawal, MAX_WITHDRAWALS_PER_PAYLOAD](
            _withdrawal_to_ssz(w) for w in p.withdrawals
        ),
        blob_gas_used=uint64(int(p.blob_gas_used)),
        excess_blob_gas=uint64(int(p.excess_blob_gas)),
        block_access_list=ByteList[MAX_BLOCK_ACCESS_LIST_BYTES](
            bytes(p.block_access_list)
        ),
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


def _execution_requests_to_ssz(
    er: ExecutionRequests,
) -> SszExecutionRequests:
    """Convert an ExecutionRequests to its SSZ form."""
    return SszExecutionRequests(
        deposits=SszList[SszDepositRequest, MAX_DEPOSIT_REQUESTS_PER_PAYLOAD](
            _deposit_request_to_ssz(d) for d in er.deposits
        ),
        withdrawals=SszList[
            SszWithdrawalRequest, MAX_WITHDRAWAL_REQUESTS_PER_PAYLOAD
        ](_withdrawal_request_to_ssz(w) for w in er.withdrawals),
        consolidations=SszList[
            SszConsolidationRequest, MAX_CONSOLIDATION_REQUESTS_PER_PAYLOAD
        ](_consolidation_request_to_ssz(c) for c in er.consolidations),
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
    )


def _new_payload_request_to_ssz(
    npr: NewPayloadRequest,
) -> SszNewPayloadRequest:
    """Convert a NewPayloadRequest to its SSZ form."""
    return SszNewPayloadRequest(
        execution_payload=_payload_to_ssz(npr.execution_payload),
        versioned_hashes=SszList[Bytes32, MAX_BLOB_COMMITMENTS_PER_BLOCK](
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


def _chain_config_to_ssz(
    cc: ChainConfig,
) -> SszChainConfig:
    """Convert a ChainConfig to its SSZ form."""
    return SszChainConfig(chain_id=uint64(int(cc.chain_id)))


def _ssz_to_chain_config(
    scc: SszChainConfig,
) -> ChainConfig:
    """Convert an SSZ chain config back."""
    return ChainConfig(chain_id=U64(scc.chain_id))


def stateless_input_to_ssz(
    si: StatelessInput,
) -> SszStatelessInput:
    """Convert a StatelessInput to its SSZ form."""
    return SszStatelessInput(
        new_payload_request=_new_payload_request_to_ssz(
            si.new_payload_request
        ),
        witness=_witness_to_ssz(si.witness),
        chain_config=_chain_config_to_ssz(si.chain_config),
        public_keys=SszList[
            ByteList[MAX_BYTES_PER_PUBLIC_KEY], MAX_PUBLIC_KEYS
        ](
            ByteList[MAX_BYTES_PER_PUBLIC_KEY](bytes(pk))
            for pk in si.public_keys
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
