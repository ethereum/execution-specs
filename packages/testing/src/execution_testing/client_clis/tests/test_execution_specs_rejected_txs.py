"""
Tests for how the EELS t8n tool handles rejected transactions.

A transaction that is rejected during admission must leave no trace in the
block: the roots and (post-Amsterdam) the block access list index must be
identical to those of a run that never received the rejected transaction.
"""

from typing import Any, Callable, List

import pytest

from execution_testing.base_types import Address, Hash, to_json
from execution_testing.client_clis import TransitionTool
from execution_testing.forks import Amsterdam, Berlin, Cancun, Fork, Prague
from execution_testing.test_types import (
    EOA,
    Account,
    Alloc,
    Environment,
    Transaction,
)

SENDER_KEY = 0x1111111111111111111111111111111111111111111111111111111111111111
RECIPIENT = Address(0x1000000000000000000000000000000000000001)


def _tx(nonce: int) -> Transaction:
    return Transaction(
        nonce=nonce,
        gas_price=10,
        gas_limit=21_000,
        to=RECIPIENT,
        value=1,
        secret_key=SENDER_KEY,
    ).with_signature_and_sender()


def _run(t8n: TransitionTool, fork: Fork, txs: List[Transaction]) -> Any:
    sender = EOA(key=SENDER_KEY)
    alloc = Alloc(
        {
            **fork.pre_allocation_blockchain(),
            sender: Account(balance=10**18),
        }
    )
    env = Environment(
        fee_recipient=Address(0xC94F5374FCE5EDBC8E2A8697C15331677E6EBF0B),
        gas_limit=30_000_000,
        number=1,
        timestamp=1000,
        difficulty=0x20000,
        prev_randao=0,
        base_fee_per_gas=7,
        excess_blob_gas=0,
        parent_beacon_block_root=0,
        parent_difficulty=0,
        block_hashes={0: Hash(0)},
    )
    return t8n.evaluate(
        transition_tool_data=TransitionTool.TransitionToolData(
            alloc=alloc,
            txs=txs,
            env=env,
            fork=fork,
            chain_id=1,
            reward=0,
            blob_schedule=fork.blob_schedule(),
        ),
    )


@pytest.mark.parametrize("fork", [Berlin, Cancun, Prague, Amsterdam])
@pytest.mark.parametrize(
    "build",
    [
        pytest.param(
            lambda: ([_tx(0), _tx(9), _tx(1)], [_tx(0), _tx(1)], [1]),
            id="rejected-in-the-middle",
        ),
        pytest.param(
            lambda: ([_tx(0), _tx(9)], [_tx(0)], [1]),
            id="rejected-last",
        ),
        pytest.param(
            lambda: ([_tx(9), _tx(0), _tx(1)], [_tx(0), _tx(1)], [0]),
            id="rejected-first",
        ),
    ],
)
def test_rejected_tx_leaves_no_trace_in_roots(
    default_t8n: TransitionTool,
    fork: Fork,
    build: Callable[[], Any],
) -> None:
    """
    Roots and receipts of a run with a rejected transaction equal those of
    a run containing only the accepted transactions.
    """
    with_rejected, accepted_only, rejected_indexes = build()

    result = _run(default_t8n, fork, with_rejected).result
    expected = _run(default_t8n, fork, accepted_only).result

    assert [r.index for r in result.rejected_transactions] == rejected_indexes
    assert result.transactions_trie == expected.transactions_trie
    assert result.receipts_root == expected.receipts_root
    assert result.gas_used == expected.gas_used
    assert to_json(result.state_root) == to_json(expected.state_root)
    assert result.block_access_list == expected.block_access_list
