"""
Validation budget tests for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

`MAX_VERIFY_GAS` bounds the work a public mempool spends simulating a
transaction's validation prefix. It is mempool policy, not consensus: a
block may include a transaction whose validation prefix exceeds it.
These tests budget a `VERIFY` frame exactly at the cap and one above
it, its code burning the budget down before approving, and check that
both execute in a valid block.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    Op,
    StateTestFiller,
    Transaction,
    WhileGas,
)

from .helpers import APPROVE_ALL, verify_frame
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")


@pytest.mark.parametrize(
    "excess",
    [
        pytest.param(0, id="at_max_verify_gas"),
        pytest.param(1, id="above_max_verify_gas"),
    ],
)
def test_verify_gas_cap_not_enforced_in_block(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    excess: int,
) -> None:
    """
    Test that a `VERIFY` frame budgeted `MAX_VERIFY_GAS`, or one more,
    burns its budget down to the approval and executes.

    The sender is a contract, so the transaction carries no signature
    entries and the frame's execution budget is the whole validation
    work the public mempool counts against `MAX_VERIFY_GAS`.
    """
    sender = pre.deploy_contract(
        code=WhileGas(
            body=Op.JUMPDEST,
            fork=fork,
            extra_gas=APPROVE_ALL.gas_cost(fork),
        )
        + APPROVE_ALL,
        balance=10**18,
    )
    tx = Transaction(
        sender=sender,
        nonce=1,
        frames=[verify_frame(gas_limit=Spec.MAX_VERIFY_GAS + excess)],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={sender: Account(nonce=2)},
    )
