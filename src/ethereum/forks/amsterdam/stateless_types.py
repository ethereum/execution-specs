"""
Stateless validation types.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from ethereum_types.bytes import Bytes, Bytes32
from ethereum_types.frozen import slotted_freezable
from ethereum_types.numeric import U256, Uint

from ethereum.crypto.hash import Hash32
from ethereum.forks.amsterdam.incremental_mpt import IncrementalMPT, build_mpt, mpt_get, mpt_root, mpt_set
from ethereum.forks.amsterdam.trie import EMPTY_TRIE_ROOT, Trie, trie_get
from ethereum.state import Account, Address, PreState, Root

from .state_tracker import BlockState


@slotted_freezable
@dataclass
class ExecutionWitness:
    """
    Execution witness data for stateless validation.
    """

    state: Tuple[Bytes, ...]
    """
    Hashed trie-node preimages needed during execution and state-root
    recomputation.
    """

    codes: Tuple[Bytes, ...]
    """
    Contract-code preimages (created or accessed) needed during execution.
    """

    headers: Tuple[Bytes, ...]
    """
    RLP-encoded block headers used for pre-state and ``BLOCKHASH`` correctness
    proofs. This may trend toward empty EIP-7709.
    """


@dataclass
class ExecutionWitnessBuilder:
    """
    Mutable accumulator for execution witness data during block execution.
    """

    pre_state_accounts_data: Trie[Address, Optional[Account]]
    pre_state_storages_data: Dict[Address, Trie[Bytes32, U256]]
    blockchain_headers: List[Bytes] = field(default_factory=list)


def build_execution_witness(
    builder: ExecutionWitnessBuilder,
    block_state: BlockState,
) -> ExecutionWitness:
    """
    Build the execution witness from the accumulated builder data.

    Sort state and codes lexicographically, headers by block number
    ascending.
    """
    ancestor_headers = get_witness_ancestors(
        builder.blockchain_headers,
        block_state.oldest_ancestor_offset,
    )
    codes = get_witness_codes(block_state.code_reads, block_state.pre_state)

    # Build account and storages IncrementalMPTs from pre-state flat data.
    incr_storage_mpts: Dict[Address, IncrementalMPT[Bytes32, U256]] = {}
    for address, data in builder.pre_state_storages_data.items():
        incr_storage_mpts[address] = build_mpt(
            data._data, secured=True, default=U256(0)
        )

    def get_pre_storage_root(address: Address) -> Root:
        if address in incr_storage_mpts:
            return mpt_root(incr_storage_mpts[address])
        return EMPTY_TRIE_ROOT

    incr_account_mpt = build_mpt(
        builder.pre_state_accounts_data._data,
        secured=True,
        default=None,
        get_storage_root=get_pre_storage_root,
    )

    # 1. Traverse all accessed and dirty storage keys on the pre-state
    # MPTs to capture pre-state trie nodes in the witness. This must
    # happen before any writes since writes mutate the tree in-place.
    all_storage_accesses: Dict[Address, Set[Bytes32]] = {}
    for address, key in block_state.storage_reads:
        all_storage_accesses.setdefault(address, set()).add(key)
    for address, slots in block_state.storage_writes.items():
        all_storage_accesses.setdefault(address, set()).update(slots)

    for address, keys in all_storage_accesses.items():
        if address not in incr_storage_mpts:
            continue
        for key in keys:
            mpt_get(incr_storage_mpts[address], key)

    # 2. Apply dirty storage to storages (writes)
    for address, dirty_keys in block_state.storage_writes.items():
        if address not in incr_storage_mpts:
            # New storage created during block
            incr_storage_mpts[address] = build_mpt(
                {}, secured=True, default=U256(0)
            )

        # We do two passes to ensure deletions are processed after
        # inserts/updates to minimize the number of nodes touched
        # in the MPT.
        # First pass: inserts and updates
        for key, value in dirty_keys.items():
            if value != 0:
                mpt_set(incr_storage_mpts[address], key, value)
        # Second pass: deletions
        for key, value in dirty_keys.items():
            if value == 0:
                mpt_set(incr_storage_mpts[address], key, value)

    # Accounts are "dirty" if:
    # - Account fields changed (nonce/balance/code) - tracked in dirty_accounts
    # - Storage changed (storage root changed) - tracked in dirty_storage
    all_dirty_accounts = (
        set(block_state.account_writes.keys())
        | set(block_state.storage_writes.keys())
    )

    # 3. Traverse all accessed and dirty accounts on the pre-state MPT
    # to capture pre-state trie nodes before writes mutate the tree.
    for address in block_state.account_reads | all_dirty_accounts:
        mpt_get(incr_account_mpt, address)

    # 4. Apply dirty accounts
    for address in all_dirty_accounts:
        # Get post-state account data
        if address in block_state.account_writes:
            account = block_state.account_writes[address]
        else:
            account = (
                block_state.pre_state.get_account_optional(address)
            )

        # Get storage root for this account
        if address in incr_storage_mpts:
            addr_storage_root = mpt_root(incr_storage_mpts[address])
        else:
            addr_storage_root = EMPTY_TRIE_ROOT

        def get_storage_root_fn(
            _: Address, sr: Root = addr_storage_root
        ) -> Root:
            return sr

        mpt_set(
            incr_account_mpt,
            address,
            account,
            get_storage_root=get_storage_root_fn,
        )

    # Collect witness from all MPTs
    accessed_nodes=dict(incr_account_mpt.witness.accessed_nodes)
    for mpt in incr_storage_mpts.values():
       accessed_nodes.update(mpt.witness.accessed_nodes)

    return ExecutionWitness(
        state=tuple(sorted(accessed_nodes.values())),
        codes=tuple(codes),
        headers=tuple(ancestor_headers),
    )


def get_witness_codes(
    code_reads: Set[Tuple[Address, Hash32]],
    pre_state: PreState,
) -> List[Bytes]:
    """
    Collect bytecodes from the pre-state for all code reads during execution.

    Include a code hash only when the same address already had that code in the
    pre-state. This avoids accidentally including bytecode created during the
    current block when the same hash already exists elsewhere.

    Parameters
    ----------
    code_reads :
        Code reads as ``(address, code_hash)`` during block execution.
    pre_state :
        The pre-execution state.

    """
    witness_code_hashes: Set[Hash32] = set()
    for address, code_hash in code_reads:
        pre_account = pre_state.get_account_optional(address)
        if pre_account is None or pre_account.code_hash != code_hash:
            continue
        witness_code_hashes.add(code_hash)

    codes: List[Bytes] = []
    for code_hash in witness_code_hashes:
        try:
            codes.append(pre_state.get_code(code_hash))
        except KeyError:
            pass
    return sorted(codes)


def get_witness_ancestors(
    block_headers: List[Bytes],
    oldest_ancestor_offset: Optional[Uint],
) -> List[Bytes]:
    """
    Collect RLP-encoded ancestor headers from ``oldest_ancestor_offset``
    blocks back onward.

    Parameters
    ----------
    block_headers :
        RLP-encoded headers.
    oldest_ancestor_offset :
        Offset from the current block to the oldest ancestor accessed
        during execution, or ``None`` if no ancestor was accessed.

    """
    if oldest_ancestor_offset is None:
        return []
    return list(block_headers[-int(oldest_ancestor_offset) :])
