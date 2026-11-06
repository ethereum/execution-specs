"""
Recursive call.

Ported from:
state_tests/stCallCreateCallCodeTest/CallLoseGasOOGFiller.json
state_tests/stCallCreateCallCodeTest/CallcodeLoseGasOOGFiller.json
state_tests/stDelegatecallTestHomestead/CallLoseGasOOGFiller.json
state_tests/stDelegatecallTestHomestead/CallcodeLoseGasOOGFiller.json
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
    [
        "state_tests/stCallCreateCallCodeTest/CallLoseGasOOGFiller.json",
        "state_tests/stCallCreateCallCodeTest/CallcodeLoseGasOOGFiller.json",
        "state_tests/stDelegatecallTestHomestead/CallLoseGasOOGFiller.json",
        "state_tests/stDelegatecallTestHomestead/CallcodeLoseGasOOGFiller.json",
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "opcode",
    [
        pytest.param(Op.CALL, id="call"),
        pytest.param(Op.CALLCODE, id="callcode"),
        pytest.param(Op.DELEGATECALL, id="delegatecall"),
    ],
)
@pytest.mark.parametrize(
    "tx_gas",
    [
        pytest.param(None, id="enough_gas"),
        pytest.param(166262, id="tx_oog"),
        pytest.param(156262, id="tx_oog_lower"),
    ],
)
def test_call_lose_gas_oog(
    state_test: StateTestFiller,
    pre: Alloc,
    opcode: Op,
    tx_gas: int | None,
) -> None:
    """
    Recurse into ADDRESS with more gas than the frame has left.

    The inner frame runs out of gas, its gas is lost and the outer frame
    finishes, unless the tx gas limit cannot cover the lost gas.
    """
    sender = pre.fund_eoa()

    # Source: lll
    # { [[ 0 ]] (ADD @@0 1) [[ 1 ]] (CALL (ADD 1(MUL @@0 100000)) <contract:target:0xbbbf5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[ 2 ]] (ADD 1(MUL @@0 1000)) }  # noqa: E501
    target = pre.deploy_contract(
        code=Op.SSTORE(0, Op.ADD(Op.SLOAD(0), 1))
        + Op.SSTORE(
            1,
            opcode(
                gas=Op.ADD(1, Op.MUL(Op.SLOAD(0), 100000)),
                address=Op.ADDRESS,
            ),
        )
        + Op.SSTORE(2, Op.ADD(1, Op.MUL(Op.SLOAD(0), 1000)))
        + Op.STOP,
    )

    tx = Transaction(sender=sender, to=target, gas_limit=tx_gas)

    if tx_gas is None:
        storage = {0: 1, 1: 0, 2: 1001}
    else:
        storage = {}
    post = {target: Account(storage=storage)}

    state_test(pre=pre, post=post, tx=tx)
