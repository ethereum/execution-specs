"""
Tests for the [EIP-7666](https://eips.ethereum.org/EIPS/eip-7666) fork
transition.

Before the fork, the identity address is a warm precompile. From the fork on,
it is ordinary code that costs as much to call as any other contract holding
the same code.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Op,
    Transaction,
)

from .helpers import compare_call_costs
from .spec import Spec, ref_spec_7666

REFERENCE_SPEC_GIT_PATH = ref_spec_7666.git_path
REFERENCE_SPEC_VERSION = ref_spec_7666.version

pytestmark = pytest.mark.valid_at_transition_to("EIP7666")


def test_identity_across_transition(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    Compare a call to the identity address with a call to a twin contract
    in the last block before the fork and the first block after it: the
    costs only match once the fork has activated.
    """
    twin = pre.deploy_contract(code=Spec.EVM_CODE)
    contract = pre.deploy_contract(
        code=Op.SSTORE(Op.NUMBER, compare_call_costs(twin))
    )
    sender = pre.fund_eoa()
    blocks = [
        Block(
            timestamp=14_999,
            txs=[Transaction(sender=sender, to=contract)],
        ),
        Block(
            timestamp=15_000,
            txs=[Transaction(sender=sender, to=contract)],
        ),
    ]
    blockchain_test(
        pre=pre,
        blocks=blocks,
        post={contract: Account(storage={1: 0, 2: 1})},
    )
