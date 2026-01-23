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
)

from .spec import ref_spec_7708, selfdestruct_log, transfer_log

REFERENCE_SPEC_GIT_PATH = ref_spec_7708.git_path
REFERENCE_SPEC_VERSION = ref_spec_7708.version


@pytest.mark.valid_at_transition_to("Amsterdam")
def test_selfdestruct_log_at_fork_transition(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    Test ETH selfdestruct log behavior at fork transition.

    Before Amsterdam: ETH selfdestructs do NOT emit logs.
    At/after Amsterdam: ETH selfdestructs emit Selfdestruct logs.
    """
    sender = pre.fund_eoa()
    contract1 = pre.deploy_contract(Op.SELFDESTRUCT(Op.ADDRESS), balance=1)
    contract2 = pre.deploy_contract(Op.SELFDESTRUCT(Op.ADDRESS), balance=2)
    contract3 = pre.deploy_contract(Op.SELFDESTRUCT(Op.ADDRESS), balance=3)

    blocks = [
        Block(
            timestamp=14_999,
            txs=[
                Transaction(
                    to=contract1,
                    sender=sender,
                    gas_limit=100_000,
                    expected_receipt=TransactionReceipt(logs=[]),
                )
            ],
        ),
        Block(
            timestamp=15_000,
            txs=[
                Transaction(
                    to=contract2,
                    sender=sender,
                    gas_limit=100_000,
                    expected_receipt=TransactionReceipt(
                        logs=[selfdestruct_log(contract2, 2)]
                    ),
                )
            ],
        ),
        Block(
            timestamp=15_001,
            txs=[
                Transaction(
                    to=contract3,
                    sender=sender,
                    gas_limit=100_000,
                    expected_receipt=TransactionReceipt(
                        logs=[selfdestruct_log(contract3, 3)]
                    ),
                )
            ],
        ),
    ]

    blockchain_test(
        pre=pre,
        blocks=blocks,
        post={
            sender: Account(nonce=3),
        },
    )


@pytest.mark.valid_at_transition_to("Amsterdam")
def test_transfer_log_fork_transition(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    Test ETH transfer log behavior at fork transition.

    Before Amsterdam: ETH transfers do NOT emit logs.
    At/after Amsterdam: ETH transfers emit Transfer logs.
    """
    sender = pre.fund_eoa()
    recipient = pre.empty_account()

    blocks = [
        Block(
            timestamp=14_999,
            txs=[
                Transaction(
                    to=recipient,
                    sender=sender,
                    value=100,
                    gas_limit=21_000,
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
                    gas_limit=21_000,
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
                    gas_limit=21_000,
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
