"""
Test_refund_suicide50procent_cap.

Ported from:
state_tests/stRefundTest/refundSuicide50procentCapFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRefundTest/refundSuicide50procentCapFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="d0",
        ),
        pytest.param(
            1,
            0,
            0,
            id="d1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_refund_suicide50procent_cap(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_refund_suicide50procent_cap."""
    coinbase = Address(0xEB201D2887816E041F6E807E804F64F3A7A226FE)
    sender = pre.fund_eoa(amount=0x3B9ACA00)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[coinbase] = Account(balance=0, nonce=1)
    # Source: lll
    # { [22] (GAS) [[ 10 ]] 1 [[ 11 ]] (CALL (CALLDATALOAD 0) <contract:0xaaae7baea6a6c7c4c2dfeb977efac326af552aaa> 0 0 0 0 0 ) [[ 1 ]] 0 [[ 2 ]] 0 [[ 3 ]] 0 [[ 4 ]] 0 [[ 5 ]] 0 [[ 6 ]] 0 [[ 7 ]] 0 [[ 8 ]] 0 [[ 23 ]] (SUB @22 (GAS)) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x16, value=Op.GAS)
        + Op.SSTORE(key=0xA, value=0x1)
        + Op.SSTORE(
            key=0xB,
            value=Op.CALL(
                gas=Op.CALLDATALOAD(offset=0x0),
                address=0x4FF65047CE9C85F968689E4369C10003026A41A9,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x1, value=0x0)
        + Op.SSTORE(key=0x2, value=0x0)
        + Op.SSTORE(key=0x3, value=0x0)
        + Op.SSTORE(key=0x4, value=0x0)
        + Op.SSTORE(key=0x5, value=0x0)
        + Op.SSTORE(key=0x6, value=0x0)
        + Op.SSTORE(key=0x7, value=0x0)
        + Op.SSTORE(key=0x8, value=0x0)
        + Op.SSTORE(key=0x17, value=Op.SUB(Op.MLOAD(offset=0x16), Op.GAS))
        + Op.STOP,
        storage={1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1},
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xA6CC2CA5611255D50118601AA8ECE6F124FC4C45),  # noqa: E501
    )
    # Source: lll
    # { (SELFDESTRUCT <contract:target:0x095e7baea6a6c7c4c2dfeb977efac326af552d87>) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SELFDESTRUCT(
            address=0xA6CC2CA5611255D50118601AA8ECE6F124FC4C45
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x4FF65047CE9C85F968689E4369C10003026A41A9),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(
                    storage={10: 1, 11: 0, 23: 0x107A7},
                    balance=0xDE0B6B3A7640000,
                ),
                sender: Account(nonce=1),
            },
        },
        {
            "indexes": {"data": 1, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(
                    storage={10: 1, 11: 1, 23: 0x166FA},
                    balance=0x1BC16D674EC80000,
                ),
                sender: Account(nonce=1),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Hash(0x1F4),
        Hash(0x10000),
    ]
    tx_gas = [10000000]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
