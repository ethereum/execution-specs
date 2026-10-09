"""
Calldepth with balance too low.

Ported from:
state_tests/stCallCreateCallCodeTest/Call1024BalanceTooLowFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

from tests.ported_static.constants import HIGH_GAS_LIMIT

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stCallCreateCallCodeTest/Call1024BalanceTooLowFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
def test_call1024_balance_too_low(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Calldepth with balance too low."""
    sender = pre.fund_eoa(amount=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)

    addr = pre.fund_eoa(amount=7000)  # noqa: F841
    # Source: lll
    # { [[ 0 ]] (ADD @@0 1) [[ 1 ]] (CALL 0xfffffffffff <contract:target:0xbbbf5374fce5edbc8e2a8697c15331677e6ebf0b> @@0 0 0 0 0) }  # noqa: E501
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
        + Op.SSTORE(
            key=0x1,
            value=Op.CALL(
                gas=0xFFFFFFFFFFF,
                address=Op.ADDRESS,
                value=Op.SLOAD(key=0x0),
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
        balance=1024,
    )

    env = Environment(gas_limit=HIGH_GAS_LIMIT)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=17592186099592,
        value=10,
    )

    post = {target: Account(storage={0: 1025, 1: 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
