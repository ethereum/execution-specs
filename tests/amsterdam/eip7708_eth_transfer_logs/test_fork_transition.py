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

from .spec import burn_log, ref_spec_7708, transfer_log

REFERENCE_SPEC_GIT_PATH = ref_spec_7708.git_path
REFERENCE_SPEC_VERSION = ref_spec_7708.version


@pytest.mark.parametrize(
    "same_tx,to_self",
    [
        pytest.param(True, True, id="same_tx_to_self"),
        pytest.param(False, True, id="pre_existing_to_self"),
        pytest.param(False, False, id="pre_existing_to_other"),
    ],
)
@pytest.mark.valid_at_transition_to("EIP7708")
def test_burn_log_at_fork_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    same_tx: bool,
    to_self: bool,
) -> None:
    """
    Test burn log emission across the EIP-7708 fork transition.

    same_tx_to_self: Factory CREATEs and selfdestructs to self in one tx.
    At/after Amsterdam emits a CREATE transfer log + Burn log.

    pre_existing_to_self: Pre-existing contract selfdestructs to self.
    No logs at any fork — SELFDESTRUCT to same account emits nothing.

    pre_existing_to_other: Pre-existing contract selfdestructs to a different
    account. At/after Amsterdam emits a Transfer log.
    """
    sender = pre.fund_eoa()
    contract_balance = 1000

    if same_tx:
        initcode = Op.SELFDESTRUCT(Op.ADDRESS)
        initcode_bytes = bytes(initcode)
        initcode_len = len(initcode_bytes)

        factory_code = Op.MSTORE(
            0, Op.PUSH32(initcode_bytes.rjust(32, b"\x00"))
        ) + Op.CREATE(
            value=contract_balance, offset=32 - initcode_len, size=initcode_len
        )

        factory = pre.deploy_contract(
            factory_code, balance=contract_balance * 3
        )
        created = [
            compute_create_address(address=factory, nonce=n)
            for n in range(1, 4)
        ]
        targets = [factory] * 3

        expected_logs = [
            [],
            [
                transfer_log(factory, created[1], contract_balance),
                burn_log(created[1], contract_balance),
            ],
            [
                transfer_log(factory, created[2], contract_balance),
                burn_log(created[2], contract_balance),
            ],
        ]
        post: dict = {
            sender: Account(nonce=3),
            created[0]: Account.NONEXISTENT,
            created[1]: Account.NONEXISTENT,
            created[2]: Account.NONEXISTENT,
        }
    elif to_self:
        targets = [
            pre.deploy_contract(
                Op.SELFDESTRUCT(Op.ADDRESS), balance=contract_balance
            )
            for _ in range(3)
        ]
        expected_logs = [[], [], []]
        post = {sender: Account(nonce=3)}
    else:
        beneficiary = pre.nonexistent_account()
        targets = [
            pre.deploy_contract(
                Op.SELFDESTRUCT(beneficiary), balance=contract_balance
            )
            for _ in range(3)
        ]
        expected_logs = [
            [],
            [transfer_log(targets[1], beneficiary, contract_balance)],
            [transfer_log(targets[2], beneficiary, contract_balance)],
        ]
        post = {
            sender: Account(nonce=3),
            beneficiary: Account(balance=contract_balance * 3),
        }

    blocks = [
        Block(
            timestamp=ts,
            txs=[
                Transaction(
                    to=targets[i],
                    sender=sender,
                    gas_limit=200_000,
                    expected_receipt=TransactionReceipt(logs=expected_logs[i]),
                )
            ],
        )
        for i, ts in enumerate([14_999, 15_000, 15_001])
    ]

    blockchain_test(pre=pre, blocks=blocks, post=post)


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
