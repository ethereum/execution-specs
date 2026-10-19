"""
Cross-EIP tests for EIP-7928 block-level access lists and EIP-7708
transfer logs.

A single block pins both views of the same value flows: the receipts
carry the EIP-7708 Transfer logs while the block access list carries the
matching balance changes, and the priority-fee payment appears in the
access list only, with no Transfer log.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    BalAccountExpectation,
    BalBalanceChange,
    BalNonceChange,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    Environment,
    Fork,
    Header,
    Op,
    RecipientType,
    Transaction,
    TransactionReceipt,
)

from ..eip7708_eth_transfer_logs.spec import Spec as Spec7708
from ..eip7708_eth_transfer_logs.spec import transfer_log
from .spec import ref_spec_7928

REFERENCE_SPEC_GIT_PATH = ref_spec_7928.git_path
REFERENCE_SPEC_VERSION = ref_spec_7928.version

pytestmark = pytest.mark.valid_from("Amsterdam")


def test_transfer_logs_and_bal_balance_changes(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
) -> None:
    """
    Ensure Transfer logs and BAL balance changes stay consistent within
    one block.

    The first transaction is a plain value transfer paying a priority
    fee: both parties get BAL balance changes, the receipt carries one
    Transfer log, and the coinbase tip appears in the BAL only. The
    second transaction sweeps a contract balance via SELFDESTRUCT with a
    zero tip: the sweep shows up both as a Transfer log and as BAL
    balance changes, while the coinbase entry stays fee-only from the
    first transaction.
    """
    coinbase = pre.fund_eoa(amount=0)

    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    intrinsic_gas = intrinsic_gas_calculator(
        calldata=b"",
        contract_creation=False,
        access_list=[],
        recipient_type=RecipientType.EMPTY_ACCOUNT,
        sends_value=True,
    )
    top_frame_state_gas = fork.transaction_top_frame_state_gas(
        sends_value=True,
        recipient_type=RecipientType.EMPTY_ACCOUNT,
    )
    expected_gas_used = intrinsic_gas + top_frame_state_gas
    tx_gas_limit = expected_gas_used + 1000  # add a small buffer
    gas_price = 0xA
    tx_value = 100
    extra_balance = 1000

    alice_initial_balance = (
        (tx_gas_limit * gas_price) + tx_value + extra_balance
    )
    alice = pre.fund_eoa(amount=alice_initial_balance)
    bob = pre.fund_eoa(amount=0)

    genesis_env = Environment(base_fee_per_gas=0x7)
    base_fee_per_gas = fork.base_fee_per_gas_calculator()(
        parent_base_fee_per_gas=int(genesis_env.base_fee_per_gas or 0),
        parent_gas_used=0,
        parent_gas_limit=genesis_env.gas_limit,
    )
    tip_to_coinbase = (gas_price - base_fee_per_gas) * expected_gas_used
    alice_final_balance = (
        alice_initial_balance - tx_value - expected_gas_used * gas_price
    )

    tx_transfer = Transaction(
        sender=alice,
        to=bob,
        value=tx_value,
        gas_limit=tx_gas_limit,
        gas_price=gas_price,
        expected_receipt=TransactionReceipt(
            logs=[transfer_log(alice, bob, tx_value)]
        ),
    )

    # SELFDESTRUCT sweep with a zero tip, so the coinbase BAL entry
    # stays fee-only from the first transaction.
    sweep_value = 500
    carol = pre.fund_eoa()
    dave = pre.fund_eoa(amount=0)
    sweeper = pre.deploy_contract(
        code=Op.SELFDESTRUCT(dave), balance=sweep_value
    )

    tx_sweep = Transaction(
        sender=carol,
        to=sweeper,
        max_fee_per_gas=base_fee_per_gas,
        max_priority_fee_per_gas=0,
        expected_receipt=TransactionReceipt(
            logs=[transfer_log(sweeper, dave, sweep_value)]
        ),
    )

    block = Block(
        txs=[tx_transfer, tx_sweep],
        fee_recipient=coinbase,
        header_verify=Header(base_fee_per_gas=base_fee_per_gas),
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=1,
                            post_balance=alice_final_balance,
                        )
                    ],
                ),
                bob: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=1, post_balance=tx_value
                        )
                    ],
                ),
                carol: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=2, post_nonce=1)
                    ],
                ),
                sweeper: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(block_access_index=2, post_balance=0)
                    ],
                ),
                dave: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=2, post_balance=sweep_value
                        )
                    ],
                ),
                # System address MUST NOT be included: EIP-7708 emits
                # Transfer logs from SYSTEM_ADDRESS, but that address is
                # not itself a BAL account access.
                Spec7708.SYSTEM_ADDRESS: None,
                # The tip is a BAL-only flow: it must never produce a
                # Transfer log, and the zero-tip second transaction must
                # not add a second balance change.
                coinbase: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=1,
                            post_balance=tip_to_coinbase,
                        )
                    ],
                ),
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            bob: Account(balance=tx_value),
            dave: Account(balance=sweep_value),
            sweeper: Account(balance=0),
        },
        genesis_environment=genesis_env,
    )
