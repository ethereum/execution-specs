"""
Recursive call.

Ported from:
state_tests/stCallCreateCallCodeTest/CallLoseGasOOGFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Amsterdam
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stCallCreateCallCodeTest/CallLoseGasOOGFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_call_lose_gas_oog(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
) -> None:
    """Recursive call."""
    sender = pre.fund_eoa(amount=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)

    addr = pre.fund_eoa(amount=7000)  # noqa: F841
    # Source: lll
    # { [[ 0 ]] (ADD @@0 1) [[ 1 ]] (CALL (ADD 1(MUL @@0 100000)) <contract:target:0xbbbf5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[ 2 ]] (ADD 1(MUL @@0 1000)) }  # noqa: E501
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
        + Op.SSTORE(
            key=0x1,
            value=Op.CALL(
                gas=Op.ADD(0x1, Op.MUL(Op.SLOAD(key=0x0), 0x186A0)),
                address=Op.ADDRESS,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(
            key=0x2, value=Op.ADD(0x1, Op.MUL(Op.SLOAD(key=0x0), 0x3E8))
        )
        + Op.STOP,
        balance=1024,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=2200000 if fork >= Amsterdam else 200000,
        value=10,
    )

    post = {target: Account(storage={0: 1, 2: 1001})}

    state_test(pre=pre, post=post, tx=tx)
