"""
Check balance in blackbox, just fill the balance consumed.

Ported from:
state_tests/stStaticCall/static_CheckCallCostOOGFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_CheckCallCostOOGFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="-g0",
        ),
        pytest.param(
            0,
            1,
            0,
            id="-g1",
        ),
    ],
)
def test_static_check_call_cost_oog(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Check balance in blackbox, just fill the balance consumed."""
    sender = pre.fund_eoa(amount=0x5AF3107A4000)

    # Source: lll
    # { (MSTORE 1 1) (KECCAK256 0x00 0x2fffff) }
    addr = pre.deploy_contract(
        code=Op.MSTORE(offset=0x1, value=0x1)
        + Op.SHA3(offset=0x0, size=0x2FFFFF)
        + Op.STOP,
    )
    # Source: lll
    # { (STATICCALL 100 <contract:0x2000000000000000000000000000000000000000> 0 0 0 0) }  # noqa: E501
    target = pre.deploy_contract(
        code=Op.STATICCALL(
            gas=0x64,
            address=addr,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
    )

    tx_data = [
        Bytes(""),
    ]
    tx_gas = [22000, 1000000]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
    )

    post = {sender: Account(nonce=1)}

    state_test(pre=pre, post=post, tx=tx)
