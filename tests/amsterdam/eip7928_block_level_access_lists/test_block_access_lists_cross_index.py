"""
Tests for EIP-7928 BAL cross-index tracking.

Tests that state changes are correctly tracked across different block indices:
- Index 1..N: Regular transactions
- Index N+1: Post-execution system operations

Includes tests for system contracts (withdrawal/consolidation) cross-index
tracking and NOOP filtering behavior.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    BalAccountExpectation,
    BalStorageChange,
    BalStorageSlot,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    Bytecode,
    Op,
    Transaction,
)

from .spec import ref_spec_7928

REFERENCE_SPEC_GIT_PATH = ref_spec_7928.git_path
REFERENCE_SPEC_VERSION = ref_spec_7928.version

pytestmark = pytest.mark.valid_from("Amsterdam")

WITHDRAWAL_REQUEST_ADDRESS = Address(
    0x00000961EF480EB55E80D19AD83579A64C007002
)
CONSOLIDATION_REQUEST_ADDRESS = Address(
    0x0000BBDDC7CE488642FB579F8B00F3A590007251
)


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
        gas_limit=1_000_000,
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
                                            tx_index=1,
                                            post_value=1,
                                        ),
                                        BalStorageChange(
                                            # Reset during post-exec
                                            tx_index=2,
                                            post_value=0,
                                        ),
                                    ],
                                ),
                                BalStorageSlot(
                                    slot=0x03,  # Target count
                                    slot_changes=[
                                        BalStorageChange(
                                            # Incremented during tx
                                            tx_index=1,
                                            post_value=1,
                                        ),
                                        BalStorageChange(
                                            # Reset during post-exec
                                            tx_index=2,
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
        gas_limit=1_000_000,
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
                                            tx_index=1,
                                            post_value=1,
                                        ),
                                        BalStorageChange(
                                            # Reset during post-exec
                                            tx_index=2,
                                            post_value=0,
                                        ),
                                    ],
                                ),
                                BalStorageSlot(
                                    slot=0x03,
                                    slot_changes=[
                                        BalStorageChange(
                                            # Incremented during tx
                                            tx_index=1,
                                            post_value=1,
                                        ),
                                        BalStorageChange(
                                            # Reset during post-exec
                                            tx_index=2,
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

    tx = Transaction(
        sender=sender,
        to=test_address,
        gas_limit=100_000,
    )

    # Expected BAL should only show actual changes
    expected_block_access_list = BlockAccessListExpectation(
        account_expectations={
            test_address: BalAccountExpectation(
                storage_changes=[
                    BalStorageSlot(
                        slot=2,
                        slot_changes=[
                            BalStorageChange(tx_index=1, post_value=42),
                        ],
                    ),
                    BalStorageSlot(
                        slot=4,
                        slot_changes=[
                            BalStorageChange(tx_index=1, post_value=200),
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
