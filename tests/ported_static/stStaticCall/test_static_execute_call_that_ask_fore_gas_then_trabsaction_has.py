"""
Test_static_execute_call_that_ask_fore_gas_then_trabsaction_has.

Ported from:
state_tests/stStaticCall/static_ExecuteCallThatAskForeGasThenTrabsactionHasFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
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

TX_DATA = [
    "0000000000000000000000003dc16a13cf554533f380cc938a2c1ab04dac534f",
    "00000000000000000000000073ef1878a0f2c9629dedc1b1e9be8d77dcf93688",
    "000000000000000000000000ce4ccbffaf450ae2126eb96dcd7c891f37764f20",
]
TX_GAS = [100000]
TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    [
        "state_tests/stStaticCall/static_ExecuteCallThatAskForeGasThenTrabsactionHasFiller.json"  # noqa: E501
    ],
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
        pytest.param(
            2,
            0,
            0,
            id="d2",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_static_execute_call_that_ask_fore_gas_then_trabsaction_has(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_execute_call_that_ask_fore_gas_then_trabsaction_has."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xDC4EFA209AECDD4C2D5201A419EA27506151B4EC687F14A613229E310932491B
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0x989680)
    # Source: lll
    # { [[1]] (STATICCALL 600000 (CALLDATALOAD 0) 0 0 0 0) }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x1,
            value=Op.STATICCALL(
                gas=0x927C0,
                address=Op.CALLDATALOAD(offset=0x0),
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
        nonce=0,
        address=Address("0xa256ebcc5536cda56e04c39fe9584ecc7594a438"),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 1 1) }
    addr_0x1000000000000000000000000000000000000001 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x1, value=0x1) + Op.STOP,
        balance=0x186A0,
        nonce=0,
        address=Address("0x3dc16a13cf554533f380cc938a2c1ab04dac534f"),  # noqa: E501
    )
    # Source: lll
    # { (def 'i 0x80) (for {} (< @i 50000) [i](+ @i 1) (EXTCODESIZE 1)) }
    addr_0x2000000000000000000000000000000000000001 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPDEST
        + Op.JUMPI(
            pc=0x1C, condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xC350))
        )
        + Op.POP(Op.EXTCODESIZE(address=0x1))
        + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
        + Op.JUMP(pc=0x0)
        + Op.JUMPDEST
        + Op.STOP,
        balance=0x186A0,
        nonce=0,
        address=Address("0x73ef1878a0f2c9629dedc1b1e9be8d77dcf93688"),  # noqa: E501
    )
    # Source: lll
    # { (SSTORE 1 1) }
    addr_0x3000000000000000000000000000000000000001 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.STOP,
        balance=0x186A0,
        nonce=0,
        address=Address("0xce4ccbffaf450ae2126eb96dcd7c891f37764f20"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [1, 2], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {target: Account(storage={1: 0})},
        },
        {
            "indexes": {"data": [0], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {target: Account(storage={1: 1})},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=target,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        nonce=0,
        gas_price=10,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
