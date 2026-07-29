"""
Verify a DELEGATECALL to a codeless, nonexistent account succeeds without
creating or touching the target.

Ported from:
state_tests/stDelegatecallTestHomestead/delegatecallEmptycontractFiller.json

@manually-enhanced: Do not overwrite. DELEGATECALL to a codeless account
returns success; dynamic addresses, gas maxed out.
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


@pytest.mark.ported_from(
    [
        "state_tests/stDelegatecallTestHomestead/delegatecallEmptycontractFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("TangerineWhistle")
def test_delegatecall_emptycontract(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """DELEGATECALL to a codeless account succeeds (returns 1)."""
    # A DELEGATECALL to an account with no code runs nothing and returns 1.
    empty = pre.nonexistent_account()
    caller = pre.deploy_contract(
        code=Op.SSTORE(
            key=0x0,
            value=Op.DELEGATECALL(
                address=empty,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.STOP,
    )

    # DELEGATECALL predates EIP-155, so the tx must go unprotected on
    # pre-SpuriousDragon forks or it fails signature validation.
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=caller,
        protected=fork.supports_protected_txs(),
    )

    # DELEGATECALL carries no value, so it must not create (or even touch)
    # the target account.
    post = {
        caller: Account(storage={0: 1}),
        empty: Account.NONEXISTENT,
    }

    state_test(pre=pre, post=post, tx=tx)
