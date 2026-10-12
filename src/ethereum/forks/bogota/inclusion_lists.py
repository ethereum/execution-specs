"""
Evaluate inclusion obligations independently of payload execution validity.

Profile 1 checks ordinary transactions at the end of payload execution.
Profile 2 fills each committee position's verification budget separately
and replays an omitted frame transaction at its builder-claimed index.
Snapshots come from successful payload execution, including its separate
execution and state gas counters, and exclude post-execution operations.

[EIP-7805]: https://eips.ethereum.org/EIPS/eip-7805
[EIP-8369]: https://eips.ethereum.org/EIPS/eip-8369
"""

from collections import Counter
from dataclasses import dataclass, replace
from typing import Dict, Set, Tuple, final

from ethereum_rlp import exceptions as rlp_exceptions
from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes, Bytes32
from ethereum_types.numeric import U64, Uint, ulen

from ethereum.crypto.hash import keccak256
from ethereum.exceptions import EthereumException

from . import vm
from .block_access_lists import BlockAccessListBuilder
from .fork_types import ExecutionGas, StateGas
from .inclusion_list_frames import (
    FrameCandidate,
    ReplayLimits,
    classify_frame_candidate,
    replay_frame_candidate,
    verify_candidate_signatures,
)
from .state_tracker import BlockState
from .transactions import (
    BlobTransaction,
    LegacyTransaction,
    Transaction,
    chain_id,
    decode_transaction,
    encode_transaction,
)
from .transactions.frame_transaction import FrameTransaction

INCLUSION_LIST_COMMITTEE_SIZE = 16
"""Number of independently budgeted inclusion-list positions."""

MAX_TRANSACTIONS_BYTES_PER_INCLUSION_LIST = 8192
"""Maximum total envelope bytes selected by one membership position."""

MAX_INCLUSION_LIST_CLAIMS = 2**12
"""Maximum number of claims in the revealed ordered list."""

MAX_VERIFY_GAS_PER_IL = Uint(2**20)
"""Execution-work allowance for each independent inclusion-list fill."""


@final
@dataclass(frozen=True)
class InclusionClaim:
    """Identify a transaction and its claimed insertion index."""

    transaction_hash: Bytes32
    transaction_index: U64


@final
@dataclass(frozen=True)
class InclusionListInputs:
    """
    Carry the consensus layer's selected envelopes, membership and claims.

    Missing membership denotes the original Profile-1-only interface.
    Profile 2 requires explicit fork replay limits; these are local fork
    configuration, never parameters supplied by the builder or a peer.
    The consensus layer authenticates the revealed claims against the bid.
    """

    transactions: Tuple[LegacyTransaction | Bytes, ...] = ()
    membership: Tuple[Bytes, ...] = ()
    claims: Tuple[InclusionClaim, ...] = ()
    replay_limits: ReplayLimits | None = None


@final
@dataclass(frozen=True)
class InclusionListSnapshot:
    """Retain execution state and both gas counters at one insertion index."""

    state: BlockState
    execution_gas_used: ExecutionGas
    state_gas_used: StateGas


def transaction_envelope(raw_tx: LegacyTransaction | Bytes) -> Bytes:
    """Return the exact transaction envelope, including legacy RLP."""
    return (
        rlp.encode(raw_tx) if isinstance(raw_tx, LegacyTransaction) else raw_tx
    )


def decode_inclusion_transaction(envelope: Bytes) -> Transaction:
    """Decode a canonical legacy or typed inclusion-list envelope."""
    if not envelope:
        raise rlp_exceptions.DecodingError("Empty transaction")
    tx: Transaction
    if envelope[0] >= 0xC0:
        tx = rlp.decode_to(LegacyTransaction, envelope)
    else:
        tx = decode_transaction(envelope)
    if transaction_envelope(encode_transaction(tx)) != envelope:
        raise rlp_exceptions.DecodingError("Noncanonical transaction")
    return tx


def validate_inclusion_list_inputs(inputs: InclusionListInputs) -> None:
    """
    Reject malformed metadata without classifying transaction contents.

    Empty or duplicate envelopes, malformed memberships and claim fields
    are container errors. Invalid transaction contents remain omission
    candidates to classify, rather than invalid payloads or RPC requests.
    """
    if len(inputs.claims) > MAX_INCLUSION_LIST_CLAIMS:
        raise ValueError("Too many inclusion claims")
    for claim in inputs.claims:
        if len(claim.transaction_hash) != 32 or not 0 <= int(
            claim.transaction_index
        ) <= int(U64.MAX_VALUE):
            raise ValueError("Invalid inclusion claim")
    if not inputs.membership:
        if inputs.claims or inputs.replay_limits is not None:
            if inputs.transactions:
                raise ValueError("Profile 2 requires explicit membership")
        return
    if len(inputs.membership) != len(inputs.transactions):
        raise ValueError("Membership length differs from transaction count")
    envelopes = tuple(map(transaction_envelope, inputs.transactions))
    if any(not envelope for envelope in envelopes):
        raise ValueError("Empty inclusion-list envelope")
    if len(set(envelopes)) != len(envelopes):
        raise ValueError("Duplicate inclusion-list envelope")
    totals = [0] * INCLUSION_LIST_COMMITTEE_SIZE
    for envelope, membership in zip(envelopes, inputs.membership, strict=True):
        if len(membership) != 2 or not any(membership):
            raise ValueError("Invalid inclusion-list membership")
        bits = int.from_bytes(membership, "little")
        for position in range(INCLUSION_LIST_COMMITTEE_SIZE):
            if bits & (1 << position):
                totals[position] += len(envelope)
                if (
                    totals[position]
                    > MAX_TRANSACTIONS_BYTES_PER_INCLUSION_LIST
                ):
                    raise ValueError("Inclusion list exceeds its byte limit")


def evaluation_indices(
    inputs: InclusionListInputs, transaction_count: Uint
) -> Dict[Bytes32, Uint]:
    """Resolve unique claims; missing or duplicated hashes default to end."""
    counts = Counter(claim.transaction_hash for claim in inputs.claims)
    return {
        claim.transaction_hash: min(
            Uint(claim.transaction_index), transaction_count
        )
        for claim in inputs.claims
        if counts[claim.transaction_hash] == 1
    }


def snapshot_indices(
    inputs: InclusionListInputs,
    transaction_count: Uint,
    transactions: Tuple[LegacyTransaction | Bytes, ...] = (),
) -> Set[Uint]:
    """Retain only states named by claims for omitted frame candidates."""
    indices = {transaction_count}
    if inputs.replay_limits is None:
        return indices
    claims = evaluation_indices(inputs, transaction_count)
    included = set(map(transaction_envelope, transactions))
    for envelope in map(transaction_envelope, inputs.transactions):
        if envelope in included:
            continue
        index = claims.get(keccak256(envelope), transaction_count)
        if index in indices:
            continue
        try:
            tx = decode_inclusion_transaction(envelope)
            if (
                isinstance(tx, FrameTransaction)
                and classify_frame_candidate(tx) is not None
            ):
                indices.add(index)
        except (EthereumException, rlp_exceptions.DecodingError):
            continue
    return indices


def copy_inclusion_state(state: BlockState) -> BlockState:
    """Copy a block overlay, sharing its immutable pre-state provider."""
    return BlockState(
        pre_state=state.pre_state,
        account_reads=set(state.account_reads),
        account_writes=dict(state.account_writes),
        storage_reads=set(state.storage_reads),
        storage_writes={
            address: dict(slots)
            for address, slots in state.storage_writes.items()
        },
        code_writes=dict(state.code_writes),
        storage_clears=set(state.storage_clears),
    )


def capture_inclusion_list_state(
    block_env: vm.BlockEnvironment, block_output: vm.BlockOutput
) -> InclusionListSnapshot:
    """Capture validated execution's indexed state and gas counters."""
    return InclusionListSnapshot(
        copy_inclusion_state(block_env.state),
        block_output.block_gas_used,
        block_output.block_state_gas_used,
    )


def admitted_frame_candidates(
    inputs: InclusionListInputs,
) -> Dict[Bytes, FrameCandidate]:
    """Fill every membership position without pooling or refunding budgets."""
    if inputs.replay_limits is None or not inputs.membership:
        return {}
    envelopes = tuple(map(transaction_envelope, inputs.transactions))
    memberships = dict(zip(envelopes, inputs.membership, strict=True))
    candidates: Dict[Bytes, FrameCandidate] = {}
    for envelope in sorted(
        set(envelopes), key=lambda value: (keccak256(value), value)
    ):
        try:
            tx = decode_inclusion_transaction(envelope)
            if not isinstance(tx, FrameTransaction):
                continue
            candidate = classify_frame_candidate(tx)
        except (EthereumException, rlp_exceptions.DecodingError):
            continue
        if candidate is not None:
            candidates[envelope] = candidate

    admitted = {}
    signature_results: Dict[Bytes, bool] = {}
    for position in range(INCLUSION_LIST_COMMITTEE_SIZE):
        remaining = MAX_VERIFY_GAS_PER_IL
        for envelope, candidate in candidates.items():
            if not int.from_bytes(memberships[envelope], "little") & (
                1 << position
            ):
                continue
            signature_cost = candidate.signature_cost
            prefix_cost = candidate.execution_cost
            if signature_cost + prefix_cost > remaining:
                continue
            remaining -= signature_cost
            if envelope not in signature_results:
                signature_results[envelope] = verify_candidate_signatures(
                    candidate
                )
            if not signature_results[envelope]:
                continue
            remaining -= prefix_cost
            admitted[envelope] = candidate
    return admitted


def check_inclusion_list(
    block_env: vm.BlockEnvironment,
    transactions: Tuple[LegacyTransaction | Bytes, ...],
    inputs: InclusionListInputs,
    snapshots: Dict[Uint, InclusionListSnapshot],
) -> bool:
    """
    Evaluate this input context after validating the payload and its BAL.

    Replays use isolated overlays and do not change execution validity,
    the payload state, its access list, or one another. Missing snapshot
    or state data propagates to the caller; it never excuses omission.
    """
    from .fork import check_transaction

    validate_inclusion_list_inputs(inputs)
    included = set(map(transaction_envelope, transactions))
    end = ulen(transactions)
    claims = evaluation_indices(inputs, end)
    admitted = admitted_frame_candidates(inputs)

    for envelope in dict.fromkeys(
        map(transaction_envelope, inputs.transactions)
    ):
        if envelope in included:
            continue
        try:
            tx = decode_inclusion_transaction(envelope)
        except (EthereumException, rlp_exceptions.DecodingError):
            continue
        if isinstance(tx, BlobTransaction):
            continue
        index = end
        if isinstance(tx, FrameTransaction):
            if envelope not in admitted:
                continue
            index = claims.get(keccak256(envelope), end)
        snapshot = snapshots[index]
        replay_env = replace(
            block_env,
            state=copy_inclusion_state(snapshot.state),
            block_access_list_builder=BlockAccessListBuilder(),
        )
        replay_output = vm.BlockOutput(
            block_gas_used=snapshot.execution_gas_used,
            block_state_gas_used=snapshot.state_gas_used,
        )
        if isinstance(tx, FrameTransaction):
            assert inputs.replay_limits is not None
            if replay_frame_candidate(
                replay_env,
                replay_output,
                admitted[envelope],
                index,
                inputs.replay_limits,
            ):
                return False
        else:
            try:
                tx_chain_id = chain_id(tx)
                if (
                    tx_chain_id is not None
                    and tx_chain_id != block_env.chain_id
                ):
                    continue
                check_transaction(replay_env, replay_output, tx, index)
            except EthereumException:
                continue
            return False
    return True
