"""
test_static_call_goes_oog_on_second_level2

Ported from:
state_tests/stStaticCall/static_CallGoesOOGOnSecondLevel2Filler.json
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
from execution_testing.vm import Op
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)

REFERENCE_SPEC_GIT_PATH = "N/A"

REFERENCE_SPEC_VERSION = "N/A"

TX_DATA = [
    "000000000000000000000000f2774cee95a518a51cd32426d3ce8db19f095b37",
    "00000000000000000000000045e70d14d712a8898dce133fe063f71179f04059",
]
TX_GAS = [160000]
TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_CallGoesOOGOnSecondLevel2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0, 0, 0,
            id="d0",
        ),
        pytest.param(
            1, 0, 0,
            id="d1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_static_call_goes_oog_on_second_level2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """test_static_call_goes_oog_on_second_level2"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x4f31b3206fbf0e0e598b9b1a7d8ac86302a0ff1d8930738f1bebae9b67173e52
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

    pre[sender] = Account(balance=0xe8d4a51000)
    # Source: lll
    # { (MSTORE 0 (CALLDATALOAD 0)) [[ 0 ]] (STATICCALL 600000 <contract:0x1000000000000000000000000000000000000113> 0 32 0 0) [[ 1 ]] 1 }
    target = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0x0))
        + Op.SSTORE(key=0x0, value=Op.STATICCALL(gas=0x927c0, address=0x666ebb8afc7a9ba4bedb7d78f85184b65639531d, args_offset=0x0, args_size=0x20, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x1, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0xb9c1c6c39cb3e528b2ef06493c17d63b7827077b"),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 8 (GAS)) (MSTORE 9 (STATICCALL 600000 (CALLDATALOAD 0) 0 0 0 0)) }
    addr_0x1000000000000000000000000000000000000113 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x8, value=Op.GAS)
        + Op.MSTORE(offset=0x9, value=Op.STATICCALL(gas=0x927c0, address=Op.CALLDATALOAD(offset=0x0), args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.STOP,
        nonce=0,
        address=Address("0x666ebb8afc7a9ba4bedb7d78f85184b65639531d"),  # noqa: E501
    )
    # Source: lll
    # { (SSTORE 1 1) }
    addr_0x1000000000000000000000000000000000000114 = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0xf2774cee95a518a51cd32426d3ce8db19f095b37"),  # noqa: E501
    )
    # Source: lll
    # {  (def 'i 0x80) (for {} (< @i 50000) [i](+ @i 1) (EXTCODESIZE 1))  }
    addr_0x2000000000000000000000000000000000000114 = pre.deploy_contract(
        code=Op.JUMPDEST
        + Op.JUMPI(pc=0x1c, condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xc350)))
        + Op.POP(Op.EXTCODESIZE(address=0x1))
        + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
        + Op.JUMP(pc=0x0) + Op.JUMPDEST + Op.STOP,
        nonce=0,
        address=Address("0x45e70d14d712a8898dce133fe063f71179f04059"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': -1, 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {target: Account(storage={0: 0, 1: 0})},
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
