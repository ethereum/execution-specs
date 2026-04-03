"""
Test_call1_mb1024_calldepth.

Ported from:
state_tests/stQuadraticComplexityTest/Call1MB1024CalldepthFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
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


@pytest.mark.ported_from(
    ["state_tests/stQuadraticComplexityTest/Call1MB1024CalldepthFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
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
@pytest.mark.pre_alloc_mutable
def test_call1_mb1024_calldepth(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_call1_mb1024_calldepth."""
    coinbase = Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    addr = Address(0x2AB8257767339461506C0C67824CF17BC77B52CA)
    sender = EOA(
        key=0xE7C72B378297589ACEE4E0BA3272841BCFC5E220F86DE253F890274CFEE9E474
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=882500000000,
    )

    pre[sender] = Account(balance=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
    pre[addr] = Account(balance=0xFFFFFFFFFFFFF)
    # Source: lll
    # { (def 'i 0x80) [[ 0 ]] (+ @@0 1) (if (LT @@0 1024) [[ 1 ]] (CALL (- (GAS) 1005000) <contract:target:0xbbbf5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 1000000 0 0) [[ 2 ]] 1 )  }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
        + Op.JUMPI(pc=0x1B, condition=Op.LT(Op.SLOAD(key=0x0), 0x400))
        + Op.SSTORE(key=0x2, value=0x1)
        + Op.JUMP(pc=0x47)
        + Op.JUMPDEST
        + Op.SSTORE(
            key=0x1,
            value=Op.CALL(
                gas=Op.SUB(Op.GAS, 0xF55C8),
                address=0x9D15232F6851F9F3A88F88A3B358ED1579977A5A,
                value=0x0,
                args_offset=0x0,
                args_size=0xF4240,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.JUMPDEST
        + Op.STOP,
        balance=0xFFFFFFFFFFFFF,
        nonce=0,
        address=Address(0x9D15232F6851F9F3A88F88A3B358ED1579977A5A),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": -1, "gas": 1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                sender: Account(storage={}, code=b"", nonce=1),
                addr: Account(storage={}, code=b"", nonce=0),
                target: Account(storage={0: 69, 1: 1}, nonce=0),
            },
        },
        {
            "indexes": {"data": -1, "gas": 0, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                sender: Account(storage={}, code=b"", nonce=1),
                addr: Account(storage={}, code=b"", nonce=0),
                target: Account(storage={}, nonce=0),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes(""),
    ]
    tx_gas = [150000, 250000000]
    tx_value = [10]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
