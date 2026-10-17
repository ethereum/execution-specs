"""
Tests for how the EELS t8n tool handles rejected transactions.

A transaction that is rejected during admission must leave no trace in the
block: the roots and (post-Amsterdam) the block access list index must be
identical to those of a run that never received the rejected transaction.
"""

from typing import Any, List

import pytest

from execution_testing.base_types import Address, Hash, to_json
from execution_testing.client_clis import TransitionTool
from execution_testing.forks import (
    Amsterdam,
    Berlin,
    Byzantium,
    Cancun,
    Constantinople,
    Fork,
    Frontier,
    Homestead,
    Istanbul,
    London,
    Paris,
    Prague,
    Shanghai,
)
from execution_testing.test_types import (
    EOA,
    Account,
    Alloc,
    Environment,
    Transaction,
)

SENDER_KEY = 0x1111111111111111111111111111111111111111111111111111111111111111
RECIPIENT = Address(0x1000000000000000000000000000000000000001)


def _tx(**overrides: Any) -> Transaction:
    """Return a signed legacy transfer, with some fields overridden."""
    fields: dict[str, Any] = {
        "nonce": 0,
        "gas_price": 10,
        "gas_limit": 21_000,
        "to": RECIPIENT,
        "value": 1,
        "protected": False,
        "secret_key": SENDER_KEY,
    }
    return Transaction(**{**fields, **overrides}).with_signature_and_sender()


# Each way of rejecting a transaction raises from a different place in
# `process_transaction`. The sender nonce is the one the transaction would
# have if it were accepted, so only the override makes it invalid.
REJECTIONS = {
    "nonce-too-high": {"nonce": 9},
    "insufficient-balance": {"value": 10**19},
    "gas-below-intrinsic": {"gas_limit": 20_999},
    "gas-above-block-limit": {"gas_limit": 30_000_001},
}


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


@pytest.mark.parametrize(
    "fork",
    [
        Frontier,
        Homestead,
        Byzantium,
        Constantinople,
        Istanbul,
        Berlin,
        London,
        Paris,
        Shanghai,
        Cancun,
        Prague,
        Amsterdam,
    ],
)
@pytest.mark.parametrize(
    "rejection", REJECTIONS.values(), ids=REJECTIONS.keys()
)
@pytest.mark.parametrize(
    "position,count",
    [
        pytest.param(1, 3, id="rejected-in-the-middle"),
        pytest.param(1, 2, id="rejected-last"),
        pytest.param(0, 3, id="rejected-first"),
        pytest.param(0, 1, id="only-rejected"),
    ],
)
def test_rejected_tx_leaves_no_trace_in_roots(
    default_t8n: TransitionTool,
    fork: Fork,
    position: int,
    count: int,
    rejection: dict[str, Any],
) -> None:
    """
    The body, roots, receipts and block access list of a run with a rejected
    transaction equal those of a run with only the accepted transactions.
    """
    # `count` transactions in total, of which the one at `position` is
    # rejected. The accepted ones keep the nonces they have in a run that
    # never saw the rejected one.
    accepted_only = [_tx(nonce=nonce) for nonce in range(count - 1)]
    with_rejected = [
        *accepted_only[:position],
        _tx(**{"nonce": position, **rejection}),
        *accepted_only[position:],
    ]

    output = _run(default_t8n, fork, with_rejected)
    expected_output = _run(default_t8n, fork, accepted_only)
    result, expected = output.result, expected_output.result

    assert [r.index for r in result.rejected_transactions] == [position]
    assert output.body == expected_output.body
    assert result.transactions_trie == expected.transactions_trie
    assert result.receipts_root == expected.receipts_root
    assert result.gas_used == expected.gas_used
    assert to_json(result.state_root) == to_json(expected.state_root)
    assert result.block_access_list == expected.block_access_list
