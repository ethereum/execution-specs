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
    Fork,
    Op,
    SystemCallPhase,
    Transaction,
    Withdrawal,
    WithdrawalRequest,
    compute_create_address,
)

from .spec import ref_spec_7928
from .test_block_access_lists_eip2935 import HISTORY_STORAGE_ADDRESS
from .test_block_access_lists_eip4788 import (
    BEACON_ROOTS_ADDRESS,
    SYSTEM_ADDRESS,
)

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


def _system_contracts_called(fork: Fork, phase: SystemCallPhase) -> list:
    """Return the fork's system contracts the block calls in `phase`."""
    return sorted(
        address
        for address, called in fork.system_contract_call_phases().items()
        if called == phase
    )


@pytest.mark.pre_alloc_mutable()
def test_bal_pre_execution_calls_net_storage_at_index_zero(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
) -> None:
    """
    Both pre-execution system calls write the same account at block access
    index 0. A slot toggled back to its starting value is a read, while a
    slot bumped twice and a nonce bumped by two CREATEs are single changes
    with the final values: writes are netted over the whole index, not per
    call. The slot holding the last caller pins the order of the two calls.
    """
    # `apply_body` calls the beacon roots contract first and the history
    # contract second; the fork's declared phases must agree on the set.
    assert _system_contracts_called(
        fork, SystemCallPhase.BEFORE_TRANSACTIONS
    ) == sorted([BEACON_ROOTS_ADDRESS, HISTORY_STORAGE_ADDRESS]), (
        "the fork grew a pre-execution system call this test does not "
        "account for"
    )

    toggle_slot = 1
    counter_slot = 2
    last_caller_slot = 3

    # The history contract toggles one slot, counts its calls, notes who
    # called and deploys an empty contract; the beacon roots contract
    # calls it, so the block runs it twice: once from the beacon roots
    # call and then from its own system call.
    pre[HISTORY_STORAGE_ADDRESS] = Account(
        nonce=1,
        code=Op.SSTORE(toggle_slot, Op.ISZERO(Op.SLOAD(toggle_slot)))
        + Op.SSTORE(counter_slot, Op.ADD(Op.SLOAD(counter_slot), 1))
        + Op.SSTORE(last_caller_slot, Op.CALLER)
        + Op.POP(Op.CREATE(0, 0, 0)),
    )
    pre[BEACON_ROOTS_ADDRESS] = Account(
        code=Op.POP(Op.CALL(address=HISTORY_STORAGE_ADDRESS)),
    )
    created = [
        compute_create_address(address=HISTORY_STORAGE_ADDRESS, nonce=nonce)
        for nonce in (1, 2)
    ]

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        HISTORY_STORAGE_ADDRESS: BalAccountExpectation(
                            storage_changes=[
                                BalStorageSlot(
                                    slot=counter_slot,
                                    slot_changes=[
                                        BalStorageChange(
                                            block_access_index=0,
                                            post_value=2,
                                        )
                                    ],
                                ),
                                BalStorageSlot(
                                    slot=last_caller_slot,
                                    slot_changes=[
                                        BalStorageChange(
                                            block_access_index=0,
                                            post_value=SYSTEM_ADDRESS,
                                        )
                                    ],
                                ),
                            ],
                            storage_reads=[toggle_slot],
                            nonce_changes=[
                                BalNonceChange(
                                    block_access_index=0, post_nonce=3
                                )
                            ],
                        ),
                        **{
                            address: BalAccountExpectation(
                                nonce_changes=[
                                    BalNonceChange(
                                        block_access_index=0, post_nonce=1
                                    )
                                ],
                                code_changes=[],
                            )
                            for address in created
                        },
                        BEACON_ROOTS_ADDRESS: BalAccountExpectation.empty(),
                        SYSTEM_ADDRESS: None,
                    }
                ),
            )
        ],
        post={
            HISTORY_STORAGE_ADDRESS: Account(
                nonce=3,
                storage={
                    toggle_slot: 0,
                    counter_slot: 2,
                    last_caller_slot: SYSTEM_ADDRESS,
                },
            ),
            **{address: Account(nonce=1, code=b"") for address in created},
        },
    )


@pytest.mark.pre_alloc_mutable()
def test_bal_system_call_change_kept_when_tx_restores_slot(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Netting stops at the index boundary: a slot the history system call
    sets at index 0 and a transaction restores at index 1 keeps both
    changes, although the block leaves it at its starting value.
    """
    caller_slot = 1
    counter_slot = 2
    alice = pre.fund_eoa()

    # The contract records its caller and counts its calls. Alice's
    # address is the caller slot's starting value, so the system call
    # moves it and her transaction puts it back; the counter reaching two
    # is what separates that round trip from neither call running.
    pre[HISTORY_STORAGE_ADDRESS] = Account(
        nonce=1,
        code=Op.SSTORE(caller_slot, Op.CALLER)
        + Op.SSTORE(counter_slot, Op.ADD(Op.SLOAD(counter_slot), 1)),
        storage={caller_slot: alice},
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[Transaction(sender=alice, to=HISTORY_STORAGE_ADDRESS)],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        HISTORY_STORAGE_ADDRESS: BalAccountExpectation(
                            storage_changes=[
                                BalStorageSlot(
                                    slot=caller_slot,
                                    slot_changes=[
                                        BalStorageChange(
                                            block_access_index=0,
                                            post_value=SYSTEM_ADDRESS,
                                        ),
                                        BalStorageChange(
                                            block_access_index=1,
                                            post_value=alice,
                                        ),
                                    ],
                                ),
                                BalStorageSlot(
                                    slot=counter_slot,
                                    slot_changes=[
                                        BalStorageChange(
                                            block_access_index=0,
                                            post_value=1,
                                        ),
                                        BalStorageChange(
                                            block_access_index=1,
                                            post_value=2,
                                        ),
                                    ],
                                ),
                            ],
                            storage_reads=[],
                        ),
                        alice: BalAccountExpectation(
                            nonce_changes=[
                                BalNonceChange(
                                    block_access_index=1, post_nonce=1
                                )
                            ],
                        ),
                    }
                ),
            )
        ],
        post={
            HISTORY_STORAGE_ADDRESS: Account(
                storage={caller_slot: alice, counter_slot: 2}
            ),
            alice: Account(nonce=1),
        },
    )


@pytest.mark.parametrize(
    "forwarded_share",
    [
        pytest.param("all", id="forward_all"),
        pytest.param("half", id="forward_half"),
    ],
)
@pytest.mark.pre_alloc_mutable()
def test_bal_withdrawals_and_dequeues_net_balance_at_last_index(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
    forwarded_share: str,
) -> None:
    """
    Withdrawals and the post-execution system calls share one block
    access index, so their balance effects net. A withdrawal credits
    each predeploy, whose own dequeue call then forwards that balance
    on: forwarding all of it records no change, forwarding half records
    the kept half.
    """
    predeploys = _system_contracts_called(
        fork, SystemCallPhase.AFTER_TRANSACTIONS
    )
    withdrawal_amount_wei = 10**9
    sink = pre.fund_eoa(amount=1)

    forwarded_value: Bytecode
    if forwarded_share == "all":
        forwarded_wei = withdrawal_amount_wei
        forwarded_value = Op.SELFBALANCE
    elif forwarded_share == "half":
        forwarded_wei = withdrawal_amount_wei // 2
        forwarded_value = Op.DIV(Op.SELFBALANCE, 2)
    else:
        raise ValueError(f"unhandled share: {forwarded_share}")
    kept_wei = withdrawal_amount_wei - forwarded_wei

    for predeploy in predeploys:
        pre[predeploy] = Account(
            code=Op.POP(Op.CALL(address=sink, value=forwarded_value)),
        )

    predeploy_expectation = BalAccountExpectation(
        balance_changes=(
            [BalBalanceChange(block_access_index=1, post_balance=kept_wei)]
            if kept_wei
            else []
        ),
        storage_changes=[],
        storage_reads=[],
    )
    sink_balance = 1 + forwarded_wei * len(predeploys)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[],
                withdrawals=[
                    Withdrawal(
                        index=i,
                        validator_index=i,
                        address=predeploy,
                        amount=1,
                    )
                    for i, predeploy in enumerate(predeploys)
                ],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        **dict.fromkeys(predeploys, predeploy_expectation),
                        sink: BalAccountExpectation(
                            balance_changes=[
                                BalBalanceChange(
                                    block_access_index=1,
                                    post_balance=sink_balance,
                                )
                            ],
                        ),
                    }
                ),
            )
        ],
        post={
            **{
                predeploy: Account(balance=kept_wei)
                for predeploy in predeploys
            },
            sink: Account(balance=sink_balance),
        },
    )
