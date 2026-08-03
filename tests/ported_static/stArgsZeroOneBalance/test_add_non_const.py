"""
Verify ADD over non-constant operands: the contract adds its own balance to
itself, where that balance equals the value sent by the transaction.

Ported from:
state_tests/stArgsZeroOneBalance/addNonConstFiller.yml

@manually-enhanced: Do not overwrite. Parametrized on the transaction value
(the real discriminator), the self-referential balance reads use
`BALANCE(ADDRESS)` instead of a hardcoded address, and the post asserts the
`2 * tx_value` result directly; env/gas boilerplate removed. A canary slot
keeps the `tx_value=0` arm observable (its result slot stays zero).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

CANARY = 0xC0DE


@pytest.mark.ported_from(
    ["state_tests/stArgsZeroOneBalance/addNonConstFiller.yml"],
)
@pytest.mark.valid_from("Frontier")
@pytest.mark.parametrize("tx_value", [0, 1])
def test_add_non_const(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    tx_value: int,
) -> None:
    """Add the contract's own balance to itself and store the result."""
    sender = pre.fund_eoa()

    # ADD with non-constant operands: the contract's own balance added to
    # itself. The balance equals the value sent by the transaction. The
    # canary proves the code ran even when the stored result is zero.
    target = pre.deploy_contract(
        code=Op.SSTORE(
            key=0x0,
            value=Op.ADD(Op.BALANCE(Op.ADDRESS), Op.BALANCE(Op.ADDRESS)),
        )
        + Op.SSTORE(key=0x1, value=CANARY)
        + Op.STOP,
    )

    # ADD(BALANCE, BALANCE) over a balance equal to the sent value.
    post = {target: Account(storage={0: 2 * tx_value, 1: CANARY})}

    tx = Transaction(
        sender=sender,
        to=target,
        value=tx_value,
        protected=fork.supports_protected_txs(),
    )

    state_test(pre=pre, post=post, tx=tx)
