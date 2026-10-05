"""
Blob schedule tests for
[EIP-8198: Quick Slots](https://eips.ethereum.org/EIPS/eip-8198).

From the fork onward, blocks carry at most the fork's maximum blob count,
the excess blob gas moves around its target blob count, and the blob base
fee uses its update fraction.
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
    ParameterSet,
    TransactionException,
)

from .helpers import BLOB_COUNT_ERRORS, blob_transactions
from .spec import ref_spec_8198

REFERENCE_SPEC_GIT_PATH = ref_spec_8198.git_path
REFERENCE_SPEC_VERSION = ref_spec_8198.version

pytestmark = pytest.mark.valid_from("EIP8198")

BASE_FEE_PER_GAS = 7
"""
Base fee of every block in these tests. It is low enough that the blob base
fee reserve price stays inactive, and blocks well below their gas target
keep it unchanged.
"""

GENESIS_EXCESS_BLOBS = 300
"""
Excess blobs at genesis, high enough that the blob base fee is well above
its minimum and depends on the update fraction.
"""


def next_excess_blob_gas(
    fork: Fork, parent_excess_blob_gas: int, parent_blob_count: int
) -> int:
    """Return the next block's excess blob gas under the fork's schedule."""
    calc_excess_blob_gas = fork.excess_blob_gas_calculator()
    return calc_excess_blob_gas(
        parent_excess_blob_gas=parent_excess_blob_gas,
        parent_blob_count=parent_blob_count,
        parent_base_fee_per_gas=BASE_FEE_PER_GAS,
    )


@pytest.mark.parametrize_by_fork(
    "blob_count",
    lambda fork: [
        pytest.param(fork.target_blobs_per_block(), id="target"),
        pytest.param(fork.max_blobs_per_block() - 1, id="max_minus_one"),
        pytest.param(fork.max_blobs_per_block(), id="max"),
        pytest.param(
            fork.max_blobs_per_block() + 1,
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
    Accept a block with up to the fork's maximum blob count and reject one
    with a blob more.
    """
    sender = pre.fund_eoa()
    destination = pre.fund_eoa(amount=0)
    get_blob_gas_price = fork.blob_gas_price_calculator()
    over_limit = blob_count > fork.max_blobs_per_block()
    txs = blob_transactions(
        sender=sender,
        destination=destination,
        fork=fork,
        blob_count=blob_count,
        max_fee_per_blob_gas=get_blob_gas_price(excess_blob_gas=0),
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
                    else Header(
                        blob_gas_used=blob_count * fork.blob_gas_per_blob()
                    )
                ),
            )
        ],
        genesis_environment=Environment(base_fee_per_gas=BASE_FEE_PER_GAS),
    )


def blob_count_sequences(fork: Fork) -> List[ParameterSet]:
    """Return the blob counts of successive blocks."""
    target = fork.target_blobs_per_block()
    maximum = fork.max_blobs_per_block()
    return [
        pytest.param([maximum] * 4, id="max_blobs"),
        pytest.param([target] * 4, id="target_blobs"),
        pytest.param([0] * 4, id="no_blobs"),
        pytest.param([maximum, 0, target, 1], id="mixed"),
    ]


@pytest.mark.parametrize_by_fork("blob_counts", blob_count_sequences)
def test_blob_base_fee_evolution(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    blob_counts: List[int],
) -> None:
    """
    Check the excess blob gas of each block and accept blob transactions
    offering exactly the blob base fee.
    """
    sender = pre.fund_eoa()
    destination = pre.fund_eoa(amount=0)
    get_blob_gas_price = fork.blob_gas_price_calculator()
    blob_gas_per_blob = fork.blob_gas_per_blob()
    genesis_excess_blob_gas = GENESIS_EXCESS_BLOBS * blob_gas_per_blob
    excess_blob_gas = next_excess_blob_gas(fork, genesis_excess_blob_gas, 0)
    blocks = []
    tx_count = 0
    blob_index = 0
    # A final one-blob block checks the excess left by the last block.
    for i, blob_count in enumerate(blob_counts + [1]):
        txs = blob_transactions(
            sender=sender,
            destination=destination,
            fork=fork,
            blob_count=blob_count,
            max_fee_per_blob_gas=get_blob_gas_price(
                excess_blob_gas=excess_blob_gas
            ),
            first_blob_index=blob_index,
        )
        blocks.append(
            Block(
                txs=txs,
                timestamp=10 * (i + 1),
                header_verify=Header(
                    excess_blob_gas=excess_blob_gas,
                    blob_gas_used=blob_count * blob_gas_per_blob,
                    base_fee_per_gas=BASE_FEE_PER_GAS,
                ),
            )
        )
        tx_count += len(txs)
        blob_index += blob_count
        excess_blob_gas = next_excess_blob_gas(
            fork, excess_blob_gas, blob_count
        )
    blockchain_test(
        pre=pre,
        post={destination: Account(balance=tx_count)},
        blocks=blocks,
        genesis_environment=Environment(
            base_fee_per_gas=BASE_FEE_PER_GAS,
            excess_blob_gas=genesis_excess_blob_gas,
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
    genesis_excess_blob_gas = GENESIS_EXCESS_BLOBS * fork.blob_gas_per_blob()
    excess_blob_gas = next_excess_blob_gas(fork, genesis_excess_blob_gas, 0)
    blob_gas_price = fork.blob_gas_price_calculator()(
        excess_blob_gas=excess_blob_gas
    )
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
                    max_fee_per_blob_gas=blob_gas_price - 1,
                    error=error,
                ),
                timestamp=10,
                exception=error,
            )
        ],
        genesis_environment=Environment(
            base_fee_per_gas=BASE_FEE_PER_GAS,
            excess_blob_gas=genesis_excess_blob_gas,
            blob_gas_used=0,
        ),
    )
