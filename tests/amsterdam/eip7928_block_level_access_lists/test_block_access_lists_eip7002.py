"""Tests for the effects of EIP-7002 transactions on EIP-7928."""

from typing import Callable

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    BalAccountExpectation,
    BalBalanceChange,
    BalNonceChange,
    BalStorageChange,
    BalStorageSlot,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    Op,
    Transaction,
)

from ...prague.eip7002_el_triggerable_withdrawals.helpers import (
    WithdrawalRequest,
    WithdrawalRequestContract,
    WithdrawalRequestInteractionBase,
    WithdrawalRequestTransaction,
)
from ...prague.eip7002_el_triggerable_withdrawals.spec import Spec as Spec7002
from .spec import ref_spec_7928

REFERENCE_SPEC_GIT_PATH = ref_spec_7928.git_path
REFERENCE_SPEC_VERSION = ref_spec_7928.version

pytestmark = pytest.mark.valid_from("Amsterdam")

"""
Note:
1. In each block, the count resets to zero after execution.
2. During a partial sweep, the head is updated after execution;
   if not written, the head remains read.
3. Similarly, the excess is modified for overflow;
   if not written, it remains read.
4. If the first 32 bytes of the public key are zero, the second slot
   in the queue performs a no-op write (i.e., a read).
"""


# --- helpers --- #
def _encode_pubkey_amount_slot(withdrawal_request: WithdrawalRequest) -> bytes:
    """
    Encode slot +2: 32 bytes containing last 16 bytes of pubkey followed by
    8 bytes of big endian amount, padded with 8 zero bytes on the right.
    Storage layout: [16 bytes pubkey][8 bytes amount][8 bytes padding].
    """
    last_16_bytes = withdrawal_request.validator_pubkey[-16:]
    amount_bytes = withdrawal_request.amount.to_bytes(8, byteorder="big")
    return last_16_bytes + amount_bytes + b"\x00" * 8


def _build_queue_storage_slots(
    senders: list, withdrawal_requests: list[WithdrawalRequest]
) -> tuple[list, list]:
    """Build queue storage slots for withdrawal requests."""
    num_reqs = len(senders)
    queue_writes = []
    queue_reads = []
    for i in range(num_reqs):
        base_slot = Spec7002.WITHDRAWAL_REQUEST_QUEUE_STORAGE_OFFSET + (i * 3)
        # Slot +0: source address
        queue_writes.append(
            BalStorageSlot(
                slot=base_slot,
                slot_changes=[
                    BalStorageChange(
                        block_access_index=i + 1,
                        post_value=senders[i],
                    )
                ],
            ),
        )
        # Slot +1: first 32 bytes of validator pubkey
        first_32_bytes = int.from_bytes(
            withdrawal_requests[i].validator_pubkey[:32], byteorder="big"
        )
        if first_32_bytes != 0:
            # Non-zero write: record as storage change
            queue_writes.append(
                BalStorageSlot(
                    slot=base_slot + 1,
                    slot_changes=[
                        BalStorageChange(
                            block_access_index=i + 1,
                            post_value=first_32_bytes,
                        )
                    ],
                ),
            )
        else:
            # Zero write (no-op): record as storage read
            queue_reads.append(base_slot + 1)
        # Slot +2: last 16 bytes of pubkey + amount
        queue_writes.append(
            BalStorageSlot(
                slot=base_slot + 2,
                slot_changes=[
                    BalStorageChange(
                        block_access_index=i + 1,
                        post_value=_encode_pubkey_amount_slot(
                            withdrawal_requests[i]
                        ),
                    )
                ],
            ),
        )
    return queue_writes, queue_reads


def _extract_post_storage_from_queue_writes(queue_writes: list) -> dict:
    """Extract post-state storage dict from queue writes."""
    post_storage = {}
    for bal_slot in queue_writes:
        # Get the final value from the last slot_change
        if bal_slot.slot_changes:
            post_storage[bal_slot.slot] = bal_slot.slot_changes[-1].post_value
    return post_storage


def _build_incremental_changes(
    count: int,
    change_class: type,
    value_param: str,
    value_fn: Callable[[int], int] = lambda i: i,
    reset_to: int | None = None,
) -> list:
    """
    Build a list of incremental changes with customizable value function.

    Args:
        count: Number of changes to create
        change_class: Class to instantiate for each change
        value_param: Parameter name for the value
                     (e.g., 'post_balance', 'post_value')
        value_fn: Function to compute value from index (default: identity)
        reset_to: Optional reset value to append at the end

    """
    changes = [
        change_class(block_access_index=i, **{value_param: value_fn(i)})
        for i in range(1, count + 1)
    ]
    if reset_to is not None:
        changes.append(
            change_class(
                block_access_index=count + 1, **{value_param: reset_to}
            )
        )
    return changes


# --- tests --- #


@pytest.mark.parametrize(
    "pubkey",
    # Use different pubkey based on parameter
    # 0x01 has first 32 bytes all zero
    # Full 48-byte pubkey with non-zero first word
    [0x01, b"key" * 16],
    ids=["pubkey_first_word_zero", "pubkey_first_word_nonzero"],
)
@pytest.mark.parametrize(
    "amount",
    [0, 1000],
    ids=["amount_zero", "amount_nonzero"],
)
def test_bal_7002_clean_sweep(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    pubkey: bytes,
    amount: int,
) -> None:
    """
    Ensure BAL correctly tracks "clean sweep" where all withdrawal requests
    are dequeued in same block (requests ≤ MAX).

    Tests combinations of:
    - pubkey with first 32 bytes zero / non-zero
    - amount zero / non-zero
    """
    alice = pre.fund_eoa()

    withdrawal_request = WithdrawalRequest(
        validator_pubkey=pubkey,
        amount=amount,
        fee=Spec7002.get_fee(0),
    )

    # Transaction to system contract
    tx = Transaction(
        sender=alice,
        to=Address(Spec7002.WITHDRAWAL_REQUEST_PREDEPLOY_ADDRESS),
        value=withdrawal_request.fee,
        data=withdrawal_request.calldata,
        gas_limit=200_000,
    )

    # Build queue writes and reads based on pubkey
    queue_writes, queue_reads = _build_queue_storage_slots(
        [alice], [withdrawal_request]
    )

    # Base storage reads that always happen
    base_storage_reads = [
        # Excess is read-only if while dequeuing queue doesn't overflow
        Spec7002.EXCESS_WITHDRAWAL_REQUESTS_STORAGE_SLOT,
        # Head slot is read while dequeuing
        Spec7002.WITHDRAWAL_REQUEST_QUEUE_HEAD_STORAGE_SLOT,
    ]

    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                Spec7002.WITHDRAWAL_REQUEST_PREDEPLOY_ADDRESS: BalAccountExpectation(  # noqa: E501
                    balance_changes=[
                        # Fee is collected.
                        BalBalanceChange(
                            block_access_index=1,
                            post_balance=withdrawal_request.fee,
                        )
                    ],
                    storage_reads=base_storage_reads + queue_reads,
                    storage_changes=[
                        BalStorageSlot(
                            slot=Spec7002.WITHDRAWAL_REQUEST_COUNT_STORAGE_SLOT,
                            # Count goes by number of request.
                            # Invariant 1: Post-execution ALWAYS resets count.
                            slot_changes=_build_incremental_changes(
                                1,
                                BalStorageChange,
                                "post_value",
                                lambda i: i,
                                reset_to=0,
                            ),
                        ),
                        BalStorageSlot(
                            slot=Spec7002.WITHDRAWAL_REQUEST_QUEUE_TAIL_STORAGE_SLOT,
                            # Tail index goes up by number of requests.
                            # Invariant 2: resets if clean sweep.
                            slot_changes=_build_incremental_changes(
                                1,
                                BalStorageChange,
                                "post_value",
                                lambda i: i,
                                reset_to=0,
                            ),
                        ),
                    ]
                    + queue_writes,
                ),
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            alice: Account(nonce=1),
            Spec7002.WITHDRAWAL_REQUEST_PREDEPLOY_ADDRESS: Account(
                balance=withdrawal_request.fee,
                storage=_extract_post_storage_from_queue_writes(queue_writes),
            ),
        },
    )


def test_bal_7002_partial_sweep(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Ensure BAL correctly tracks queue overflow when requests exceed MAX.
    Block 1: 20 requests (partial sweep, 16 dequeued).
    Block 2: Empty (clean sweep of remaining 4).
    """
    num_requests = 20
    fee = Spec7002.get_fee(0)
    senders = [pre.fund_eoa() for _ in range(num_requests)]

    # Block 1: 20 withdrawal requests
    withdrawal_requests = [
        WithdrawalRequest(validator_pubkey=i + 1, amount=0, fee=fee)
        for i in range(num_requests)
    ]

    eip7002_address = Address(Spec7002.WITHDRAWAL_REQUEST_PREDEPLOY_ADDRESS)

    txs_block_1 = [
        Transaction(
            sender=sender,
            to=eip7002_address,
            value=withdrawal_request.fee,
            data=withdrawal_request.calldata,
            gas_limit=200_000,
        )
        for sender, withdrawal_request in zip(
            senders, withdrawal_requests, strict=True
        )
    ]

    excess_after_block_1 = Spec7002.get_excess_withdrawal_requests(
        0, num_requests
    )

    block_1_expectations: dict = {
        sender: BalAccountExpectation(
            nonce_changes=[
                BalNonceChange(block_access_index=i + 1, post_nonce=1)
            ]
        )
        for i, sender in enumerate(senders)
    }

    # Build queue writes and reads
    queue_writes, queue_reads = _build_queue_storage_slots(
        senders, withdrawal_requests
    )

    block_1_expectations[eip7002_address] = BalAccountExpectation(
        balance_changes=_build_incremental_changes(
            num_requests,
            BalBalanceChange,
            "post_balance",
            lambda i: fee * i,
        ),
        storage_reads=queue_reads,
        storage_changes=[
            # Excess is only updated once during
            # dequeue
            BalStorageSlot(
                slot=Spec7002.EXCESS_WITHDRAWAL_REQUESTS_STORAGE_SLOT,
                slot_changes=[
                    BalStorageChange(
                        block_access_index=num_requests + 1,
                        post_value=excess_after_block_1,
                    )
                ],
            ),
            BalStorageSlot(
                slot=Spec7002.WITHDRAWAL_REQUEST_COUNT_STORAGE_SLOT,
                slot_changes=_build_incremental_changes(
                    num_requests,
                    BalStorageChange,
                    "post_value",
                    lambda i: i,
                    reset_to=0,
                ),
            ),
            BalStorageSlot(
                slot=Spec7002.WITHDRAWAL_REQUEST_QUEUE_HEAD_STORAGE_SLOT,
                slot_changes=[
                    BalStorageChange(
                        block_access_index=num_requests + 1,
                        post_value=Spec7002.MAX_WITHDRAWAL_REQUESTS_PER_BLOCK,
                    )
                ],
            ),
            BalStorageSlot(
                slot=Spec7002.WITHDRAWAL_REQUEST_QUEUE_TAIL_STORAGE_SLOT,
                slot_changes=_build_incremental_changes(
                    num_requests,
                    BalStorageChange,
                    "post_value",
                    lambda i: i,
                ),
            ),
        ]
        + queue_writes,
    )

    # Block 2: Empty block, clean sweep of remaining 4 requests
    excess_after_block_2 = Spec7002.get_excess_withdrawal_requests(
        excess_after_block_1, 0
    )

    block_2_expectations = {
        eip7002_address: BalAccountExpectation(
            storage_reads=[Spec7002.WITHDRAWAL_REQUEST_COUNT_STORAGE_SLOT],
            storage_changes=[
                BalStorageSlot(
                    slot=Spec7002.EXCESS_WITHDRAWAL_REQUESTS_STORAGE_SLOT,
                    slot_changes=[
                        BalStorageChange(
                            block_access_index=1,
                            post_value=excess_after_block_2,
                        )
                    ],
                ),
                # Head is cleared
                BalStorageSlot(
                    slot=Spec7002.WITHDRAWAL_REQUEST_QUEUE_HEAD_STORAGE_SLOT,
                    slot_changes=[
                        BalStorageChange(block_access_index=1, post_value=0)
                    ],
                ),
                # Tail is cleared
                BalStorageSlot(
                    slot=Spec7002.WITHDRAWAL_REQUEST_QUEUE_TAIL_STORAGE_SLOT,
                    slot_changes=[
                        BalStorageChange(block_access_index=1, post_value=0)
                    ],
                ),
            ],
        )
    }

    # Build post state storage: queue data persists even after dequeue
    post_storage = _extract_post_storage_from_queue_writes(queue_writes)
    post_storage[Spec7002.EXCESS_WITHDRAWAL_REQUESTS_STORAGE_SLOT] = (
        excess_after_block_2
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=txs_block_1,
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations=block_1_expectations
                ),
            ),
            Block(
                txs=[],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations=block_2_expectations
                ),
            ),
        ],
        post={
            **{sender: Account(nonce=1) for sender in senders},
            eip7002_address: Account(
                balance=fee * num_requests,
                storage=post_storage,
            ),
        },
    )


def test_bal_7002_no_withdrawal_requests(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Ensure BAL captures EIP-7002 system contract dequeue operation even
    when block has no withdrawal requests.

    This test verifies that the post-execution dequeue system call always
    reads queue state (slots 0-3), even when no requests are present. The
    system contract should have storage_reads but no storage_changes.
    """
    alice = pre.fund_eoa()
    bob = pre.fund_eoa(amount=0)

    value = 10

    tx = Transaction(
        sender=alice,
        to=bob,
        value=value,
        gas_limit=200_000,
    )

    block = Block(
        txs=[tx],
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
                            block_access_index=1, post_balance=value
                        )
                    ],
                ),
                Spec7002.WITHDRAWAL_REQUEST_PREDEPLOY_ADDRESS: BalAccountExpectation(  # noqa: E501
                    storage_reads=[
                        Spec7002.EXCESS_WITHDRAWAL_REQUESTS_STORAGE_SLOT,
                        Spec7002.WITHDRAWAL_REQUEST_COUNT_STORAGE_SLOT,
                        Spec7002.WITHDRAWAL_REQUEST_QUEUE_HEAD_STORAGE_SLOT,
                        Spec7002.WITHDRAWAL_REQUEST_QUEUE_TAIL_STORAGE_SLOT,
                    ],
                    storage_changes=[],
                ),
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            alice: Account(nonce=1),
            bob: Account(balance=value),
        },
    )


def test_bal_7002_request_from_contract(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Ensure BAL captures withdrawal request from contract with correct
    source address.

    Alice calls RelayContract which internally calls EIP-7002 system
    contract with withdrawal request. Withdrawal request should have
    source_address = RelayContract (not Alice).
    """
    fee = Spec7002.get_fee(0)

    # Create withdrawal request interaction using Prague helper
    interaction = WithdrawalRequestContract(
        requests=[
            WithdrawalRequest(
                validator_pubkey=0x01,
                amount=0,
                fee=fee,
            )
        ],
        contract_balance=fee,
    )

    # Set up pre-state using helper
    interaction.update_pre(pre)

    alice = interaction.sender_account
    relay_contract = interaction.contract_address

    # Build queue storage slots with contract as source
    queue_writes, queue_reads = _build_queue_storage_slots(
        [relay_contract], interaction.requests
    )

    block = Block(
        txs=interaction.transactions(),
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                relay_contract: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=1,
                            post_balance=0,
                        )
                    ],
                ),
                Spec7002.WITHDRAWAL_REQUEST_PREDEPLOY_ADDRESS: BalAccountExpectation(  # noqa: E501
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=1,
                            post_balance=fee,
                        )
                    ],
                    storage_reads=[
                        Spec7002.EXCESS_WITHDRAWAL_REQUESTS_STORAGE_SLOT,
                        Spec7002.WITHDRAWAL_REQUEST_QUEUE_HEAD_STORAGE_SLOT,
                    ]
                    + queue_reads,
                    storage_changes=[
                        BalStorageSlot(
                            slot=Spec7002.WITHDRAWAL_REQUEST_COUNT_STORAGE_SLOT,
                            slot_changes=_build_incremental_changes(
                                1,
                                BalStorageChange,
                                "post_value",
                                lambda i: i,
                                reset_to=0,
                            ),
                        ),
                        BalStorageSlot(
                            slot=Spec7002.WITHDRAWAL_REQUEST_QUEUE_TAIL_STORAGE_SLOT,
                            slot_changes=_build_incremental_changes(
                                1,
                                BalStorageChange,
                                "post_value",
                                lambda i: i,
                                reset_to=0,
                            ),
                        ),
                    ]
                    + queue_writes,
                ),
            }
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            alice: Account(nonce=1),
            relay_contract: Account(balance=0),
            Spec7002.WITHDRAWAL_REQUEST_PREDEPLOY_ADDRESS: Account(
                balance=fee,
                storage=_extract_post_storage_from_queue_writes(queue_writes),
            ),
        },
    )


@pytest.mark.parametrize(
    "interaction",
    [
        pytest.param(
            WithdrawalRequestTransaction(
                requests=[
                    WithdrawalRequest(
                        validator_pubkey=0x01,
                        amount=0,
                        fee=0,  # Below MIN_WITHDRAWAL_REQUEST_FEE
                        valid=False,
                    )
                ]
            ),
            id="insufficient_fee",
        ),
        pytest.param(
            WithdrawalRequestTransaction(
                requests=[
                    WithdrawalRequest(
                        validator_pubkey=0x01,
                        amount=0,
                        fee=Spec7002.get_fee(0),
                        calldata_modifier=lambda x: x[
                            :-1
                        ],  # 55 bytes instead of 56
                        valid=False,
                    )
                ]
            ),
            id="calldata_too_short",
        ),
        pytest.param(
            WithdrawalRequestTransaction(
                requests=[
                    WithdrawalRequest(
                        validator_pubkey=0x01,
                        amount=0,
                        fee=Spec7002.get_fee(0),
                        calldata_modifier=lambda x: x
                        + b"\x00",  # 57 bytes instead of 56
                        valid=False,
                    )
                ]
            ),
            id="calldata_too_long",
        ),
        pytest.param(
            WithdrawalRequestTransaction(
                requests=[
                    WithdrawalRequest(
                        validator_pubkey=0x01,
                        amount=0,
                        fee=Spec7002.get_fee(0),
                        gas_limit=25_000,  # Insufficient gas
                        valid=False,
                    )
                ]
            ),
            id="oog",
        ),
        pytest.param(
            WithdrawalRequestContract(
                requests=[
                    WithdrawalRequest(
                        validator_pubkey=0x01,
                        amount=0,
                        fee=Spec7002.get_fee(0),
                        valid=False,
                    )
                ],
                call_type=Op.DELEGATECALL,
            ),
            id="invalid_call_type_delegatecall",
        ),
        pytest.param(
            WithdrawalRequestContract(
                requests=[
                    WithdrawalRequest(
                        validator_pubkey=0x01,
                        amount=0,
                        fee=Spec7002.get_fee(0),
                        valid=False,
                    )
                ],
                call_type=Op.STATICCALL,
            ),
            id="invalid_call_type_staticcall",
        ),
        pytest.param(
            WithdrawalRequestContract(
                requests=[
                    WithdrawalRequest(
                        validator_pubkey=0x01,
                        amount=0,
                        fee=Spec7002.get_fee(0),
                        valid=False,
                    )
                ],
                call_type=Op.CALLCODE,
            ),
            id="invalid_call_type_callcode",
        ),
        pytest.param(
            WithdrawalRequestContract(
                requests=[
                    WithdrawalRequest(
                        validator_pubkey=0x01,
                        amount=0,
                        fee=Spec7002.get_fee(0),
                        valid=False,
                    )
                ],
                extra_code=Op.REVERT(0, 0),
            ),
            id="contract_reverts",
        ),
    ],
)
def test_bal_7002_request_invalid(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    interaction: WithdrawalRequestInteractionBase,
) -> None:
    """
    Ensure BAL correctly handles invalid withdrawal request scenarios.

    Tests various failure modes:
    - insufficient_fee: Transaction reverts due to fee below minimum
    - calldata_too_short: Transaction reverts due to short calldata (55 bytes)
    - calldata_too_long: Transaction reverts due to long calldata (57 bytes)
    - oog: Transaction runs out of gas before completion
    - invalid_call_type_*: Contract call via DELEGATECALL/STATICCALL/CALLCODE
    - contract_reverts: Contract calls system contract but reverts after

    In all cases:
    - Sender's nonce increments (transaction executed)
    - Sender pays gas costs
    - System contract is accessed during dequeue but has no state changes
    - No withdrawal request is queued
    """
    # Use helper to set up pre-state and get transaction
    interaction.update_pre(pre)
    tx = interaction.transactions()[0]
    alice = interaction.sender_account

    # Build account expectations
    account_expectations = {
        alice: BalAccountExpectation(
            nonce_changes=[BalNonceChange(block_access_index=1, post_nonce=1)],
        ),
        Spec7002.WITHDRAWAL_REQUEST_PREDEPLOY_ADDRESS: BalAccountExpectation(
            storage_reads=[
                Spec7002.EXCESS_WITHDRAWAL_REQUESTS_STORAGE_SLOT,
                Spec7002.WITHDRAWAL_REQUEST_COUNT_STORAGE_SLOT,
                Spec7002.WITHDRAWAL_REQUEST_QUEUE_HEAD_STORAGE_SLOT,
                Spec7002.WITHDRAWAL_REQUEST_QUEUE_TAIL_STORAGE_SLOT,
            ],
            storage_changes=[],
        ),
    }

    # For all invalid scenarios, system contract should have reads but
    # no write since the dequeue operation still happens post-execution
    block = Block(
        txs=[tx],
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations=account_expectations
        ),
    )

    post: dict = {
        alice: Account(nonce=1),
        Spec7002.WITHDRAWAL_REQUEST_PREDEPLOY_ADDRESS: Account(storage={}),
    }

    # Add relay contract to post-state for contract scenarios
    if isinstance(interaction, WithdrawalRequestContract):
        post[interaction.contract_address] = Account()

    blockchain_test(
        pre=pre,
        blocks=[block],
        post=post,
    )
