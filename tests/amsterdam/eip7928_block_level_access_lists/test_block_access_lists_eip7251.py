"""Tests for the effects of EIP-7251 consolidation requests on EIP-7928."""

from typing import List

import pytest
from execution_testing import (
    Address,
    Alloc,
    BalAccountExpectation,
    BalStorageChange,
    BalStorageSlot,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    ConsolidationRequest,
    Environment,
    SystemContractInteractionTransaction,
)

from tests.prague.eip7251_consolidations.spec import Spec, ref_spec_7251

REFERENCE_SPEC_GIT_PATH = ref_spec_7251.git_path
REFERENCE_SPEC_VERSION = ref_spec_7251.version

pytestmark = pytest.mark.valid_from("Amsterdam")

CONSOLIDATION_REQUEST_PREDEPLOY_ADDRESS = (
    ConsolidationRequest.system_contract_address
)
CONSOLIDATION_REQUEST_COUNT_STORAGE_SLOT = ConsolidationRequest.count_slot
CONSOLIDATION_REQUEST_QUEUE_HEAD_STORAGE_SLOT = (
    ConsolidationRequest.queue_head_slot
)
CONSOLIDATION_REQUEST_QUEUE_TAIL_STORAGE_SLOT = (
    ConsolidationRequest.queue_tail_slot
)
MAX_CONSOLIDATION_REQUESTS_PER_BLOCK = ConsolidationRequest.max_per_block
SYSTEM_ADDRESS = Address(Spec.SYSTEM_ADDRESS)


@pytest.mark.parametrize(
    "blocks_consolidation_requests",
    [
        pytest.param(
            [
                SystemContractInteractionTransaction(
                    requests=[
                        ConsolidationRequest(
                            source_pubkey=0x01,
                            target_pubkey=0x02,
                            fee=ConsolidationRequest.get_fee(0),
                        )
                    ],
                )
            ],
            id="single_block_single_consolidation_request_from_eoa",
        ),
        pytest.param(
            [
                SystemContractInteractionTransaction(
                    requests=[
                        ConsolidationRequest(
                            source_pubkey=i * 2 + 1,
                            target_pubkey=i * 2 + 2,
                            fee=ConsolidationRequest.get_fee(0),
                        )
                    ],
                )
                for i in range(MAX_CONSOLIDATION_REQUESTS_PER_BLOCK)
            ],
            id="single_block_max_consolidation_per_block",
        ),
        pytest.param(
            [
                SystemContractInteractionTransaction(
                    requests=[
                        ConsolidationRequest(
                            source_pubkey=i * 2 + 1,
                            target_pubkey=i * 2 + 2,
                            fee=ConsolidationRequest.get_fee(0),
                        )
                    ],
                )
                for i in range(MAX_CONSOLIDATION_REQUESTS_PER_BLOCK + 1)
            ],
            id="single_block_max_consolidation_per_block_plus1",
        ),
    ],
)
def test_bal_system_dequeue_consolidations_eip7251(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    blocks_consolidation_requests: List[SystemContractInteractionTransaction],
) -> None:
    """Test making a consolidation request to the beacon chain."""
    txs = []

    for request in blocks_consolidation_requests:
        prepared = request.update_pre(pre=pre)
        txs += prepared.transactions()

    num = len(txs)

    count_slot_changes = []
    head_slot_changes = []
    tail_slot_changes = []

    for idx, _ in enumerate(txs):
        count_slot_changes.append(
            BalStorageChange(block_access_index=idx + 1, post_value=idx + 1)
        )

        tail_slot_changes.append(
            BalStorageChange(block_access_index=idx + 1, post_value=idx + 1)
        )

    # Count slot is always reset to zero after request processing
    count_slot_changes.append(
        BalStorageChange(block_access_index=num + 1, post_value=0)
    )

    if num > MAX_CONSOLIDATION_REQUESTS_PER_BLOCK:
        head_slot_changes.append(
            BalStorageChange(
                block_access_index=num + 1,
                post_value=MAX_CONSOLIDATION_REQUESTS_PER_BLOCK,
            )
        )
    else:
        tail_slot_changes.append(
            BalStorageChange(block_access_index=num + 1, post_value=0)
        )

    storage_changes = []
    if any(count_slot_changes):
        storage_changes.append(
            BalStorageSlot(
                slot=CONSOLIDATION_REQUEST_COUNT_STORAGE_SLOT,
                slot_changes=count_slot_changes,
            )
        )

    if any(head_slot_changes):
        storage_changes.append(
            BalStorageSlot(
                slot=CONSOLIDATION_REQUEST_QUEUE_HEAD_STORAGE_SLOT,
                slot_changes=head_slot_changes,
            )
        )

    if any(tail_slot_changes):
        storage_changes.append(
            BalStorageSlot(
                slot=CONSOLIDATION_REQUEST_QUEUE_TAIL_STORAGE_SLOT,
                slot_changes=tail_slot_changes,
            )
        )

    # The dequeue rewrites the excess slot; when the block's count leaves
    # it unchanged the write is a no-op and the slot surfaces as a read.
    excess_after_block = ConsolidationRequest.get_excess(0, num)
    if excess_after_block > 0:
        storage_changes.insert(
            0,
            BalStorageSlot(
                slot=ConsolidationRequest.excess_slot,
                slot_changes=[
                    BalStorageChange(
                        block_access_index=num + 1,
                        post_value=excess_after_block,
                    )
                ],
            ),
        )
        predeploy_expectation = BalAccountExpectation(
            storage_changes=storage_changes
        )
    else:
        predeploy_expectation = BalAccountExpectation(
            storage_changes=storage_changes,
            storage_reads=[ConsolidationRequest.excess_slot],
        )

    block = Block(
        txs=txs,
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                CONSOLIDATION_REQUEST_PREDEPLOY_ADDRESS: predeploy_expectation
            }
        ),
    )

    blockchain_test(
        genesis_environment=Environment(),
        pre=pre,
        post={},
        blocks=[block],
    )
