"""
Create a contract at an address that already holds code.

Ported from:
state_tests/stEIP3607/initCollidingWithNonEmptyAccountFiller.yml

@manually-enhanced: Do not overwrite. Collapsed into one checked case.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Header,
    StateTestFiller,
    Transaction,
    compute_create2_address,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

GAS_LIMIT = 400_000
CALL_VALUE = 10_000


@pytest.mark.ported_from(
    ["state_tests/stEIP3607/initCollidingWithNonEmptyAccountFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_init_colliding_with_non_empty_account(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Fail a creation transaction that targets a nonce-0 account with code.

    The collision consumes all the gas and none of the init code runs.
    """
    sender = pre.fund_eoa()
    callee = pre.deploy_contract(code=Op.STOP)
    collider = compute_create_address(address=sender, nonce=0)
    pre.deploy_contract(
        code=Op.SSTORE(1, 0),
        balance=10**18,
        nonce=0,
        address=collider,
    )

    initcode = (
        Op.SSTORE(0, 1)
        + Op.POP(Op.CALL(address=callee, value=CALL_VALUE))
        + Op.POP(Op.DELEGATECALL(address=callee))
        + Op.POP(Op.CREATE2(value=CALL_VALUE, offset=0, size=0x20, salt=0))
        + Op.POP(Op.CREATE(value=CALL_VALUE, offset=0, size=0x20))
        + Op.RETURN(offset=0, size=0x20)
    )
    tx = Transaction(
        sender=sender,
        to=None,
        data=initcode,
        gas_limit=GAS_LIMIT,
        value=100_000,
    )

    post = {
        collider: Account(
            storage={}, code=Op.SSTORE(1, 0), nonce=0, balance_change=0
        ),
        callee: Account(balance=0),
        compute_create2_address(collider, 0, bytes(0x20)): Account.NONEXISTENT,
        compute_create_address(address=collider, nonce=0): Account.NONEXISTENT,
        sender: Account(nonce=1),
    }
    state_test(
        pre=pre,
        post=post,
        tx=tx,
        blockchain_test_header_verify=Header(gas_used=GAS_LIMIT),
    )
