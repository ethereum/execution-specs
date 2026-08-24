"""Fork-transition tests for EIP-8368 (CPSB recalibration)."""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Fork,
    Op,
    Transaction,
    TransactionReceipt,
)
from execution_testing.checklists import EIPChecklist

from .spec import ref_spec_8368

REFERENCE_SPEC_GIT_PATH = ref_spec_8368.git_path
REFERENCE_SPEC_VERSION = ref_spec_8368.version

FORK_TIMESTAMP = 15_000


# TODO: Un-skip when a real post-Amsterdam spec fork exists. Under the
#  pseudo-fork model both sides of the transition execute the same
#  Amsterdam spec module, so the pre-fork block cannot exhibit the
#  original EIP-8037 charge this test pins.
@EIPChecklist.GasCostChanges.Test.ForkTransition.Before()
@EIPChecklist.GasCostChanges.Test.ForkTransition.After()
@pytest.mark.skip(
    reason="requires a real post-Amsterdam spec fork; the Bogota pseudo-fork "
    "executes Amsterdam on both sides of the transition"
)
@pytest.mark.valid_at_transition_to("EIP8368")
def test_cpsb_recalibrates_at_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    The cost per state byte changes at the fork boundary: an identical
    fresh storage set is billed at the original CPSB in the last
    pre-fork block and at the recalibrated CPSB right after.
    """
    pre_fork = fork.fork_at(timestamp=FORK_TIMESTAMP - 1_000)
    post_fork = fork.fork_at(timestamp=FORK_TIMESTAMP)

    code = Op.SSTORE(0, 1)
    before = pre.deploy_contract(code=code)
    after = pre.deploy_contract(code=code)

    def billed(at_fork: Fork) -> int:
        intrinsic = at_fork.transaction_intrinsic_cost_calculator()()
        return (
            intrinsic + code.execution_cost(at_fork) + code.state_cost(at_fork)
        )

    assert billed(post_fork) > billed(pre_fork), (
        "the recalibration must raise the storage set charge"
    )

    sender = pre.fund_eoa()
    blocks = [
        Block(
            timestamp=FORK_TIMESTAMP - 1_000,
            txs=[
                Transaction(
                    to=before,
                    gas_limit=1_000_000,
                    sender=sender,
                    expected_receipt=TransactionReceipt(
                        cumulative_gas_used=billed(pre_fork)
                    ),
                )
            ],
        ),
        Block(
            timestamp=FORK_TIMESTAMP,
            txs=[
                Transaction(
                    to=after,
                    gas_limit=1_000_000,
                    sender=sender,
                    expected_receipt=TransactionReceipt(
                        cumulative_gas_used=billed(post_fork)
                    ),
                )
            ],
        ),
    ]

    post = {
        before: Account(storage={0: 1}),
        after: Account(storage={0: 1}),
    }
    blockchain_test(pre=pre, post=post, blocks=blocks)
