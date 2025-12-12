"""Tests for the effects of EIP-4895 withdrawals on EIP-7928."""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    BalAccountExpectation,
    BalBalanceChange,
    BalCodeChange,
    BalNonceChange,
    BalStorageChange,
    BalStorageSlot,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    Environment,
    Fork,
    Header,
    Initcode,
    Op,
    Transaction,
    Withdrawal,
    compute_create_address,
)

from .spec import ref_spec_7928

REFERENCE_SPEC_GIT_PATH = ref_spec_7928.git_path
REFERENCE_SPEC_VERSION = ref_spec_7928.version

pytestmark = pytest.mark.valid_from("Amsterdam")

GWEI = 10**9


def test_bal_withdrawal_empty_block(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Ensure BAL captures withdrawal balance changes in empty block.

    Charlie starts with 1 gwei balance (existing account).
    Block with 0 transactions and 1 withdrawal of 10 gwei to Charlie.
    Charlie ends with 11 gwei balance.
    """
    charlie = pre.fund_eoa(amount=1 * GWEI)

    block = Block(
        txs=[],
        withdrawals=[
            Withdrawal(
                index=0,
                validator_index=0,
                address=charlie,
                amount=10,
            )
        ],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                charlie: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=1, post_balance=11 * GWEI
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
            charlie: Account(balance=11 * GWEI),
        },
    )


def test_bal_withdrawal_and_transaction(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Ensure BAL captures both transaction and withdrawal balance changes.

    Alice starts with 1 ETH, Bob starts with 0, Charlie starts with 0.
    Alice sends 5 wei to Bob.
    Charlie receives 10 gwei withdrawal.
    Bob ends with 5 wei, Charlie ends with 10 gwei.
    """
    alice = pre.fund_eoa()
    bob = pre.fund_eoa(amount=0)
    charlie = pre.fund_eoa(amount=0)

    tx = Transaction(
        sender=alice,
        to=bob,
        value=5,
        max_fee_per_gas=50,
        max_priority_fee_per_gas=5,
    )

    block = Block(
        txs=[tx],
        withdrawals=[
            Withdrawal(
                index=0,
                validator_index=0,
                address=charlie,
                amount=10,
            )
        ],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                bob: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(block_access_index=1, post_balance=5)
                    ],
                ),
                charlie: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=2, post_balance=10 * GWEI
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
            alice: Account(nonce=1),
            bob: Account(balance=5),
            charlie: Account(balance=10 * GWEI),
        },
    )


def test_bal_withdrawal_to_nonexistent_account(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Ensure BAL captures withdrawal to non-existent account.

    Charlie is a non-existent address (not in pre-state).
    Block with 0 transactions and 1 withdrawal of 10 gwei to Charlie.
    Charlie ends with 10 gwei balance.
    """
    charlie = Address(0xCC)

    block = Block(
        txs=[],
        withdrawals=[
            Withdrawal(
                index=0,
                validator_index=0,
                address=charlie,
                amount=10,
            )
        ],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                charlie: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=1, post_balance=10 * GWEI
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
            charlie: Account(balance=10 * GWEI),
        },
    )


def test_bal_withdrawal_no_evm_execution(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Ensure BAL captures withdrawal without triggering EVM execution.

    Oracle contract starts with 0 balance and storage slot 0x01 = 0x42.
    Oracle's code writes 0xFF to slot 0x01 when called.
    Block with 0 transactions and 1 withdrawal of 10 gwei to Oracle.
    Storage slot 0x01 remains 0x42 (EVM never executes).
    """
    oracle = pre.deploy_contract(
        code=Op.SSTORE(0x01, 0xFF),
        storage={0x01: 0x42},
    )

    block = Block(
        txs=[],
        withdrawals=[
            Withdrawal(
                index=0,
                validator_index=0,
                address=oracle,
                amount=10,
            )
        ],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                oracle: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=1, post_balance=10 * GWEI
                        )
                    ],
                    storage_reads=[],
                    storage_changes=[],
                ),
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            oracle: Account(
                balance=10 * GWEI,
                storage={0x01: 0x42},
            ),
        },
    )


def test_bal_withdrawal_and_state_access_same_account(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Ensure BAL captures both state access and withdrawal to same address.

    Oracle contract starts with 0 balance and storage slot 0x01 = 0x42.
    Alice calls Oracle (reads slot 0x01, writes 0x99 to slot 0x02).
    Oracle receives withdrawal of 10 gwei.
    Both state access and withdrawal are captured in BAL.
    """
    alice = pre.fund_eoa()
    oracle = pre.deploy_contract(
        code=Op.SLOAD(0x01) + Op.SSTORE(0x02, 0x99),
        storage={0x01: 0x42},
    )

    tx = Transaction(
        sender=alice,
        to=oracle,
        gas_limit=1_000_000,
        gas_price=0xA,
    )

    block = Block(
        txs=[tx],
        withdrawals=[
            Withdrawal(
                index=0,
                validator_index=0,
                address=oracle,
                amount=10,
            )
        ],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                oracle: BalAccountExpectation(
                    storage_reads=[0x01],
                    storage_changes=[
                        BalStorageSlot(
                            slot=0x02,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=1, post_value=0x99
                                )
                            ],
                        )
                    ],
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=2, post_balance=10 * GWEI
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
            alice: Account(nonce=1),
            oracle: Account(
                balance=10 * GWEI,
                storage={0x01: 0x42, 0x02: 0x99},
            ),
        },
    )


def test_bal_withdrawal_and_value_transfer_same_address(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Ensure BAL captures both value transfer and withdrawal to same address.

    Alice starts with 1 ETH, Bob starts with 0.
    Alice sends 5 gwei to Bob.
    Bob receives withdrawal of 10 gwei.
    Bob ends with 15 gwei (5 from tx + 10 from withdrawal).
    """
    alice = pre.fund_eoa()
    bob = pre.fund_eoa(amount=0)

    tx = Transaction(
        sender=alice,
        to=bob,
        value=5 * GWEI,
        gas_price=0xA,
    )

    block = Block(
        txs=[tx],
        withdrawals=[
            Withdrawal(
                index=0,
                validator_index=0,
                address=bob,
                amount=10,
            )
        ],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                bob: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=1, post_balance=5 * GWEI
                        ),
                        BalBalanceChange(
                            block_access_index=2, post_balance=15 * GWEI
                        ),
                    ],
                ),
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            alice: Account(nonce=1),
            bob: Account(balance=15 * GWEI),
        },
    )


def test_bal_multiple_withdrawals_same_address(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Ensure BAL accumulates multiple withdrawals to same address.

    Charlie starts with 0 balance.
    Block empty block with 3 withdrawals to Charlie: 5 gwei, 10 gwei, 15 gwei.
    Charlie ends with 30 gwei balance (cumulative).
    """
    charlie = pre.fund_eoa(amount=0)

    block = Block(
        txs=[],
        withdrawals=[
            Withdrawal(index=i, validator_index=i, address=charlie, amount=amt)
            for i, amt in enumerate([5, 10, 15])
        ],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                charlie: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=1, post_balance=30 * GWEI
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
            charlie: Account(balance=30 * GWEI),
        },
    )


def test_bal_withdrawal_and_selfdestruct(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Ensure BAL captures withdrawal to self-destructed contract address.

    Oracle contract starts with 100 gwei balance.
    Alice triggers Oracle to self-destruct, sending balance to Bob.
    Oracle receives withdrawal of 50 gwei after self-destructing.
    Oracle ends with 50 gwei (funded by withdrawal).
    """
    alice = pre.fund_eoa()
    bob = pre.fund_eoa(amount=0)
    oracle = pre.deploy_contract(
        balance=100 * GWEI,
        code=Op.SELFDESTRUCT(bob),
    )

    tx = Transaction(
        sender=alice,
        to=oracle,
        gas_limit=1_000_000,
        gas_price=0xA,
    )

    block = Block(
        txs=[tx],
        withdrawals=[
            Withdrawal(
                index=0,
                validator_index=0,
                address=oracle,
                amount=50,
            )
        ],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                bob: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=1, post_balance=100 * GWEI
                        )
                    ],
                ),
                oracle: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(block_access_index=1, post_balance=0),
                        BalBalanceChange(
                            block_access_index=2, post_balance=50 * GWEI
                        ),
                    ],
                ),
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            alice: Account(nonce=1),
            bob: Account(balance=100 * GWEI),
            oracle: Account(balance=50 * GWEI),
        },
    )


def test_bal_withdrawal_and_new_contract(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Ensure BAL captures withdrawal to newly created contract.

    Alice deploys Oracle contract with 5 gwei initial balance.
    Oracle receives withdrawal of 10 gwei in same block.
    Oracle ends with 15 gwei (5 from deployment + 10 from withdrawal).
    """
    alice = pre.fund_eoa()

    code = Op.STOP
    initcode = Initcode(deploy_code=code)
    oracle = compute_create_address(address=alice)

    tx = Transaction(
        sender=alice,
        to=None,
        data=initcode,
        value=5 * GWEI,
        gas_limit=1_000_000,
        gas_price=0xA,
    )

    block = Block(
        txs=[tx],
        withdrawals=[
            Withdrawal(
                index=0,
                validator_index=0,
                address=oracle,
                amount=10,
            )
        ],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                oracle: BalAccountExpectation(
                    code_changes=[
                        BalCodeChange(block_access_index=1, new_code=code)
                    ],
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=1, post_balance=5 * GWEI
                        ),
                        BalBalanceChange(
                            block_access_index=2, post_balance=15 * GWEI
                        ),
                    ],
                ),
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            alice: Account(nonce=1),
            oracle: Account(balance=15 * GWEI, code=code),
        },
    )


@pytest.mark.parametrize(
    "initial_balance",
    [
        pytest.param(5 * GWEI, id="existing_account"),
        pytest.param(0, id="nonexistent_account"),
    ],
)
def test_bal_zero_withdrawal(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    initial_balance: int,
) -> None:
    """
    Ensure BAL handles zero-amount withdrawal correctly.

    Charlie either exists with initial balance or is non-existent.
    Block with 0 transactions and 1 zero-amount withdrawal to Charlie.
    Charlie appears in BAL but with empty changes, balance unchanged.
    """
    if initial_balance > 0:
        charlie = pre.fund_eoa(amount=initial_balance)
    else:
        charlie = EOA(0xCC)

    block = Block(
        txs=[],
        withdrawals=[
            Withdrawal(
                index=0,
                validator_index=0,
                address=charlie,
                amount=0,
            )
        ],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                charlie: BalAccountExpectation.empty(),
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            charlie: Account(balance=initial_balance)
            if initial_balance > 0
            else Account.NONEXISTENT,
        },
    )


@pytest.mark.pre_alloc_group(
    "withdrawal_to_precompiles",
    reason="Expects clean precompile balances, isolate in EngineX",
)
@pytest.mark.parametrize_by_fork(
    "precompile",
    lambda fork: [
        pytest.param(addr, id=f"0x{int.from_bytes(addr, 'big'):02x}")
        for addr in fork.precompiles(block_number=0, timestamp=0)
    ],
)
def test_bal_withdrawal_to_precompiles(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    precompile: Address,
) -> None:
    """
    Ensure BAL captures withdrawal to precompile addresses.

    Block with 0 transactions and 1 withdrawal of 10 gwei to precompile.
    Precompile ends with 10 gwei balance.
    """
    block = Block(
        txs=[],
        withdrawals=[
            Withdrawal(
                index=0,
                validator_index=0,
                address=precompile,
                amount=10,
            )
        ],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                precompile: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=1, post_balance=10 * GWEI
                        )
                    ],
                    storage_reads=[],
                    storage_changes=[],
                ),
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            precompile: Account(balance=10 * GWEI),
        },
    )


def test_bal_withdrawal_largest_amount(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Ensure BAL captures withdrawal with largest amount.

    Block with 0 transactions and 1 withdrawal of maximum
    uint64 value (2^64-1)Gwei to Charlie.
    Charlie ends with (2^64-1) Gwei.
    """
    charlie = pre.fund_eoa(amount=0)
    max_amount = 2**64 - 1

    block = Block(
        txs=[],
        withdrawals=[
            Withdrawal(
                index=0,
                validator_index=0,
                address=charlie,
                amount=max_amount,
            )
        ],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                charlie: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=1,
                            post_balance=max_amount * GWEI,
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
            charlie: Account(balance=max_amount * GWEI),
        },
    )


def test_bal_withdrawal_to_coinbase(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
) -> None:
    """
    Ensure BAL captures withdrawal to coinbase address.

    Block with 1 transaction and 1 withdrawal to coinbase/fee recipient.
    Coinbase receives both transaction fees and withdrawal.
    """
    alice = pre.fund_eoa()
    bob = pre.fund_eoa(amount=0)
    coinbase = pre.fund_eoa(amount=0)

    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    intrinsic_gas = intrinsic_gas_calculator()
    tx_gas_limit = intrinsic_gas + 1000
    gas_price = 0xA

    tx = Transaction(
        sender=alice,
        to=bob,
        value=5,
        gas_limit=tx_gas_limit,
        gas_price=gas_price,
    )

    # Calculate tip to coinbase
    genesis_env = Environment(base_fee_per_gas=0x7)
    base_fee_per_gas = fork.base_fee_per_gas_calculator()(
        parent_base_fee_per_gas=int(genesis_env.base_fee_per_gas or 0),
        parent_gas_used=0,
        parent_gas_limit=genesis_env.gas_limit,
    )
    tip_to_coinbase = (gas_price - base_fee_per_gas) * intrinsic_gas
    coinbase_final_balance = tip_to_coinbase + (10 * GWEI)

    block = Block(
        txs=[tx],
        fee_recipient=coinbase,
        header_verify=Header(base_fee_per_gas=base_fee_per_gas),
        withdrawals=[
            Withdrawal(
                index=0,
                validator_index=0,
                address=coinbase,
                amount=10,
            )
        ],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                bob: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(block_access_index=1, post_balance=5)
                    ],
                ),
                coinbase: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=1, post_balance=tip_to_coinbase
                        ),
                        BalBalanceChange(
                            block_access_index=2,
                            post_balance=coinbase_final_balance,
                        ),
                    ],
                ),
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            alice: Account(nonce=1),
            bob: Account(balance=5),
            coinbase: Account(balance=coinbase_final_balance),
        },
        genesis_environment=genesis_env,
    )


def test_bal_withdrawal_to_coinbase_empty_block(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Ensure BAL captures withdrawal to coinbase when there are no transactions.

    Empty block with 1 withdrawal of 10 gwei to coinbase/fee recipient.
    Coinbase receives only withdrawal (no transaction fees).
    """
    coinbase = pre.fund_eoa(amount=0)

    block = Block(
        txs=[],
        fee_recipient=coinbase,
        withdrawals=[
            Withdrawal(
                index=0,
                validator_index=0,
                address=coinbase,
                amount=10,
            )
        ],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                coinbase: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=1, post_balance=10 * GWEI
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
            coinbase: Account(balance=10 * GWEI),
        },
    )
