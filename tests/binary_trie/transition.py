"""
State-tree transition helpers used by binary-tree reorg tests.

The production MPT -> PBT migration requires the verified snapshot and
preimage machinery described by EIP-8347. The in-memory EELS MPT already
retains those original account and storage keys in ``Trie._data``, so tests
can model the activation boundary deterministically without pretending to
implement snapshot distribution or BAL replay.

The conversion deliberately copies every mutable mapping. The MPT snapshot
therefore remains usable after the returned PBT state advances, which is the
property a reorg across the activation boundary depends on.
"""

from ethereum import state_mpt, state_pbt


def pbt_from_mpt_snapshot(state: state_mpt.State) -> state_pbt.State:
    """
    Return a PBT state cloned from an in-memory MPT snapshot.

    Storage without a live account is omitted, matching the PBT embedding
    rule that storage belongs to an account. The source MPT state is never
    mutated or aliased through a mutable mapping.
    """
    accounts = {
        address: account
        for address, account in state._main_trie._data.items()
        if account is not None
    }
    storage = {
        address: dict(trie._data)
        for address, trie in state._storage_tries.items()
        if address in accounts and trie._data
    }

    return state_pbt.State(
        _accounts=dict(accounts),
        _storage=storage,
        _code_store=dict(state._code_store),
    )
