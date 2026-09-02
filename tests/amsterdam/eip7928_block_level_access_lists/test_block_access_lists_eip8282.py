"""
Tests for the effects of EIP-8282 builder requests on EIP-7928.

Pin the block access list produced by the builder deposit and exit
predeploys: the enqueuing transactions grow the count and queue tail
slots, and the post-execution system call dequeues the records, resetting
or advancing the queue slots depending on whether the sweep is clean or
partial.
"""

from typing import Dict, List, Tuple, Type

import pytest
from execution_testing import (
    Alloc,
    BalAccountExpectation,
    BalNonceChange,
    BalStorageChange,
    BalStorageSlot,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    BuilderDepositRequest,
    BuilderExitRequest,
    FeeSystemContractRequest,
    SystemContractInteractionBase,
    SystemContractInteractionContract,
    SystemContractInteractionTransaction,
)

from .spec import ref_spec_7928

REFERENCE_SPEC_GIT_PATH = ref_spec_7928.git_path
REFERENCE_SPEC_VERSION = ref_spec_7928.version

pytestmark = pytest.mark.valid_from("Amsterdam")


def _request(
    request_class: Type[FeeSystemContractRequest], index: int, fee: int
) -> FeeSystemContractRequest:
    """Build a request from a sequential index, paying `fee` to enqueue."""
    return request_class.from_index(index).copy(fee=fee)


def _request_queue_expectation(
    request_class: Type[FeeSystemContractRequest],
    enqueues: List[Tuple[int, int]],
    system_call_index: int,
) -> BalAccountExpectation:
    """
    Build the BAL expectation for a request queue predeploy.

    `enqueues` lists `(block_access_index, cumulative_count)` for each
    transaction that enqueues into this predeploy. The count and queue tail
    grow with each of them; the system call at `system_call_index` then
    resets the count and either resets the tail (clean sweep) or advances
    the head to `max_per_block` (partial sweep), writing the new excess if
    the enqueued total exceeded the target.
    """
    total = enqueues[-1][1] if enqueues else 0
    new_excess = max(total - request_class.target_per_block, 0)
    partial_sweep = total > request_class.max_per_block

    count_changes = [
        BalStorageChange(block_access_index=index, post_value=cumulative)
        for index, cumulative in enqueues
    ] + [BalStorageChange(block_access_index=system_call_index, post_value=0)]

    tail_changes = [
        BalStorageChange(block_access_index=index, post_value=cumulative)
        for index, cumulative in enqueues
    ]
    head_changes = []
    if partial_sweep:
        # Partial sweep: the head advances past the dequeued records and
        # the tail keeps the queue's end.
        head_changes.append(
            BalStorageChange(
                block_access_index=system_call_index,
                post_value=request_class.max_per_block,
            )
        )
    else:
        # Clean sweep: the head stays at zero (a read) and the tail resets.
        tail_changes.append(
            BalStorageChange(
                block_access_index=system_call_index, post_value=0
            )
        )

    storage_changes = []
    if new_excess:
        storage_changes.append(
            BalStorageSlot(
                slot=request_class.excess_slot,
                slot_changes=[
                    BalStorageChange(
                        block_access_index=system_call_index,
                        post_value=new_excess,
                    )
                ],
            )
        )
    storage_changes.append(
        BalStorageSlot(
            slot=request_class.count_slot, slot_changes=count_changes
        )
    )
    if head_changes:
        storage_changes.append(
            BalStorageSlot(
                slot=request_class.queue_head_slot,
                slot_changes=head_changes,
            )
        )
    storage_changes.append(
        BalStorageSlot(
            slot=request_class.queue_tail_slot, slot_changes=tail_changes
        )
    )

    storage_reads = []
    if not new_excess:
        storage_reads.append(request_class.excess_slot)
    if not partial_sweep:
        storage_reads.append(request_class.queue_head_slot)

    kwargs: Dict = {"storage_changes": storage_changes}
    if storage_reads:
        kwargs["storage_reads"] = storage_reads
    return BalAccountExpectation(**kwargs)


@pytest.mark.parametrize(
    "request_class",
    [BuilderDepositRequest, BuilderExitRequest],
    ids=["deposit", "exit"],
)
@pytest.mark.parametrize(
    "scenario,via_contract",
    [
        pytest.param("single", False, id="single_from_eoa"),
        pytest.param("target_exceeded", False, id="target_exceeded_from_eoa"),
        pytest.param("carry_over", True, id="carry_over_from_contract"),
    ],
)
def test_bal_builder_request_dequeue(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    request_class: Type[FeeSystemContractRequest],
    scenario: str,
    via_contract: bool,
) -> None:
    """
    Ensure BAL tracks a builder request predeploy across a clean sweep, a
    target-exceeding sweep that writes the excess, and a partial sweep that
    advances the queue head.
    """
    if scenario == "single":
        num_requests = 1
    elif scenario == "target_exceeded":
        num_requests = request_class.target_per_block + 1
    else:  # carry_over: exceed the per-block dequeue cap
        num_requests = request_class.max_per_block + 1
    requests = [
        _request(request_class, i, fee)
        for i, fee in enumerate(request_class.get_enqueue_fees(num_requests))
    ]
    interaction: SystemContractInteractionBase
    if via_contract:
        interaction = SystemContractInteractionContract(requests=requests)
    else:
        interaction = SystemContractInteractionTransaction(requests=requests)
    prepared = interaction.update_pre(pre)
    txs = prepared.transactions()
    system_call_index = len(txs) + 1

    if via_contract:
        enqueues = [(1, num_requests)]
    else:
        enqueues = [(i + 1, i + 1) for i in range(num_requests)]

    sender = prepared.sender_account
    assert sender is not None

    block = Block(
        txs=txs,
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                sender: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(
                            block_access_index=i + 1, post_nonce=i + 1
                        )
                        for i in range(len(txs))
                    ],
                ),
                request_class.system_contract_address: (
                    _request_queue_expectation(
                        request_class, enqueues, system_call_index
                    )
                ),
            }
        ),
    )

    blockchain_test(pre=pre, blocks=[block], post={})


def test_bal_builder_deposits_and_exits_same_block(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Ensure BAL tracks both builder predeploys when a single block
    interleaves deposit and exit requests, pinning which transaction
    indices each contract's queue-slot changes carry.
    """
    deposit_fees = BuilderDepositRequest.get_enqueue_fees(2)
    exit_fees = BuilderExitRequest.get_enqueue_fees(2)
    interactions = [
        SystemContractInteractionTransaction(
            requests=[_request(BuilderDepositRequest, 0, deposit_fees[0])]
        ),
        SystemContractInteractionTransaction(
            requests=[_request(BuilderExitRequest, 0, exit_fees[0])]
        ),
        SystemContractInteractionTransaction(
            requests=[_request(BuilderDepositRequest, 1, deposit_fees[1])]
        ),
        SystemContractInteractionTransaction(
            requests=[_request(BuilderExitRequest, 1, exit_fees[1])]
        ),
    ]

    txs = []
    senders = []
    for interaction in interactions:
        prepared = interaction.update_pre(pre)
        txs += prepared.transactions()
        assert prepared.sender_account is not None
        senders.append(prepared.sender_account)
    system_call_index = len(txs) + 1

    account_expectations: Dict = {
        sender: BalAccountExpectation(
            nonce_changes=[
                BalNonceChange(block_access_index=i + 1, post_nonce=1)
            ],
        )
        for i, sender in enumerate(senders)
    }
    # Deposits are enqueued by transactions 1 and 3, exits by 2 and 4.
    account_expectations[BuilderDepositRequest.system_contract_address] = (
        _request_queue_expectation(
            BuilderDepositRequest, [(1, 1), (3, 2)], system_call_index
        )
    )
    account_expectations[BuilderExitRequest.system_contract_address] = (
        _request_queue_expectation(
            BuilderExitRequest, [(2, 1), (4, 2)], system_call_index
        )
    )

    block = Block(
        txs=txs,
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations=account_expectations
        ),
    )

    blockchain_test(pre=pre, blocks=[block], post={})


@pytest.mark.parametrize(
    "request_obj",
    [
        pytest.param(
            BuilderDepositRequest(
                pubkey=1,
                withdrawal_credentials=2,
                amount=BuilderDepositRequest.min_deposit_wei // 10**9,
                signature=3,
                fee=0,
                valid=False,
            ),
            id="deposit_insufficient_fee",
        ),
        pytest.param(
            BuilderExitRequest(pubkey=1, fee=0, valid=False),
            id="exit_insufficient_fee",
        ),
    ],
)
def test_bal_builder_request_invalid(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    request_obj: FeeSystemContractRequest,
) -> None:
    """
    Ensure BAL records only reads on a builder predeploy when the request
    call reverts for an insufficient fee: the reverted enqueue leaves no
    storage change and the system-call dequeue finds an empty queue.
    """
    interaction = SystemContractInteractionTransaction(requests=[request_obj])
    prepared = interaction.update_pre(pre)
    txs = prepared.transactions()
    sender = prepared.sender_account
    assert sender is not None

    contract = request_obj.system_contract_address

    block = Block(
        txs=txs,
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                sender: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                contract: BalAccountExpectation(
                    storage_reads=[
                        request_obj.excess_slot,
                        request_obj.count_slot,
                        request_obj.queue_head_slot,
                        request_obj.queue_tail_slot,
                    ],
                    storage_changes=[],
                ),
            }
        ),
    )

    blockchain_test(pre=pre, blocks=[block], post={})
