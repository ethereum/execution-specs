"""
Tests for EIP-7708 fork transition behavior.

Tests that verify transfer logs are emitted correctly at the Amsterdam fork
transition boundary.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Op,
    Transaction,
    TransactionReceipt,
    compute_create_address,
)

from .spec import ref_spec_7708, transfer_log

REFERENCE_SPEC_GIT_PATH = ref_spec_7708.git_path
REFERENCE_SPEC_VERSION = ref_spec_7708.version


@pytest.mark.valid_at_transition_to("EIP7708")
def test_transfer_log_fork_transition(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    Test ETH transfer log behavior at fork transition.

    Before Amsterdam: ETH transfers do NOT emit logs.
    At/after Amsterdam: ETH transfers emit Transfer logs.
    """
    sender = pre.fund_eoa()
    recipient = pre.nonexistent_account()

    blocks = [
        Block(
            timestamp=14_999,
            txs=[
                Transaction(
                    to=recipient,
                    sender=sender,
                    value=100,
                    expected_receipt=TransactionReceipt(logs=[]),
                )
            ],
        ),
        Block(
            timestamp=15_000,
            txs=[
                Transaction(
                    to=recipient,
                    sender=sender,
                    value=100,
                    expected_receipt=TransactionReceipt(
                        logs=[transfer_log(sender, recipient, 100)]
                    ),
                )
            ],
        ),
        Block(
            timestamp=15_001,
            txs=[
                Transaction(
                    to=recipient,
                    sender=sender,
                    value=100,
                    expected_receipt=TransactionReceipt(
                        logs=[transfer_log(sender, recipient, 100)]
                    ),
                )
            ],
        ),
    ]

    blockchain_test(
        pre=pre,
        blocks=blocks,
        post={
            recipient: Account(balance=300),
        },
    )


@pytest.mark.parametrize(
    "emission_point",
    [
        pytest.param("call", id="call"),
        pytest.param("create", id="create"),
        pytest.param("selfdestruct", id="selfdestruct"),
    ],
)
@pytest.mark.valid_at_transition_to("EIP7708")
def test_emission_point_fork_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    emission_point: str,
) -> None:
    """
    Test the CALL, CREATE, and SELFDESTRUCT emission points at the fork
    transition boundary.

    Clients gate each emission site in a separate code path, so every
    site is checked at the transition independently of the
    transaction-level log.
    """
    sender = pre.fund_eoa()
    value = 100
    recipient = pre.deploy_contract(Op.STOP)

    if emission_point == "call":
        code = Op.CALL(address=recipient, value=Op.CALLVALUE)
    elif emission_point == "create":
        code = Op.CREATE(value=Op.CALLVALUE, offset=0, size=0)
    else:
        code = Op.SELFDESTRUCT(recipient)
    contract = pre.deploy_contract(code)

    blocks = []
    for nonce, (timestamp, active) in enumerate(
        [(14_999, False), (15_000, True), (15_001, True)], start=1
    ):
        if emission_point == "create":
            inner_recipient = compute_create_address(
                address=contract, nonce=nonce
            )
        else:
            inner_recipient = recipient
        logs = (
            [
                transfer_log(sender, contract, value),
                transfer_log(contract, inner_recipient, value),
            ]
            if active
            else []
        )
        blocks.append(
            Block(
                timestamp=timestamp,
                txs=[
                    Transaction(
                        to=contract,
                        sender=sender,
                        value=value,
                        expected_receipt=TransactionReceipt(logs=logs),
                    )
                ],
            )
        )

    if emission_point == "create":
        post = {
            compute_create_address(address=contract, nonce=nonce): Account(
                balance=value
            )
            for nonce in (1, 2, 3)
        }
    else:
        post = {recipient: Account(balance=3 * value)}

    blockchain_test(pre=pre, blocks=blocks, post=post)
