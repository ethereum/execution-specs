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
    Environment,
)

from tests.prague.eip7251_consolidations.helpers import (
    ConsolidationRequest,
    ConsolidationRequestTransaction,
)
from tests.prague.eip7251_consolidations.spec import Spec, ref_spec_7251

REFERENCE_SPEC_GIT_PATH = ref_spec_7251.git_path
REFERENCE_SPEC_VERSION = ref_spec_7251.version

pytestmark = pytest.mark.valid_from("Amsterdam")

CONSOLIDATION_REQUEST_PREDEPLOY_ADDRESS = (
    Spec.CONSOLIDATION_REQUEST_PREDEPLOY_ADDRESS
)
CONSOLIDATION_REQUEST_COUNT_STORAGE_SLOT = (
    Spec.CONSOLIDATION_REQUEST_COUNT_STORAGE_SLOT
)
CONSOLIDATION_REQUEST_QUEUE_HEAD_STORAGE_SLOT = (
    Spec.CONSOLIDATION_REQUEST_QUEUE_HEAD_STORAGE_SLOT
)
CONSOLIDATION_REQUEST_QUEUE_TAIL_STORAGE_SLOT = (
    Spec.CONSOLIDATION_REQUEST_QUEUE_TAIL_STORAGE_SLOT
)
MAX_CONSOLIDATION_REQUESTS_PER_BLOCK = (
    Spec.MAX_CONSOLIDATION_REQUESTS_PER_BLOCK
)
SYSTEM_ADDRESS = Address(Spec.SYSTEM_ADDRESS)


@pytest.mark.parametrize(
    "blocks_consolidation_requests",
    [
        pytest.param(
            [
                ConsolidationRequestTransaction(
                    requests=[
                        ConsolidationRequest(
                            source_pubkey=0x01,
                            target_pubkey=0x02,
                            fee=Spec.get_fee(0),
                        )
                    ],
                )
            ],
            id="single_block_single_consolidation_request_from_eoa",
        ),
        pytest.param(
            [
                ConsolidationRequestTransaction(
                    requests=[
                        ConsolidationRequest(
                            source_pubkey=i * 2 + 1,
                            target_pubkey=i * 2 + 2,
                            fee=Spec.get_fee(0),
                        )
                    ],
                )
                for i in range(MAX_CONSOLIDATION_REQUESTS_PER_BLOCK)
            ],
            id="single_block_max_consolidation_per_block",
        ),
        pytest.param(
            [
                ConsolidationRequestTransaction(
                    requests=[
                        ConsolidationRequest(
                            source_pubkey=i * 2 + 1,
                            target_pubkey=i * 2 + 2,
                            fee=Spec.get_fee(0),
                        )
                    ],
                )
                for i in range(MAX_CONSOLIDATION_REQUESTS_PER_BLOCK + 1)
            ],
            id="single_block_max_consolidation_per_block_plus1",
        ),
    ],
)
@pytest.mark.pre_alloc_group(
    "consolidation_requests",
    reason="Tests standard consolidation request functionality",
)
def test_bal_system_dequeue_consolidations_eip7251(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    blocks_consolidation_requests: List[ConsolidationRequestTransaction],
) -> None:
    """Test making a consolidation request to the beacon chain."""
    txs = []

    for request in blocks_consolidation_requests:
        request.update_pre(pre=pre)
        txs += request.transactions()

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

    block = Block(
        txs=txs,
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                CONSOLIDATION_REQUEST_PREDEPLOY_ADDRESS: (
                    BalAccountExpectation(storage_changes=storage_changes)
                )
            }
        ),
    )

    blockchain_test(
        genesis_environment=Environment(),
        pre=pre,
        post={},
        blocks=[block],
    )
