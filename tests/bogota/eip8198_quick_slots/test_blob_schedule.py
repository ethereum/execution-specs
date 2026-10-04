"""
Blob schedule tests for
[EIP-8198: Quick Slots](https://eips.ethereum.org/EIPS/eip-8198).

From the fork onward, blocks carry at most `MAX_BLOBS_PER_BLOCK` blobs, the
excess blob gas moves around `TARGET_BLOBS_PER_BLOCK`, and the blob base fee
uses `BLOB_BASE_FEE_UPDATE_FRACTION`.
"""

from typing import List

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    EIPChecklist,
    Environment,
    Fork,
    Header,
    TransactionException,
)

from .helpers import blob_transactions
from .spec import Spec, ref_spec_8198

REFERENCE_SPEC_GIT_PATH = ref_spec_8198.git_path
REFERENCE_SPEC_VERSION = ref_spec_8198.version

pytestmark = pytest.mark.valid_from("EIP8198")

BASE_FEE_PER_GAS = 7
"""
Base fee of every block in these tests. It is low enough that the blob base
fee reserve price stays inactive, and blocks well below their gas target
keep it unchanged.
"""

GENESIS_EXCESS_BLOB_GAS = 300 * Spec.GAS_PER_BLOB
"""
Excess blob gas at genesis, high enough that the blob base fee is well above
its minimum and depends on the update fraction.
"""

BLOB_COUNT_ERRORS = [
    TransactionException.TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED,
    TransactionException.TYPE_3_TX_BLOB_COUNT_EXCEEDED,
]


def blob_base_fee(excess_blob_gas: int) -> int:
    """Return the blob base fee under the fork's update fraction."""
    return Spec.blob_base_fee(
        excess_blob_gas=excess_blob_gas,
        update_fraction=Spec.BLOB_BASE_FEE_UPDATE_FRACTION,
    )


def next_excess_blob_gas(excess_blob_gas: int, blob_count: int) -> int:
    """Return the next block's excess blob gas under the fork's schedule."""
    return Spec.next_excess_blob_gas(
        parent_excess_blob_gas=excess_blob_gas,
        parent_blob_gas_used=blob_count * Spec.GAS_PER_BLOB,
        parent_base_fee_per_gas=BASE_FEE_PER_GAS,
        target_blobs_per_block=Spec.TARGET_BLOBS_PER_BLOCK,
        max_blobs_per_block=Spec.MAX_BLOBS_PER_BLOCK,
        update_fraction=Spec.BLOB_BASE_FEE_UPDATE_FRACTION,
    )


@pytest.mark.parametrize(
    "blob_count",
    [
        pytest.param(Spec.TARGET_BLOBS_PER_BLOCK, id="target"),
        pytest.param(Spec.MAX_BLOBS_PER_BLOCK - 1, id="max_minus_one"),
        pytest.param(Spec.MAX_BLOBS_PER_BLOCK, id="max"),
        pytest.param(
            Spec.MAX_BLOBS_PER_BLOCK + 1,
            id="max_plus_one",
            marks=pytest.mark.exception_test,
        ),
    ],
)
@EIPChecklist.BlockLevelConstraint.Test.Boundary.Under()
@EIPChecklist.BlockLevelConstraint.Test.Boundary.Exact()
@EIPChecklist.BlockLevelConstraint.Test.Boundary.Over()
def test_blob_count_limit(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    blob_count: int,
) -> None:
    """
    Accept a block with up to `MAX_BLOBS_PER_BLOCK` blobs and reject one with
    a blob more.
    """
    sender = pre.fund_eoa()
    destination = pre.fund_eoa(amount=0)
    over_limit = blob_count > Spec.MAX_BLOBS_PER_BLOCK
    txs = blob_transactions(
        sender=sender,
        destination=destination,
        fork=fork,
        blob_count=blob_count,
        max_fee_per_blob_gas=blob_base_fee(0),
        error=BLOB_COUNT_ERRORS if over_limit else None,
    )
    blockchain_test(
        pre=pre,
        post={} if over_limit else {destination: Account(balance=len(txs))},
        blocks=[
            Block(
                txs=txs,
                timestamp=10,
                exception=BLOB_COUNT_ERRORS if over_limit else None,
                header_verify=(
                    None
                    if over_limit
                    else Header(blob_gas_used=blob_count * Spec.GAS_PER_BLOB)
                ),
            )
        ],
        genesis_environment=Environment(base_fee_per_gas=BASE_FEE_PER_GAS),
    )


@pytest.mark.parametrize(
    "blob_counts",
    [
        pytest.param([Spec.MAX_BLOBS_PER_BLOCK] * 4, id="max_blobs"),
        pytest.param([Spec.TARGET_BLOBS_PER_BLOCK] * 4, id="target_blobs"),
        pytest.param([0] * 4, id="no_blobs"),
        pytest.param(
            [Spec.MAX_BLOBS_PER_BLOCK, 0, Spec.TARGET_BLOBS_PER_BLOCK, 1],
            id="mixed",
        ),
    ],
)
def test_blob_base_fee_evolution(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    blob_counts: List[int],
) -> None:
    """
    Check the excess blob gas of each block and that its blob transactions
    are accepted when they offer exactly the blob base fee.

    Every block is followed by one more carrying a single blob, so the excess
    blob gas left by each block is also checked.
    """
    sender = pre.fund_eoa()
    destination = pre.fund_eoa(amount=0)
    excess_blob_gas = next_excess_blob_gas(GENESIS_EXCESS_BLOB_GAS, 0)
    blocks = []
    tx_count = 0
    blob_index = 0
    for i, blob_count in enumerate(blob_counts + [1]):
        txs = blob_transactions(
            sender=sender,
            destination=destination,
            fork=fork,
            blob_count=blob_count,
            max_fee_per_blob_gas=blob_base_fee(excess_blob_gas),
            first_blob_index=blob_index,
        )
        blocks.append(
            Block(
                txs=txs,
                timestamp=10 * (i + 1),
                header_verify=Header(
                    excess_blob_gas=excess_blob_gas,
                    blob_gas_used=blob_count * Spec.GAS_PER_BLOB,
                    base_fee_per_gas=BASE_FEE_PER_GAS,
                ),
            )
        )
        tx_count += len(txs)
        blob_index += blob_count
        excess_blob_gas = next_excess_blob_gas(excess_blob_gas, blob_count)
    blockchain_test(
        pre=pre,
        post={destination: Account(balance=tx_count)},
        blocks=blocks,
        genesis_environment=Environment(
            base_fee_per_gas=BASE_FEE_PER_GAS,
            excess_blob_gas=GENESIS_EXCESS_BLOB_GAS,
            blob_gas_used=0,
        ),
    )


@pytest.mark.exception_test
def test_insufficient_max_fee_per_blob_gas(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Reject a blob transaction offering one wei less than the blob base fee
    given by the fork's update fraction.
    """
    sender = pre.fund_eoa()
    destination = pre.fund_eoa(amount=0)
    excess_blob_gas = next_excess_blob_gas(GENESIS_EXCESS_BLOB_GAS, 0)
    error = TransactionException.INSUFFICIENT_MAX_FEE_PER_BLOB_GAS
    blockchain_test(
        pre=pre,
        post={},
        blocks=[
            Block(
                txs=blob_transactions(
                    sender=sender,
                    destination=destination,
                    fork=fork,
                    blob_count=1,
                    max_fee_per_blob_gas=blob_base_fee(excess_blob_gas) - 1,
                    error=error,
                ),
                timestamp=10,
                exception=error,
            )
        ],
        genesis_environment=Environment(
            base_fee_per_gas=BASE_FEE_PER_GAS,
            excess_blob_gas=GENESIS_EXCESS_BLOB_GAS,
            blob_gas_used=0,
        ),
    )
