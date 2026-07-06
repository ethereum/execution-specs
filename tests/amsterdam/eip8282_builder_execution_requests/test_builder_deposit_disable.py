"""
Disable-switch tests for
[EIP-8282: Builder Execution Requests](https://eips.ethereum.org/EIPS/eip-8282).

The builder deposit predeploy carries a reversible kill switch (sys-asm#49):
while `EXCESS_INHIBITOR` sits in the excess slot, deposits revert, and the
next end-of-block system call clears the slot and re-enables the queue. Only
a system call carrying input sets the inhibitor, and the protocol never sends
input, so the disabled state is seeded directly here rather than triggered.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Fork,
    Requests,
    SystemContractInteractionTransaction,
)

from .helpers import BuilderDepositRequest
from .spec import Spec, ref_spec_8282

REFERENCE_SPEC_GIT_PATH = ref_spec_8282.git_path
REFERENCE_SPEC_VERSION = ref_spec_8282.version

pytestmark = [
    pytest.mark.valid_from("Amsterdam"),
    pytest.mark.pre_alloc_mutable(),
]


@pytest.fixture
def inhibited_pre(pre: Alloc, fork: Fork) -> Alloc:
    """Seed the builder deposit predeploy with the disable inhibitor set."""
    predeploy = fork.pre_allocation_blockchain()[
        Spec.BUILDER_DEPOSIT_CONTRACT_ADDRESS
    ]
    pre[Spec.BUILDER_DEPOSIT_CONTRACT_ADDRESS] = Account(
        nonce=predeploy["nonce"],
        code=predeploy["code"],
        storage={
            Spec.EXCESS_DEPOSIT_REQUESTS_STORAGE_SLOT: Spec.EXCESS_INHIBITOR
        },
    )
    return pre


def test_builder_deposit_inhibited(
    blockchain_test: BlockchainTestFiller,
    inhibited_pre: Alloc,
) -> None:
    """
    A deposit to an inhibited predeploy reverts and produces no request, while
    the end-of-block system call clears the inhibitor back to zero.
    """
    deposit = SystemContractInteractionTransaction(
        requests=[BuilderDepositRequest.from_index(0)]
    ).update_pre(inhibited_pre)

    blockchain_test(
        pre=inhibited_pre,
        blocks=[
            Block(
                txs=deposit.transactions(),
                requests_hash=Requests(),
            ),
        ],
        post={
            Spec.BUILDER_DEPOSIT_CONTRACT_ADDRESS: Account(
                storage={Spec.EXCESS_DEPOSIT_REQUESTS_STORAGE_SLOT: 0},
            ),
        },
    )
