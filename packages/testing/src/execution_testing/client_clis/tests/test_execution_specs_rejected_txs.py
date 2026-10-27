"""
Tests for how the EELS t8n tool handles rejected transactions.

A transaction that is rejected during admission must leave no trace in the
block: the body, the roots and (post-Amsterdam) the block access list index
must be identical to those of a run that never received the rejected
transaction.
"""

from typing import Any, List

import pytest
from ethereum_rlp import rlp

from execution_testing.base_types import Address, Hash, to_json
from execution_testing.client_clis import TransitionTool
from execution_testing.forks import (
    Fork,
    get_deployed_forks,
    get_development_forks,
)
from execution_testing.recipient_type import RecipientType
from execution_testing.test_types import (
    EOA,
    Account,
    Alloc,
    AuthorizationTuple,
    Blob,
    Environment,
    Transaction,
)

SENDER_KEY = 0x1111111111111111111111111111111111111111111111111111111111111111
AUTHORITY_KEY = (
    0x2222222222222222222222222222222222222222222222222222222222222222
)
RECIPIENT = Address(0x1000000000000000000000000000000000000001)
# Below the EIP-7825 transaction gas cap, so a transaction over the block
# limit is rejected for that and not for the cap.
BLOCK_GAS_LIMIT = 1_000_000


def _type_fields(fork: Fork, tx_type: int) -> dict[str, Any]:
    """Return the fields a transfer of this type needs to be valid."""
    if tx_type in (0, 1, 2):
        return {}
    elif tx_type == 3:
        return {
            "max_fee_per_blob_gas": 10**9,
            "blob_versioned_hashes": [Blob.from_fork(fork).versioned_hash],
        }
    elif tx_type == 4:
        return {
            "authorization_list": [
                AuthorizationTuple(
                    chain_id=1,
                    address=RECIPIENT,
                    nonce=0,
                    signer=EOA(key=AUTHORITY_KEY),
                )
            ]
        }
    raise NotImplementedError(
        f"{fork.name()} has transaction type {tx_type}, which this test "
        "cannot build yet. Add the fields it needs here."
    )


def _intrinsic_gas(fork: Fork, tx_type: int) -> int:
    """Return the intrinsic gas of a transfer to the funded recipient."""
    return fork.transaction_intrinsic_cost_calculator()(
        authorization_list_or_count=_type_fields(fork, tx_type).get(
            "authorization_list"
        ),
        sends_value=True,
        recipient_type=RecipientType.EOA,
    )


def _tx(fork: Fork, tx_type: int, **overrides: Any) -> Transaction:
    """Return a signed transfer, with some fields overridden."""
    fields: dict[str, Any] = {
        "ty": tx_type,
        "nonce": 0,
        "gas_limit": _intrinsic_gas(fork, tx_type),
        "to": RECIPIENT,
        "value": 1,
        "protected": False,
        "secret_key": SENDER_KEY,
        **_type_fields(fork, tx_type),
    }
    return Transaction(**{**fields, **overrides}).with_signature_and_sender()


def _rejection(fork: Fork, tx_type: int, rejection: str) -> dict[str, Any]:
    """
    Return the fields that make a transfer invalid. Each way of rejecting a
    transaction raises from a different place in `process_transaction`.
    The nonce is the one the transaction would have if it were accepted, so
    only these fields make it invalid.
    """
    if rejection == "nonce-too-high":
        return {"nonce": 9}
    elif rejection == "insufficient-balance":
        return {"value": 10**19}
    elif rejection == "gas-below-intrinsic":
        return {"gas_limit": _intrinsic_gas(fork, tx_type) - 1}
    elif rejection == "gas-above-block-limit":
        return {"gas_limit": BLOCK_GAS_LIMIT + 1}
    raise ValueError(f"unknown rejection: {rejection}")


def _run(t8n: TransitionTool, fork: Fork, txs: List[Transaction]) -> Any:
    sender = EOA(key=SENDER_KEY)
    alloc = Alloc(
        {
            **fork.pre_allocation_blockchain(),
            sender: Account(balance=10**18),
            RECIPIENT: Account(balance=1),
        }
    )
    env = Environment(
        fee_recipient=Address(0xC94F5374FCE5EDBC8E2A8697C15331677E6EBF0B),
        gas_limit=BLOCK_GAS_LIMIT,
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
            inclusion_list_txs=(
                []
                if fork.engine_new_payload_inclusion_list_transactions()
                else None
            ),
        ),
    )


# BPO forks change only blob parameters, which nothing here depends on.
FORKS = [
    fork
    for fork in get_deployed_forks() + get_development_forks()
    if not fork.bpo_fork()
]


@pytest.mark.parametrize(
    "fork,tx_type",
    [
        pytest.param(fork, tx_type, id=f"{fork.name()}-type-{tx_type}")
        for fork in FORKS
        for tx_type in fork.tx_types()
    ],
)
@pytest.mark.parametrize(
    "rejection",
    [
        "nonce-too-high",
        "insufficient-balance",
        "gas-below-intrinsic",
        "gas-above-block-limit",
    ],
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
    tx_type: int,
    position: int,
    count: int,
    rejection: str,
) -> None:
    """
    The body, roots, receipts and block access list of a run with a rejected
    transaction equal those of a run with only the accepted transactions.
    """
    # `count` transactions in total, of which the one at `position` is
    # rejected. The accepted ones keep the nonces they have in a run that
    # never saw the rejected one.
    accepted_only = [
        _tx(fork, tx_type, nonce=nonce) for nonce in range(count - 1)
    ]
    with_rejected = [
        *accepted_only[:position],
        _tx(
            fork,
            tx_type,
            **{"nonce": position, **_rejection(fork, tx_type, rejection)},
        ),
        *accepted_only[position:],
    ]

    output = _run(default_t8n, fork, with_rejected)
    expected_output = _run(default_t8n, fork, accepted_only)
    result, expected = output.result, expected_output.result

    assert [r.index for r in result.rejected_transactions] == [position]
    assert output.body == expected_output.body
    assert output.body == rlp.encode(
        [tx.serializable_list for tx in accepted_only]
    )
    assert result.transactions_trie == expected.transactions_trie
    assert result.receipts_root == expected.receipts_root
    assert result.gas_used == expected.gas_used
    assert result.blob_gas_used == expected.blob_gas_used
    assert to_json(result.state_root) == to_json(expected.state_root)
    assert result.block_access_list == expected.block_access_list
