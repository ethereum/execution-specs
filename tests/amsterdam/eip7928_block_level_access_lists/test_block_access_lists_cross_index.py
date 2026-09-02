"""
Tests for EIP-7928 BAL cross-index tracking.

Tests that state changes are correctly tracked across different block indices:
- Index 1..N: Execution transactions
- Index N+1: Post-execution system operations

Includes tests for system contracts (withdrawal/consolidation) cross-index
tracking and NOOP filtering behavior.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    BalAccountAbsentValues,
    BalAccountExpectation,
    BalBalanceChange,
    BalNonceChange,
    BalStorageChange,
    BalStorageSlot,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    Bytecode,
    ConsolidationRequest,
    Op,
    Transaction,
    WithdrawalRequest,
)

from .spec import ref_spec_7928

REFERENCE_SPEC_GIT_PATH = ref_spec_7928.git_path
REFERENCE_SPEC_VERSION = ref_spec_7928.version

pytestmark = pytest.mark.valid_from("Amsterdam")

WITHDRAWAL_REQUEST_ADDRESS = WithdrawalRequest.system_contract_address
CONSOLIDATION_REQUEST_ADDRESS = ConsolidationRequest.system_contract_address


def test_bal_withdrawal_contract_cross_index(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Test that the withdrawal system contract shows storage changes at both
    index 1 (during transaction) and index 2 (during post-execution).

    This verifies that slots 0x01 and 0x03 are:
    1. Incremented during the transaction (index 1)
    2. Reset during post-execution (index 2)
    """
    sender = pre.fund_eoa()

    withdrawal_calldata = (
        (b"\x01" + b"\x00" * 47)  # validator pubkey
        + (b"\x00" * 8)  # amount
    )

    tx = Transaction(
        sender=sender,
        to=WITHDRAWAL_REQUEST_ADDRESS,
        value=1,
        data=withdrawal_calldata,
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        WITHDRAWAL_REQUEST_ADDRESS: BalAccountExpectation(
                            # slots 0x01 and 0x03 change at BOTH indices
                            storage_changes=[
                                BalStorageSlot(
                                    slot=0x01,  # Request count
                                    slot_changes=[
                                        BalStorageChange(
                                            # Incremented during tx
                                            block_access_index=1,
                                            post_value=1,
                                        ),
                                        BalStorageChange(
                                            # Reset during post-exec
                                            block_access_index=2,
                                            post_value=0,
                                        ),
                                    ],
                                ),
                                BalStorageSlot(
                                    slot=0x03,  # Target count
                                    slot_changes=[
                                        BalStorageChange(
                                            # Incremented during tx
                                            block_access_index=1,
                                            post_value=1,
                                        ),
                                        BalStorageChange(
                                            # Reset during post-exec
                                            block_access_index=2,
                                            post_value=0,
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    }
                ),
            )
        ],
        post={},
    )


def test_bal_consolidation_contract_cross_index(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Test that the consolidation system contract shows storage changes at both
    index 1 (during transaction) and index 2 (during post-execution).
    """
    sender = pre.fund_eoa()

    consolidation_calldata = (
        (b"\x01" + b"\x00" * 47)  # source pubkey
        + (b"\x02" + b"\x00" * 47)  # target pubkey
    )

    tx = Transaction(
        sender=sender,
        to=CONSOLIDATION_REQUEST_ADDRESS,
        value=1,
        data=consolidation_calldata,
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        CONSOLIDATION_REQUEST_ADDRESS: BalAccountExpectation(
                            storage_changes=[
                                BalStorageSlot(
                                    slot=0x01,
                                    slot_changes=[
                                        BalStorageChange(
                                            # Incremented during tx
                                            block_access_index=1,
                                            post_value=1,
                                        ),
                                        BalStorageChange(
                                            # Reset during post-exec
                                            block_access_index=2,
                                            post_value=0,
                                        ),
                                    ],
                                ),
                                BalStorageSlot(
                                    slot=0x03,
                                    slot_changes=[
                                        BalStorageChange(
                                            # Incremented during tx
                                            block_access_index=1,
                                            post_value=1,
                                        ),
                                        BalStorageChange(
                                            # Reset during post-exec
                                            block_access_index=2,
                                            post_value=0,
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    }
                ),
            )
        ],
        post={},
    )


def test_bal_noop_write_filtering(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Test that NOOP writes (writing same value or 0 to empty) are filtered.

    This verifies that:
    1. Writing 0 to an uninitialized slot doesn't appear in BAL
    2. Writing the same value to a slot doesn't appear in BAL
    3. Only actual changes are tracked
    """
    test_code = Bytecode(
        # Write 0 to uninitialized slot 1 (noop)
        Op.SSTORE(1, 0)
        # Write 42 to slot 2
        + Op.SSTORE(2, 42)
        # Write 100 to slot 3 (will be same as pre-state, should be filtered)
        + Op.SSTORE(3, 100)
        # Write 200 to slot 4 (different from pre-state 150, should appear)
        + Op.SSTORE(4, 200)
    )

    sender = pre.fund_eoa()
    test_address = pre.deploy_contract(
        code=test_code,
        storage={3: 100, 4: 150},
    )

    tx = Transaction(sender=sender, to=test_address)

    # Expected BAL should only show actual changes
    expected_block_access_list = BlockAccessListExpectation(
        account_expectations={
            test_address: BalAccountExpectation(
                storage_changes=[
                    BalStorageSlot(
                        slot=2,
                        slot_changes=[
                            BalStorageChange(
                                block_access_index=1, post_value=42
                            ),
                        ],
                    ),
                    BalStorageSlot(
                        slot=4,
                        slot_changes=[
                            BalStorageChange(
                                block_access_index=1, post_value=200
                            ),
                        ],
                    ),
                ],
            ),
        }
    )

    block = Block(
        txs=[tx],
        expected_block_access_list=expected_block_access_list,
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            test_address: Account(storage={2: 42, 3: 100, 4: 200}),
        },
    )


def test_bal_intra_tx_round_trip_after_prior_tx_write(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Verify a per-tx no-op SSTORE round-trip is not recorded as a storage
    change when an earlier tx in the same block wrote the slot.

    Per EIP-7928 §Storage, a write is compared against "the storage value
    as of immediately before the current `block_access_index` (i.e., the
    cumulative state from all prior indices, falling back to the pre-block
    state)", and "a no-op write MUST NOT remove `storage_changes` entries
    from earlier indices for the same slot".

    Both txs call the same contract whose runtime SSTOREs 0xff then 0x42
    to slot 1. Tx 1 changes slot 1 from 0 to 0x42 (real change). Tx 1's
    write becomes tx 2's baseline, so tx 2's 0x42 -> 0xff -> 0x42 nets to
    a no-op and only tx 1 appears in `storage_changes` (with tx 1's entry
    left intact).
    """
    # Runtime: write 0xff to slot 1, then write 0x42 to slot 1, STOP.
    # The two SSTOREs hit the journal at every call, but the net effect
    # on the slot is `pre_value -> 0x42` — a no-op when pre_value == 0x42.
    contract_code = Bytecode(Op.SSTORE(1, 0xFF) + Op.SSTORE(1, 0x42) + Op.STOP)
    contract = pre.deploy_contract(code=contract_code)

    sender_a = pre.fund_eoa()
    sender_b = pre.fund_eoa()

    # Both txs go into the same block; tx 1 makes the real 0 -> 0x42
    # change, tx 2 starts from 0x42 and ends at 0x42 (per-tx no-op).
    tx_1 = Transaction(sender=sender_a, to=contract)
    tx_2 = Transaction(sender=sender_b, to=contract)

    expected_block_access_list = BlockAccessListExpectation(
        account_expectations={
            contract: BalAccountExpectation(
                # Only tx 1's real change appears. Tx 2's same-value
                # round-trip MUST be classified as a read for tx 2.
                storage_changes=[
                    BalStorageSlot(
                        slot=1,
                        slot_changes=[
                            BalStorageChange(
                                block_access_index=1, post_value=0x42
                            ),
                        ],
                    ),
                ],
                # `storage_changes` is only verified as a sub-sequence
                # at fill time, so this additional check guards against a
                # reference regression that emits tx 2's no-op as a
                # spurious index-2 change.
                absent_values=BalAccountAbsentValues(
                    storage_changes=[
                        BalStorageSlot(
                            slot=1,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=2, post_value=0x42
                                ),
                            ],
                        ),
                    ],
                ),
            ),
            sender_a: BalAccountExpectation(
                nonce_changes=[
                    BalNonceChange(block_access_index=1, post_nonce=1),
                ],
            ),
            sender_b: BalAccountExpectation(
                nonce_changes=[
                    BalNonceChange(block_access_index=2, post_nonce=1),
                ],
            ),
        }
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx_1, tx_2],
                expected_block_access_list=expected_block_access_list,
            ),
        ],
        post={contract: Account(storage={1: 0x42})},
    )


def test_bal_system_contract_noop_filtering(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Test that system contract post-execution calls filter net-zero
    storage writes.

    When no transaction interacts with withdrawal/consolidation contracts
    during a block, the post-execution system calls read storage slots
    0-3 but don't modify them. These should appear as storage READS,
    not storage CHANGES.
    """
    sender = pre.fund_eoa()
    receiver = pre.fund_eoa(amount=0)

    # simple transfer that doesn't interact with system contracts
    tx = Transaction(
        sender=sender,
        to=receiver,
        value=100,
    )

    # withdrawal and consolidation contracts should NOT have any storage
    # changes since they weren't modified - only reads occurred during
    # post-execution system calls
    expected_block_access_list = BlockAccessListExpectation(
        account_expectations={
            WITHDRAWAL_REQUEST_ADDRESS: BalAccountExpectation(
                storage_changes=[],
                storage_reads=[0x00, 0x01, 0x02, 0x03],
            ),
            CONSOLIDATION_REQUEST_ADDRESS: BalAccountExpectation(
                storage_changes=[],
                storage_reads=[0x00, 0x01, 0x02, 0x03],
            ),
        }
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_block_access_list=expected_block_access_list,
            )
        ],
        post={
            receiver: Account(balance=100),
        },
    )


def test_bal_withdrawal_predeploy_balance_observed_cross_tx(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Test that a subsequent transaction observes the post-state balance of the
    withdrawal predeploy after a prior transaction in the same block paid the
    withdrawal fee.

    Within one block:
      - tx 0: EOA sends `fee` wei to WITHDRAWAL_REQUEST_PREDEPLOY with a valid
        withdrawal-request calldata. The predeploy retains the fee, so its
        balance transitions 0 -> fee (BAL balance_change at index 1).
      - tx 1: calls a reader contract that performs
        `SSTORE(0, BALANCE(WITHDRAWAL_REQUEST_PREDEPLOY))`.

    Per EIP-7928, the BAL prefix consumed by tx 1's execution must include
    tx 0's balance change for the predeploy, so the BALANCE opcode returns
    `fee` and slot 0 of the reader ends at `fee`. The predeploy is also
    touched by the prepare-block system call (storage reads at slots 0-3),
    making its address one whose pre-block snapshot would otherwise mask the
    BAL overlay if consulted ahead of the BAL prefix.
    """
    fee = 1  # WithdrawalRequest.get_fee(0) with no excess; one request fits.
    withdrawal_calldata = (
        (b"\x01" + b"\x00" * 47)  # 48-byte validator pubkey
        + (b"\x00" * 8)  # 8-byte amount
    )

    sender_0 = pre.fund_eoa()
    sender_1 = pre.fund_eoa()

    reader = pre.deploy_contract(
        code=Bytecode(
            Op.SSTORE(
                0,
                Op.BALANCE(WITHDRAWAL_REQUEST_ADDRESS),
            )
            + Op.STOP
        ),
    )

    tx_pay_fee = Transaction(
        sender=sender_0,
        to=WITHDRAWAL_REQUEST_ADDRESS,
        value=fee,
        data=withdrawal_calldata,
    )

    tx_read_balance = Transaction(sender=sender_1, to=reader)

    expected_block_access_list = BlockAccessListExpectation(
        account_expectations={
            # Predeploy: tx 0 records the fee as a BAL balance_change at
            # index 1; the framework also verifies the system-call storage
            # behaviour through its own post-execution invariants.
            WITHDRAWAL_REQUEST_ADDRESS: BalAccountExpectation(
                balance_changes=[
                    BalBalanceChange(
                        block_access_index=1,
                        post_balance=fee,
                    ),
                ],
            ),
            # Reader: tx 1 stores the predeploy balance at slot 0.
            # If the consumed BAL prefix did not surface tx 0's balance
            # change to BALANCE, post_value would be 0 and the assertion
            # below would fail.
            reader: BalAccountExpectation(
                storage_changes=[
                    BalStorageSlot(
                        slot=0,
                        slot_changes=[
                            BalStorageChange(
                                block_access_index=2,
                                post_value=fee,
                            ),
                        ],
                    ),
                ],
            ),
            sender_0: BalAccountExpectation(
                nonce_changes=[
                    BalNonceChange(block_access_index=1, post_nonce=1),
                ],
            ),
            sender_1: BalAccountExpectation(
                nonce_changes=[
                    BalNonceChange(block_access_index=2, post_nonce=1),
                ],
            ),
        }
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx_pay_fee, tx_read_balance],
                expected_block_access_list=expected_block_access_list,
            ),
        ],
        post={
            reader: Account(storage={0: fee}),
        },
    )
