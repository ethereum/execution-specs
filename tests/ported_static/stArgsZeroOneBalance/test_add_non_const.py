"""
Test_add_non_const.

Ported from:
state_tests/stArgsZeroOneBalance/addNonConstFiller.yml

@manually-enhanced: Do not overwrite. Parametrized on the transaction value
(the real discriminator), the self-referential balance reads use
`BALANCE(ADDRESS)` instead of a hardcoded address, and the post asserts the
`2 * tx_value` result directly; env/gas boilerplate removed.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stArgsZeroOneBalance/addNonConstFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("tx_value", [0, 1])
@pytest.mark.pre_alloc_mutable
def test_add_non_const(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_value: int,
) -> None:
    """Test_add_non_const."""
    sender = pre.fund_eoa()

    # ADD with non-constant operands: the contract's own balance added to
    # itself. The balance equals the value sent by the transaction.
    target = pre.deploy_contract(
        code=Op.SSTORE(
            key=0x0,
            value=Op.ADD(Op.BALANCE(Op.ADDRESS), Op.BALANCE(Op.ADDRESS)),
        )
        + Op.STOP,
    )

    # ADD(BALANCE, BALANCE) over a balance equal to the sent value.
    post = {target: Account(storage={0: 2 * tx_value})}

    tx = Transaction(
        sender=sender,
        to=target,
        value=tx_value,
    )

    state_test(pre=pre, post=post, tx=tx)
