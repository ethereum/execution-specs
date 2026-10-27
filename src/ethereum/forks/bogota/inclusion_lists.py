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
from functools import cached_property
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
"""Maximum total envelope bytes in one inclusion list."""

MAX_OMISSION_CLAIMS = 2**12
"""Maximum number of claims in the revealed ordered list."""

MAX_VERIFY_GAS_PER_IL = Uint(2**20)
"""Execution-work allowance for each independent inclusion-list fill."""


@final
@dataclass(frozen=True)
class OmissionClaim:
    """Identify a transaction and its claimed insertion index."""

    transaction_hash: Bytes32
    evaluation_index: U64


@final
@dataclass(frozen=True)
class InclusionListInputs:
    """
    Carry separate selected ILs and the authenticated omission claims.

    The legacy flat transaction field supports Profile-1-only test tools.
    Consensus callers supply exactly one list per committee position.
    """

    transactions: Tuple[LegacyTransaction | Bytes, ...] = ()
    inclusion_lists: (
        Tuple[Tuple[LegacyTransaction | Bytes, ...], ...] | None
    ) = None
    claims: Tuple[OmissionClaim, ...] = ()

    @cached_property
    def admitted_candidates(self) -> Dict[Bytes, FrameCandidate]:
        """Reuse the static fill for snapshot selection and later replay."""
        return admitted_frame_candidates(self)

    @property
    def all_transactions(self) -> Tuple[LegacyTransaction | Bytes, ...]:
        """Return all entries for deduplication by the evaluation rules."""
        if self.inclusion_lists is None:
            return self.transactions
        return tuple(tx for il in self.inclusion_lists for tx in il)


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

    Empty envelopes, malformed lists and claim fields are container errors.
    Invalid transaction contents remain omission
    candidates to classify, rather than invalid payloads or RPC requests.
    """
    if len(inputs.claims) > MAX_OMISSION_CLAIMS:
        raise ValueError("Too many omission claims")
    for claim in inputs.claims:
        if len(claim.transaction_hash) != 32 or not 0 <= int(
            claim.evaluation_index
        ) <= int(U64.MAX_VALUE):
            raise ValueError("Invalid omission claim")
    if inputs.inclusion_lists is None:
        if inputs.claims:
            raise ValueError("Profile 2 requires separate inclusion lists")
        return
    if inputs.transactions:
        raise ValueError("Cannot combine flat and separate inclusion lists")
    if len(inputs.inclusion_lists) != INCLUSION_LIST_COMMITTEE_SIZE:
        raise ValueError("Expected one inclusion list per committee position")
    for inclusion_list in inputs.inclusion_lists:
        envelopes = tuple(map(transaction_envelope, inclusion_list))
        if any(not envelope for envelope in envelopes):
            raise ValueError("Empty inclusion-list envelope")
        if (
            sum(map(len, envelopes))
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
            Uint(claim.evaluation_index), transaction_count
        )
        for claim in inputs.claims
        if counts[claim.transaction_hash] == 1
    }


def snapshot_indices(
    inputs: InclusionListInputs,
    transaction_count: Uint,
    transactions: Tuple[LegacyTransaction | Bytes, ...] = (),
) -> Set[Uint]:
    """Retain only states needed by omitted, admitted frame candidates."""
    indices = {transaction_count}
    if inputs.inclusion_lists is None:
        return indices
    claims = evaluation_indices(inputs, transaction_count)
    included = set(map(transaction_envelope, transactions))
    for envelope in inputs.admitted_candidates:
        if envelope not in included:
            indices.add(claims.get(keccak256(envelope), transaction_count))
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
    """Fill each separate list without pooling or refunding budgets."""
    if inputs.inclusion_lists is None:
        return {}
    envelopes = tuple(map(transaction_envelope, inputs.all_transactions))
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
    for inclusion_list in inputs.inclusion_lists:
        members = set(map(transaction_envelope, inclusion_list))
        remaining = MAX_VERIFY_GAS_PER_IL
        for envelope, candidate in candidates.items():
            if envelope not in members:
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
    admitted = inputs.admitted_candidates

    for envelope in dict.fromkeys(
        map(transaction_envelope, inputs.all_transactions)
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
            if replay_frame_candidate(
                replay_env, replay_output, admitted[envelope], index
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
